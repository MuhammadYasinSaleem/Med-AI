from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from .models import InterviewSession, QuestionAnswer, ClinicalSummary
from .agent import generate_next_question, reasoning_agent_gemini, initial_greeting, should_stop_interview, generate_pdf, PREDEFINED_QUESTIONS
from .serializers import (
    StartInterviewRequestSerializer,
    SubmitAnswerRequestSerializer,
    GenerateSummaryRequestSerializer,
    TriageRequestSerializer,
    TriageResponseSerializer
)
from django.utils import timezone
from datetime import timedelta
from django.core.files.base import ContentFile
from django.http import FileResponse, Http404
from django.conf import settings
import os

MIN_QUESTIONS = 5
CHECK_EVERY = 3
MAX_CONTEXT = 5

from .orchestrator import Orchestrator
from .symptom_extractor import SymptomExtractor

CLINICAL_FIELDS = {
    "age": {
        "English": ["year", "age"],
        "Roman Urdu": ["saal", "umar"],
        "Urdu": ["سال", "عمر"]
    },
    "duration": {
        "English": ["day", "week", "month", "since"],
        "Roman Urdu": ["din", "haftay", "mahine", "se"],
        "Urdu": ["دن", "ہفتے", "مہینے", "سے"]
    },
    "severity": {
        "English": ["mild", "moderate", "severe", "scale", "pain"],
        "Roman Urdu": ["tez", "zyada", "kam", "dard", "shiddat"],
        "Urdu": ["شدید", "ہلکا", "درد", "زیادہ"]
    },
    "location": {
        "English": ["left", "right", "side", "where"],
        "Roman Urdu": ["jaga", "left", "right", "side"],
        "Urdu": ["جگہ", "بائیں", "دائیں"]
    },
    "associated": {
        "English": ["fever", "nausea", "vomit", "cough", "fatigue"],
        "Roman Urdu": ["bukhar", "ulti", "khansi", "kamzori"],
        "Urdu": ["بخار", "الٹی", "کھانسی", "کمزوری"]
    },
    "red_flags": {
        "English": ["chest", "breath", "bleeding", "faint"],
        "Roman Urdu": ["seena", "saans", "bleeding", "behosh"],
        "Urdu": ["سینہ", "سانس", "خون", "بے ہوش"]
    }
}

RULE_BASED_QUESTIONS = {
    "severity": {
        "English": "How severe are your symptoms on a scale of 1 to 10?",
        "Roman Urdu": "Dard ya symptoms ki shiddat 1 se 10 tak kitni hai?",
        "Urdu": "آپ کی علامات کی شدت 1 سے 10 تک کتنی ہے؟"
    },
    "location": {
        "English": "Where exactly do you feel the problem?",
        "Roman Urdu": "Masla kis jagah mehsoos hota hai?",
        "Urdu": "مسئلہ کہاں محسوس ہوتا ہے؟"
    },
    "associated": {
        "English": "Do you have any other symptoms like fever, nausea, or weakness?",
        "Roman Urdu": "Kya bukhar, ulti ya kamzori bhi hai?",
        "Urdu": "کیا بخار، الٹی یا کمزوری بھی ہے؟"
    },
    "red_flags": {
        "English": "Are you experiencing chest pain, breathing difficulty, or bleeding?",
        "Roman Urdu": "Kya seene mein dard, saans ka masla ya bleeding ho rahi hai?",
        "Urdu": "کیا سینے میں درد، سانس کی تکلیف یا خون بہہ رہا ہے؟"
    }
}


def detect_covered_fields(responses, language):
    text = " ".join(responses).lower()
    covered = set()

    for field, lang_map in CLINICAL_FIELDS.items():
        keywords = lang_map.get(language, lang_map["English"])
        if any(k.lower() in text for k in keywords):
            covered.add(field)

    return covered

# Initialize extractor and orchestrator
extractor = SymptomExtractor()
orchestrator = Orchestrator()

class StartInterview(APIView):

    @extend_schema(request=StartInterviewRequestSerializer)
    def post(self, request):
        serializer = StartInterviewRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        language = serializer.validated_data.get("language", "English")
        session = InterviewSession.objects.create(language=language)

        greeting = initial_greeting(language=language)

        # STORE agent greeting as unanswered question
        QuestionAnswer.objects.create(
            session=session,
            question=greeting,
            answer=""
        )

        return Response({
            "session_id": session.id,
            "agent_message": greeting
        })


