import json

def normalize(text):
    return text.lower().strip()

try:
    print("🚀 Starting full intent deduplication")

    with open("intent_knowledge_base_combined_disclaimed.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    total_removed = 0

    for intent, entries in data.items():
        print(f"\n🔍 Processing intent: {intent}")
        original_count = len(entries)
        seen = set()
        cleaned = []

        for entry in entries:
            norm_text = normalize(entry["en"])
            if norm_text not in seen:
                seen.add(norm_text)
                cleaned.append(entry)

        data[intent] = cleaned
        removed = original_count - len(cleaned)
        total_removed += removed

        print(f"Original: {original_count}, Cleaned: {len(cleaned)}, Removed: {removed}")

    with open("intent_knowledge_base_combined_disclaimed_cleaned.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ All intents cleaned. Total duplicates removed: {total_removed}")

except Exception as e:
    print("❌ Error occurred:", e)
