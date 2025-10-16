import json

# Load alias map and KB
with open("data_structured/condition_aliases.json", "r", encoding="utf-8") as f:
    alias_map = json.load(f)

with open("data_structured/structured_conditions_verified.json", "r", encoding="utf-8") as f:
    kb_data = json.load(f)

# Extract all condition names from KB
kb_conditions = set(entry["condition"]["en"].strip() for entry in kb_data)

# Check for alias keys missing in KB
missing = []
for alias_key in alias_map.keys():
    if alias_key.strip() not in kb_conditions:
        missing.append(alias_key)

# Report results
if missing:
    print("❌ Missing KB entries for alias keys:")
    for key in missing:
        print(f"- {key}")
else:
    print("✅ All alias keys have matching KB entries.")
