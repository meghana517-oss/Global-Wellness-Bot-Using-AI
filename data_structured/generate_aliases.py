import json
import re
from pathlib import Path

# 🔹 Load structured conditions
kb_path = Path("data_structured/structured_conditions.json")
with open(kb_path, "r", encoding="utf-8") as f:
    entries = json.load(f)

alias_map = {}

def extract_aliases(text: str) -> list:
    aliases = [text.strip()]
    # Add acronym if present in parentheses
    match = re.search(r"\((.*?)\)", text)
    if match:
        aliases.append(match.group(1).strip())
    # Add lowercase tokens
    tokens = re.sub(r"[^\w\s]", " ", text.lower()).split()
    aliases += tokens
    return list(set(aliases))

# 🔹 Build alias map
for entry in entries:
    condition_en = entry["condition"]["en"]
    condition_hi = entry["condition"]["hi"]

    alias_map[condition_en] = {
        "en": extract_aliases(condition_en),
        "hi": extract_aliases(condition_hi)
    }

# 🔹 Save to separate file
alias_path = Path("data_structured/condition_aliases.json")
with open(alias_path, "w", encoding="utf-8") as f:
    json.dump(alias_map, f, indent=2, ensure_ascii=False)

print(f"✅ Alias file saved to {alias_path}")
