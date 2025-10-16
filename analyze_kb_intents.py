import json
from collections import defaultdict

# Load KB
with open("data_structured/structured_conditions.json", "r", encoding="utf-8") as f:
    kb = json.load(f)

# Define all relevant fields to inspect
fields_to_check = [
    "description",
    "possible_symptom",
    "first_aid_tips",
    "prevention_tips",
    "medication_guidance",
    "disclaimer",
    "translation_quality"
]

# Track entries per field
field_entries = defaultdict(list)

# Scan KB
for entry in kb:
    for field in fields_to_check:
        if field in entry and isinstance(entry[field], dict) and "en" in entry[field]:
            field_entries[field].append(entry)

# Display summary
print("\nField Presence Summary in structured_conditions.json\n" + "-"*50)
for field, entries in field_entries.items():
    print(f"\nField: {field}")
    print(f"Total entries: {len(entries)}")
    print("First 5 entries:")
    for i, entry in enumerate(entries[:5], start=1):
        name = entry.get("condition", {}).get("en", "Unnamed")
        print(f"  {i}. {name}")
