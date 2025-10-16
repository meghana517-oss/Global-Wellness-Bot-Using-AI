import json
from datetime import datetime
from pathlib import Path
from backend.main import SessionLocal, ConditionInfo

# Path to JSON file
json_path = Path(__file__).resolve().parent.parent / "data_structured" / "structured_conditions_verified.json"

if not json_path.exists():
    raise FileNotFoundError(f"❌ JSON file not found at: {json_path}")

with open(json_path, "r", encoding="utf-8") as f:
    raw_data = json.load(f)

db = SessionLocal()
inserted = 0
skipped = 0

for i, entry in enumerate(raw_data):
    try:
        condition = ConditionInfo(
            condition_en=entry["condition"]["en"],
            condition_hi=entry["condition"]["hi"],
            description_en=entry["description"]["en"],
            description_hi=entry["description"]["hi"],
            symptom_en=entry["possible_symptom"]["en"],
            symptom_hi=entry["possible_symptom"]["hi"],
            first_aid_en=entry["first_aid_tips"]["en"],
            first_aid_hi=entry["first_aid_tips"]["hi"],
            prevention_en=entry["prevention_tips"]["en"],
            prevention_hi=entry["prevention_tips"]["hi"],
            disclaimer_en=entry["disclaimer"]["en"],
            disclaimer_hi=entry["disclaimer"]["hi"],
            intent_category=entry.get("condition", {}).get("en", "").lower().replace(" ", "_"),
            created_at=datetime.utcnow()
        )
        db.merge(condition)
        inserted += 1
    except KeyError as e:
        print(f"⚠️ Skipping entry {i} due to missing key: {e}")
        skipped += 1

db.commit()
db.close()

print(f"✅ Seeding complete: {inserted} inserted, {skipped} skipped.")
