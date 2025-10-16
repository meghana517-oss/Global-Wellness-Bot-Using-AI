import json
import os
import re

# Curated condition keywords (expandable)
known_conditions = [
    "Cysticercosis", "Whipworm", "Stroke", "Cancer", "Ataxia", "Dystonia",
    "Spinocerebellar ataxia", "Glycogen storage disease", "Danlos syndrome",
    "Congenital", "Heart", "Blood", "Hereditary", "Chromosome", "LCMV",
    "Marine toxins", "Yellow fever", "Ciguatera poisoning", "Shellfish poisoning"
]

# Filter out noisy phrases
noisy_starts = [
    "This information is", "Please consult a", "What are the", "How is", "There is no",
    "The", "Is", "Yes", "Review", "Summary", "Overview", "These resources", "Institute of",
    "National", "American", "United", "States", "Center", "Hospital"
]

def detect_condition(text):
    # Check known conditions first
    for keyword in known_conditions:
        if keyword.lower() in text.lower():
            return keyword

    # Fallback: extract first capitalized phrase that isn't noisy
    candidates = re.findall(r"\b([A-Z][a-z]+(?: [a-z]+){0,2})\b", text)
    for phrase in candidates:
        if not any(phrase.startswith(noise) for noise in noisy_starts):
            return phrase.strip()
    return "Unknown"

def detect_source(text):
    text = text.lower()
    if "cdc" in text or "centers for disease control" in text or "lcvm" in text:
        return "CDC"
    elif "who" in text or "world health organization" in text or "soil-transmitted helminth" in text:
        return "WHO"
    elif "opendengue" in text:
        return "OpenDengue"
    elif "mayo clinic" in text:
        return "Mayo Clinic"
    elif "health department" in text or "public health" in text or "shellfish monitoring" in text or "dinoflagellate toxins" in text:
        return "Local Health Authority"
    else:
        return "Unknown"

try:
    print("🔍 Refining condition and source tags (v2)")

    with open("intent_knowledge_base_tagged.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    for intent, entries in data.items():
        for entry in entries:
            entry["condition"] = detect_condition(entry["en"])
            entry["source"] = detect_source(entry["en"])

    output_path = "intent_knowledge_base_tagged_refined.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("✅ Smart tagging complete")
    print("📁 Saved to:", os.path.abspath(output_path))

except Exception as e:
    print("❌ Error occurred:", e)
