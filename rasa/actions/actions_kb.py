from typing import Any, Text, Dict, List, Optional
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import requests, json, os, re

# ✅ Backend imports
from backend.main import SessionLocal, ConditionInfo


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

# ✅ Load alias map
def load_condition_aliases() -> Dict:
    alias_path = os.path.join("data_structured", "condition_aliases.json")
    with open(alias_path, "r", encoding="utf-8") as f:
        return json.load(f)

class ActionQueryKB(Action):
    def name(self) -> Text:
        return "action_query_kb"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        condition = tracker.get_slot("condition")
        intent = tracker.latest_message["intent"].get("name")
        user_text = tracker.latest_message.get("text", "")
        lang = tracker.get_slot("language")

        if not lang or lang not in ["hi", "en"]:
            lang = "hi" if any("\u0900" <= c <= "\u097F" for c in user_text) else "en"

        aliases = load_condition_aliases()
        matched = False

        if condition:
            for canonical, lang_map in aliases.items():
                if condition in lang_map.get(lang, []):
                    condition = canonical
                    matched = True
                    break

        if not matched:
            for canonical, lang_map in aliases.items():
                if any(alias in user_text for alias in lang_map.get(lang, [])):
                    condition = canonical
                    matched = True
                    break

        if not matched:
            try:
                suggest_url = f"http://localhost:8000/kb/search?q={condition or user_text}"
                suggest_res = requests.get(suggest_url)
                if suggest_res.status_code == 200:
                    suggestions = suggest_res.json().get("suggestions", [])
                    if suggestions:
                        condition = suggestions[0]
                        matched = True
            except Exception as e:
                print(f"❌ Suggestion fetch failed: {e}")

        if not matched:
            fallback_response = "कृपया उस बीमारी का नाम बताएं जिसके बारे में आप जानना चाहते हैं।"
            dispatcher.utter_message(
                text=fallback_response,
                custom={"intent": intent, "condition": ""}
            )
            log_message("anonymous", user_text, fallback_response, "unknown")
            return []

        try:
            url = f"http://localhost:8000/kb/{condition}"
            response = requests.get(url)

            if response.status_code == 404:
                fallback_response = "माफ़ कीजिए, उस बीमारी की जानकारी नहीं मिली।"
                dispatcher.utter_message(
                    text=fallback_response,
                    custom={"intent": intent, "condition": condition}
                )
                log_message("anonymous", user_text, fallback_response, "unknown")
                return []

            data = response.json()

            if intent == "ask_about_condition" and "description" in data:
                bot_response = data["description"][lang]
            elif intent == "ask_about_symptom" and "possible_symptom" in data:
                bot_response = data["possible_symptom"][lang]
            elif intent == "query_first_aid" and "first_aid_tips" in data:
                bot_response = data["first_aid_tips"][lang]
            elif intent == "ask_about_prevention" and "prevention_tips" in data:
                bot_response = data["prevention_tips"][lang]
            elif "disclaimer" in data:
                bot_response = data["disclaimer"][lang]
            else:
                bot_response = "माफ़ कीजिए, जानकारी नहीं मिल सकी।"

            dispatcher.utter_message(
                text=bot_response,
                custom={"intent": intent, "condition": condition}
            )
            log_message("anonymous", user_text, bot_response, intent)

        except Exception as e:
            error_response = "सर्वर से जुड़ने में समस्या हुई। कृपया बाद में प्रयास करें।"
            dispatcher.utter_message(
                text=error_response,
                custom={"intent": intent, "condition": condition}
            )
            log_message("anonymous", user_text, error_response, "unknown")

        return []
