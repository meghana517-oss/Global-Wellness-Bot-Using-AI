import json
import re
import torch
from transformers import MarianMTModel, MarianTokenizer
import os

# ✅ Load model
print("🔄 Loading model...")
model_name = "Helsinki-NLP/opus-mt-en-hi"
tokenizer = MarianTokenizer.from_pretrained(model_name)
model = MarianMTModel.from_pretrained(model_name)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)
print(f"✅ Model loaded on {device}")

# ✅ Hindi disclaimer
DISCLAIMER_HI = "यह जानकारी केवल शैक्षिक उद्देश्यों के लिए है और इसे चिकित्सीय सलाह नहीं माना जाना चाहिए। कृपया व्यक्तिगत मार्गदर्शन के लिए किसी स्वास्थ्य विशेषज्ञ से परामर्श लें।"

# ✅ Entity protection
ENTITY_MAP = {
    "LCMV": "__LCMV__",
    "Taenia solium": "__TAENIA__",
    "Whipworm": "__WHIPWORM__"
}

def protect_entities(text):
    for k, v in ENTITY_MAP.items():
        text = text.replace(k, v)
    return text

def restore_entities(text):
    for k, v in ENTITY_MAP.items():
        text = text.replace(v, k)
    return text

def strip_disclaimer(text):
    return re.sub(r"This information.*?guidance\.", "", text, flags=re.I).strip()

def batch_translate(texts):
    inputs = tokenizer(texts, return_tensors="pt", padding=True, truncation=True).to(device)
    outputs = model.generate(**inputs, max_length=256)
    return [tokenizer.decode(t, skip_special_tokens=True) for t in outputs]

# ✅ File paths
weak_file = "intent_hi_debug_failed.json"
patched_file = "intent_hi_debug_patched.json"

# ✅ Load weak entries
print(f"📁 Loading weak entries from {weak_file}...")
with open(weak_file, "r", encoding="utf-8") as f:
    weak_data = json.load(f)

# ✅ Load existing patched entries if resuming
if os.path.exists(patched_file):
    print(f"🔄 Resuming from existing {patched_file}...")
    with open(patched_file, "r", encoding="utf-8") as f:
        patched_dict = json.load(f)
else:
    patched_dict = {}

total = sum(len(v) for v in weak_data.values())
print(f"🔍 Found {total} weak entries to patch")

# ✅ Resume logic
for intent_group, entries in weak_data.items():
    patched_entries = patched_dict.get(intent_group, [])
    already_done = set(e["en"] for e in patched_entries)
    batch = []

    for i, entry in enumerate(entries):
        en_text = entry.get("en", "").strip()
        if not en_text or en_text in already_done:
            continue

        informative_en = strip_disclaimer(en_text)
        protected_en = protect_entities(informative_en)
        batch.append((entry, protected_en))

        if len(batch) == 50:
            print(f"🚀 Translating batch {i+1}/{len(entries)} in {intent_group}...")
            texts = [b[1] for b in batch]
            translations = batch_translate(texts)
            for (entry, _), hi_raw in zip(batch, translations):
                hi_final = f"{restore_entities(hi_raw).strip()} {DISCLAIMER_HI}"
                entry["hi"] = hi_final
                entry["notes"] = "Regenerated with Helsinki-NLP"
                patched_entries.append(entry)
            batch = []

            # ✅ Save progress every 500 entries
            if len(patched_entries) % 500 == 0:
                patched_dict[intent_group] = patched_entries
                with open(patched_file, "w", encoding="utf-8") as f:
                    json.dump(patched_dict, f, indent=2, ensure_ascii=False)
                print(f"💾 Checkpoint saved at {len(patched_entries)} entries for {intent_group}")

    # Final batch
    if batch:
        print(f"🚀 Translating final batch for {intent_group}...")
        texts = [b[1] for b in batch]
        translations = batch_translate(texts)
        for (entry, _), hi_raw in zip(batch, translations):
            hi_final = f"{restore_entities(hi_raw).strip()} {DISCLAIMER_HI}"
            entry["hi"] = hi_final
            entry["notes"] = "Regenerated with Helsinki-NLP"
            patched_entries.append(entry)

    patched_dict[intent_group] = patched_entries

# ✅ Final save
print(f"💾 Saving final patched file to {patched_file}...")
with open(patched_file, "w", encoding="utf-8") as f:
    json.dump(patched_dict, f, indent=2, ensure_ascii=False)

print(f"✅ Done! Patched {sum(len(v) for v in patched_dict.values())} entries.")
