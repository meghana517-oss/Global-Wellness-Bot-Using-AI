import requests

# Backend URL
BASE_URL = "http://localhost:8000/kb"

# Conditions to test
conditions = [
    "Dengue", "Malaria", "Typhoid", "LCMV", "COVID-19", "Fever", "Headache", "Dehydration", "Fatigue", "Stress"
]

# Intents to simulate
intents = [
    "ask_about_condition",
    "ask_about_symptom",
    "query_first_aid",
    "ask_about_prevention"
]

# Languages to test
languages = ["en", "hi"]

# Run tests
for condition in conditions:
    print(f"\n🔍 Testing condition: {condition}")
    for lang in languages:
        print(f"🌐 Language: {lang}")
        try:
            response = requests.get(f"{BASE_URL}/{condition}")
            if response.status_code != 200:
                print(f"❌ Failed: {response.status_code} - {response.text}")
                continue

            data = response.json()
            for intent in intents:
                if intent in data and lang in data[intent]:
                    print(f"✅ {intent}: {data[intent][lang][:60]}...")
                else:
                    print(f"⚠️ Missing {intent} in {lang}")
        except Exception as e:
            print(f"❌ Exception: {e}")
