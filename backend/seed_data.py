from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Symptom, WellnessTip, FirstAid, Medication

DATABASE_URL = "sqlite:///./wellness.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # 🩺 Symptoms
    symptoms = [
        Symptom(symptom_name="headache", description="Pain or discomfort in the head or scalp."),
        Symptom(symptom_name="fever", description="Elevated body temperature, often with chills."),
        Symptom(symptom_name="nausea", description="Feeling of sickness with an urge to vomit."),
        Symptom(symptom_name="fatigue", description="Feeling of tiredness or lack of energy."),
        Symptom(symptom_name="cough", description="A reflex to clear the throat or lungs."),
        Symptom(symptom_name="dizziness", description="Feeling lightheaded or unsteady."),
        Symptom(symptom_name="body pain", description="Generalized discomfort or soreness."),
        Symptom(symptom_name="cold", description="Runny nose, sneezing, and mild fever."),
        Symptom(symptom_name="sore throat", description="Pain or irritation in the throat."),
        Symptom(symptom_name="migraine", description="Severe headache often with nausea or sensitivity to light.")
    ]

    # 💊 Medications
    medications = [
        Medication(condition="fever", medicine_name="Paracetamol"),
        Medication(condition="headache", medicine_name="Ibuprofen"),
        Medication(condition="nausea", medicine_name="Domperidone"),
        Medication(condition="migraine", medicine_name="Sumatriptan"),
        Medication(condition="cold", medicine_name="Cetirizine"),
        Medication(condition="cough", medicine_name="Dextromethorphan"),
        Medication(condition="body pain", medicine_name="Diclofenac"),
        Medication(condition="sore throat", medicine_name="Azithromycin"),
        Medication(condition="dizziness", medicine_name="Meclizine"),
        Medication(condition="fatigue", medicine_name="Vitamin B12 supplements")
    ]

    # 🌱 Wellness Tips – Specific Categories
    tips = [
        WellnessTip(category="hydration", tip_text="Drink at least 8 glasses of water daily."),
        WellnessTip(category="hydration", tip_text="Sip water throughout the day, not just when you're thirsty."),
        WellnessTip(category="hydration", tip_text="Coconut water is a great natural hydrator with electrolytes."),
        WellnessTip(category="sleep", tip_text="Aim for 7–9 hours of sleep each night."),
        WellnessTip(category="sleep", tip_text="Avoid screens 30 minutes before bedtime."),
        WellnessTip(category="mindfulness", tip_text="Practice deep breathing for 5 minutes daily."),
        WellnessTip(category="nutrition", tip_text="Eat balanced meals with fruits, vegetables, and whole grains."),
        WellnessTip(category="movement", tip_text="Stretch or walk for 10 minutes every hour."),
        WellnessTip(category="screen break", tip_text="Take a 5-minute break from screens every 30 minutes."),
        WellnessTip(category="mental health", tip_text="Write down 3 things you're grateful for each day."),
        WellnessTip(category="routine", tip_text="Wake up and sleep at consistent times."),
        WellnessTip(category="stress", tip_text="Try progressive muscle relaxation."),
        WellnessTip(category="energy", tip_text="Avoid heavy meals during work hours.")
    ]

    # 🌟 General Wellness Tips – For vague queries like "give me a wellness tip"
    general_tips = [
        WellnessTip(category="general", tip_text="Take short walks during the day to boost circulation."),
        WellnessTip(category="general", tip_text="Stay hydrated and avoid sugary drinks."),
        WellnessTip(category="general", tip_text="Practice gratitude to improve mental well-being."),
        WellnessTip(category="general", tip_text="Stretch your body after long periods of sitting."),
        WellnessTip(category="general", tip_text="Eat slowly and mindfully to aid digestion."),
        WellnessTip(category="general", tip_text="Get sunlight exposure for natural vitamin D."),
        WellnessTip(category="general", tip_text="Limit screen time before bed to improve sleep quality."),
        WellnessTip(category="general", tip_text="Take deep breaths when feeling overwhelmed."),
        WellnessTip(category="general", tip_text="Maintain a consistent daily routine."),
        WellnessTip(category="general", tip_text="Check in with yourself emotionally once a day.")
    ]

    # 🆘 First Aid
    first_aid = [
        FirstAid(issue="burn", steps="Cool the burn under running water for 10 minutes."),
        FirstAid(issue="cut", steps="Apply pressure to stop bleeding and clean the wound."),
        FirstAid(issue="fainting", steps="Lay the person down and elevate their legs."),
        FirstAid(issue="sprain", steps="Rest, ice, compress, and elevate the injured area."),
        FirstAid(issue="nosebleed", steps="Lean forward and pinch the nose for 10 minutes."),
        FirstAid(issue="choking", steps="Perform the Heimlich maneuver if trained."),
        FirstAid(issue="bee sting", steps="Remove the stinger and apply a cold compress."),
        FirstAid(issue="heatstroke", steps="Move to a cool place and hydrate slowly."),
        FirstAid(issue="eye irritation", steps="Rinse with clean water and avoid rubbing."),
        FirstAid(issue="minor fracture", steps="Immobilize the area and seek medical help.")
    ]

    # ✅ Helper to avoid duplicates
    def safe_add(model, field, value, obj):
        exists = db.query(model).filter(getattr(model, field) == value).first()
        if not exists:
            db.add(obj)

    # ✅ Insert all records safely
    for s in symptoms:
        safe_add(Symptom, "symptom_name", s.symptom_name, s)

    for m in medications:
        safe_add(Medication, "condition", m.condition, m)

    for t in tips + general_tips:
        safe_add(WellnessTip, "tip_text", t.tip_text, t)

    for f in first_aid:
        safe_add(FirstAid, "issue", f.issue, f)

    db.commit()
    db.close()
    print("✅ Seeded wellness.db successfully.")

if __name__ == "__main__":
    seed()