class SubmitAnswer(APIView):

    @extend_schema(request=SubmitAnswerRequestSerializer)
    def post(self, request):
        serializer = SubmitAnswerRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        session_id = serializer.validated_data["session_id"]
        answer_text = serializer.validated_data["answer"].strip()

        if not answer_text:
            return Response({"error": "Answer cannot be empty"}, status=400)

        try:
            session = InterviewSession.objects.get(id=session_id)
        except InterviewSession.DoesNotExist:
            return Response({"error": "Invalid session ID"}, status=404)

        # Time limit
        if timezone.now() - session.started_at > timedelta(minutes=15):
            return Response({"next_step": "generate_summary"})

        # Save answer
        qa = QuestionAnswer.objects.filter(session=session, answer="").first()
        if not qa:
            return Response({"error": "No pending question"}, status=400)

        qa.answer = answer_text
        qa.save()

        # Fetch conversation
        answered_qs = QuestionAnswer.objects.filter(
            session=session
        ).exclude(answer="").order_by("created_at")

        responses = list(answered_qs.values_list("answer", flat=True))
        asked_questions = set(answered_qs.values_list("question", flat=True))

        # Clinical coverage detection
        covered = detect_covered_fields(responses, session.language)

        # Ask rule-based missing clinical questions FIRST
        for field, lang_questions in RULE_BASED_QUESTIONS.items():
            question = lang_questions.get(session.language, lang_questions["English"])

            if field not in covered and question not in asked_questions:
                QuestionAnswer.objects.create(
                    session=session,
                    question=question,
                    answer=""
                )
                return Response({"next_question": question})

        # HARD STOP if enough info
        if len(covered) >= 4:
            return Response({
                "message": "Interview complete",
                "next_step": "generate_summary"
            })

        # AI follow-up (only if really needed)
        conversation = [
            f"Q: {q.question}\nA: {q.answer}"
            for q in answered_qs
        ]

        ai_question = generate_next_question(
            conversation,
            language=session.language
        )

        # Semantic repetition guard
        if any(q.lower() in ai_question.lower() for q in asked_questions):
            return Response({
                "message": "Interview complete",
                "next_step": "generate_summary"
            })

        QuestionAnswer.objects.create(
            session=session,
            question=ai_question,
            answer=""
        )

        return Response({"next_question": ai_question})


class GenerateSummary(APIView):

    @extend_schema(request=GenerateSummaryRequestSerializer)
    def post(self, request):
        serializer = GenerateSummaryRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        session_id = serializer.validated_data["session_id"]

        try:
            session = InterviewSession.objects.get(id=session_id)
        except InterviewSession.DoesNotExist:
            return Response(
                {"error": "Invalid session ID"},
                status=status.HTTP_404_NOT_FOUND
            )

        answers_qs = QuestionAnswer.objects.filter(session=session).order_by("created_at")

        if not answers_qs.exists():
            return Response(
                {"error": "No answers found for this session"},
                status=status.HTTP_400_BAD_REQUEST
            )

        responses = list(answers_qs.values_list("answer", flat=True))

        soap_note = reasoning_agent_gemini(
            responses,
            language=session.language
        )

        summary, created = ClinicalSummary.objects.get_or_create(
            session=session,
            defaults={"soap_note": soap_note}
        )

        if not created:
            summary.soap_note = soap_note
            summary.save()

        pdf_buffer = generate_pdf(summary.soap_note)

        summary.pdf.save(
            f"session_{session.id}_soap.pdf",
            ContentFile(pdf_buffer.read()),
            save=True
        )

        session.completed = True
        session.save()

        # Return API endpoint URL instead of direct media URL
        pdf_url = f"/medai/interview/pdf/{session.id}/"
        
        return Response({
            "soap_note": summary.soap_note,
            "pdf_url": pdf_url,
            "session_completed": True
        })
        
    
# ===============================
# Triage API
# ===============================
class TriageAPIView(GenericAPIView):
    serializer_class = TriageRequestSerializer

    @extend_schema(
        request=TriageRequestSerializer,
        responses=TriageResponseSerializer
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_text = serializer.validated_data["text"]

        # Extract symptoms using SymptomExtractor
        symptoms = extractor.extract(user_text)

        if not symptoms:
            # No symptoms detected
            response_data = {
                "triage": "STANDARD",
                "message": "No identifiable symptoms reported."
            }
            return Response(TriageResponseSerializer(response_data).data, status=status.HTTP_200_OK)

        # Route to orchestrator (triage_patient)
        result = orchestrator.handle_triage(symptoms)

        # Handle TriageLevel enum conversion
        triage_level = result.get("triage")
        if triage_level:
            # If it's a TriageLevel enum, get its name; otherwise use the string value
            if hasattr(triage_level, 'name'):
                triage_str = triage_level.name
            else:
                triage_str = str(triage_level)
        else:
            triage_str = "STANDARD"

        # Get message from messages list or use empty string
        messages = result.get("messages", [])
        message = messages[0] if messages else "No specific message available."

        response_data = {
            "triage": triage_str,
            "message": message
        }

        return Response(TriageResponseSerializer(response_data).data, status=status.HTTP_200_OK)


# ===============================
# PDF Download View
# ===============================
class DownloadPDF(APIView):
    """
    Serve PDF files for interview summaries
    """
    def get(self, request, session_id):
        try:
            summary = ClinicalSummary.objects.get(session_id=session_id)
            if not summary.pdf:
                return Response(
                    {"error": "PDF not found for this session"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get the file path
            file_path = summary.pdf.path
            
            if not os.path.exists(file_path):
                return Response(
                    {"error": "PDF file does not exist"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Serve the file with proper headers
            # FileResponse will automatically close the file when done
            file_handle = open(file_path, 'rb')
            response = FileResponse(
                file_handle,
                content_type='application/pdf',
                as_attachment=False  # Display inline in browser
            )
            response['Content-Disposition'] = f'inline; filename="{os.path.basename(file_path)}"'
            response['Content-Length'] = os.path.getsize(file_path)
            return response
        except ClinicalSummary.DoesNotExist:
            return Response(
                {"error": "Session summary not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"Error serving PDF: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )