"""
Conversational Interface for Orchestrator
Provides a chat-like interface where patients can interact naturally,
and the orchestrator guides them through the appropriate workflows.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from .orchestrator import orchestrator, WorkflowType
from .advanced_orchestrator import advanced_orchestrator
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class ConversationSession:
    """Manages conversation state for a patient session."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.messages = []
        self.symptoms = []
        self.context = {
            "has_lab_report": False,
            "has_medications": False,
            "triage_level": None,
            "patient_age": None,
            "conditions": []
        }
        self.current_workflow = None
        self.lab_report_id = None
        self.medications = []
        self.stage = "greeting"  # greeting, collecting_info, triage, workflow_execution, completed
    
    def add_message(self, role: str, content: str):
        """Add a message to the conversation."""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": None  # Can add timestamp if needed
        })
    
    def update_context(self, **kwargs):
        """Update conversation context."""
        self.context.update(kwargs)
    
    def to_dict(self):
        """Convert session to dictionary for storage."""
        return {
            "session_id": self.session_id,
            "messages": self.messages,
            "symptoms": self.symptoms,
            "context": self.context,
            "current_workflow": self.current_workflow.value if self.current_workflow else None,
            "lab_report_id": self.lab_report_id,
            "medications": self.medications,
            "stage": self.stage
        }


# In-memory session storage (in production, use Redis or database)
conversation_sessions: Dict[str, ConversationSession] = {}


class StartConversationAPIView(APIView):
    """
    Start a new conversational session with the orchestrator.
    """
    
    @extend_schema(
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'patient_age': {'type': 'integer'},
                    'initial_message': {'type': 'string'}
                }
            }
        }
    )
    def post(self, request):
        """Start a new conversation."""
        import uuid
        
        session_id = str(uuid.uuid4())
        session = ConversationSession(session_id)
        
        # Set initial context if provided
        if 'patient_age' in request.data:
            session.context['patient_age'] = request.data['patient_age']
            session.update_context(patient_age=request.data['patient_age'])
        
        # Generate natural, human-like greeting using AI
        greeting = self._generate_natural_greeting()
        
        session.add_message("assistant", greeting)
        conversation_sessions[session_id] = session
        
        return Response({
            "session_id": session_id,
            "message": greeting,
            "stage": session.stage
        })
    
    def _generate_natural_greeting(self) -> str:
        """Generate a natural, human-like greeting using AI."""
        try:
            from interviews.agent import initial_greeting
            # Use AI to generate a natural greeting
            greeting = initial_greeting(language="English")
            return greeting
        except Exception as e:
            logger.error(f"Error generating greeting: {e}")
            # Fallback to natural greeting
            return "Hi there! I'm here to help you with your health concerns. What's going on today?"


