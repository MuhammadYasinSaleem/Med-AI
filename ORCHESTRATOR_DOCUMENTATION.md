# 🎯 MedAI Unified Orchestrator Documentation

## Overview

The MedAI Unified Orchestrator is a sophisticated workflow coordination system that intelligently routes requests and manages multi-step workflows across all three MedAI modules:

1. **Lab Report Analyzer** - AI-powered lab report analysis
2. **Clinical Interview & Triage** - Patient interviews and triage assessment
3. **Medication Interaction Checker** - Drug interaction analysis

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Unified Orchestrator                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Triage     │  │ Lab Analysis │  │ Medication   │ │
│  │  Module      │  │   Module     │  │   Module     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## 🔄 Workflow Types

### 1. **TRIAGE_ONLY**
Simple triage assessment based on symptoms.

**Use Case:** Patient reports symptoms, needs urgency assessment.

**Input:**
```json
{
  "workflow_type": "triage_only",
  "symptoms": ["chest pain", "shortness of breath"],
  "text": "I have chest pain and can't breathe well"
}
```

**Output:**
```json
{
  "workflow_type": "triage_only",
  "steps": [
    {
      "step": "triage",
      "result": {
        "triage": "IMMEDIATE",
        "messages": ["Possible heart attack. Call 1122 immediately!"]
      }
    }
  ],
  "final_result": {
    "triage": "IMMEDIATE",
    "messages": ["Possible heart attack. Call 1122 immediately!"]
  },
  "recommendations": [
    "Consider lab analysis for comprehensive assessment",
    "Review current medications for potential interactions"
  ]
}
```

---

### 2. **TRIAGE_TO_LAB**
Triage assessment followed by lab analysis.

**Use Case:** Patient has symptoms AND lab report available.

**Input:**
```json
{
  "workflow_type": "triage_to_lab",
  "symptoms": ["fatigue", "dizziness"],
  "lab_report_id": "uuid-of-lab-report"
}
```

**Output:**
```json
{
  "workflow_type": "triage_to_lab",
  "steps": [
    {
      "step": "triage",
      "result": { "triage": "URGENT", "messages": [...] }
    },
    {
      "step": "lab_analysis",
      "result": {
        "critical_findings": [...],
        "abnormal_findings": [...]
      }
    }
  ],
  "final_result": {
    "triage": {...},
    "lab_analysis": {...},
    "combined_assessment": {
      "urgency": "CRITICAL",
      "message": "Urgent triage combined with critical lab values",
      "recommendations": [...]
    }
  }
}
```

---

### 3. **TRIAGE_TO_MEDICATION**
Triage assessment followed by medication check.

**Use Case:** Patient has symptoms AND is taking medications.

**Input:**
```json
{
  "workflow_type": "triage_to_medication",
  "symptoms": ["nausea", "dizziness"],
  "medications": [
    { "name": "Ibuprofen", "is_new": false },
    { "name": "Aspirin", "is_new": true }
  ],
  "patient_age": 65,
  "conditions": ["CKD Stage 3"]
}
```

---

### 4. **COMPREHENSIVE_CARE**
Full patient journey: Triage → Lab → Medications.

**Use Case:** Complete patient assessment with all available data.

**Input:**
```json
{
  "workflow_type": "comprehensive_care",
  "symptoms": ["chest pain", "shortness of breath"],
  "lab_report_id": "uuid-of-lab-report",
  "medications": [
    { "name": "Metformin", "is_new": false }
  ],
  "patient_age": 55,
  "conditions": ["Diabetes"]
}
```

**Output:**
```json
{
  "workflow_type": "comprehensive_care",
  "steps": [
    { "step": "triage", "result": {...} },
    { "step": "lab_analysis", "result": {...} },
    { "step": "medication_check", "result": {...} }
  ],
  "final_result": {
    "triage": {...},
    "lab_analysis": {...},
    "medication_interactions": {...},
    "comprehensive_assessment": {
      "overall_urgency": "IMMEDIATE",
      "key_findings": [...],
      "recommendations": [...],
      "next_steps": [...]
    }
  }
}
```

---

## 📡 API Endpoints

### 1. **Suggest Workflow**
Intelligently suggests the best workflow based on available context.

**Endpoint:** `POST /medai/workflow/suggest/`

**Request:**
```json
{
  "symptoms": ["chest pain"],
  "has_lab_report": true,
  "has_medications": false,
  "triage_level": "URGENT",
  "patient_age": 45
}
```

**Response:**
```json
{
  "suggested_workflow": "triage_to_lab",
  "description": "Triage assessment followed by lab analysis",
  "context": {...}
}
```

---

### 2. **Execute Workflow**
Execute a specific workflow type.

**Endpoint:** `POST /medai/workflow/execute/`

