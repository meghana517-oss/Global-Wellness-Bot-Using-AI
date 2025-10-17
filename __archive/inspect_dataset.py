import json

with open("intent_dataset.jsonl", "r", encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        line = line.strip()
        if not line:
            continue
        try:
            sample = json.loads(line)
            print(f"{i}: {sample['text']} → {sample['intent']}")
        except json.JSONDecodeError as e:
            print(f"Line {i} is invalid:", e)
