import json
from pathlib import Path
from sqlalchemy import create_engine, Column, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# -----------------------
# SQLite Setup
# -----------------------
DATABASE_URL = "sqlite:///C:/Users/bantu/Downloads/Wellbot/backend/wellness.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# -----------------------
# Intent Category Mapping
# -----------------------
INTENT_CATEGORY_MAP = {
    # Symptoms & Diagnosis
    "Fever": "Symptoms & Diagnosis",
    "Headache": "Symptoms & Diagnosis",
    "Nausea": "Symptoms & Diagnosis",
    "Rash": "Symptoms & Diagnosis",
    "Fatigue": "Symptoms & Diagnosis",
    "Cough": "Symptoms & Diagnosis",
    "Leg Pain": "Symptoms & Diagnosis",
    "Body Ache": "Symptoms & Diagnosis",
    "Skin Issues": "Symptoms & Diagnosis",
    "Itching": "Symptoms & Diagnosis",
    "Back Pain": "Symptoms & Diagnosis",
    "Eye Irritation": "Symptoms & Diagnosis",
    "Hair Fall": "Symptoms & Diagnosis",
    "Vomiting": "Symptoms & Diagnosis",
    "Diarrhea": "Symptoms & Diagnosis",
    "Chest Pain": "Symptoms & Diagnosis",
    "Persistent Headache": "Symptoms & Diagnosis",
    "Child Fever": "Symptoms & Diagnosis",
    "Stomach Ache": "Symptoms & Diagnosis",

    # Diseases & Conditions
    "Dengue": "Diseases & Conditions",
    "Malaria": "Diseases & Conditions",
    "Typhoid": "Diseases & Conditions",
    "COVID-19": "Diseases & Conditions",
    "Flu (Influenza)": "Diseases & Conditions",
    "Iron Deficiency": "Diseases & Conditions",
    "High Blood Pressure": "Diseases & Conditions",
    "Asthma Awareness": "Diseases & Conditions",

    # First Aid & Emergency
    "Burns": "First Aid & Emergency",
    "Cuts": "First Aid & Emergency",
    "Dehydration": "First Aid & Emergency",
    "Nosebleeds": "First Aid & Emergency",
    "Heatstroke": "First Aid & Emergency",
    "Choking": "First Aid & Emergency",
    "Fainting": "First Aid & Emergency",
    "Painkillers": "First Aid & Emergency",
    "ORS": "First Aid & Emergency",

    # Wellness & Mental Health
    "Anxiety": "Wellness & Mental Health",
    "Insomnia": "Wellness & Mental Health",
    "Stress": "Wellness & Mental Health",
    "Mood Swings": "Wellness & Mental Health",
    "Emotional Wellness": "Wellness & Mental Health",
    "Feeling Drained": "Wellness & Mental Health",
    "Overwhelmed Emotion": "Wellness & Mental Health",

    # Lifestyle & Prevention
    "Hygiene": "Lifestyle & Prevention",
    "Vaccination": "Lifestyle & Prevention",
    "Mosquito Protection": "Lifestyle & Prevention",
    "Balanced Diet": "Lifestyle & Prevention",
    "Hydration Tips": "Lifestyle & Prevention",
    "Sleep Hygiene": "Lifestyle & Prevention",
    "Healthy Diet": "Lifestyle & Prevention",
    "Exercise Routine": "Lifestyle & Prevention",
    "Mindfulness": "Lifestyle & Prevention",
    "Yoga": "Lifestyle & Prevention",
    "Meditation": "Lifestyle & Prevention",
    "Antibiotic Awareness": "Lifestyle & Prevention",

    # Special Cases & Care
    "Menstrual Cramps": "Special Cases & Care",
    "Toothache": "Special Cases & Care",
    "Ear Pain": "Special Cases & Care",
    "Elderly Cough Care": "Special Cases & Care"
}

# -----------------------
# Table Definition
# -----------------------
class ConditionInfo(Base):
    __tablename__ = "conditions"
    condition_en = Column(String, primary_key=True)
    condition_hi = Column(String)
    description_en = Column(Text)
    description_hi = Column(Text)
    symptom_en = Column(Text)
    symptom_hi = Column(Text)
    first_aid_en = Column(Text)
    first_aid_hi = Column(Text)
    prevention_en = Column(Text)
    prevention_hi = Column(Text)
    disclaimer_en = Column(Text)
    disclaimer_hi = Column(Text)
    intent_category = Column(String)

Base.metadata.create_all(bind=engine)

# -----------------------
# Load JSON and Update DB
# -----------------------
json_path = Path(__file__).resolve().parent / "data_structured" / "structured_conditions_verified.json"

with open(json_path, "r", encoding="utf-8") as f:
    kb_data = json.load(f)

db = SessionLocal()
updated = 0
skipped = 0

for entry in kb_data:
    try:
        condition_en = entry["condition"]["en"].strip()
        category = INTENT_CATEGORY_MAP.get(condition_en, "Uncategorized")

        # Update only if condition exists
        existing = db.query(ConditionInfo).filter_by(condition_en=condition_en).first()
        if existing:
            existing.intent_category = category
            db.commit()
            print(f"🔄 Updated: {condition_en} → {category}")
            updated += 1
        else:
            print(f"⏭️ Skipped (not found): {condition_en}")
            skipped += 1

    except Exception as e:
        db.rollback()
        print(f"❌ Failed to update {entry.get('condition', {}).get('en', 'Unknown')}: {e}")

db.close()
print(f"\n✅ Update complete: {updated} updated, {skipped} skipped.")
