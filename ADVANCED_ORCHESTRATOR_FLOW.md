# 🎯 Advanced Orchestrator - Real-Time Conversation Flow

## Overview

The Advanced Orchestrator implements a sophisticated multi-agent conversation system that works exactly like the example you provided:

```
TIME    ACTOR               ACTION
0:00    Patient             "میرے سینے میں درد ہے" (Chest pain)
0:01    Orchestrator        Detects language (Urdu), routes to Safety Agent
0:02    Safety Agent        Identifies as potential cardiac emergency
0:03    Orchestrator        Immediate response: "Call 1122 NOW!"
                          Simultaneously activates Documentation Agent
0:05    Documentation       Starts SOAP note
        Agent
0:10    Orchestrator        Follow-up: "کیا درد آپ کے بازو میں جا رہا ہے؟"
                          (Is pain radiating to your arm?)
0:15    Patient             "جی ہاں، بائیں بازو میں"
0:16    Orchestrator        Updates triage to "IMMEDIATE"
                          Notifies hospital emergency contact
0:20    Orchestrator        Sends summary to ER: "65M, chest pain + L arm radiation, diaphoresis"
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│         Advanced Orchestrator (Flow Controller)           │
│                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   Safety      │  │   Triage     │  │Documentation │   │
│  │   Agent       │  │   Agent      │  │   Agent      │   │
│  │ (Emergency)   │  │ (Urgency)    │  │ (SOAP Note) │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
│                                                           │
│  ┌──────────────┐  ┌──────────────┐                      │
│  │  Interview   │  │  Language    │                      │
│  │   Agent       │  │   Agent      │                      │
│  │ (Questions)   │  │ (Detection)  │                      │
│  └──────────────┘  └──────────────┘                      │
└─────────────────────────────────────────────────────────┘
```

## 🔄 Conversation Flow

### Step-by-Step Process

1. **Patient Message Arrives**
   ```
   Input: "میرے سینے میں درد ہے"
   ```

2. **Language Detection (Language Agent)**
   ```
   Orchestrator detects: Urdu
   Updates context.language = "Urdu"
   ```

3. **Safety Agent (ALWAYS FIRST)**
   ```
   Checks for emergency keywords:
   - "chest pain" / "سینے میں درد" → IMMEDIATE
   - "shortness of breath" → IMMEDIATE
   - "unconscious" → IMMEDIATE
   
   Result: IMMEDIATE urgency detected
   ```

4. **Orchestrator Response**
   ```
   - Immediate message: "🚨 ایمرجنسی! فوری طور پر 1122 پر کال کریں!"
   - Action required: "Call 1122 NOW!"
   - Simultaneously activates Documentation Agent
   ```

5. **Documentation Agent**
   ```
   Starts SOAP note:
   - Subjective: "Patient reports: chest pain"
   - Assessment: "Triage Level: IMMEDIATE"
   - Plan: "1. Call 1122 immediately\n2. Monitor vital signs"
   ```

6. **Interview Agent (Follow-up)**
   ```
   Generates follow-up question:
   "کیا درد آپ کے بازو یا جبڑے میں جا رہا ہے؟"
   (Is pain radiating to your arm or jaw?)
   ```

7. **Patient Response**
   ```
   Input: "جی ہاں، بائیں بازو میں"
   (Yes, in left arm)
   ```

8. **Orchestrator Updates**
   ```
   - Updates triage to IMMEDIATE (confirmed)
   - Adds symptom: "left arm radiation"
   - Updates SOAP note
   - Generates next question
   ```

## 🎯 Key Responsibilities

### 1. Conversation Flow Control
**Decides which agent speaks next**

```python
def process_message(session_id, message):
    # 1. Safety Agent (ALWAYS FIRST)
    safety_result = route_to_safety_agent(context, message)
    
    # 2. If emergency → Immediate response + Documentation
    if urgency == IMMEDIATE:
        doc_result = route_to_documentation_agent(context)
        return immediate_response
    
    # 3. Triage Agent
    triage_result = route_to_triage_agent(context)
    
    # 4. Documentation Agent
    if triage_complete:
        doc_result = route_to_documentation_agent(context)
    
    # 5. Interview Agent (follow-up questions)
    follow_up = route_to_interview_agent(context)
```

### 2. Context Maintenance
**Remembers patient history across sessions**

```python
class ConversationContext:
    - symptoms: List[str]  # All symptoms mentioned
    - patient_responses: List[Dict]  # Full conversation history
    - agent_actions: List[Dict]  # All agent decisions
    - soap_note: Dict  # Ongoing documentation
    - progress: Dict  # What's been collected
    - conflicts: List[Dict]  # Contradictions detected
```

### 3. Urgency Management
**Escalates/de-escalates based on symptoms**

```python
def escalate_urgency(context, new_level):
    # Only escalate, never de-escalate automatically
    if new_level > current_level:
        context.urgency_level = new_level
        # Trigger immediate actions
        if new_level == IMMEDIATE:
            notify_emergency_services()
            start_documentation()
```

### 4. Language Bridging
**Ensures consistent language/terminology**

```python
def detect_language(text):
    # Detects: Urdu, Punjabi, Pashto, Sindhi, English
    # All responses in same language
    # SOAP notes always in English (clinical standard)
```

