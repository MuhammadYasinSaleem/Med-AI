# interviews/red_flag_evaluator.py

from .red_flags import RED_FLAG_RULES
from .triage_contract import TriageLevel
import string

def normalize_symptom(symptom: str) -> str:
    """
    Normalize a symptom string: lowercase, remove punctuation, strip spaces.
    """
    if not symptom:
        return ""
    return symptom.lower().translate(str.maketrans('', '', string.punctuation)).strip()

def normalize_symptom_set(symptom_set):
    """
    Normalize a set or list of symptoms.
    """
    return {normalize_symptom(s) for s in symptom_set if s}

def match_rule(rule, user_symptoms_set):
    """
    Check if a rule matches the user's symptoms.
    """
    rule_all = normalize_symptom_set(rule.get("all", set()))
    rule_any = normalize_symptom_set(rule.get("any", set()))

    # All symptoms in 'all' must be present
    if rule_all and not rule_all.issubset(user_symptoms_set):
        return False

    # At least one symptom in 'any' must be present (if specified)
    if rule_any and not rule_any.intersection(user_symptoms_set):
        return False

    return True

def evaluate_red_flags(user_symptoms):
    """
    Evaluate user symptoms against RED_FLAG_RULES.

    Args:
        user_symptoms (list[str]): list of symptoms from the patient

    Returns:
        dict: {
            "triage": TriageLevel,
            "matched_rules": list of matched rule IDs,
            "messages": list of messages
        }
    """
    user_symptoms_set = normalize_symptom_set(set(user_symptoms))

    matched_rules = []
    messages = []
    highest_triage = TriageLevel.STANDARD  # default if nothing matches

    for rule in RED_FLAG_RULES:
        if match_rule(rule, user_symptoms_set):
            matched_rules.append(rule["id"])
            messages.append(rule["message"])
            # Determine the most urgent triage
            if rule["triage"].value < highest_triage.value:
                highest_triage = rule["triage"]

    return {
        "triage": highest_triage,
        "matched_rules": matched_rules,
        "messages": messages
    }

# =========================
# Example usage
# =========================
if __name__ == "__main__":
    sample_symptoms = [
        "Chest pain",
        "Radiates to arm or jaw",
        "Sweating"
    ]

    result = evaluate_red_flags(sample_symptoms)
    print("Triage Level:", result["triage"])
    print("Matched Rules:", result["matched_rules"])
    print("Messages:", result["messages"])
