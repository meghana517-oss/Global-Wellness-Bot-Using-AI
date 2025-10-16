import csv
import os

# ✅ Paths
base_dir = os.path.dirname(__file__)
input_path = os.path.join(base_dir, "intent_dataset.csv")
output_path = os.path.join(base_dir, "intent_dataset_fixed.csv")

with open(input_path, "r", encoding="utf-8") as infile, open(output_path, "w", encoding="utf-8", newline="") as outfile:
    reader = csv.reader(infile)
    writer = csv.writer(outfile)

    for row in reader:
        # ❌ Skip empty or malformed rows
        if not row or len(row) < 2:
            continue

        # ✅ Clean and quote text field
        text = str(row[0]).strip()
        if "," in text and not (text.startswith('"') and text.endswith('"')):
            text = f'"{text}"'

        # ✅ Join and clean label field
        label_parts = row[1:]
        labels = ",".join([str(l).strip() for l in label_parts if str(l).strip()])

        # ❌ Skip rows with missing or invalid labels
        if not labels or labels.lower() == "nan":
            continue

        # ✅ Write cleaned row
        writer.writerow([text, labels])

print(f"✅ Cleaned CSV saved as {output_path}")
