import json
import os
print("Saved to:", os.path.abspath("intent_knowledge_base_combined_disclaimed_cleaned.json"))


def normalize(text):
    return text.lower().strip()

try:
    print("🚀 Script started")

    with open("intent_knowledge_base_combined_disclaimed.json", "r", encoding="utf-8") as f:
        print("📂 File opened successfully")
        data = json.load(f)
        print("✅ JSON loaded")

    original_entries = data.get("ask_condition_info", [])
    print("Loaded ask_condition_info entries:", len(original_entries))

    seen = set()
    cleaned_entries = []

    for entry in original_entries:
        norm_text = normalize(entry["en"])
        if norm_text not in seen:
            seen.add(norm_text)
            cleaned_entries.append(entry)

    data["ask_condition_info"] = cleaned_entries
    with open("intent_knowledge_base_combined_disclaimed_cleaned.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Original entries: {len(original_entries)}")
    print(f"Cleaned entries: {len(cleaned_entries)}")
    print("Duplicates removed:", len(original_entries) - len(cleaned_entries))
    print("✅ Deduplication complete.")

except Exception as e:
    print("❌ Error occurred:", e)


