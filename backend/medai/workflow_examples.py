"""
Example usage of the Unified Orchestrator.
These examples demonstrate how to use the orchestrator in different scenarios.
"""
from .orchestrator import orchestrator, WorkflowType


def example_triage_only():
    """Example: Simple triage assessment."""
    data = {
        "symptoms": ["chest pain", "shortness of breath", "sweating"],
        "text": "I have severe chest pain and can't breathe"
    }
    
    result = orchestrator.execute_workflow(WorkflowType.TRIAGE_ONLY, data)
    print("Triage Result:", result["final_result"])
    return result


def example_triage_to_lab():
    """Example: Triage followed by lab analysis."""
    data = {
        "symptoms": ["fatigue", "dizziness"],
        "lab_report_id": "your-lab-report-uuid-here"
    }
    
    result = orchestrator.execute_workflow(WorkflowType.TRIAGE_TO_LAB, data)
    print("Combined Assessment:", result["final_result"]["combined_assessment"])
    return result


def example_comprehensive_care():
    """Example: Full comprehensive care workflow."""
    data = {
        "symptoms": ["chest pain", "shortness of breath"],
        "lab_report_id": "your-lab-report-uuid-here",
        "medications": [
            {"name": "Aspirin", "is_new": False},
            {"name": "Ibuprofen", "is_new": True}
        ],
        "patient_age": 65,
        "conditions": ["CKD Stage 3", "Hypertension"]
    }
    
    result = orchestrator.execute_workflow(WorkflowType.COMPREHENSIVE_CARE, data)
    print("Comprehensive Assessment:", result["final_result"]["comprehensive_assessment"])
    return result


def example_workflow_suggestion():
    """Example: Get workflow suggestion based on context."""
    context = {
        "symptoms": ["chest pain"],
        "has_lab_report": True,
        "has_medications": True,
        "triage_level": "URGENT"
    }
    
    suggested = orchestrator.suggest_workflow(context)
    print(f"Suggested Workflow: {suggested.value}")
    return suggested


if __name__ == "__main__":
    print("=== Example 1: Triage Only ===")
    example_triage_only()
    
    print("\n=== Example 2: Workflow Suggestion ===")
    example_workflow_suggestion()
    
    print("\n=== Example 3: Comprehensive Care ===")
    # Note: This requires actual lab_report_id and valid data
    # example_comprehensive_care()
