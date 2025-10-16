import json
import os

def detect_source(text):
    text = text.lower()
    if "cdc" in text or "centers for disease control" in text:
        return "CDC"
    elif "who" in text or "world health organization" in text:
        return "WHO"
    elif "opendengue" in text:
        return "OpenDengue"
    elif "mayo clinic" in text:
        return "Mayo Clinic"
    elif "health department" in text or "public health" in text:
        return "Local Health Authority"
    else:
        return "Unknown"

try:
    print("🔍 Refining sources in tagged dataset")

    with open("intent_knowledge_base_tagged.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    for intent, entries in data.items():
        for entry in entries:
            entry["source"] = detect_source(entry["en"])

    output_path = "intent_knowledge_base_tagged_refined.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("✅ Source refinement complete")
    print("📁 Saved to:", os.path.abspath(output_path))

except Exception as e:
    print("❌ Error occurred:", e)
