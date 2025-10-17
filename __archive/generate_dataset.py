import pandas as pd
import os

# ✅ STEP 1: Make sure file is created in backend folder
output_path = os.path.join(os.path.dirname(__file__), "intent_dataset.csv")

# ✅ STEP 2: Create 240 dummy examples (40 per intent)
intents = (
    ["greeting"] * 40
    + ["ask_about_symptom"] * 40
    + ["query_first_aid"] * 40
    + ["ask_about_medication"] * 40
    + ["ask_about_wellness_tip"] * 40
    + ["express_emotion"] * 40
)

texts = [
    "Hello there!", "Hi!", "Good morning!", "Hey!", "How are you?"
] * 8 + [
    "I have a headache", "My stomach hurts", "I feel dizzy", "I am coughing"
] * 10 + [
    "What should I do if I burn my hand?", "How to treat a cut?", "First aid for fever?", "What to do for a sprain?"
] * 10 + [
    "Can I take paracetamol?", "Is ibuprofen safe?", "Should I use antibiotics?", "Can I take vitamin C daily?"
] * 10 + [
    "Give me a wellness tip", "How can I stay healthy?", "Suggest some exercise", "How to reduce stress?"
] * 10 + [
    "I feel sad", "I am happy", "I am anxious", "I feel scared"
] * 10

# ✅ Make sure lengths match
assert len(intents) == len(texts), "Mismatch between intents and texts!"

# ✅ Create DataFrame
df = pd.DataFrame({"text": texts, "label": intents})

# ✅ Save dataset
df.to_csv(output_path, index=False, encoding="utf-8")

print(f"✅ Dataset generated with {len(df)} samples at {output_path}")