class ContinueConversationAPIView(APIView):
    """
    Continue an existing conversation.
    The orchestrator intelligently guides the conversation and executes workflows.
    """
    
    @extend_schema(
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'session_id': {'type': 'string'},
                    'message': {'type': 'string'},
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
                    }
                },
                'required': ['session_id', 'message']
            }
        }
    )
    def post(self, request):
        """Process user message and respond intelligently."""
        session_id = request.data.get('session_id')
        user_message = request.data.get('message', '').strip()
        
        if not session_id or session_id not in conversation_sessions:
            return Response(
                {"error": "Invalid or expired session. Please start a new conversation."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        session = conversation_sessions[session_id]
        session.add_message("user", user_message)
        
        # Use Advanced Orchestrator for real-time conversation flow
        # It handles: language detection, safety agent, triage, documentation, interview agents
        try:
            result = advanced_orchestrator.process_message(session.session_id, user_message)
            
            # Extract symptoms from result
            context = result.get("context", {})
            if context.get("symptoms"):
                session.symptoms.extend(context["symptoms"])
                session.symptoms = list(set(session.symptoms))
            
            # Update language if detected
            if context.get("language"):
                session.language = context["language"]
            
            # Get response message
            response_message = result.get("message", "")
            
            # Add follow-up question if available
            if result.get("follow_up_question"):
                response_message += f"\n\n{result.get('follow_up_question')}"
            
            # Handle immediate emergency
            if result.get("urgency") == "IMMEDIATE":
                if result.get("action_required"):
                    response_message = f"🚨 {result.get('action_required')}\n\n{response_message}"
                session.stage = "triage"
                session.add_message("assistant", response_message)
                return Response({
                    "session_id": session_id,
                    "message": response_message,
                    "stage": session.stage,
                    "symptoms": session.symptoms,
                    "urgency": "IMMEDIATE",
                    "action_required": result.get("action_required"),
                    "context": context
                })
            
            # Normal flow
            next_stage = "triage" if result.get("urgency") in ["VERY_URGENT", "URGENT"] else session.stage
            session.stage = next_stage
            session.add_message("assistant", response_message)
            
            return Response({
                "session_id": session_id,
                "message": response_message,
                "stage": session.stage,
                "symptoms": session.symptoms,
                "suggested_workflow": session.current_workflow.value if session.current_workflow else None,
                "urgency": result.get("urgency", "STANDARD"),
                "context": context
            })
        
        except Exception as e:
            logger.error(f"Error in advanced orchestrator: {str(e)}")
            # Fallback to original processing
            if session.stage in ["greeting", "collecting_info"]:
                extracted_symptoms = orchestrator.symptom_extractor.extract(user_message)
                if extracted_symptoms:
                    session.symptoms.extend(extracted_symptoms)
                    session.symptoms = list(set(session.symptoms))
            
            response_message, next_stage = self._process_message_fallback(session, user_message)
            session.stage = next_stage
            session.add_message("assistant", response_message)
            
            return Response({
                "session_id": session_id,
                "message": response_message,
                "stage": session.stage,
                "symptoms": session.symptoms,
                "suggested_workflow": session.current_workflow.value if session.current_workflow else None,
                "context": session.context
            })
    
    def _process_message(self, session: ConversationSession, user_message: str) -> tuple[str, str]:
        """Process user message using advanced orchestrator."""
        
        # Use advanced orchestrator for real-time conversation flow
        try:
            result = advanced_orchestrator.process_message(session.session_id, user_message)
            
            # Handle immediate emergency
            if result.get("urgency") == "IMMEDIATE":
                response_parts = []
                
                # Emergency message
                response_parts.append(result.get("message", ""))
                
                # Action required
                if result.get("action_required"):
                    response_parts.append(f"\n\n**{result.get('action_required')}**")
                
                # Follow-up question
                if result.get("follow_up_question"):
                    response_parts.append(f"\n\n{result.get('follow_up_question')}")
                
                # Update session context
                context = result.get("context", {})
                if context.get("symptoms"):
                    session.symptoms.extend(context["symptoms"])
                    session.symptoms = list(set(session.symptoms))
                
                if context.get("language"):
                    session.language = context["language"]
                
                return "\n".join(response_parts), "triage"
            
            # Handle normal flow
            response_parts = []
            
            # Main message
            if result.get("message"):
                response_parts.append(result.get("message"))
            
            # Follow-up question
            if result.get("follow_up_question"):
                response_parts.append(f"\n\n{result.get('follow_up_question')}")
            
            # Update session
            context = result.get("context", {})
            if context.get("symptoms"):
                session.symptoms.extend(context["symptoms"])
                session.symptoms = list(set(session.symptoms))
            
            if context.get("language"):
                session.language = context["language"]
            
            urgency = result.get("urgency", "STANDARD")
            if urgency in ["IMMEDIATE", "VERY_URGENT"]:
                return "\n".join(response_parts), "triage"
            else:
                return "\n".join(response_parts) if response_parts else "How can I help you further?", "triage"
        
        except Exception as e:
            logger.error(f"Error in advanced orchestrator: {str(e)}")
            # Fallback to original logic
            return self._process_message_fallback(session, user_message)
    
    def _process_message_fallback(self, session: ConversationSession, user_message: str) -> tuple[str, str]:
        """Fallback message processing (original logic)."""
        
        # Stage 1: Greeting - Extract initial information
        if session.stage == "greeting":
            if session.symptoms:
                # Move to triage stage
                return self._perform_triage(session)
            else:
                return (
                    "I understand you're looking for help. Could you please describe your symptoms "
                    "or what medical assistance you need? For example: 'I have chest pain and shortness of breath' "
                    "or 'I need to check my lab report'.",
                    "collecting_info"
                )
        
        # Stage 2: Collecting Info - Gather more information
        elif session.stage == "collecting_info":
            if session.symptoms:
                return self._perform_triage(session)
            else:
                return (
                    "I'm here to help! Please describe:\n"
                    "• Your symptoms (e.g., 'chest pain', 'fever', 'headache')\n"
                    "• If you have a lab report to analyze\n"
                    "• If you're taking any medications\n\n"
                    "The more information you provide, the better I can assist you.",
                    "collecting_info"
                )
        
        # Stage 3: After Triage - Suggest and execute workflows
        elif session.stage == "triage":
            # Suggest workflow based on available context
            suggested_workflow = orchestrator.suggest_workflow(session.context)
            session.current_workflow = suggested_workflow
            
            response_parts = []
            
            # Check what user wants to do next
            user_lower = user_message.lower()
            
            if any(word in user_lower for word in ["lab", "report", "test", "results"]):
                if session.lab_report_id:
                    return self._execute_workflow(session, suggested_workflow)
                else:
                    return (
                        "I can help analyze your lab report! Please upload your lab report, "
                        "and I'll provide a detailed analysis. You can also tell me if you have "
                        "medications to check for interactions.",
                        "triage"
                    )
            
            elif any(word in user_lower for word in ["medication", "drug", "medicine", "pill"]):
                if session.medications:
                    return self._execute_workflow(session, suggested_workflow)
                else:
                    return (
                        "I can check for medication interactions! Please tell me:\n"
                        "• What medications you're currently taking\n"
                        "• If any are new medications\n"
                        "• Your age and any medical conditions\n\n"
                        "For example: 'I take Aspirin and Ibuprofen, and I have CKD Stage 3'",
                        "triage"
                    )
            
            elif any(word in user_lower for word in ["yes", "okay", "sure", "proceed", "go ahead"]):
                return self._execute_workflow(session, suggested_workflow)
            
            else:
                # Provide options based on suggested workflow
                workflow_desc = self._get_workflow_description(suggested_workflow)
                return (
                    f"Based on your symptoms, I recommend: **{workflow_desc}**\n\n"
                    "Would you like me to:\n"
                    "• Analyze a lab report (if you have one)\n"
                    "• Check medication interactions\n"
                    "• Provide a comprehensive assessment\n\n"
                    "Just let me know what you'd like to do next, or say 'yes' to proceed with my recommendation.",
                    "triage"
                )
        
        # Stage 4: Workflow Execution - Provide results
        elif session.stage == "workflow_execution":
            return (
                "I've completed the analysis. Is there anything else you'd like me to help with? "
                "You can ask about:\n"
                "• More details about the results\n"
                "• Additional tests or checks\n"
                "• Next steps or recommendations",
                "completed"
            )
        
        # Default response
        return (
            "I'm here to help! Please describe your symptoms or what you need assistance with.",
            session.stage
        )
    
    def _perform_triage(self, session: ConversationSession) -> tuple[str, str]:
        """Perform triage assessment."""
        if not session.symptoms:
            return (
                "I need to understand your symptoms better. Could you please describe what you're experiencing?",
                "collecting_info"
            )
        
        triage_result = orchestrator.handle_triage(session.symptoms)
        triage_level = triage_result.get("triage", "STANDARD")
        message = triage_result.get("messages", [""])[0] if triage_result.get("messages") else ""
        
        session.context['triage_level'] = str(triage_level)
        
        # Format response based on urgency
        if triage_level in ["IMMEDIATE", "VERY_URGENT"]:
            response = (
                f"🚨 **URGENT ASSESSMENT**\n\n"
                f"{message}\n\n"
                f"**Your Symptoms:** {', '.join(session.symptoms)}\n"
                f"**Priority Level:** {triage_level}\n\n"
                "I strongly recommend immediate medical attention. Would you like me to:\n"
                "• Analyze any lab reports you have\n"
                "• Check your medications for interactions\n"
                "• Provide a comprehensive assessment"
            )
        else:
            response = (
                f"**Triage Assessment Complete**\n\n"
                f"{message}\n\n"
                f"**Your Symptoms:** {', '.join(session.symptoms)}\n"
                f"**Priority Level:** {triage_level}\n\n"
                "How would you like to proceed?\n"
                "• Analyze a lab report\n"
                "• Check medication interactions\n"
                "• Get a comprehensive assessment"
            )
        
        return response, "triage"
    
    def _execute_workflow(self, session: ConversationSession, workflow_type: WorkflowType) -> tuple[str, str]:
        """Execute the suggested workflow."""
        # Prepare data for workflow execution
        workflow_data = {
            "symptoms": session.symptoms,
            "text": " ".join(session.messages[-3:]) if len(session.messages) >= 3 else ""
        }
        
        if session.lab_report_id:
            workflow_data["lab_report_id"] = session.lab_report_id
        
        if session.medications:
            workflow_data["medications"] = session.medications
        
        if session.context.get("patient_age"):
            workflow_data["patient_age"] = session.context["patient_age"]
        
        if session.context.get("conditions"):
            workflow_data["conditions"] = session.context["conditions"]
        
        # Execute workflow
        try:
            result = orchestrator.execute_workflow(workflow_type, workflow_data)
            
            # Format response based on workflow results
            response = self._format_workflow_results(result, workflow_type)
            
            return response, "workflow_execution"
        
        except Exception as e:
            logger.error(f"Error executing workflow: {str(e)}")
            return (
                f"I encountered an error while processing your request: {str(e)}\n\n"
                "Please try again or provide more information.",
                session.stage
            )
    
    def _format_workflow_results(self, result: Dict[str, Any], workflow_type: WorkflowType) -> str:
        """Format workflow results into a user-friendly message."""
        if result.get("error"):
            return f"❌ Error: {result['error']}"
        
        final_result = result.get("final_result", {})
        response_parts = []
        
        # Add triage results if available
        if "triage" in final_result:
            triage = final_result["triage"]
            triage_level = triage.get("triage", "STANDARD")
            triage_msg = triage.get("messages", [""])[0] if triage.get("messages") else ""
            response_parts.append(f"**Triage Assessment:** {triage_level}\n{triage_msg}")
        
        # Add lab analysis results if available
        if "lab_analysis" in final_result:
            lab = final_result["lab_analysis"]
            if lab.get("critical_findings"):
                response_parts.append(
                    f"🚨 **Critical Lab Findings:** {len(lab['critical_findings'])} critical values detected"
                )
            if lab.get("abnormal_findings"):
                response_parts.append(
                    f"⚠️ **Abnormal Lab Values:** {len(lab['abnormal_findings'])} abnormalities found"
                )
        
        # Add medication interaction results if available
        if "medication_interactions" in final_result:
            med = final_result["medication_interactions"]
            severity = med.get("severity", "MINOR")
            if severity in ["CONTRAINDICATED", "MAJOR"]:
                response_parts.append(
                    f"🚨 **Medication Alert:** {severity} interactions detected"
                )
            else:
                response_parts.append(
                    f"✅ **Medication Check:** {severity} interactions found"
                )
        
        # Add comprehensive assessment if available
        if "comprehensive_assessment" in final_result:
            assessment = final_result["comprehensive_assessment"]
            response_parts.append(
                f"\n**Overall Assessment:**\n"
                f"• Urgency: {assessment.get('overall_urgency', 'STANDARD')}\n"
                f"• Key Findings: {', '.join(assessment.get('key_findings', []))}\n"
                f"• Recommendations: {', '.join(assessment.get('recommendations', []))}"
            )
        
        # Add combined assessment if available
        if "combined_assessment" in final_result:
            combined = final_result["combined_assessment"]
            response_parts.append(
                f"\n**Combined Assessment:**\n"
                f"{combined.get('message', '')}\n"
                f"Recommendations: {', '.join(combined.get('recommendations', []))}"
            )
        
        if not response_parts:
            return "✅ Analysis complete. Please review the detailed results."
        
        return "\n\n".join(response_parts)
    
    def _get_workflow_description(self, workflow_type: WorkflowType) -> str:
        """Get human-readable workflow description."""
        descriptions = {
            WorkflowType.TRIAGE_ONLY: "Triage Assessment",
            WorkflowType.TRIAGE_TO_LAB: "Triage + Lab Analysis",
            WorkflowType.TRIAGE_TO_MEDICATION: "Triage + Medication Check",
            WorkflowType.COMPREHENSIVE_CARE: "Comprehensive Assessment",
            WorkflowType.LAB_TO_MEDICATION: "Lab Analysis + Medication Check"
        }
        return descriptions.get(workflow_type, "Medical Assessment")


class GetConversationHistoryAPIView(APIView):
    """Get conversation history for a session."""
    
    def get(self, request, session_id):
        """Retrieve conversation history."""
        if session_id not in conversation_sessions:
            return Response(
                {"error": "Session not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        session = conversation_sessions[session_id]
        return Response(session.to_dict())
