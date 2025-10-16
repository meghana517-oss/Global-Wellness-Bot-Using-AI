import os
import json
import torch
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, f1_score
from datasets import Dataset, DatasetDict
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments
)

# ✅ STEP 1: Load JSONL dataset
dataset_path = Path(__file__).parent / "intent_dataset.jsonl"
with open(dataset_path, "r", encoding="utf-8") as f:
    samples = [json.loads(line) for line in f if line.strip()]
df = pd.DataFrame(samples)
df = df.dropna(subset=["intent"])
df["text"] = df["text"].astype(str).str.strip()

# ✅ STEP 2: Define intents and encode labels
valid_intents = {
    "ask_about_medication",
    "ask_about_symptom",
    "ask_about_wellness_tip",
    "express_emotion",
    "greeting",
    "query_first_aid"
}
all_labels = sorted(valid_intents)
label2id = {label: i for i, label in enumerate(all_labels)}
id2label = {i: label for label, i in label2id.items()}
num_labels = len(label2id)

def parse_labels(label_field):
    if isinstance(label_field, list):
        return [l for l in label_field if l in label2id]
    elif isinstance(label_field, str):
        return [l.strip() for l in label_field.split(",") if l.strip() in label2id]
    return []

def encode_labels(label_list):
    vec = np.zeros(num_labels, dtype=np.float32)
    for l in label_list:
        vec[label2id[l]] = 1.0
    return vec

df["label_list"] = df["intent"].apply(parse_labels)
df["label_vec"] = df["label_list"].apply(encode_labels)

# ✅ STEP 3: Train/test split
train_texts, test_texts, train_labels, test_labels = train_test_split(
    df["text"], df["label_vec"], test_size=0.2, random_state=42
)
train_df = pd.DataFrame({"text": train_texts, "label_vec": train_labels})
test_df = pd.DataFrame({"text": test_texts, "label_vec": test_labels})
dataset = DatasetDict({
    "train": Dataset.from_pandas(train_df),
    "test": Dataset.from_pandas(test_df)
})

# ✅ STEP 4: Tokenization
model_name = "bert-base-multilingual-cased"
tokenizer = AutoTokenizer.from_pretrained(model_name)

def tokenize(batch):
    enc = tokenizer(batch["text"], padding="max_length", truncation=True, max_length=64)
    enc["labels"] = [np.array(vec, dtype=np.float32) for vec in batch["label_vec"]]
    return enc

encoded = dataset.map(tokenize, batched=True)
encoded.set_format(type="torch", columns=["input_ids", "attention_mask", "labels"])

# ✅ STEP 5: Load model
model_dir = Path(__file__).parent / "intent_model_multi"
model = AutoModelForSequenceClassification.from_pretrained(
    model_dir if model_dir.exists() else model_name,
    num_labels=num_labels,
    problem_type="multi_label_classification"
)

# ✅ STEP 6: Training setup
training_args = TrainingArguments(
    output_dir=str(model_dir),
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=4,
    learning_rate=2e-5,
    logging_dir=str(model_dir / "logs"),
    logging_steps=10,
    save_strategy="epoch",
    seed=42
)

# ✅ STEP 7: Metrics
def compute_metrics(pred):
    probs = torch.sigmoid(torch.tensor(pred.predictions)).numpy()
    y_true = np.array(pred.label_ids)
    y_pred = (probs > 0.4).astype(int)

    report = classification_report(
        y_true,
        y_pred,
        target_names=[id2label[i] for i in range(num_labels)],
        digits=3,
        zero_division=0
    )
    print("\n📊 Classification Report:\n", report)

    with open(model_dir / "classification_report.txt", "w", encoding="utf-8") as f:
        f.write(report)

    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "f1": f1_score(y_true, y_pred, average="weighted")
    }

# ✅ STEP 8: Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=encoded["train"],
    eval_dataset=encoded["test"],
    tokenizer=tokenizer,
    compute_metrics=compute_metrics
)

# ✅ STEP 9: Prediction function
def predict_intents(text, threshold=0.3):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    device = model.device
    inputs = {k: v.to(device) for k, v in inputs.items()}
    model.eval()
    with torch.no_grad():
        logits = model(**inputs).logits
        probs = torch.sigmoid(logits).squeeze().cpu().numpy()
        intents = [id2label[i] for i, p in enumerate(probs) if p > threshold]
        confidence_scores = {id2label[i]: float(p) for i, p in enumerate(probs)}
        return {
            "intents": intents,
            "confidence_scores": confidence_scores
        }

# ✅ STEP 10: Train and evaluate
if __name__ == "__main__":
    trainer.train()
    trainer.evaluate()
    model.save_pretrained(str(model_dir))
    tokenizer.save_pretrained(str(model_dir))
    print(f"🎉 Model trained and saved to {model_dir}")

    with open(model_dir / "label_map.json", "w", encoding="utf-8") as f:
        json.dump({"id2label": id2label, "label2id": label2id}, f, indent=2)

    print("\n🧠 Sample predictions:")
    for query in [
        "Hi, I feel anxious and need a wellness tip",
        "मुझे सिरदर्द है और मुझे प्राथमिक उपचार चाहिए",
        "Hello, I need medicine and a wellness suggestion",
        "I feel sad and have a fever",
        "स्वस्थ रहने के उपाय बताओ और सिरदर्द के लिए क्या करें?",
        "What should I do for a burn?",
        "How to treat a bleeding wound?",
        "मधुमक्खी के काटने पर क्या करें?"
    ]:
        result = predict_intents(query)
        print(f"{query} → {result['intents']}")
