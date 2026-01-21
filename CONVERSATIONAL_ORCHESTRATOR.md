# 💬 Conversational Orchestrator - Patient Interaction Guide

## Overview

The Conversational Orchestrator provides a natural, chat-like interface where patients can interact with MedAI through the main page search input. The orchestrator intelligently guides the conversation and automatically routes to appropriate workflows.

## 🎯 How It Works

### Flow Diagram

```
Patient types in search box
        ↓
Click/Focus → Opens Chat Interface
        ↓
Orchestrator greets patient
        ↓
Patient describes symptoms/needs
        ↓
Orchestrator extracts symptoms
        ↓
Performs triage assessment
        ↓
Suggests appropriate workflow
        ↓
Patient provides additional info (lab report, medications)
        ↓
Orchestrator executes workflow
        ↓
Returns comprehensive results
```

## 🚀 User Experience

### Step 1: Starting a Conversation

**On the Home Page:**
1. Patient sees the search box at the bottom
2. Patient clicks on the input field or types a message
3. Chat interface opens automatically
4. Orchestrator greets: *"Hello! I'm your MedAI assistant..."*

### Step 2: Patient Describes Symptoms

**Patient types:** *"I have chest pain and shortness of breath"*

**Orchestrator:**
- Extracts symptoms: `["chest pain", "shortness of breath"]`
- Performs triage assessment
- Responds with urgency level and recommendations

**Example Response:**
```
🚨 URGENT ASSESSMENT

Possible heart attack. Call 1122 immediately!

Your Symptoms: chest pain, shortness of breath
Priority Level: IMMEDIATE

I strongly recommend immediate medical attention. Would you like me to:
• Analyze any lab reports you have
• Check your medications for interactions
• Provide a comprehensive assessment
```

### Step 3: Orchestrator Suggests Workflow

Based on the conversation context, orchestrator intelligently suggests:
- **TRIAGE_ONLY** - If only symptoms provided
- **TRIAGE_TO_LAB** - If symptoms + lab report available
- **TRIAGE_TO_MEDICATION** - If symptoms + medications available
- **COMPREHENSIVE_CARE** - If all data available

### Step 4: Patient Provides Additional Info

**Patient:** *"I have a lab report to analyze"*

**Orchestrator:**
- Recognizes lab report request
- Guides patient to upload or provide lab report ID
- Executes `TRIAGE_TO_LAB` workflow
- Combines triage + lab results

### Step 5: Comprehensive Results

**Orchestrator returns:**
- Triage assessment
- Lab analysis results
- Combined assessment with recommendations
- Next steps

## 📡 API Endpoints

### 1. Start Conversation
```http
POST /medai/conversation/start/
Content-Type: application/json

{
  "patient_age": 45,  // optional
  "initial_message": "Hello"  // optional
}
```

**Response:**
```json
{
  "session_id": "uuid-here",
  "message": "Hello! I'm your MedAI assistant...",
  "stage": "greeting"
}
```

### 2. Continue Conversation
```http
POST /medai/conversation/continue/
Content-Type: application/json

{
  "session_id": "uuid-here",
  "message": "I have chest pain",
  "lab_report_id": "uuid-optional",
  "medications": [
    {"name": "Aspirin", "is_new": false}
  ]
}
```

**Response:**
```json
{
  "session_id": "uuid-here",
  "message": "🚨 URGENT ASSESSMENT...",
  "stage": "triage",
  "symptoms": ["chest pain"],
  "suggested_workflow": "triage_to_lab",
  "context": {
    "has_lab_report": true,
    "has_medications": false,
    "triage_level": "IMMEDIATE"
  }
}
```

### 3. Get Conversation History
```http
GET /medai/conversation/{session_id}/
```

## 🎨 Frontend Integration

### Home Page Search Box

The search input on the home page now:
- Opens chat interface when clicked
- Supports conversational flow
- Integrates with orchestrator

### Conversation Chat Component

**Features:**
- Real-time chat interface
- Message history
- Symptom extraction display
- Workflow suggestions
- Loading states
- Error handling

**Usage:**
```jsx
import ConversationChat from '../components/ConversationChat'

<ConversationChat
  onClose={() => setShowChat(false)}
  initialMessage="I have chest pain"
/>
```

## 🔄 Conversation Stages

### Stage 1: Greeting
- Initial welcome message
- Explains capabilities
- Asks how to help

### Stage 2: Collecting Info
- Extracts symptoms from patient messages
- Gathers additional context
- Prepares for triage

### Stage 3: Triage
- Performs triage assessment
- Shows urgency level
- Suggests next steps

### Stage 4: Workflow Execution
- Executes suggested workflow
- Combines results from multiple modules
- Provides comprehensive assessment

### Stage 5: Completed
- Results provided
- Offers additional assistance
- Ready for new queries

## 💡 Example Conversations

### Example 1: Simple Triage

**Patient:** "I have a headache"

**Orchestrator:** 
```
Triage Assessment Complete

Your headache has been assessed.
Priority Level: STANDARD

How would you like to proceed?
• Analyze a lab report
• Check medication interactions
• Get a comprehensive assessment
```

### Example 2: Urgent Case

**Patient:** "Severe chest pain, can't breathe, sweating"

**Orchestrator:**
```
🚨 URGENT ASSESSMENT

Possible heart attack. Call 1122 immediately!

Your Symptoms: chest pain, shortness of breath, sweating
Priority Level: IMMEDIATE

I strongly recommend immediate medical attention...
```

### Example 3: Comprehensive Care

**Patient:** "I have chest pain. I take Aspirin and Ibuprofen. I have a lab report."

**Orchestrator:**
- Extracts symptoms
- Performs triage
- Suggests comprehensive workflow
- Executes: Triage → Lab → Medication check
- Returns combined assessment

## 🎯 Key Features

1. **Natural Language Processing**
   - Extracts symptoms from free text
   - Understands patient intent
   - Handles multiple languages

2. **Intelligent Routing**
   - Suggests best workflow automatically
   - Adapts to available data
   - Guides patient through process

3. **Multi-Step Workflows**
   - Coordinates across modules
   - Combines results intelligently
   - Provides unified assessment

4. **Context Awareness**
   - Remembers conversation history
   - Tracks symptoms and data
   - Maintains session state

5. **User-Friendly Interface**
   - Chat-like experience
   - Clear formatting
   - Visual indicators for urgency

## 🔧 Technical Details

### Session Management
- Sessions stored in memory (can be moved to Redis/DB)
- Each session maintains:
  - Conversation history
  - Extracted symptoms
  - Context (lab reports, medications)
  - Current workflow
  - Stage

### Symptom Extraction
- Uses `SymptomExtractor` from interviews module
- Extracts symptoms from natural language
- Preserves original language

### Workflow Execution
- Uses `Orchestrator.execute_workflow()`
- Handles errors gracefully
- Returns formatted results

## 🚀 Future Enhancements

1. **Persistent Sessions** - Store in database
2. **Voice Input** - Support voice messages
3. **File Upload** - Direct lab report upload in chat
4. **Rich Media** - Images, charts in responses
5. **Multi-language** - Full multilingual support
6. **History** - View past conversations
7. **Notifications** - Alert for urgent cases

## 📝 Usage Tips

### For Patients:
- Describe symptoms clearly
- Mention if you have lab reports or medications
- Follow orchestrator's suggestions
- Ask questions if unclear

### For Developers:
- Session IDs are UUIDs
- Sessions expire after inactivity (can be configured)
- Error handling is comprehensive
- All endpoints return JSON

---

**Last Updated:** 2026-01-10
**Version:** 1.0.0
