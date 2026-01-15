"""
Advanced Orchestrator with Real-Time Conversation Flow Control
Manages multi-agent conversations with context, urgency, and language detection.
Uses AI to generate natural, human-like responses.
"""
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from datetime import datetime
import logging
import google.generativeai as genai
from django.conf import settings

logger = logging.getLogger(__name__)

# Configure Gemini for natural conversation
try:
    api_key = getattr(settings, 'GEMINI_API_KEY', None) or getattr(settings, 'GOOGLE_API_KEY', None) or 'AIzaSyB8tF9bjsK1hNpzIG74uBOSIQKs77VGx9g'
    if api_key:
        genai.configure(api_key=api_key)
except Exception as e:
    logger.error(f"Failed to configure Gemini API: {e}")


class ConversationState(Enum):
    """States of the conversation."""
    INITIAL = "initial"
    COLLECTING_SYMPTOMS = "collecting_symptoms"
    TRIAGE_ASSESSMENT = "triage_assessment"
    DETAILED_INTERVIEW = "detailed_interview"
    DOCUMENTATION = "documentation"
    FOLLOW_UP = "follow_up"
    COMPLETED = "completed"


class UrgencyLevel(Enum):
    """Urgency levels."""
    IMMEDIATE = "IMMEDIATE"  # Call 1122 NOW
    VERY_URGENT = "VERY_URGENT"  # ER within 1 hour
    URGENT = "URGENT"  # ER within 2-4 hours
    STANDARD = "STANDARD"  # Routine care


class AgentType(Enum):
    """Types of agents in the system."""
    SAFETY_AGENT = "safety_agent"  # Detects emergencies
    TRIAGE_AGENT = "triage_agent"  # Assesses urgency
    DOCUMENTATION_AGENT = "documentation_agent"  # Creates SOAP notes
    INTERVIEW_AGENT = "interview_agent"  # Asks follow-up questions
    LANGUAGE_AGENT = "language_agent"  # Detects and manages language


