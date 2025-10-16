import re
from difflib import get_close_matches
from typing import List, Dict

from backend.main import SessionLocal
from backend.models import Symptom, Medication, WellnessTip, FirstAid
from backend.knowledge_base import LANGUAGE_MAP

# 🔹 Canonical symptom mapping
SYMPTOM_CANONICAL = {
    "migraine": "headache",
    "head pain": "headache",
    "dizzzy": "dizziness",
    "diziness": "dizziness",
    "lightheaded": "dizziness",
    "faint": "dizziness",
    "tired": "fatigue",
    "sleepy": "fatigue",
    "temperature": "fever",
    "high temperature": "fever",
    "feverish": "fever"
}

# 🔹 Synonym mapping across all intents
SYNONYM_MAP = {
    "flu": "cold",
    "rhinitis": "cold",
    "sneezing": "cold",
    "runny nose": "cold",
    "blocked nose": "cold",
    "nasal congestion": "cold",
    "body heat": "fever",
    "temperature": "fever",
    "feverish": "fever",
    "head pain": "headache",
    "migraine": "headache",
    "tiredness": "fatigue",
    "exhausted": "fatigue",
    "sleepy": "fatigue",
    "lightheaded": "dizziness",
    "dizzy": "dizziness",
    "nauseated": "nausea",
    "pill": "medicine",
    "tablet": "medicine",
    "drug": "medicine",
    "remedy": "medicine",
    "hydrate": "hydration",
    "hydrated": "hydration",
    "water": "hydration",
    "nutrition": "diet",
    "rest": "sleep",
    "relax": "stress",
    "routine": "routine",
    "wellness": "routine",
    "tip": "routine",
    "injured": "injury",
    "wound": "cut",
    "bleed": "bleeding",
    "burned": "burn",
    "sad": "hopeless",
    "anxious": "worried",
    "angry": "frustrated",
    "depressed": "hopeless",
    "lonely": "isolated"
}

# 🔹 Intent to table mapping
INTENT_TABLE_MAP = {
    "ask_about_symptom": "symptoms",
    "ask_about_medication": "medications",
    "ask_about_wellness_tip": "wellness_tips",
    "query_first_aid": "first_aid"
}

# 🔹 Static responses
STATIC_RESPONSES = {
    "greeting": "Hello! How can I support your wellness today?",
    "express_emotion": "I'm here for you. It's okay to feel this way."
}

# 🔹 Keyword lists for each table
COLUMN_KEYWORDS = {
    "symptoms": [
        "headache", "fever", "cough", "cold", "nausea", "pain", "fatigue", "dizziness", "sore throat"
    ],
    "medications": [
        "fever", "cold", "pain", "headache", "dizziness", "fatigue", "nausea", "sore throat"
    ],
    "first_aid": [
        "burn", "cut", "sprain", "bleeding", "injury", "headache", "choking", "snake bite"
    ],
    "wellness_tips": [
        "hydration", "diet", "sleep", "stress", "anxiety", "energy", "routine", "fatigue", "mental health", "exercise"
    ]
}

class DialogueManager:
    def __init__(self):
        self.db = SessionLocal()

    def normalize_query(self, text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r"[^\w\s]", "", text)

        for hindi, eng in LANGUAGE_MAP.items():
            text = text.replace(hindi, eng)

        for raw, canonical in SYMPTOM_CANONICAL.items():
            text = text.replace(raw, canonical)

        for raw, canonical in SYNONYM_MAP.items():
            text = text.replace(raw, canonical)

        return text

    def extract_keyword(self, text: str, keywords: List[str], intent: str = "") -> str:
        text = self.normalize_query(text)
        for word in keywords:
            if word in text:
                return word
        for token in text.split():
            if token in SYNONYM_MAP and SYNONYM_MAP[token] in keywords:
                return SYNONYM_MAP[token]
            match = get_close_matches(token, keywords, n=1, cutoff=0.7)
            if match:
                return match[0]
        return ""

    def infer_intents(self, query: str) -> List[str]:
        query_lower = self.normalize_query(query)
        intents = []

        # Prioritize medication if medicine-related terms are present
        if any(word in query_lower for word in ["pill", "tablet", "medicine", "drug", "remedy"]):
            intents.append("ask_about_medication")

        if any(word in query_lower for word in ["hello", "hi", "hey", "greetings", "good morning", "good evening", "नमस्ते", "सुप्रभात"]):
            intents.append("greeting")

        if any(word in query_lower for word in COLUMN_KEYWORDS["symptoms"]):
            intents.append("ask_about_symptom")

        if any(word in query_lower for word in COLUMN_KEYWORDS["medications"]):
            if "ask_about_medication" not in intents:
                intents.append("ask_about_medication")

        if any(word in query_lower for word in COLUMN_KEYWORDS["wellness_tips"]):
            intents.append("ask_about_wellness_tip")

        if any(word in query_lower for word in ["overwhelmed", "anxious", "hopeless", "isolated", "not okay", "depressed", "worried"]):
            intents.append("express_emotion")

        if any(word in query_lower for word in COLUMN_KEYWORDS["first_aid"]):
            intents.append("query_first_aid")

        return intents if intents else []

    def query_database(self, table: str, keyword: str) -> str:
        try:
            if table == "symptoms":
                result = self.db.query(Symptom).filter(Symptom.symptom_name.ilike(f"%{keyword}%")).first()
                return f"Symptom info: {result.description}" if result else ""

            elif table == "medications":
                result = self.db.query(Medication).filter(Medication.condition.ilike(f"%{keyword}%")).first()
                return f"Recommended medicine: {result.medicine_name}" if result else ""

            elif table == "wellness_tips":
                result = self.db.query(WellnessTip).filter(WellnessTip.category.ilike(f"%{keyword}%")).first()
                return f"Wellness tip: {result.tip_text}" if result else ""

            elif table == "first_aid":
                result = self.db.query(FirstAid).filter(FirstAid.issue.ilike(f"%{keyword}%")).first()
                return f"First aid steps: {result.steps}" if result else ""

        except Exception as e:
            return f"⚠️ Database error: {str(e)}"

        return ""

    def generate_response(self, query_text: str) -> Dict[str, str]:
        intents = self.infer_intents(query_text)
        query_clean = self.normalize_query(query_text)

        for intent in intents:
            if intent in STATIC_RESPONSES:
                return {"intent": intent, "response": STATIC_RESPONSES[intent]}

            table = INTENT_TABLE_MAP.get(intent)
            if not table:
                continue

            keywords = COLUMN_KEYWORDS.get(table, [])
            keyword = self.extract_keyword(query_clean, keywords, intent)
            if not keyword:
                continue

            response = self.query_database(table, keyword)
            if response:
                return {"intent": intent, "response": response}

        # Log unmatched queries for future training
        with open("unmatched_queries.log", "a", encoding="utf-8") as f:
            f.write(query_text + "\n")

        return {"intent": "unknown", "response": "No exact match found in the knowledge base."}

    def close(self):
        self.db.close()
