import sqlite3
import os

# Define database path relative to this file
db_path = os.path.join(os.path.dirname(__file__), "wellness.db")

# Connect to SQLite database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# -----------------------
# Create Tables
# -----------------------

cursor.execute("""
    CREATE TABLE IF NOT EXISTS symptoms (
        symptom_name TEXT PRIMARY KEY,
        description TEXT
    );
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS medications (
        condition TEXT PRIMARY KEY,
        medicine_name TEXT
    );
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS first_aid (
        issue TEXT PRIMARY KEY,
        steps TEXT
    );
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS wellness_tips (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        tip_text TEXT NOT NULL
    );
""")

# -----------------------
# Seed Data
# -----------------------

symptom_data = [
    ("headache", "May be caused by stress, dehydration, or screen fatigue."),
    ("fever", "Elevated body temperature, often due to infection."),
    ("cough", "Could be dry or wet, linked to respiratory irritation."),
    ("cold", "Runny nose, sneezing, and mild fever."),
    ("fatigue", "Feeling tired or low energy, often due to poor sleep or stress."),
    ("dizziness", "Lightheadedness or imbalance, may be caused by dehydration.")
]

medication_data = [
    ("fever", "Paracetamol"),
    ("cold", "Cetirizine"),
    ("pain", "Ibuprofen"),
    ("headache", "Ibuprofen"),
    ("dizziness", "Meclizine"),
    ("fatigue", "Vitamin B12")
]

first_aid_data = [
    ("burn", "Cool with water, cover with clean cloth, avoid ointments."),
    ("cut", "Apply pressure, clean with antiseptic, bandage."),
    ("sprain", "Rest, ice, compress, elevate."),
    ("bleeding", "Apply pressure, elevate, seek medical help if severe."),
    ("choking", "Perform Heimlich maneuver or back blows."),
    ("snake bite", "Keep calm, immobilize limb, seek emergency care.")
]

wellness_tip_data = [
    ("hydration", "Drink at least 2 liters of water daily."),
    ("diet", "Include fruits, vegetables, and whole grains."),
    ("sleep", "Aim for 7–8 hours of sleep per night."),
    ("stress", "Try breathing exercises and short breaks during work."),
    ("anxiety", "Practice mindfulness or talk to someone you trust."),
    ("routine", "Maintain a consistent daily schedule."),
    ("energy", "Stretch regularly and take short walks."),
    ("fatigue", "Avoid caffeine late in the day and get sunlight exposure.")
]

# -----------------------
# Insert Data
# -----------------------

cursor.executemany("INSERT OR IGNORE INTO symptoms VALUES (?, ?);", symptom_data)
cursor.executemany("INSERT OR IGNORE INTO medications VALUES (?, ?);", medication_data)
cursor.executemany("INSERT OR IGNORE INTO first_aid VALUES (?, ?);", first_aid_data)
cursor.executemany("INSERT OR IGNORE INTO wellness_tips (category, tip_text) VALUES (?, ?);", wellness_tip_data)

# Finalize and close
conn.commit()
conn.close()

print("✅ wellness.db created and seeded successfully.")
