import json
import re
from typing import Any, Text, Dict, List, Optional
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from .actions_kb import ActionQueryKB

# ✅ DB logging imports
from backend.main import SessionLocal, Message
from datetime import datetime

# ✅ Logging helper
def log_message(email: str, user_text: str, bot_response: str, intent: str):
    try:
        db = SessionLocal()
        new_entry = Message(
            email=email,
            user_text=user_text,
            bot_response=bot_response,
            intent=intent if intent else "unknown",
            source="milestone3",
            timestamp=datetime.utcnow()
        )
        db.add(new_entry)
        db.commit()
        db.close()
    except Exception as e:
        print(f"❌ Failed to log message: {e}")

# ✅ Load structured KB
def load_kb():
    with open("data_structured/structured_conditions_verified.json", "r", encoding="utf-8") as f:
        return json.load(f)

# ✅ Load unified alias map
def load_condition_aliases():
    with open("data_structured/condition_aliases.json", "r", encoding="utf-8") as f:
        return json.load(f)

# ✅ Detect language from full message
def get_lang(tracker: Tracker) -> str:
    text = tracker.latest_message.get("text", "")
    return "hi" if re.search(r"[अ-ह]", text) else "en"

# ✅ Detect language from greeting only
def detect_language(text: str) -> str:
    return "hi" if re.search(r"[अ-ह]", text) else "en"

# ✅ Match best condition using alias scoring
def find_best_match(
    user_message: str,
    data: List[Dict],
    alias_map: Dict,
    lang: str,
    intent: Optional[str] = None,
    required_fields: Optional[List[str]] = None,
    debug: bool = False
) -> Optional[Dict]:
    # Normalize user message
    user_message_clean = re.sub(r"[^\w\s]", " ", user_message.lower()).strip()
    user_tokens = set(user_message_clean.split())

    best_entry = None
    best_score = 0

    for entry in data:
        # Skip if required fields are missing
        if required_fields:
            if any(field not in entry or not entry[field].get(lang) for field in required_fields):
                continue

        condition_key = entry["condition"]["en"].strip()
        aliases = [entry["condition"][lang].lower()]
        aliases += alias_map.get(condition_key, {}).get(lang, [])

        for alias in aliases:
            alias_clean = re.sub(r"[^\w\s]", " ", alias.lower()).strip()

            # ✅ Exact phrase match
            if alias_clean.strip() == user_message_clean.strip():
                if debug:
                    print(f"✅ Exact phrase match: '{alias_clean}'")
                return entry

            # ✅ Substring match (for Hindi phrases)
            if alias_clean in user_message_clean:
                if debug:
                    print(f"✅ Substring match: '{alias_clean}' in '{user_message_clean}'")
                return entry

            # ✅ Token overlap scoring
            alias_tokens = set(alias_clean.split())
            match_count = len(alias_tokens & user_tokens)

            if debug:
                print(f"🔍 Alias: '{alias_clean}' | Match count: {match_count}")

            if match_count > best_score:
                best_score = match_count
                best_entry = entry

    # ✅ Final return logic
    threshold = 2 if lang == "en" else 1
    if debug:
        print(f"🏁 Best score: {best_score} | Threshold: {threshold}")
    if best_entry and best_score >= threshold:
        return best_entry
    else:
        return None

# ✅ Action: Provide Symptoms
class ActionProvideSymptoms(Action):
    def name(self) -> Text:
        return "action_provide_symptoms"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        lang = get_lang(tracker)
        symptoms = tracker.get_slot("symptom") or []
        body_parts = tracker.get_slot("body_part") or []
        duration = tracker.get_slot("duration")
        user_message = tracker.latest_message.get("text", "").lower()

        data = load_kb()
        alias_map = load_condition_aliases()

        entry = find_best_match(...)

        if entry:
            response = (
                f"🩺 Commonly reported symptoms related to *{entry['condition'][lang]}* include:\n"
                f"{entry['possible_symptom'][lang]}\n\n"
                f"⚠️ Disclaimer:\n{entry['disclaimer'][lang]}"
            )
        else:
            entity_text = ", ".join(symptoms + body_parts) if (symptoms or body_parts) else "your symptoms"
            duration_text = f"\nDuration: {duration}" if duration else ""
            response = (
                f"🩺 Reported symptoms: {entity_text}{duration_text}\n\n"
                f"These may be managed with rest and hydration.\n\n"
                f"⚠️ Disclaimer:\nThis information is for educational purposes only and should not be considered medical advice."
            )

        dispatcher.utter_message(text=response)
        log_message("anonymous", user_message, response, "ask_about_symptom")
        return []

# ✅ Action: Provide FirstAid
class ActionProvideFirstAid(Action):
    def name(self) -> Text:
        return "action_provide_first_aid"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        lang = get_lang(tracker)
        symptoms = tracker.get_slot("symptom") or []
        body_parts = tracker.get_slot("body_part") or []
        medication = tracker.get_slot("medication")
        user_message = tracker.latest_message.get("text", "").lower()

        data = load_kb()
        alias_map = load_condition_aliases()

        entry = find_best_match(...)

        if entry:
            response = (
                f"Here’s some general first aid guidance related to *{entry['condition'][lang]}*:\n"
                f"{entry['first_aid_tips'][lang]}\n\n"
                f"⚠️ Disclaimer:\n{entry['disclaimer'][lang]}"
            )
        else:
            entity_text = ", ".join(symptoms + body_parts) if (symptoms or body_parts) else "your symptoms"
            med_text = f"\nMedication mentioned: {medication}" if medication else ""
            response = (
                f"You may be experiencing symptoms that are commonly managed with rest and hydration.\n\n"
                f"General first aid guidance for *{entity_text}*:{med_text}\n"
                f"- Sip water slowly\n- Use oral rehydration salts\n- Rest in a cool place\n\n"
                f"⚠️ Disclaimer:\nThis information is for educational purposes only and should not be considered medical advice."
            )

        dispatcher.utter_message(text=response)
        log_message("anonymous", user_message, response, "query_first_aid")
        return []