class ConversationContext:
    """Maintains conversation context and state."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.language = "English"  # Default, will be detected
        self.detected_language = None
        self.urgency_level = UrgencyLevel.STANDARD
        self.state = ConversationState.INITIAL
        self.symptoms = []
        self.patient_responses = []
        self.agent_actions = []
        self.soap_note = {}
        self.progress = {
            "symptoms_collected": False,
            "triage_complete": False,
            "documentation_started": False,
            "follow_up_questions": []
        }
        self.conflicts = []
        self.timestamp = datetime.now()
    
    def add_symptom(self, symptom: str):
        """Add symptom to context."""
        if symptom not in self.symptoms:
            self.symptoms.append(symptom)
    
    def add_response(self, response: str):
        """Add patient response."""
        self.patient_responses.append({
            "text": response,
            "timestamp": datetime.now(),
            "language": self.language
        })
    
    def add_agent_action(self, agent: AgentType, action: str, result: Any):
        """Log agent action."""
        self.agent_actions.append({
            "agent": agent.value,
            "action": action,
            "result": result,
            "timestamp": datetime.now()
        })
    
    def escalate_urgency(self, new_level: UrgencyLevel):
        """Escalate urgency level."""
        urgency_order = {
            UrgencyLevel.IMMEDIATE: 4,
            UrgencyLevel.VERY_URGENT: 3,
            UrgencyLevel.URGENT: 2,
            UrgencyLevel.STANDARD: 1
        }
        if urgency_order.get(new_level, 0) > urgency_order.get(self.urgency_level, 0):
            self.urgency_level = new_level
            return True
        return False
    
    def detect_conflict(self, new_info: Dict[str, Any]) -> bool:
        """Detect conflicts in information."""
        # Example: If patient says "no pain" but earlier said "severe pain"
        if "pain" in str(new_info).lower():
            for response in self.patient_responses:
                if "no pain" in response["text"].lower() and "severe pain" in str(self.symptoms).lower():
                    self.conflicts.append({
                        "type": "contradiction",
                        "old": "severe pain",
                        "new": "no pain",
                        "timestamp": datetime.now()
                    })
                    return True
        return False


class AdvancedOrchestrator:
    """
    Advanced orchestrator with real-time conversation flow control.
    
    Responsibilities:
    - Conversation Flow Control: Decides which agent speaks next
    - Context Maintenance: Remembers patient history
    - Urgency Management: Escalates/de-escalates based on symptoms
    - Language Bridging: Ensures consistent language
    - Progress Tracking: Knows what information has been gathered
    - Conflict Resolution: Handles contradictory information
    """
    
    def __init__(self):
        self.contexts: Dict[str, ConversationContext] = {}
        self._triage_orchestrator = None
        self._symptom_extractor = None
        self._language_detector = None
    
    def get_context(self, session_id: str) -> ConversationContext:
        """Get or create conversation context."""
        if session_id not in self.contexts:
            self.contexts[session_id] = ConversationContext(session_id)
        return self.contexts[session_id]
    
    @property
    def triage_orchestrator(self):
        """Lazy load triage orchestrator."""
        if self._triage_orchestrator is None:
            from interviews.orchestrator import Orchestrator as TriageOrchestrator
            self._triage_orchestrator = TriageOrchestrator()
        return self._triage_orchestrator
    
    @property
    def symptom_extractor(self):
        """Lazy load symptom extractor."""
        if self._symptom_extractor is None:
            from interviews.symptom_extractor import SymptomExtractor
            self._symptom_extractor = SymptomExtractor()
        return self._symptom_extractor
    
    def detect_language(self, text: str) -> str:
        """
        Detect language from patient message.
        Returns: Language code (en, ur, pa, ps, sd)
        """
        # Simple keyword-based detection (can be enhanced with ML)
        text_lower = text.lower()
        
        # Urdu detection
        urdu_keywords = ['میں', 'ہے', 'ہیں', 'درد', 'سینے', 'بازو', 'جی', 'ہاں']
        if any(keyword in text for keyword in urdu_keywords):
            return "Urdu"
        
        # Punjabi detection
        punjabi_keywords = ['ਮੈਂ', 'ਹੈ', 'ਦਰਦ', 'ਸੀਨੇ']
        if any(keyword in text for keyword in punjabi_keywords):
            return "Punjabi"
        
        # Pashto detection
        pashto_keywords = ['زه', 'دی', 'درد', 'سینه']
        if any(keyword in text for keyword in pashto_keywords):
            return "Pashto"
        
        # Sindhi detection
        sindhi_keywords = ['مان', 'آهي', 'درد', 'سيني']
        if any(keyword in text for keyword in sindhi_keywords):
            return "Sindhi"
        
        return "English"  # Default
    
    def route_to_safety_agent(self, context: ConversationContext, message: str) -> Dict[str, Any]:
        """
        Safety Agent: Detects emergencies immediately.
        Returns: Safety assessment with urgency level.
        """
        # Extract symptoms
        symptoms = self.symptom_extractor.extract(message)
        context.add_symptom(symptoms[0] if symptoms else message)
        
        # Check for immediate emergencies
        emergency_keywords = {
            "chest pain": UrgencyLevel.IMMEDIATE,
            "سینے میں درد": UrgencyLevel.IMMEDIATE,
            "shortness of breath": UrgencyLevel.IMMEDIATE,
            "سانس لینے میں مشکل": UrgencyLevel.IMMEDIATE,
            "unconscious": UrgencyLevel.IMMEDIATE,
            "بے ہوش": UrgencyLevel.IMMEDIATE,
            "severe bleeding": UrgencyLevel.IMMEDIATE,
            "شدید خون بہنا": UrgencyLevel.IMMEDIATE
        }
        
        message_lower = message.lower()
        for keyword, urgency in emergency_keywords.items():
            if keyword in message_lower:
                context.escalate_urgency(urgency)
                context.add_agent_action(
                    AgentType.SAFETY_AGENT,
                    "emergency_detected",
                    {"keyword": keyword, "urgency": urgency.value}
                )
                return {
                    "agent": "safety_agent",
                    "urgency": urgency.value,
                    "action_required": "IMMEDIATE" if urgency == UrgencyLevel.IMMEDIATE else None,
                    "message": self._get_emergency_message(context.language, urgency)
                }
        
        return {
            "agent": "safety_agent",
            "urgency": context.urgency_level.value,
            "action_required": None
        }
    
    def route_to_triage_agent(self, context: ConversationContext) -> Dict[str, Any]:
        """
        Triage Agent: Assesses urgency based on symptoms.
        """
        if not context.symptoms:
            # Generate natural follow-up question using AI
            natural_message = self._generate_natural_response(
                context,
                "The patient hasn't provided symptoms yet. Ask naturally and empathetically what's bothering them.",
                include_urgency=False
            )
            return {
                "agent": "triage_agent",
                "action": "need_more_info",
                "message": natural_message
            }
        
        # Use existing triage system
        triage_result = self.triage_orchestrator.handle_triage(context.symptoms)
        triage_level = triage_result.get("triage", "STANDARD")
        
        # Map to urgency level
        urgency_map = {
            "IMMEDIATE": UrgencyLevel.IMMEDIATE,
            "VERY_URGENT": UrgencyLevel.VERY_URGENT,
            "URGENT": UrgencyLevel.URGENT,
            "STANDARD": UrgencyLevel.STANDARD
        }
        
        urgency = urgency_map.get(triage_level, UrgencyLevel.STANDARD)
        context.escalate_urgency(urgency)
        context.state = ConversationState.TRIAGE_ASSESSMENT
        context.progress["triage_complete"] = True
        
        context.add_agent_action(
            AgentType.TRIAGE_AGENT,
            "triage_assessment",
            {"level": triage_level, "urgency": urgency.value}
        )
        
        # Generate natural response based on triage result
        triage_message = triage_result.get("messages", [""])[0] if triage_result.get("messages") else ""
        natural_message = self._generate_natural_response(
            context,
            f"Based on the symptoms: {', '.join(context.symptoms)}. Triage level: {triage_level}. Message: {triage_message}. Respond naturally and empathetically, like a caring medical assistant.",
            urgency=urgency
        )
        
        return {
            "agent": "triage_agent",
            "urgency": urgency.value,
            "triage_level": triage_level,
            "message": natural_message
        }
    
    def route_to_documentation_agent(self, context: ConversationContext) -> Dict[str, Any]:
        """
        Documentation Agent: Starts SOAP note creation.
        """
        if not context.progress["triage_complete"]:
            return {
                "agent": "documentation_agent",
                "action": "wait_for_triage",
                "message": "Waiting for triage completion"
            }
        
        # Start SOAP note
        context.soap_note = {
            "subjective": self._extract_subjective(context),
            "objective": "",
            "assessment": f"Triage Level: {context.urgency_level.value}",
            "plan": self._generate_plan(context)
        }
        
        context.progress["documentation_started"] = True
        context.state = ConversationState.DOCUMENTATION
        
        context.add_agent_action(
            AgentType.DOCUMENTATION_AGENT,
            "soap_note_started",
            {"urgency": context.urgency_level.value}
        )
        
        return {
            "agent": "documentation_agent",
            "action": "soap_note_started",
            "soap_note": context.soap_note
        }
    
    def route_to_interview_agent(self, context: ConversationContext) -> Optional[str]:
        """
        Interview Agent: Asks natural follow-up questions based on context using AI.
        """
        # Generate natural follow-up questions using AI based on conversation context
        conversation_history = " ".join([r["text"] for r in context.patient_responses[-3:]])
        symptoms_text = ", ".join(context.symptoms) if context.symptoms else "none yet"
        
        # Determine what to ask based on context
        if context.urgency_level == UrgencyLevel.IMMEDIATE:
            # Critical questions for immediate cases
            if "chest pain" in str(context.symptoms).lower() or "سینے میں درد" in str(context.symptoms):
                prompt = f"Patient reports chest pain. Ask ONE natural, empathetic follow-up question about pain radiation or other critical symptoms. Be conversational, not robotic. Language: {context.language}"
            else:
                prompt = f"Patient has urgent symptoms: {symptoms_text}. Ask ONE natural, empathetic follow-up question to gather critical information. Be conversational. Language: {context.language}"
        elif context.urgency_level == UrgencyLevel.VERY_URGENT:
            prompt = f"Patient reports: {symptoms_text}. Conversation: {conversation_history}. Ask ONE natural, caring follow-up question to understand their condition better. Be conversational. Language: {context.language}"
        elif not context.symptoms or len(context.symptoms) < 2:
            prompt = f"Patient said: {conversation_history}. Ask ONE natural, empathetic question to understand their symptoms better. Be conversational and caring. Language: {context.language}"
        else:
            # Enough info collected, no follow-up needed
            return None
        
        try:
            question = self._generate_natural_question(prompt, context.language)
            if question:
                context.progress["follow_up_questions"].append(question)
                return question
        except Exception as e:
            logger.error(f"Error generating follow-up question: {e}")
        
        return None
    
    def process_message(
        self,
        session_id: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Main entry point: Process patient message and coordinate agents.
        
        Flow:
        1. Detect language
        2. Route to Safety Agent (check for emergencies)
        3. If emergency → Immediate response + Documentation Agent
        4. Route to Triage Agent
        5. Route to Interview Agent (follow-up questions)
        6. Update context and progress
        """
        context = self.get_context(session_id)
        
        # Step 1: Detect language
        detected_lang = self.detect_language(message)
        if detected_lang != "English":
            context.language = detected_lang
            context.detected_language = detected_lang
        
        context.add_response(message)
        
        # Step 2: Check for conflicts
        if context.detect_conflict({"text": message}):
            natural_clarification = self._generate_natural_response(
                context,
                "I noticed some conflicting information in what the patient said. Ask naturally and empathetically for clarification, like a caring assistant would.",
                include_urgency=False
            )
            return {
                "agent": "orchestrator",
                "message": natural_clarification,
                "conflict_detected": True
            }
        
        # Step 3: Route to Safety Agent (ALWAYS FIRST - detects emergencies)
        safety_result = self.route_to_safety_agent(context, message)
        
        # If immediate emergency detected
        if safety_result.get("urgency") == "IMMEDIATE":
            # Start documentation immediately
            doc_result = self.route_to_documentation_agent(context)
            
            # Generate natural, empathetic emergency response
            immediate_message = safety_result.get("message", "")
            if not immediate_message or len(immediate_message) < 20:
                # Generate natural emergency message
                immediate_message = self._generate_natural_response(
                    context,
                    f"Patient has IMMEDIATE emergency symptoms: {', '.join(context.symptoms)}. Respond with urgency but calm empathy. Guide them to call 1122 immediately. Be human and caring.",
                    urgency=UrgencyLevel.IMMEDIATE
                )
            
            # Ask critical follow-up question naturally
            follow_up = self.route_to_interview_agent(context)
            
            return {
                "agent": "safety_agent",
                "urgency": "IMMEDIATE",
                "message": immediate_message,
                "follow_up_question": follow_up,
                "action_required": "Please call 1122 immediately for emergency medical assistance.",
                "documentation_started": True,
                "context": {
                    "symptoms": context.symptoms,
                    "language": context.language,
                    "state": context.state.value
                }
            }
        
        # Step 4: Route to Triage Agent
        triage_result = self.route_to_triage_agent(context)
        
        # Get natural response message
        response_message = triage_result.get("message", "")
        
        # If message is too short or seems generic, enhance it with AI
        if not response_message or len(response_message) < 30:
            # Generate natural response based on conversation context
            conversation_summary = " ".join([r["text"] for r in context.patient_responses[-2:]])
            response_message = self._generate_natural_response(
                context,
                f"Patient said: {conversation_summary}. Symptoms: {', '.join(context.symptoms) if context.symptoms else 'none yet'}. "
                f"Triage level: {triage_result.get('urgency', 'STANDARD')}. "
                "Respond naturally and empathetically, acknowledging what they said and providing helpful guidance. "
                "Sound like a caring medical assistant, not a robot.",
                urgency=UrgencyLevel[triage_result.get("urgency", "STANDARD")] if triage_result.get("urgency") else None
            )
        
        # Step 5: Route to Documentation Agent (if triage complete)
        doc_result = None
        if context.progress["triage_complete"]:
            doc_result = self.route_to_documentation_agent(context)
        
        # Step 6: Route to Interview Agent (follow-up questions)
        follow_up_question = self.route_to_interview_agent(context)
        
        # Update state
        if context.state == ConversationState.INITIAL:
            context.state = ConversationState.COLLECTING_SYMPTOMS
        
        return {
            "agent": "orchestrator",
            "urgency": triage_result.get("urgency", "STANDARD"),
            "message": response_message,
            "follow_up_question": follow_up_question,
            "documentation": doc_result.get("soap_note") if doc_result else None,
            "context": {
                "symptoms": context.symptoms,
                "language": context.language,
                "state": context.state.value,
                "progress": context.progress
            }
        }
    
    def _get_emergency_message(self, language: str, urgency: UrgencyLevel) -> str:
        """Generate natural emergency message using AI."""
        urgency_descriptions = {
            UrgencyLevel.IMMEDIATE: "immediate emergency requiring 1122 call right now",
            UrgencyLevel.VERY_URGENT: "very urgent situation requiring ER visit within 1 hour",
            UrgencyLevel.URGENT: "urgent care needed, ER visit within 2-4 hours"
        }
        
        prompt = f"""You are a caring medical assistant. A patient has a {urgency_descriptions[urgency]}.

Respond naturally and empathetically, but with appropriate urgency. Be human, not robotic. 
- For IMMEDIATE: Be direct but calm, emphasize calling 1122 immediately
- For VERY_URGENT/URGENT: Show concern and guide them to seek care promptly
- Use natural language, like you're talking to a friend who needs help
- Language: {language}

Respond in ONE short, natural sentence. No bullet points, no formal structure."""
        
        try:
            return self._generate_natural_response_ai(prompt, language)
        except Exception as e:
            logger.error(f"Error generating emergency message: {e}")
            # Fallback
            if urgency == UrgencyLevel.IMMEDIATE:
                return "I'm very concerned about what you're describing. Please call 1122 right away - this needs immediate medical attention."
            elif urgency == UrgencyLevel.VERY_URGENT:
                return "This sounds serious. I'd strongly recommend going to the emergency room within the next hour."
            else:
                return "This needs prompt medical attention. Please visit the ER within the next few hours."
    
    def _generate_natural_response(self, context: ConversationContext, instruction: str, urgency: Optional[UrgencyLevel] = None, include_urgency: bool = True) -> str:
        """Generate natural, human-like response using AI based on context and instruction."""
        conversation_history = " ".join([r["text"] for r in context.patient_responses[-3:]])
        symptoms_text = ", ".join(context.symptoms) if context.symptoms else "none yet"
        
        urgency_context = ""
        if urgency and include_urgency:
            urgency_context = f" Urgency level: {urgency.value}. "
        
        prompt = f"""You are a caring, empathetic medical assistant having a natural conversation with a patient.

Context:
- Patient's recent messages: {conversation_history}
- Symptoms mentioned: {symptoms_text}
- Language: {context.language}
{urgency_context}

Instruction: {instruction}

Guidelines:
- Sound natural and human, like a caring friend who happens to be a medical professional
- Be empathetic and warm
- Use conversational language, not robotic or formal
- Keep it concise (1-2 sentences max)
- Don't use bullet points or lists
- Respond in {context.language}
- Make it feel like a real conversation

Generate ONE natural, empathetic response:"""
        
        try:
            return self._generate_natural_response_ai(prompt, context.language)
        except Exception as e:
            logger.error(f"Error generating natural response: {e}")
            # Fallback to simple natural message
            return "I understand. Can you tell me a bit more about what you're experiencing?"
    
    def _generate_natural_question(self, prompt: str, language: str) -> str:
        """Generate a natural follow-up question using AI."""
        full_prompt = f"""You are a caring medical assistant. {prompt}

Generate ONE natural, conversational question. Make it sound like you genuinely care and want to help. 
No formal structure, just a natural question someone would ask a friend."""
        
        try:
            return self._generate_natural_response_ai(full_prompt, language)
        except Exception as e:
            logger.error(f"Error generating natural question: {e}")
            return None
    
    def _generate_natural_response_ai(self, prompt: str, language: str) -> str:
        """Use Gemini to generate natural, human-like responses."""
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            text = response.text.strip()
            
            # Clean up any markdown or formatting
            text = text.replace('**', '').replace('*', '').replace('#', '').strip()
            
            # Ensure it's in the right language
            if language != "English":
                # For non-English, ensure response is in that language
                if language == "Urdu" and not any(ord(c) > 127 for c in text[:10]):
                    # If response is not in Urdu, translate instruction
                    pass  # Will use the prompt language
            
            return text
        except Exception as e:
            logger.error(f"Error in AI response generation: {e}")
            raise
    
    def _get_message(self, language: str, message_type: str) -> str:
        """Get message in appropriate language (fallback method)."""
        messages = {
            "English": {
                "need_symptoms": "I'd like to help you. What symptoms are you experiencing?",
                "chest_pain_radiation": "Does the pain spread to your arm or jaw?",
                "more_symptoms": "Can you tell me more about what you're feeling?",
                "clarification_needed": "I want to make sure I understand correctly. Can you help clarify?"
            },
            "Urdu": {
                "need_symptoms": "میں آپ کی مدد کرنا چاہتا ہوں۔ آپ کو کیا علامات محسوس ہو رہی ہیں؟",
                "chest_pain_radiation": "کیا درد آپ کے بازو یا جبڑے میں پھیل رہا ہے؟",
                "more_symptoms": "کیا آپ مجھے بتا سکتے ہیں کہ آپ کیا محسوس کر رہے ہیں؟",
                "clarification_needed": "میں یقینی بنانا چاہتا ہوں کہ میں صحیح سمجھ رہا ہوں۔ کیا آپ وضاحت کر سکتے ہیں؟"
            },
            "Punjabi": {
                "need_symptoms": "ਮੈਂ ਤੁਹਾਡੀ ਮਦਦ ਕਰਨਾ ਚਾਹੁੰਦਾ ਹਾਂ। ਤੁਹਾਨੂੰ ਕੀ ਲੱਛਣ ਮਹਿਸੂਸ ਹੋ ਰਹੇ ਹਨ?",
                "chest_pain_radiation": "ਕੀ ਦਰਦ ਤੁਹਾਡੀ ਬਾਂਹ ਜਾਂ ਜਬੜੇ ਵਿੱਚ ਫੈਲ ਰਿਹਾ ਹੈ?",
                "more_symptoms": "ਕੀ ਤੁਸੀਂ ਮੈਨੂੰ ਦੱਸ ਸਕਦੇ ਹੋ ਕਿ ਤੁਸੀਂ ਕੀ ਮਹਿਸੂਸ ਕਰ ਰਹੇ ਹੋ?",
                "clarification_needed": "ਮੈਂ ਯਕੀਨੀ ਬਣਾਉਣਾ ਚਾਹੁੰਦਾ ਹਾਂ ਕਿ ਮੈਂ ਸਹੀ ਸਮਝ ਰਿਹਾ ਹਾਂ। ਕੀ ਤੁਸੀਂ ਸਪੱਸ਼ਟੀਕਰਣ ਕਰ ਸਕਦੇ ਹੋ?"
            }
        }
        return messages.get(language, messages["English"]).get(message_type, "")
    
    def _extract_subjective(self, context: ConversationContext) -> str:
        """Extract subjective information from conversation."""
        symptoms_text = ", ".join(context.symptoms)
        responses_text = " ".join([r["text"] for r in context.patient_responses[-3:]])
        return f"Patient reports: {symptoms_text}. {responses_text}"
    
    def _generate_plan(self, context: ConversationContext) -> str:
        """Generate plan based on urgency."""
        if context.urgency_level == UrgencyLevel.IMMEDIATE:
            return "1. Call 1122 immediately\n2. Monitor vital signs\n3. Prepare for emergency transport"
        elif context.urgency_level == UrgencyLevel.VERY_URGENT:
            return "1. Go to ER within 1 hour\n2. Monitor symptoms\n3. Avoid exertion"
        else:
            return "1. Continue monitoring\n2. Follow up as needed\n3. Seek care if symptoms worsen"


# Global instance
advanced_orchestrator = AdvancedOrchestrator()
