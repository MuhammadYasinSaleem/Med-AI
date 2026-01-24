from .red_flag_evaluator import evaluate_red_flags
from .triage_contract import TriageLevel
from .test_set_triage_agent import test_symptoms
from .api_key_manager import api_key_manager
from google import genai
import json
import re

def llm_triage(symptoms: list[str]) -> dict:
    """
    Use Gemini Pro to classify triage level and generate a layman-friendly message.
    Uses single API key with fallback system.
    """
    prompt = f"""
Patient reports these symptoms:
{', '.join(symptoms)}

- Give triage level: IMMEDIATE / VERY_URGENT / URGENT / STANDARD
- Be accurate: do not overstate or understate urgency
- Respond in the language of the symptoms
- Short, actionable, layperson-friendly message only, preferably one sentence
- Do NOT include diagnoses or extra explanation
- the symptoms might be just some traumatic event or medical condition. Do handle those appropriately.
- Respond ONLY in JSON: {{ "triage": "...", "message": "..." }}
"""

    try:
        key = api_key_manager.get_key()
        client = genai.Client(api_key=key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        text = response.text.strip()  # correct property per docs

        # Remove Markdown code fences if present
        text = re.sub(r"^```.*?\n", "", text)
        text = re.sub(r"\n```$", "", text)

        return json.loads(text)

    except Exception as e:
        print(f"[Warning] Triage API call failed: {e}")
        # Fallback if API call fails
        return {
            "triage": "STANDARD",
            "message": "Unable to determine urgency. Monitor symptoms and seek medical care if worsens."
        }


def triage_patient(symptoms: list[str]) -> dict:
    result = evaluate_red_flags(symptoms)

    if not result["matched_rules"]:
        llm_result = llm_triage(symptoms)
        # Get the triage value from LLM output
        raw_triage = llm_result.get("triage", "").upper().replace(" ", "_")  # normalize
        triage_map = {
            "IMMEDIATE": TriageLevel.IMMEDIATE,
            "VERY_URGENT": TriageLevel.VERY_URGENT,
            "URGENT": TriageLevel.URGENT,
            "STANDARD": TriageLevel.STANDARD
        }
        # Validate and fallback
        if raw_triage not in triage_map:
            print(f"[Warning] Unrecognized triage level from LLM: {raw_triage}, defaulting to STANDARD")
            raw_triage = "STANDARD"

        result["triage"] = triage_map[raw_triage]
        result["messages"].append(llm_result.get("message", ""))

    return result


# =========================
# Example usage
# =========================
if __name__ == "__main__":
    symptoms = ['headache', 'nausea', 'vomiting']
    print(triage_patient(symptoms))