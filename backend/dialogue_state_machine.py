from backend.knowledge_base import query_db, extract_keyword, LANGUAGE_MAP

class DialogueStateMachine:
    def __init__(self):
        self.state = "start"
        self.context = {}

    def transition(self, intent: str, query_text: str, confidence: float = 1.0) -> tuple:
        query_text = query_text.strip().lower()

        # 🔄 Translate embedded Hindi keywords
        for hindi_word, english_word in LANGUAGE_MAP.items():
            query_text = query_text.replace(hindi_word, english_word)

        # 🔄 Normalize synonyms
        for raw, canonical in {
            "migraine": "headache",
            "dizzy": "dizziness",
            "dizzzy": "dizziness",
            "diziness": "dizziness",
            "lightheaded": "dizziness",
            "faint": "dizziness",
            "tired": "fatigue",
            "sleepy": "fatigue"
        }.items():
            query_text = query_text.replace(raw, canonical)

        known_symptoms = ["headache", "fever", "cough", "cold", "nausea", "pain", "fatigue", "dizziness"]
        known_tips = ["hydration", "diet", "sleep", "stress", "anxiety", "energy", "routine", "fatigue"]
        known_first_aid = ["burn", "cut", "sprain", "bleeding", "injury", "wound", "headache"]
        known_greetings = ["नमस्ते", "hello", "hi", "hey", "सुप्रभात", "आप कैसे हैं", "greetings", "good morning", "good evening", "good afternoon"]

        # 🟢 Greeting
        if query_text in known_greetings or intent == "greeting":
            self.state = "awaiting_query"
            return "Hello! How can I support your wellness today?", "greeting"

        # 🟢 Medication
        if intent == "ask_about_medication":
            symptom = self.context.get("symptom", query_text)
            self.state = "medication"
            med = query_db("medications", symptom)
            return (med, intent) if med else ("", intent)

        # 🟢 Symptom
        if intent == "ask_about_symptom":
            keyword = extract_keyword(query_text, known_symptoms)
            self.context["symptom"] = keyword
            self.state = "symptom_logged"
            response = query_db("symptoms", keyword)
            return (response, intent) if response else ("", intent)

        # 🟢 First Aid
        if intent == "query_first_aid":
            keyword = extract_keyword(query_text, known_first_aid)
            self.state = "first_aid"
            aid = query_db("first_aid", keyword)
            return (aid, intent) if aid else ("", intent)

        # 🟢 Wellness Tip
        if intent == "ask_about_wellness_tip":
            keyword = extract_keyword(query_text, known_tips)
            self.state = "wellness_tip"
            tip = query_db("wellness_tips", keyword)
            return (tip, intent) if tip else ("", intent)

        # 🟢 Emotion
        if intent == "express_emotion":
            return "I'm here for you. It's okay to feel this way.", intent

        # 🟢 Unknown or unsupported
        return "", intent or "unknown"
