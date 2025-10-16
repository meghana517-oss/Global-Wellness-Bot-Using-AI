import sqlite3
import os
import difflib

# 🔗 Path to your SQLite database
db_path = os.path.join(os.path.dirname(__file__), "extend.db")

# 🔹 Hindi-to-English symptom mapping
LANGUAGE_MAP = {
    "बुखार": "fever",
    "सरदर्द": "headache",
    "थकान": "fatigue",
    "चक्कर": "dizziness",
    "खांसी": "cough",
    "ठंड": "cold",
    "मतली": "nausea",
    "दर्द": "pain",
    "नींद": "sleep",
    "तनाव": "stress",
    "ऊर्जा": "energy",
    "आहार": "diet",
    "हाइड्रेशन": "hydration",
    "दिनचर्या": "routine"
}

def extract_keyword(query_text: str, keywords: list) -> str:
    query_text = query_text.lower().strip()

    # 🔄 Step 0: Translate full query if it's a single Hindi word
    if query_text in LANGUAGE_MAP:
        query_text = LANGUAGE_MAP[query_text]

    # 🔄 Step 1: Translate embedded Hindi keywords
    for hindi_word, english_word in LANGUAGE_MAP.items():
        if hindi_word in query_text:
            query_text = query_text.replace(hindi_word, english_word)

    # ✅ Step 2: Exact match
    for word in keywords:
        if word in query_text:
            print(f"✅ Exact match found: {word}")
            return word

    # 🔍 Step 3: Fuzzy match
    query_words = query_text.split()
    for word in query_words:
        match = difflib.get_close_matches(word, keywords, n=1, cutoff=0.7)
        if match:
            print(f"🔍 Fuzzy match found: {match[0]}")
            return match[0]

    print(f"⚠️ No match found. Returning raw query: {query_text}")
    return query_text  # fallback

def query_db(table_name: str, query_text: str) -> str:
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 🗂️ Define searchable columns and keywords per table
        column_map = {
            "symptoms": ("symptom_name", ["headache", "fever", "cough", "cold", "nausea", "pain", "fatigue", "dizziness"]),
            "medications": ("condition", ["fever", "cold", "pain", "headache", "dizziness", "fatigue"]),
            "first_aid": ("issue", ["burn", "cut", "sprain", "bleeding", "injury", "headache"]),
            "wellness_tips": ("topic", ["hydration", "diet", "sleep", "stress", "anxiety", "energy", "routine", "fatigue"])
        }

        if table_name not in column_map:
            return "⚠️ Unknown action. No query executed."

        column_name, keywords = column_map[table_name]
        keyword = extract_keyword(query_text, keywords)
        print(f"🔎 Final keyword used for DB lookup: {keyword}")

        # 🔍 Case-insensitive match
        cursor.execute(
            f"SELECT * FROM {table_name} WHERE LOWER({column_name}) LIKE ?",
            (f"%{keyword.lower()}%",)
        )
        result = cursor.fetchone()

        # 🧠 Return formatted response
        if result:
            if table_name == "symptoms":
                return f"Symptom info: {result[1]}"
            elif table_name == "medications":
                return f"Recommended medicine: {result[1]}"
            elif table_name == "first_aid":
                return f"First aid steps: {result[1]}"
            elif table_name == "wellness_tips":
                return f"Wellness tip: {result[1]}"
        else:
            return "I didn’t quite catch that, but I’m listening. Want to try saying it another way."

    except sqlite3.OperationalError as e:
        return f"⚠️ Database error: {str(e)}"

    finally:
        if conn:
            conn.close()
