# interviews/triage_contract.py

from enum import IntEnum
from typing import Optional, Dict


class TriageLevel(IntEnum):
    """
    Higher number = higher urgency
    This allows safe max() resolution
    """
    STANDARD = 1
    URGENT = 2
    VERY_URGENT = 3
    IMMEDIATE = 4


TRIAGE_ACTIONS = {
    TriageLevel.IMMEDIATE: {
        "action": "CALL_1122_NOW",
        "message": "🚨 EMERGENCY: Call 1122 immediately or go to the nearest ER."
    },
    TriageLevel.VERY_URGENT: {
        "action": "GO_TO_ER_1_HOUR",
        "message": "⚠️ Very urgent: Go to the emergency room within 1 hour."
    },
    TriageLevel.URGENT: {
        "action": "SEE_DOCTOR_TODAY",
        "message": "🩺 Urgent: See a doctor as soon as possible today."
    },
    TriageLevel.STANDARD: {
        "action": "ROUTINE_CARE",
        "message": "ℹ️ Routine: Monitor symptoms or book a regular appointment."
    }
}


def resolve_final_triage(
    deterministic: Optional[TriageLevel] = None,
    heuristic: Optional[TriageLevel] = None,
    llm: Optional[TriageLevel] = None
) -> Dict:
    """
    SAFETY RULE:
    - Deterministic > Heuristic > LLM
    - Final triage = MAX urgency
    - LLM is NEVER allowed to downgrade
    """

    levels = [
        level for level in [deterministic, heuristic, llm]
        if level is not None
    ]

    final_level = max(levels) if levels else TriageLevel.STANDARD

    # Determine source (for transparency)
    if deterministic == final_level:
        source = "DETERMINISTIC"
    elif heuristic == final_level:
        source = "HEURISTIC"
    elif llm == final_level:
        source = "LLM_ESCALATION"
    else:
        source = "DEFAULT"

    return {
        "triage_level": final_level.name,
        "action": TRIAGE_ACTIONS[final_level]["action"],
        "message": TRIAGE_ACTIONS[final_level]["message"],
        "decision_source": source
    }
