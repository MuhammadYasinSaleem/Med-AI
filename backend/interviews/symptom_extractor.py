import google.generativeai as genai
import json
import re
import os
from typing import List

# Configure Gemini API with fallback system
def get_api_key():
    """Get API key with fallback: .env -> settings -> universal paid key"""
    universal_key = 'AIzaSyB8tF9bjsK1hNpzIG74uBOSIQKs77VGx9g'  # Universal paid key
    
    try:
        from django.conf import settings
        return settings.GEMINI_API_KEY or settings.GOOGLE_API_KEY or universal_key
    except:
        return os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY') or universal_key

api_key = get_api_key()
if api_key:
    genai.configure(api_key=api_key)


class SymptomExtractor:
    """
    Extracts user-reported symptoms from free text.
    No diagnosis. No triage. No urgency.
    """

    def extract(self, user_text: str) -> List[str]:
        prompt = f"""
You are a medical symptom extraction assistant.

User message:
"{user_text}"

TASK:
- Extract ONLY symptoms explicitly mentioned by the user
- Use simple, layman-understandable symptom phrases, in the original language
- Do NOT infer or guess missing symptoms
- Do NOT add diagnoses or causes
- If the users describes a traumatic event, or medical condition, just return that as the symptom
= try an not exagerate too much to scare the patient.
- If no symptoms are present, return an empty list

Respond ONLY in JSON:
{{ "symptoms": [string, string, ...] }}

No markdown. No explanations.
"""

        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)

            text = response.text.strip()

            # Safety cleanup (handles occasional ```json wrappers)
            text = re.sub(r"^```.*?\n", "", text)
            text = re.sub(r"\n```$", "", text)

            data = json.loads(text)
            return data.get("symptoms", [])

        except Exception as e:
            print("Symptom extraction failed:", e)
            return []

if __name__ == "__main__":

    symptoms_text = 'Severe body aches, with neck stiffness and an intense headache'
    extractor = SymptomExtractor()  # create instance
    extracted_symptoms = extractor.extract(symptoms_text)
    print(extracted_symptoms)