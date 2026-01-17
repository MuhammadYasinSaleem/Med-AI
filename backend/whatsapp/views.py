from rest_framework.views import APIView
from django.http import HttpResponse

from twilio.twiml.messaging_response import MessagingResponse

from interviews.orchestrator import Orchestrator
from interviews.symptom_extractor import SymptomExtractor


orchestrator = Orchestrator()
extractor = SymptomExtractor()


class WhatsAppWebhook(APIView):
    """
    Twilio WhatsApp webhook.
    Receives incoming WhatsApp messages and returns TwiML.
    """

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        # Twilio sends x-www-form-urlencoded, use request.POST
        user_message = request.POST.get("Body", "").strip()

        response = MessagingResponse()

        if not user_message:
            response.message(
                "Please describe your symptoms so I can help you."
            )
            return HttpResponse(str(response), content_type="application/xml")

        # Extract symptoms (language preserved)
        symptoms = extractor.extract(user_message)

        if not symptoms:
            response.message(
                "I couldn't clearly identify symptoms. "
                "Please describe how you're feeling."
            )
            return HttpResponse(
                str(response),
                content_type="application/xml"
            )

        # Run triage
        result = orchestrator.handle_triage(symptoms)

        # Prepare reply
        message = result.get("messages", [""])[0]

        response.message(message)

        return HttpResponse(
            str(response),
            content_type="application/xml"
        )
