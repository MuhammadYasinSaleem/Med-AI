from rest_framework import serializers
from .models import InterviewSession, QuestionAnswer, ClinicalSummary

class InterviewSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewSession
        fields = '__all__'

class QuestionAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionAnswer
        fields = '__all__'

class ClinicalSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicalSummary
        fields = '__all__'

class StartInterviewRequestSerializer(serializers.Serializer):
    language = serializers.CharField(required=False, default="English")

class SubmitAnswerRequestSerializer(serializers.Serializer):
    session_id = serializers.IntegerField()
    answer = serializers.CharField()

class GenerateSummaryRequestSerializer(serializers.Serializer):
    session_id = serializers.IntegerField()

class TriageRequestSerializer(serializers.Serializer):
    """
    Incoming request from frontend.
    User can type freely in natural language describing symptoms.
    """
    text = serializers.CharField(
        max_length=2000,
        help_text="User-described symptoms in natural language"
    )


class TriageResponseSerializer(serializers.Serializer):
    """
    Response sent back to frontend.
    No diagnoses exposed.
    """
    triage = serializers.CharField(
        help_text="Triage level: IMMEDIATE / VERY_URGENT / URGENT / STANDARD"
    )
    message = serializers.CharField(
        help_text="Layman-friendly actionable message for the patient"
    )