# ✅ Action: Provide Wellness Tip
class ActionProvideWellnessTip(Action):
    def name(self) -> Text:
        return "action_provide_wellness_tip"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        lang = get_lang(tracker)
        emotion = tracker.get_slot("emotion")
        age_group = tracker.get_slot("age_group")
        user_message = tracker.latest_message.get("text", "").lower()

        if emotion or age_group:
            focus = emotion or age_group
            response = (
                f"🧘 Wellness Tip related to *{focus}*:\n"
                f"- Maintain a balanced routine\n- Stay hydrated\n- Seek support when needed\n\n"
                f"⚠️ Disclaimer:\nThis information is for educational purposes only and should not be considered medical advice."
            )
        else:
            data = load_kb()
            alias_map = load_condition_aliases()
            entry = find_best_match(...)
            if entry:
                response = (
                    f"🧘 Wellness Tip related to *{entry['condition'][lang]}*:\n"
                    f"{entry['prevention_tips'][lang]}\n\n"
                    f"⚠️ Disclaimer:\n{entry['disclaimer'][lang]}"
                )
            else:
                response = "माफ़ कीजिए..." if lang == "hi" else "Sorry..."

        dispatcher.utter_message(text=response)
        log_message("anonymous", user_message, response, "ask_about_wellness_tip")
        return []
    
# ✅ Action: Health Info
class ActionHealthInfo(Action):
    def name(self) -> Text:
        return "action_health_info"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        lang = get_lang(tracker)
        user_message = tracker.latest_message.get("text", "").lower()
        data = load_kb()
        alias_map = load_condition_aliases()

        entry = find_best_match(
            user_message=user_message,
            data=data,
            alias_map=alias_map,
            lang=lang,
            intent="ask_about_condition",
            required_fields=[
                "description",
                "possible_symptom",
                "first_aid_tips",
                "prevention_tips",
                "disclaimer"
            ]
        )

        if entry:
            if lang == "hi":
                response = (
                    f"🩺 *{entry['condition']['hi']}*\n\n"
                    f"📄 विवरण: {entry['description']['hi']}\n"
                    f"⚠️ लक्षण: {entry['possible_symptom']['hi']}\n"
                    f"🧃 प्राथमिक उपचार: {entry['first_aid_tips']['hi']}\n"
                    f"🛡️ रोकथाम: {entry['prevention_tips']['hi']}\n\n"
                    f"📢 अस्वीकरण:\n{entry['disclaimer']['hi']}"
                )
            else:
                response = (
                    f"🩺 *{entry['condition']['en']}*\n\n"
                    f"📄 Description: {entry['description']['en']}\n"
                    f"⚠️ Symptoms: {entry['possible_symptom']['en']}\n"
                    f"🧃 First Aid: {entry['first_aid_tips']['en']}\n"
                    f"🛡️ Prevention: {entry['prevention_tips']['en']}\n\n"
                    f"📢 Disclaimer:\n{entry['disclaimer']['en']}"
                )
        else:
            response = (
                "माफ़ कीजिए, मुझे उस स्थिति की जानकारी नहीं मिली।"
                if lang == "hi"
                else "Sorry, I couldn't find health information for that condition."
            )

        dispatcher.utter_message(text=response)
        log_message("anonymous", user_message, response, "ask_about_condition")

        return [
            SlotSet("symptom", None),
            SlotSet("body_part", None),
            SlotSet("emotion", None),
            SlotSet("medication", None),
            SlotSet("duration", None)
        ]

# ✅ Action: Greet
class ActionGreet(Action):
    def name(self) -> Text:
        return "action_greet"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        user_text = tracker.latest_message.get("text", "")
        lang = detect_language(user_text)

        if lang == "hi":
            dispatcher.utter_message(text="नमस्ते! मैं वेलचैट हूँ, आपका स्वास्थ्य साथी। मैं आपकी कैसे मदद कर सकता हूँ?")
        else:
            dispatcher.utter_message(text="Hello! I'm WellChat, your wellness companion. How can I support you today?")
        return []

# ✅ Action: Goodbye
class ActionGoodbye(Action):
    def name(self) -> Text:
        return "action_goodbye"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        user_text = tracker.latest_message.get("text", "")
        lang = detect_language(user_text)

        if lang == "hi":
            dispatcher.utter_message(text="स्वस्थ रहें! अगर आपको स्वास्थ्य सुझाव या प्राथमिक उपचार की जानकारी चाहिए, तो मैं हमेशा यहाँ हूँ।")
        else:
            dispatcher.utter_message(text="Take care! If you need health tips or first aid info, I'm always here.")
        return []

# ✅ Action: Bot Identity
class ActionBotChallenge(Action):
    def name(self) -> Text:
        return "action_bot_challenge"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        user_text = tracker.latest_message.get("text", "")
        lang = detect_language(user_text)

        if lang == "hi":
            dispatcher.utter_message(text="मैं वेलचैट हूँ, एक स्वास्थ्य-केंद्रित एआई सहायक जो आपकी भलाई के सफर में मदद करता है।")
        else:
            dispatcher.utter_message(text="I'm WellChat, a health-focused AI assistant here to support your wellness journey.")
        return []


