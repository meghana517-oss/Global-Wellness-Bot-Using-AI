from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

class IndicTrans2Translator:
    def __init__(self, src_lang, tgt_lang, model_name="Helsinki-NLP/opus-mt-en-hi"):
        self.src_lang = src_lang
        self.tgt_lang = tgt_lang
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

    def translate_paragraphs(self, paragraphs, batch_size=16):
        results = []
        for i in range(0, len(paragraphs), batch_size):
            batch = paragraphs[i:i+batch_size]
            inputs = self.tokenizer(batch, return_tensors="pt", padding=True, truncation=True).to(self.device)
            outputs = self.model.generate(**inputs, max_new_tokens=256)
            translations = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)
            results.extend(translations)
        return results
