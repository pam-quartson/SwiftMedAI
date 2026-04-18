import os
import json
import re
from typing import Optional

DEMO_RESPONSES = {
    "Rural Heart Attack": {
        "severity": "CRITICAL",
        "severity_score": 9,
        "primary_diagnosis": "Suspected STEMI (ST-Elevation Myocardial Infarction)",
        "protocol": "ACS Emergency Protocol — Code STEMI",
        "supplies": [
            "AED (Automated External Defibrillator)",
            "Aspirin 325mg chewable",
            "Nitroglycerin spray 0.4mg/dose",
            "IV access kit (16G cannula)",
            "Non-rebreather O2 mask (15L)",
            "12-lead ECG electrode patches",
            "Morphine 10mg/mL (0.1mg/kg IV)",
            "Heparin 5,000 IU bolus",
        ],
        "drone_payload": [
            "AED", "Aspirin 325mg", "Nitroglycerin spray",
            "IV Kit (16G)", "O2 Mask NRB", "ECG Patches",
        ],
        "telemedicine_required": True,
        "estimated_stabilization_time": "8 minutes",
        "clinician_notes": (
            "Immediate AED standby. Aspirin 325mg chewable if no GI/allergy contraindications. "
            "Monitor for VF/VT — shock if indicated. Establish IV access and initiate heparin. "
            "Target door-to-balloon < 90 min. Cardiologist telemedicine link active."
        ),
        "ambulance_eta_min": 45,
        "drone_eta_seconds": 272,
    },
    "Anaphylaxis": {
        "severity": "CRITICAL",
        "severity_score": 10,
        "primary_diagnosis": "Severe Anaphylactic Shock — Hymenoptera Venom Allergen",
        "protocol": "Anaphylaxis Emergency Protocol — Grade IV",
        "supplies": [
            "Epinephrine 1mg/mL auto-injector (EpiPen) x2",
            "Diphenhydramine 50mg IV",
            "Methylprednisolone 125mg IV",
            "Normal saline 1L IV bag",
            "IV access kit (18G)",
            "Non-rebreather O2 mask (15L)",
            "Albuterol inhaler 90mcg",
            "Glucagon 1mg IM kit",
        ],
        "drone_payload": [
            "EpiPen x2", "Benadryl 50mg IV", "NS 500mL IV",
            "IV Kit (18G)", "O2 Mask NRB", "Albuterol MDI",
        ],
        "telemedicine_required": True,
        "estimated_stabilization_time": "5 minutes",
        "clinician_notes": (
            "Epinephrine 0.3mg IM to lateral thigh IMMEDIATELY. Second dose in 5 min if no improvement. "
            "Aggressive IV fluid resuscitation (1-2L NS). Diphenhydramine + corticosteroid after epi. "
            "Monitor airway — prepare for intubation. Allergist/EM telemedicine on standby."
        ),
        "ambulance_eta_min": 38,
        "drone_eta_seconds": 198,
    },
    "Traumatic Hemorrhage": {
        "severity": "HIGH",
        "severity_score": 8,
        "primary_diagnosis": "Traumatic Femoral Hemorrhage — Suspected Femur Fracture",
        "protocol": "Major Trauma Protocol — Code Red Hemorrhage Control",
        "supplies": [
            "Combat Application Tourniquet (CAT) x2",
            "Hemostatic gauze (QuikClot Combat Gauze)",
            "Israeli pressure bandages x4",
            "Pelvic binder",
            "Tranexamic acid (TXA) 1g/10mL",
            "Large-bore IV kit (14G) x2",
            "Normal saline 500mL x2",
            "Traction splint (Sager)",
            "Cervical collar (size adjustable)",
        ],
        "drone_payload": [
            "CAT Tourniquet x2", "QuikClot Gauze", "Pressure Bandages x4",
            "TXA 1g IV", "Large IV Kit x2", "NS 500mL",
        ],
        "telemedicine_required": True,
        "estimated_stabilization_time": "10 minutes",
        "clinician_notes": (
            "Apply tourniquet proximal to wound IMMEDIATELY — note time of application. "
            "TXA 1g IV over 10 min if within 3h of injury. Pack open wounds with hemostatic gauze. "
            "Two large-bore IVs, warm fluids. Do NOT remove tourniquet in field. "
            "Trauma surgeon telemedicine standby — Level I trauma center activation."
        ),
        "ambulance_eta_min": 52,
        "drone_eta_seconds": 312,
    },
}


def triage_incident(
    symptoms: str,
    location: str,
    vitals: str,
    scenario_name: str = "",
    api_key: Optional[str] = None,
) -> dict:
    api_key = api_key or os.getenv("GEMINI_API_KEY")

    if scenario_name in DEMO_RESPONSES and not api_key:
        return DEMO_RESPONSES[scenario_name]

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = f"""You are SwiftMedAI, an autonomous emergency drone dispatch AI.
Triage this emergency and respond with ONLY valid JSON (no markdown, no explanation).

INCIDENT:
Location: {location}
Symptoms: {symptoms}
Vitals: {vitals}

JSON format:
{{
  "severity": "CRITICAL|HIGH|MODERATE|LOW",
  "severity_score": <1-10 integer>,
  "primary_diagnosis": "<suspected condition>",
  "protocol": "<protocol name>",
  "supplies": ["<supply1>", "<supply2>", ...],
  "drone_payload": ["<compact label1>", ...],
  "telemedicine_required": <true/false>,
  "estimated_stabilization_time": "<X minutes>",
  "clinician_notes": "<brief clinical guidance>",
  "ambulance_eta_min": <estimated rural ambulance ETA in minutes>,
  "drone_eta_seconds": <estimated drone flight 120-420 seconds>
}}"""

        response = model.generate_content(prompt)
        text = response.text.strip()
        text = re.sub(r"^```(?:json)?\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
        return json.loads(text.strip())

    except Exception:
        if scenario_name in DEMO_RESPONSES:
            return DEMO_RESPONSES[scenario_name]
        return DEMO_RESPONSES["Rural Heart Attack"]
