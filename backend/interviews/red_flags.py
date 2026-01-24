# interviews/red_flags.py

from .triage_contract import TriageLevel

RED_FLAG_RULES = [

    # =========================
    # CARDIAC EMERGENCIES
    # =========================
    {
        "id": "MI_CLASSIC",
        "all": {"chest pain", "radiates to arm or jaw"},
        "any": {"sweating", "nausea"},
        "triage": TriageLevel.IMMEDIATE,
        "message": "Possible heart attack. Call 1122 immediately!"
    },
    {
        "id": "MI_ATYPICAL",
        "all": {"chest discomfort", "shortness of breath"},
        "any": {"fatigue", "dizziness"},
        "triage": TriageLevel.IMMEDIATE,
        "message": "Possible heart attack (atypical). Call 1122 immediately!"
    },

    # =========================
    # STROKE
    # =========================
    {
        "id": "STROKE_FAST",
        "any": {"face droop", "arm weakness", "slurred speech"},
        "all": set(),
        "triage": TriageLevel.IMMEDIATE,
        "message": "Possible stroke detected. Call 1122 immediately!"
    },

    # =========================
    # SEVERE HEADACHE / SAH
    # =========================
    {
        "id": "SAH",
        "all": {"sudden severe headache", "neck stiffness"},
        "any": {"vomiting"},
        "triage": TriageLevel.IMMEDIATE,
        "message": "Possible brain bleed. Call 1122 immediately!"
    },

    # =========================
    # RESPIRATORY EMERGENCIES
    # =========================
    {
        "id": "PE",
        "all": {"shortness of breath", "leg swelling"},
        "any": {"chest pain"},
        "triage": TriageLevel.IMMEDIATE,
        "message": "Possible pulmonary embolism. Call 1122 immediately!"
    },
    {
        "id": "SEVERE_ASTHMA",
        "all": {"severe shortness of breath", "wheezing"},
        "any": {"unable to speak in full sentences"},
        "triage": TriageLevel.IMMEDIATE,
        "message": "Severe asthma attack. Call 1122 immediately!"
    },

    # =========================
    # METABOLIC EMERGENCIES
    # =========================
    {
        "id": "DKA",
        "all": {"diabetes", "vomiting"},
        "any": {"extreme thirst", "fast breathing", "confusion"},
        "triage": TriageLevel.IMMEDIATE,
        "message": "Possible diabetic ketoacidosis. Call 1122 immediately!"
    },

    {
        "id": "HYPOGLYCEMIA",
        "all": {"confusion", "sweating"},
        "any": {"shakiness", "dizziness"},
        "triage": TriageLevel.IMMEDIATE,
        "message": "Dangerously low blood sugar. Call 1122 immediately!"
    },

    # =========================
    # ALLERGIC EMERGENCIES
    # =========================
    {
        "id": "ANAPHYLAXIS",
        "all": {"difficulty breathing", "throat swelling"},
        "any": {"rash", "vomiting"},
        "triage": TriageLevel.IMMEDIATE,
        "message": "Severe allergic reaction. Call 1122 immediately!"
    },

    # =========================
    # INFECTIOUS EMERGENCIES
    # =========================
    {
        "id": "SEPSIS",
        "all": {"fever", "confusion"},
        "any": {"rapid breathing", "low blood pressure (if measurable)"},
        "triage": TriageLevel.IMMEDIATE,
        "message": "Possible sepsis. Call 1122 immediately!"
    },

    # =========================
    # TRAUMA
    # =========================
    {
        "id": "HEAD_INJURY",
        "all": {"head injury"},
        "any": {"loss of consciousness", "vomiting"},
        "triage": TriageLevel.IMMEDIATE,
        "message": "Serious head injury. Call 1122 immediately!"
    },
    {
        "id": "FRACTURE_SERIOUS",
        "all": {"deformed limb"},
        "any": {"inability to move limb", "severe pain"},
        "triage": TriageLevel.VERY_URGENT,
        "message": "Possible serious fracture. Go to ER within 1 hour."
    },

    # =========================
    # GI EMERGENCIES
    # =========================
    {
        "id": "GI_BLEED",
        "all": {"vomiting blood"},
        "any": {"black/tarry stools", "dizziness"},
        "triage": TriageLevel.IMMEDIATE,
        "message": "Possible gastrointestinal bleeding. Call 1122 immediately!"
    },

    {
        "id": "APPENDICITIS",
        "all": {"abdominal pain lower right"},
        "any": {"nausea", "vomiting", "fever"},
        "triage": TriageLevel.VERY_URGENT,
        "message": "Possible appendicitis. Go to ER within 2 hours."
    },

    # =========================
    # OBSTETRIC EMERGENCIES
    # =========================
    {
        "id": "ECTOPIC_PREGNANCY",
        "all": {"pregnant", "abdominal pain"},
        "any": {"dizziness", "vaginal bleeding"},
        "triage": TriageLevel.IMMEDIATE,
        "message": "Possible ectopic pregnancy. Call 1122 immediately!"
    },

    # =========================
    # TOXICOLOGY
    # =========================
    {
        "id": "OVERDOSE",
        "all": {"overdose", "poison ingestion"},
        "any": {"confusion", "vomiting", "unconscious"},
        "triage": TriageLevel.IMMEDIATE,
        "message": "Possible overdose. Call 1122 immediately!"
    },
    # 11. Pneumonia severe
    {
        "id": "SEVERE_PNEUMONIA",
        "all": {"fever", "shortness of breath"},
        "any": {"chest pain", "cough with sputum"},
        "triage": TriageLevel.VERY_URGENT,
        "message": "Possible severe pneumonia. Go to ER within 1 hour."
    },

    # 12. Meningitis (alternative combo)
    {
        "id": "MENINGITIS_ALT",
        "all": {"fever", "headache"},
        "any": {"neck stiffness", "sensitivity to light"},
        "triage": TriageLevel.IMMEDIATE,
        "message": "Possible meningitis. Call 1122 immediately!"
    },

    # 13. Severe dehydration (kids / elderly)
    {
        "id": "SEVERE_DEHYDRATION",
        "all": {"extreme thirst"},
        "any": {"dry mouth", "dizziness", "sunken eyes"},
        "triage": TriageLevel.VERY_URGENT,
        "message": "Severe dehydration suspected. Go to ER within 1 hour."
    },

    # 14. Tension / migraine with red flags
    {
        "id": "MIGRAINE_RED_FLAGS",
        "all": {"sudden severe headache"},
        "any": {"vomiting", "visual disturbances", "confusion"},
        "triage": TriageLevel.IMMEDIATE,
        "message": "Possible serious headache. Call 1122 immediately!"
    },

    # 15. Pulmonary edema / heart failure
    {
        "id": "PULMONARY_EDEMA",
        "all": {"shortness of breath"},
        "any": {"swelling in legs", "cough with frothy sputum"},
        "triage": TriageLevel.IMMEDIATE,
        "message": "Possible heart failure with fluid in lungs. Call 1122 immediately!"
    },

    # 16. Severe GI obstruction / volvulus
    {
        "id": "GI_OBSTRUCTION",
        "all": {"abdominal pain", "vomiting"},
        "any": {"abdominal distension", "no passing stool"},
        "triage": TriageLevel.VERY_URGENT,
        "message": "Possible bowel obstruction. Go to ER within 2 hours."
    },

    # 17. Severe burns
    {
        "id": "SEVERE_BURNS",
        "all": {"burn injury"},
        "any": {"large area affected", "charring", "blistering"},
        "triage": TriageLevel.VERY_URGENT,
        "message": "Severe burns. Go to ER within 1 hour."
    },

    # 18. Eye emergency - chemical / traumatic
    {
        "id": "EYE_EMERGENCY",
        "all": {"eye injury"},
        "any": {"severe pain", "loss of vision"},
        "triage": TriageLevel.IMMEDIATE,
        "message": "Serious eye injury. Call 1122 immediately!"
    },

    # 19. Epileptic seizure ongoing
    {
        "id": "STATUS_EPILEPTICUS",
        "all": {"seizure ongoing"},
        "any": {"loss of consciousness"},
        "triage": TriageLevel.IMMEDIATE,
        "message": "Ongoing seizure. Call 1122 immediately!"
    },

    # 20. Heat stroke / hyperthermia
    {
        "id": "HEAT_STROKE",
        "all": {"very high body temperature"},
        "any": {"confusion", "dizziness", "nausea"},
        "triage": TriageLevel.IMMEDIATE,
        "message": "Possible heat stroke. Call 1122 immediately!"
    },
    # 21. Severe Asthma (alternate combo)
    {
        "id": "SEVERE_ASTHMA_ALT",
        "all": {"shortness of breath", "wheezing"},
        "any": {"chest tightness", "unable to speak full sentences"},
        "triage": TriageLevel.IMMEDIATE,
        "message": "Severe asthma attack. Call 1122 immediately!"
    },

    # 22. Pulmonary Embolism (alternate combo)
    {
        "id": "PE_ALT",
        "all": {"shortness of breath"},
        "any": {"chest pain", "coughing blood", "leg swelling"},
        "triage": TriageLevel.IMMEDIATE,
        "message": "Possible pulmonary embolism. Call 1122 immediately!"
    },

    # 23. Acute Heart Failure (new combo)
    {
        "id": "ACUTE_HEART_FAILURE",
        "all": {"shortness of breath", "swelling in legs"},
        "any": {"fatigue", "coughing pink frothy sputum"},
        "triage": TriageLevel.IMMEDIATE,
        "message": "Possible acute heart failure. Call 1122 immediately!"
    },

    # 24. Severe Abdominal Pain (general emergency)
    {
        "id": "ACUTE_ABDOMINAL_EMERGENCY",
        "all": {"sudden severe abdominal pain"},
        "any": {"vomiting", "abdominal distension", "dizziness"},
        "triage": TriageLevel.IMMEDIATE,
        "message": "Severe abdominal emergency. Call 1122 immediately!"
    },

    # 25. Stroke – altered level of consciousness
    {
        "id": "STROKE_ALT",
        "all": {"confusion", "weakness on one side"},
        "any": {"slurred speech", "drooping face"},
        "triage": TriageLevel.IMMEDIATE,
        "message": "Possible stroke. Call 1122 immediately!"
    },

    # 26. Severe Infection – cellulitis / necrotizing infection
    {
        "id": "SEVERE_SKIN_INFECTION",
        "all": {"fever", "painful red swelling"},
        "any": {"blisters", "confusion"},
        "triage": TriageLevel.IMMEDIATE,
        "message": "Possible severe infection. Call 1122 immediately!"
    },

    # 27. Severe Vomiting / dehydration (general emergency)
    {
        "id": "SEVERE_VOMITING",
        "all": {"vomiting"},
        "any": {"dizziness", "extreme thirst", "confusion"},
        "triage": TriageLevel.VERY_URGENT,
        "message": "Severe vomiting / dehydration. Go to ER within 1 hour."
    },

    # 28. Heat exhaustion (less severe than heat stroke)
    {
        "id": "HEAT_EXHAUSTION",
        "all": {"dizziness", "heavy sweating"},
        "any": {"nausea", "fatigue"},
        "triage": TriageLevel.VERY_URGENT,
        "message": "Possible heat exhaustion. Go to ER within 2 hours."
    },

    # 29. Hypovolemic shock (from bleeding)
    {
        "id": "SHOCK_FROM_BLEEDING",
        "all": {"severe bleeding"},
        "any": {"dizziness", "confusion", "rapid heart rate"},
        "triage": TriageLevel.IMMEDIATE,
        "message": "Possible shock from bleeding. Call 1122 immediately!"
    },

    # 30. Allergic reaction (alternate combo)
    {
        "id": "ALLERGIC_REACTION_ALT",
        "all": {"hives", "swelling of lips or tongue"},
        "any": {"difficulty breathing", "dizziness"},
        "triage": TriageLevel.IMMEDIATE,
        "message": "Severe allergic reaction. Call 1122 immediately!"
    },
    # 31. Early sepsis (subtle)
    {
        "id": "EARLY_SEPSIS",
        "all": {"fever", "rapid breathing"},
        "any": {"confusion", "weakness", "cold hands/feet"},
        "triage": TriageLevel.IMMEDIATE,
        "message": "Possible early sepsis. Call 1122 immediately!"
    },

    # 32. Silent heart attack (atypical)
    {
        "id": "SILENT_MI",
        "all": {"fatigue", "shortness of breath"},
        "any": {"mild chest discomfort", "dizziness"},
        "triage": TriageLevel.IMMEDIATE,
        "message": "Possible silent heart attack. Call 1122 immediately!"
    },

    # 33. Stroke – subtle onset
    {
        "id": "STROKE_SUBTLE",
        "all": {"slight weakness on one side"},
        "any": {"mild speech difficulty", "face asymmetry"},
        "triage": TriageLevel.IMMEDIATE,
        "message": "Possible stroke. Call 1122 immediately!"
    },

    # 34. Hypoglycemia – mild early signs
    {
        "id": "HYPOGLYCEMIA_MILD",
        "all": {"shakiness", "sweating"},
        "any": {"hunger", "mild confusion"},
        "triage": TriageLevel.VERY_URGENT,
        "message": "Possible low blood sugar. Check quickly and seek help."
    },

    # 35. Dehydration – early signs
    {
        "id": "DEHYDRATION_MILD",
        "all": {"dry mouth", "thirst"},
        "any": {"dizziness", "fatigue"},
        "triage": TriageLevel.VERY_URGENT,
        "message": "Early dehydration. Drink fluids and monitor; go to ER if worsens."
    },

    # 36. Early pulmonary embolism
    {
        "id": "PE_SUBTLE",
        "all": {"shortness of breath"},
        "any": {"slight chest pain", "leg swelling"},
        "triage": TriageLevel.IMMEDIATE,
        "message": "Possible pulmonary embolism. Call 1122 immediately!"
    },

    # 37. Early meningitis
    {
        "id": "MENINGITIS_SUBTLE",
        "all": {"fever", "headache"},
        "any": {"neck stiffness", "light sensitivity"},
        "triage": TriageLevel.IMMEDIATE,
        "message": "Possible meningitis. Call 1122 immediately!"
    },

    # 38. Early appendicitis
    {
        "id": "APPENDICITIS_SUBTLE",
        "all": {"abdominal pain near belly button"},
        "any": {"nausea", "mild fever"},
        "triage": TriageLevel.VERY_URGENT,
        "message": "Possible early appendicitis. Go to ER soon."
    },

    # 39. Early ectopic pregnancy
    {
        "id": "ECTOPIC_SUBTLE",
        "all": {"abdominal pain"},
        "any": {"missed period", "light vaginal bleeding", "dizziness"},
        "triage": TriageLevel.IMMEDIATE,
        "message": "Possible ectopic pregnancy. Call 1122 immediately!"
    },

    # 40. Early stroke – balance/dizziness
    {
        "id": "STROKE_BALANCE",
        "all": {"sudden dizziness or loss of balance"},
        "any": {"slurred speech", "double vision"},
        "triage": TriageLevel.IMMEDIATE,
        "message": "Possible stroke affecting balance. Call 1122 immediately!"
    },
]
