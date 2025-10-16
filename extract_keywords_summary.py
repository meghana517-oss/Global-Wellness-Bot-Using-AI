import json
import os
import re
from collections import Counter

def extract_keywords(text):
    # Grab capitalized phrases (likely conditions or topics)
    return re.findall(r"\b([A-Z][a-z]+(?: [a-z]+){0,2})\b", text)

def extract_source_phrases(text):
    text = text.lower()
    phrases = []
    if "cdc" in text or "centers for disease control" in text:
        phrases.append("CDC")
    if "who" in text or "world health organization" in text:
        phrases.append("WHO")
    if "opendengue" in text:
        phrases.append("OpenDengue")
    if "mayo clinic" in text:
        phrases.append("Mayo Clinic")
    if "health department" in text or "public health" in text or "shellfish monitoring" in text:
        phrases.append("Local Health Authority")
    return phrases

try:
    print("🔍 Extracting keywords and sources")

    with open("intent_knowledge_base_tagged.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    condition_counter = Counter()
    source_counter = Counter()

    for intent, entries in data.items():
        for entry in entries:
            text = entry["en"]
            for keyword in extract_keywords(text):
                condition_counter[keyword] += 1
            for source in extract_source_phrases(text):
                source_counter[source] += 1

    summary = {
        "top_conditions": condition_counter.most_common(100),
        "top_sources": source_counter.most_common()
    }

    output_path = "keyword_summary.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("✅ Keyword summary saved")
    print("📁 Saved to:", os.path.abspath(output_path))

except Exception as e:
    print("❌ Error occurred:", e)
