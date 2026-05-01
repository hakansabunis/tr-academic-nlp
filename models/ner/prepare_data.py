import json
import os
import random
from transformers import AutoTokenizer

input_file = r"C:\Users\SABUNIS\OneDrive\Desktop\tr-academic-nlp\docs\labeler-eval\api-sonnet-2k-cleaned.jsonl"
output_dir = r"C:\Users\SABUNIS\OneDrive\Desktop\tr-academic-nlp\models\ner\data"
model_name = "dbmdz/bert-base-turkish-cased"

label_list = [
    "O", 
    "B-YAZAR", "I-YAZAR", 
    "B-KURUM", "I-KURUM", 
    "B-YIL", "I-YIL", 
    "B-METODOLOJI", "I-METODOLOJI", 
    "B-DATASET", "I-DATASET", 
    "B-METRİK", "I-METRİK", 
    "B-DERGİ", "I-DERGİ"
]
label_to_id = {l: i for i, l in enumerate(label_list)}

# Save label mapping for the model configuration later
os.makedirs(r"C:\Users\SABUNIS\OneDrive\Desktop\tr-academic-nlp\models\ner", exist_ok=True)
with open(r"C:\Users\SABUNIS\OneDrive\Desktop\tr-academic-nlp\models\ner\label_mapping.json", "w", encoding="utf-8") as f:
    json.dump({"label_to_id": label_to_id, "id_to_label": {i: l for l, i in label_to_id.items()}}, f, ensure_ascii=False)

print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(model_name)

def prepare_dataset(jsonl_path, out_dir):
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    dataset = []
    dropped = 0
    
    for line in lines:
        data = json.loads(line)
        text = data.get("text", "")
        spans = data.get("spans", [])
        
        # Tokenize text and get character offsets
        tokenized = tokenizer(text, return_offsets_mapping=True, truncation=True, max_length=512)
        offsets = tokenized["offset_mapping"]
        input_ids = tokenized["input_ids"]
        attention_mask = tokenized["attention_mask"]
        
        # Initialize string labels
        str_labels = ["O"] * len(input_ids)
        
        for span in spans:
            start_char = span["start"]
            end_char = span["end"]
            entity_type = span["entity"]
            
            if entity_type not in ["YAZAR", "KURUM", "YIL", "METODOLOJI", "DATASET", "METRİK", "DERGİ"]:
                continue # Ignore unknown entities
                
            token_indices = []
            for i, (start_off, end_off) in enumerate(offsets):
                # Ignore special tokens
                if start_off == 0 and end_off == 0:
                    continue
                    
                # Check for overlap
                if start_off >= start_char and end_off <= end_char:
                    token_indices.append(i)
                elif start_off < end_char and end_off > start_char:
                    token_indices.append(i)
                    
            for idx, t_idx in enumerate(token_indices):
                if str_labels[t_idx] == "O":
                    if idx == 0:
                        str_labels[t_idx] = f"B-{entity_type}"
                    else:
                        str_labels[t_idx] = f"I-{entity_type}"
                        
        # Convert string labels to IDs, masking special tokens with -100
        labels = []
        for i, (start_off, end_off) in enumerate(offsets):
            if start_off == 0 and end_off == 0:
                labels.append(-100) # PyTorch ignores -100 in CrossEntropyLoss
            else:
                labels.append(label_to_id.get(str_labels[i], 0))
                
        dataset.append({
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "labels": labels,
            "tokens": tokenizer.convert_ids_to_tokens(input_ids),
            "str_labels": str_labels
        })
        
    # Split dataset
    random.seed(42)
    random.shuffle(dataset)
    split_idx = int(len(dataset) * 0.8)
    
    train_ds = dataset[:split_idx]
    eval_ds = dataset[split_idx:]
    
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "train.json"), "w", encoding="utf-8") as f:
        json.dump(train_ds, f, ensure_ascii=False)
    with open(os.path.join(out_dir, "eval.json"), "w", encoding="utf-8") as f:
        json.dump(eval_ds, f, ensure_ascii=False)
        
    print(f"Dataset prepared successfully.")
    print(f"Train size: {len(train_ds)}, Eval size: {len(eval_ds)}")
    
    # Print a debug example
    if len(train_ds) > 0:
        ex = train_ds[0]
        print("\n--- Example Alignment ---")
        for tok, lbl in zip(ex["tokens"], ex["str_labels"]):
            if tok not in ["[CLS]", "[SEP]"] and lbl != "O":
                print(f"{tok:15} -> {lbl}")

if __name__ == "__main__":
    prepare_dataset(input_file, output_dir)