### 5. Progress Tracking
**Knows what information has been gathered**

```python
context.progress = {
    "symptoms_collected": True/False,
    "triage_complete": True/False,
    "documentation_started": True/False,
    "follow_up_questions": List[str]
}
```

### 6. Conflict Resolution
**Handles contradictory information**

```python
def detect_conflict(context, new_info):
    # Example: Patient says "no pain" but earlier said "severe pain"
    if contradiction_detected:
        context.conflicts.append({
            "type": "contradiction",
            "old": "...",
            "new": "..."
        })
        return clarification_question()
```

## 📊 Agent Responsibilities

### Safety Agent
- **Priority:** ALWAYS FIRST
- **Role:** Detect emergencies immediately
- **Keywords:** chest pain, shortness of breath, unconscious, severe bleeding
- **Action:** Escalate to IMMEDIATE if detected

### Triage Agent
- **Priority:** After Safety Agent
- **Role:** Assess urgency level
- **Input:** All symptoms collected
- **Output:** Urgency level (IMMEDIATE, VERY_URGENT, URGENT, STANDARD)

### Documentation Agent
- **Priority:** After Triage complete
- **Role:** Create SOAP notes
- **Triggers:** 
  - Immediately if IMMEDIATE urgency
  - After triage complete for others
- **Output:** Ongoing SOAP note

### Interview Agent
- **Priority:** After Safety/Triage
- **Role:** Ask follow-up questions
- **Logic:**
  - IMMEDIATE: Critical questions (radiation, severity)
  - VERY_URGENT: Detailed symptom questions
  - STANDARD: General follow-up

### Language Agent
- **Priority:** First (runs in parallel)
- **Role:** Detect and maintain language
- **Output:** Language code, ensures all responses match

## 🔄 Example Conversation Flow

### Scenario: Urdu-speaking patient with chest pain

```
TIME    ACTOR               ACTION
─────────────────────────────────────────────────────────
0:00    Patient             "میرے سینے میں درد ہے"
                            (I have chest pain)

0:01    Language Agent      Detects: Urdu
        Orchestrator        Updates context.language = "Urdu"

0:02    Safety Agent        Keyword detected: "سینے میں درد"
                            Escalates: IMMEDIATE

0:03    Orchestrator        Response: "🚨 ایمرجنسی! فوری طور پر 1122 پر کال کریں!"
                            Action: "Call 1122 NOW!"
                            Activates: Documentation Agent

0:05    Documentation       Starts SOAP note:
        Agent               Subjective: "Patient reports: chest pain"
                            Assessment: "Triage Level: IMMEDIATE"
                            Plan: "1. Call 1122 immediately"

0:10    Interview Agent     Generates follow-up:
                            "کیا درد آپ کے بازو میں جا رہا ہے؟"
                            (Is pain radiating to your arm?)

0:15    Patient             "جی ہاں، بائیں بازو میں"
                            (Yes, in left arm)

0:16    Safety Agent        Confirms: IMMEDIATE (radiation present)
        Orchestrator        Updates: symptom "left arm radiation"
                            Updates: SOAP note
                            Triage: IMMEDIATE (confirmed)

0:20    Documentation       Updates SOAP:
        Agent               "65M, chest pain + L arm radiation"
                            Ready for ER transmission
```

## 🎯 Implementation Details

### Language Detection
```python
def detect_language(text):
    # Urdu keywords
    if any(keyword in text for keyword in ['میں', 'ہے', 'درد', 'سینے']):
        return "Urdu"
    
    # Punjabi keywords
    if any(keyword in text for keyword in ['ਮੈਂ', 'ਹੈ', 'ਦਰਦ']):
        return "Punjabi"
    
    # Default to English
    return "English"
```

### Emergency Detection
```python
emergency_keywords = {
    "chest pain": IMMEDIATE,
    "سینے میں درد": IMMEDIATE,
    "shortness of breath": IMMEDIATE,
    "سانس لینے میں مشکل": IMMEDIATE
}
```

### Follow-up Questions
```python
if urgency == IMMEDIATE:
    if "chest pain" in symptoms:
        return "Is pain radiating to your arm or jaw?"
        # In Urdu: "کیا درد آپ کے بازو یا جبڑے میں جا رہا ہے؟"
```

## 📡 API Response Format

```json
{
  "agent": "safety_agent",
  "urgency": "IMMEDIATE",
  "message": "🚨 ایمرجنسی! فوری طور پر 1122 پر کال کریں!",
  "action_required": "Call 1122 NOW!",
  "follow_up_question": "کیا درد آپ کے بازو میں جا رہا ہے؟",
  "documentation_started": true,
  "context": {
    "symptoms": ["chest pain"],
    "language": "Urdu",
    "state": "triage_assessment"
  }
}
```

## 🚀 Benefits

1. **Real-Time Response** - Immediate emergency detection
2. **Multi-Language** - Automatic language detection and response
3. **Context Aware** - Remembers entire conversation
4. **Progressive** - Builds information over time
5. **Conflict Resolution** - Detects and resolves contradictions
6. **Documentation** - Automatic SOAP note generation

---

**Last Updated:** 2026-01-10
**Version:** 2.0.0 (Advanced Orchestrator)
