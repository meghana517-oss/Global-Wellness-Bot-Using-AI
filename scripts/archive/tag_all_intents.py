import json
import os
import re

# 🔖 Map known conditions/topics to category tags
tag_map = {
    "Fever": ["pain", "first_aid"],
    "Cough": ["respiratory", "first_aid"],
    "Diarrhea": ["digestion", "first_aid"],
    "Vomiting": ["digestion", "first_aid"],
    "ORS": ["hydration", "medication"],
    "Yoga": ["lifestyle", "emotional_wellness"],
    "Meditation": ["lifestyle", "emotional_wellness"],
    "Healthy Diet": ["lifestyle", "preventive_care"],
    "Exercise Routine": ["lifestyle", "general_wellness"],
    "Mindfulness": ["emotional_wellness", "lifestyle"],
    "Menstrual Cramps": ["women_health", "pain"],
    "Toothache": ["pain", "first_aid"],
    "Ear Pain": ["pain", "first_aid"],
    "Eye Irritation": ["pain", "first_aid"],
    "Back Pain": ["pain", "first_aid"],
    "Leg Pain": ["pain", "first_aid"],
    "Body Ache": ["pain", "general_wellness"],
    "Fatigue": ["general_wellness"],
    "Stress": ["emotional_wellness"],
    "Anxiety": ["emotional_wellness"],
    "Mood Swings": ["emotional_wellness"],
    "Insomnia": ["emotional_wellness"],
    "Sleep Hygiene": ["lifestyle", "emotional_wellness"],
    "Hydration Tips": ["hydration", "preventive_care"],
    "Iron Deficiency": ["general_wellness", "nutrition"],
    "Vaccination": ["preventive_care"],
    "Mosquito Protection": ["preventive_care"],
    "Hygiene": ["preventive_care"],
    "Painkillers": ["medication"],
    "Antibiotic Awareness": ["medication"],
    "Choking": ["injury", "first_aid"],
    "Fainting": ["injury", "first_aid"],
    "Heatstroke": ["respiratory", "first_aid"],
    "Sprains and Strains": ["injury", "first_aid"],
    "Nosebleeds": ["injury", "first_aid"],
    "Asthma Awareness": ["respiratory", "medication"],
    "Emotional Wellness": ["emotional_wellness"],
}

# 🧠 Extract condition/topic from English text
def infer_condition(text):
    match = re.search(r"^([A-Z][a-z]+(?: [a-z]+){0,3})", text)
    return match.group(1).strip() if match else "Unknown"

try:
    print("🏷️ Tagging all intents")

    with open("intent_knowledge_base_combined_disclaimed_cleaned.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    tagged_data = {}

    for intent, entries in data.items():
        print(f"🔍 Tagging intent: {intent}")
        tagged_entries = []

        for entry in entries:
            text = entry.get("en", "")
            condition_or_topic = infer_condition(text)
            tags = tag_map.get(condition_or_topic, ["general_wellness"])

            tagged_entry = {
                "en": text,
                "hi": entry.get("hi", ""),
                "intent": intent,
                "condition": condition_or_topic,
                "tags": tags,
                "source": entry.get("source", "Unknown")
            }
            tagged_entries.append(tagged_entry)

        tagged_data[intent] = tagged_entries

    output_path = "intent_knowledge_base_tagged.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(tagged_data, f, indent=2, ensure_ascii=False)

    print("✅ Tagging complete")
    print("📁 Saved to:", os.path.abspath(output_path))

except Exception as e:
    print("❌ Error occurred:", e)
