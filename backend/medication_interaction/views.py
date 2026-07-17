import json
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from .models import MedicationSession, PatientMedication, InteractionReport
from .agent import medication_interaction_agent
from .serializers import MedicationAnalysisRequestSerializer

logger = logging.getLogger(__name__)

class AnalyzeInteraction(APIView):
    @extend_schema(
        request=MedicationAnalysisRequestSerializer,
        responses={200: InteractionReport}  # You could also make a custom serializer for response
    )
    def post(self, request):
        try:
            serializer = MedicationAnalysisRequestSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data

            # Validate medications are provided
            if not data.get('medications') or len(data['medications']) == 0:
                return Response(
                    {"error": "At least one medication must be provided"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Filter out empty medication names
            valid_medications = [m for m in data['medications'] if m.get('name', '').strip()]
            if not valid_medications:
                return Response(
                    {"error": "Medication names cannot be empty"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 1. Create Session
            session = MedicationSession.objects.create(
                language=data['language'],
                patient_age=data['patient_age'],
                conditions=data['conditions']
            )

            # 2. Save Medications
            for med in valid_medications:
                PatientMedication.objects.create(
                    session=session,
                    med_name=med['name'].strip(),
                    is_new=med['is_new']
                )

            # 3. Call Agent for Reasoning
            logger.info(f"Calling medication interaction agent with {len(valid_medications)} medications")
            try:
                analysis = medication_interaction_agent(
                    {"age": data['patient_age'], "conditions": data['conditions']},
                    valid_medications
                )
                logger.info(f"Agent returned analysis with keys: {list(analysis.keys()) if isinstance(analysis, dict) else 'Not a dict'}")
                logger.info(f"Agent severity: {analysis.get('severity') if isinstance(analysis, dict) else 'N/A'}")
            except Exception as e:
                logger.error(f"Error calling medication interaction agent: {str(e)}", exc_info=True)
                return Response(
                    {"error": f"Failed to analyze medication interactions: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Validate agent response
            if not analysis or not isinstance(analysis, dict):
                logger.error(f"Invalid agent response: {analysis} (type: {type(analysis)})")
                return Response(
                    {"error": "Invalid response from medication interaction agent"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # 4. Save and Return Report
            report = InteractionReport.objects.create(
                session=session,
                severity=analysis.get('severity', 'MINOR'),
                raw_analysis=json.dumps(analysis.get('findings', [])),  # store findings as string
                soap_note=analysis.get('soap_note', '')
            )
            
            # Ensure findings is always a list
            findings = analysis.get('findings', [])
            if isinstance(findings, str):
                try:
                    findings = json.loads(findings)
                except:
                    findings = [findings]
            
            # Ensure interaction_graph is always a dict
            interaction_graph = analysis.get("interaction_graph", {})
            if not isinstance(interaction_graph, dict):
                interaction_graph = {}
            
            response_data = {
                "report_id": report.id,
                "severity": report.severity,
                "interaction_graph": interaction_graph,
                "findings": findings if isinstance(findings, list) else [],
                "soap_note": report.soap_note or analysis.get('soap_note', '')
            }
            
            # Log response details for debugging
            response_size = len(json.dumps(response_data))
            logger.info(f"Medication interaction analysis completed successfully for session {session.id}")
            logger.info(f"Response data size: {response_size} bytes")
            logger.info(f"Response severity: {response_data['severity']}")
            logger.info(f"Response findings count: {len(response_data['findings'])}")
            logger.info(f"Response interaction_graph keys: {list(response_data['interaction_graph'].keys()) if isinstance(response_data['interaction_graph'], dict) else 'Not a dict'}")
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Unexpected error in medication interaction analysis: {str(e)}", exc_info=True)
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )