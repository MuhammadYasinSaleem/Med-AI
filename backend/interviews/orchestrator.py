from typing import Dict, Any

from .triage_agent import triage_patient


class Orchestrator:
    """
    Routes requests to the correct use-case agent.
    Contains NO business or medical logic.
    """

    def handle_triage(self, symptoms: list[str]) -> Dict[str, Any]:
        """
        Route to the triage use case.
        """
        return triage_patient(symptoms)
