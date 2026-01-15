"""
Unified Workflow API Views
Provides endpoints for orchestrator-based workflows.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from .orchestrator import orchestrator, WorkflowType
from typing import Dict, Any


class WorkflowSuggestAPIView(APIView):
    """
    Suggest the best workflow based on available context.
    """
    
    @extend_schema(
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'symptoms': {'type': 'array', 'items': {'type': 'string'}},
                    'has_lab_report': {'type': 'boolean'},
                    'has_medications': {'type': 'boolean'},
                    'triage_level': {'type': 'string'},
                    'patient_age': {'type': 'integer'}
                }
            }
        }
    )
    def post(self, request):
        """Suggest workflow based on context."""
        context = request.data
        suggested_workflow = orchestrator.suggest_workflow(context)
        
        return Response({
            "suggested_workflow": suggested_workflow.value,
            "description": _get_workflow_description(suggested_workflow),
            "context": context
        })


class ExecuteWorkflowAPIView(APIView):
    """
    Execute a complete workflow using the orchestrator.
    """
    
    @extend_schema(
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'workflow_type': {
                        'type': 'string',
                        'enum': [wt.value for wt in WorkflowType]
                    },
                    'symptoms': {'type': 'array', 'items': {'type': 'string'}},
                    'text': {'type': 'string'},
                    'lab_report_id': {'type': 'string'},
                    'medications': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'name': {'type': 'string'},
                                'is_new': {'type': 'boolean'}
                            }
                        }
                    },
                    'patient_age': {'type': 'integer'},
                    'conditions': {'type': 'array', 'items': {'type': 'string'}}
                },
                'required': ['workflow_type']
            }
        }
    )
    def post(self, request):
        """Execute a workflow."""
        workflow_type_str = request.data.get('workflow_type')
        
        try:
            workflow_type = WorkflowType(workflow_type_str)
        except ValueError:
            return Response(
                {
                    "error": f"Invalid workflow type: {workflow_type_str}",
                    "available_types": [wt.value for wt in WorkflowType]
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = request.data
        result = orchestrator.execute_workflow(workflow_type, data)
        
        return Response(result, status=status.HTTP_200_OK)


class ComprehensiveCareAPIView(APIView):
    """
    Execute comprehensive care workflow (all modules).
    This is a convenience endpoint for the most common use case.
    """
    
    @extend_schema(
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'symptoms': {'type': 'array', 'items': {'type': 'string'}},
                    'text': {'type': 'string'},
                    'lab_report_id': {'type': 'string'},
                    'medications': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'name': {'type': 'string'},
                                'is_new': {'type': 'boolean'}
                            }
                        }
                    },
                    'patient_age': {'type': 'integer'},
                    'conditions': {'type': 'array', 'items': {'type': 'string'}}
                }
            }
        }
    )
    def post(self, request):
        """Execute comprehensive care workflow."""
        data = request.data
        result = orchestrator.execute_workflow(WorkflowType.COMPREHENSIVE_CARE, data)
        
        return Response(result, status=status.HTTP_200_OK)


def _get_workflow_description(workflow_type: WorkflowType) -> str:
    """Get human-readable description of workflow type."""
    descriptions = {
        WorkflowType.TRIAGE_ONLY: "Simple triage assessment based on symptoms",
        WorkflowType.LAB_ANALYSIS_ONLY: "Lab report analysis without triage",
        WorkflowType.MEDICATION_CHECK_ONLY: "Medication interaction check",
        WorkflowType.INTERVIEW_ONLY: "Patient interview session",
        WorkflowType.COMPREHENSIVE_CARE: "Full patient assessment: Triage → Lab → Medications",
        WorkflowType.TRIAGE_TO_LAB: "Triage assessment followed by lab analysis",
        WorkflowType.TRIAGE_TO_MEDICATION: "Triage assessment followed by medication check",
        WorkflowType.LAB_TO_MEDICATION: "Lab analysis followed by medication check",
        WorkflowType.INTERVIEW_TO_LAB: "Patient interview followed by lab analysis"
    }
    return descriptions.get(workflow_type, "Unknown workflow type")
