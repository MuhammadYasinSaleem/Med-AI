import json
import logging
import re
from google import genai

from interviews.api_key_manager import api_key_manager

logger = logging.getLogger(__name__)


def medication_interaction_agent(patient_data: dict, medications: list[dict]) -> dict:
    """
    Gemini-powered Medication Interaction Agent
    - Uses gemini-2.5-flash for speed
    - Strict JSON output
    - API key fallback via api_key_manager
    """

    # -----------------------
    # Input validation
    # -----------------------
    if not medications:
        raise ValueError("At least one medication must be provided")

    valid_medications = [m for m in medications if m.get("name", "").strip()]
    if not valid_medications:
        raise ValueError("Medication names cannot be empty")

    current_meds = [m["name"].strip() for m in valid_medications if not m.get("is_new")]
    new_meds = [m["name"].strip() for m in valid_medications if m.get("is_new")]

    current_meds_str = ", ".join(current_meds) if current_meds else "None"
    new_meds_str = ", ".join(new_meds) if new_meds else "None"

    logger.info(f"Medication interaction check | Current: {current_meds_str} | New: {new_meds_str}")

    # -----------------------
    # Prompt
    # -----------------------
    prompt = f"""
SYSTEM: You are a Medication Interaction Intelligence Agent.
CONSTRAINT: Be extremely concise. Use short bullets or fragments. No fluff.

PATIENT PROFILE:
- Age: {patient_data.get("age")}
- Conditions: {patient_data.get("conditions")}

CURRENT MEDICATIONS:
{current_meds_str}

NEW MEDICATIONS:
{new_meds_str}

TASK:
1. Build an interaction graph mapping relationships between:
   - Drug-Drug (Existing vs New)
   - Drug-Disease (New drug vs Patient conditions)
   - Drug-Food (Common dietary interactions for the new drug)
2. Return ONLY the highest severity:
   CONTRAINDICATED | MAJOR | MODERATE | MINOR
3. Explicitly check red flags:
   - Ibuprofen + CKD
   - Ibuprofen + Aspirin (GI bleed risk)

OUTPUT (STRICT JSON ONLY):
{{
  "severity": "LEVEL",
  "interaction_graph": {{
    "drug_drug": [{{ "relation": "Drug A + Drug B", "effect": "Short summary of effect", "risk": "level" }}],
    "drug_disease": [{{ "relation": "Drug + Condition", "effect": "Short summary of effect", "risk": "level" }}],
    "drug_food": [{{ "relation": "Drug + Food", "effect": "Short summary of effect" }}]
  }},
  "findings": ["short point"],
  "soap_note": "Very concise SOAP summary"
}}
"""

    # -----------------------
    # Gemini call with fallback
    # -----------------------
    try:
        key = api_key_manager.get_key()
        client = genai.Client(api_key=key)

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )

        text = response.text.strip()

        # Remove accidental markdown fences
        text = re.sub(r"^```.*?\n", "", text)
        text = re.sub(r"\n```$", "", text)

        result = json.loads(text)

        # -----------------------
        # Defensive validation
        # -----------------------
        if not isinstance(result, dict):
            raise ValueError("Model response is not a JSON object")

        result.setdefault("severity", "MINOR")
        result.setdefault("interaction_graph", {})
        result.setdefault("findings", [])
        result.setdefault("soap_note", "")

        logger.info(f"Interaction analysis complete | Severity: {result['severity']}")
        return result

    # -----------------------
    # JSON failure fallback
    # -----------------------
    except json.JSONDecodeError as e:
        logger.error("JSON parsing failed", exc_info=True)
        return {
            "severity": "ERROR",
            "interaction_graph": {},
            "findings": ["Failed to parse AI response"],
            "soap_note": "Agent error: malformed JSON output."
        }

    # -----------------------
    # API / network / quota fallback
    # -----------------------
    except Exception as e:
        logger.error("Medication interaction agent failed", exc_info=True)
        return {
            "severity": "ERROR",
            "interaction_graph": {},
            "findings": [f"Interaction analysis failed: {str(e)}"],
            "soap_note": "Agent failure due to API or system error."
        }
