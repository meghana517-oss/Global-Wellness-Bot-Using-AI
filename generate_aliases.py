import json
import re
from pathlib import Path

# 🔹 Load structured conditions
kb_path = Path("data_structured/structured_conditions.json")
with open(kb_path, "r", encoding="utf-8") as f:
    entries = json.load(f)

alias_map = {}

def extract_aliases(text: str, lang: str) -> list:
    aliases = [text.strip()]

    # Add acronym if present in parentheses
    match = re.search(r"\((.*?)\)", text)
    if match:
        aliases.append(match.group(1).strip())

    # English: tokenize by punctuation and space
    if lang == "en":
        tokens = re.sub(r"[^\w\s]", " ", text.lower()).split()
        aliases += tokens

    # Hindi: split by space only, preserve compound words
    elif lang == "hi":
        clean_text = text.replace("(", "").replace(")", "")
        tokens = clean_text.split()
        aliases += tokens

    return sorted(set(aliases))

# 🔹 Build alias map
for entry in entries:
    condition_en = entry["condition"]["en"].strip()
    condition_hi = entry["condition"]["hi"].strip()

    alias_map[condition_en] = {
        "en": extract_aliases(condition_en, "en"),
        "hi": extract_aliases(condition_hi, "hi")
    }

# 🔹 Save to separate file
alias_path = Path("data_structured/condition_aliases.json")
with open(alias_path, "w", encoding="utf-8") as f:
    json.dump(alias_map, f, indent=2, ensure_ascii=False)

print(f"✅ Clean alias file saved to {alias_path}")