**Request:**
```json
{
  "workflow_type": "triage_to_lab",
  "symptoms": ["fatigue"],
  "lab_report_id": "uuid-here"
}
```

**Response:**
```json
{
  "workflow_type": "triage_to_lab",
  "steps": [...],
  "final_result": {...},
  "recommendations": [...]
}
```

---

### 3. **Comprehensive Care**
Convenience endpoint for full patient assessment.

**Endpoint:** `POST /medai/workflow/comprehensive/`

**Request:**
```json
{
  "symptoms": ["chest pain"],
  "lab_report_id": "uuid-here",
  "medications": [
    { "name": "Aspirin", "is_new": false }
  ],
  "patient_age": 60,
  "conditions": ["Hypertension"]
}
```

---

## 🎯 Intelligent Workflow Selection

The orchestrator uses intelligent logic to suggest workflows:

1. **If triage is IMMEDIATE/VERY_URGENT** → Suggest `COMPREHENSIVE_CARE`
2. **If symptoms + lab report** → Suggest `TRIAGE_TO_LAB`
3. **If symptoms + medications** → Suggest `TRIAGE_TO_MEDICATION`
4. **If lab + medications** → Suggest `LAB_TO_MEDICATION`
5. **If only symptoms** → Suggest `TRIAGE_ONLY`
6. **If only lab report** → Suggest `LAB_ANALYSIS_ONLY`
7. **If only medications** → Suggest `MEDICATION_CHECK_ONLY`

---

## 🔧 Usage Examples

### Python Example

```python
import requests

# Suggest workflow
response = requests.post('http://localhost:8000/medai/workflow/suggest/', json={
    "symptoms": ["chest pain"],
    "has_lab_report": True,
    "has_medications": True
})
suggested = response.json()
print(f"Suggested: {suggested['suggested_workflow']}")

# Execute workflow
response = requests.post('http://localhost:8000/medai/workflow/execute/', json={
    "workflow_type": "comprehensive_care",
    "symptoms": ["chest pain", "shortness of breath"],
    "lab_report_id": "your-lab-report-uuid",
    "medications": [
        {"name": "Aspirin", "is_new": False}
    ],
    "patient_age": 55,
    "conditions": ["Hypertension"]
})
result = response.json()
print(f"Overall Urgency: {result['final_result']['comprehensive_assessment']['overall_urgency']}")
```

### JavaScript/React Example

```javascript
// Suggest workflow
const suggestWorkflow = async (context) => {
  const response = await fetch('http://localhost:8000/medai/workflow/suggest/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(context)
  });
  return await response.json();
};

// Execute comprehensive care
const comprehensiveCare = async (data) => {
  const response = await fetch('http://localhost:8000/medai/workflow/comprehensive/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return await response.json();
};

// Usage
const result = await comprehensiveCare({
  symptoms: ['chest pain'],
  lab_report_id: 'uuid-here',
  medications: [{ name: 'Aspirin', is_new: false }],
  patient_age: 55,
  conditions: ['Hypertension']
});

console.log('Overall Urgency:', result.final_result.comprehensive_assessment.overall_urgency);
```

---

## 🎨 Benefits

1. **Unified Interface** - Single entry point for all workflows
2. **Intelligent Routing** - Automatically suggests best workflow
3. **Multi-Step Coordination** - Handles complex workflows seamlessly
4. **State Management** - Manages state across multiple modules
5. **Combined Assessments** - Provides unified results from multiple modules
6. **Recommendations** - Generates actionable recommendations

---

## 🔒 Error Handling

The orchestrator handles errors gracefully:

```json
{
  "workflow_type": "triage_to_lab",
  "steps": [...],
  "error": "Error message if something fails",
  "final_result": null
}
```

---

## 📊 Workflow Flow Diagram

```
User Request
    ↓
Orchestrator.suggest_workflow()
    ↓
WorkflowType Selected
    ↓
Orchestrator.execute_workflow()
    ↓
┌─────────────────────────────────┐
│ Step 1: Triage (if needed)      │
│ Step 2: Lab Analysis (if needed)│
│ Step 3: Medication Check       │
│         (if needed)             │
└─────────────────────────────────┘
    ↓
Combine Results
    ↓
Generate Recommendations
    ↓
Return Unified Result
```

---

## 🚀 Future Enhancements

1. **Workflow History** - Track patient workflows over time
2. **Workflow Templates** - Predefined workflow templates
3. **Parallel Processing** - Execute independent steps in parallel
4. **Workflow Scheduling** - Schedule workflows for later execution
5. **Workflow Analytics** - Track workflow performance and outcomes

---

## 📝 Notes

- The orchestrator uses lazy loading to avoid circular dependencies
- All workflows are synchronous by default (can be extended for async)
- Error handling is comprehensive but can be enhanced
- The orchestrator is stateless (each request is independent)

---

**Last Updated:** 2026-01-10
**Version:** 1.0.0
