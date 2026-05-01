import os
import json
import numpy as np
import torch
from datasets import load_dataset
from transformers import (
    AutoModelForTokenClassification,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForTokenClassification
)

# Otomatik bağımlılık kurulumu
import sys
try:
    import evaluate
except ImportError:
    print("Gerekli paketler yükleniyor (evaluate, seqeval)...")
    os.system(f"{sys.executable} -m pip install evaluate seqeval")
    import evaluate

def main():
    base_dir = r"C:\Users\SABUNIS\OneDrive\Desktop\tr-academic-nlp\models\ner"
    data_dir = os.path.join(base_dir, "data")
    output_dir = os.path.join(base_dir, "trakad-ner-v1")
    model_name = "dbmdz/bert-base-turkish-cased"

    print("GPU Durumu:", "Aktif" if torch.cuda.is_available() else "Pasif (CPU'da çalışacak)")

    # Etiket haritasını yükle
    with open(os.path.join(base_dir, "label_mapping.json"), "r", encoding="utf-8") as f:
        mapping = json.load(f)
        label2id = mapping["label_to_id"]
        id2label = {int(k): v for k, v in mapping["id_to_label"].items()}

    # Verisetlerini yükle
    datasets = load_dataset("json", data_files={
        "train": os.path.join(data_dir, "train.json"),
        "validation": os.path.join(data_dir, "eval.json")
    })

    print("Model ve Tokenizer yükleniyor...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForTokenClassification.from_pretrained(
        model_name,
        num_labels=len(label2id),
        id2label=id2label,
        label2id=label2id
    )

    data_collator = DataCollatorForTokenClassification(tokenizer)
    metric = evaluate.load("seqeval")

    label_list = [id2label[i] for i in range(len(id2label))]

    def compute_metrics(p):
        predictions, labels = p
        predictions = np.argmax(predictions, axis=2)

        # PyTorch CrossEntropyLoss için -100 olanları temizle
        true_predictions = [
            [label_list[p] for (p, l) in zip(prediction, label) if l != -100]
            for prediction, label in zip(predictions, labels)
        ]
        true_labels = [
            [label_list[l] for (p, l) in zip(prediction, label) if l != -100]
            for prediction, label in zip(predictions, labels)
        ]

        results = metric.compute(predictions=true_predictions, references=true_labels)
        return {
            "precision": results["overall_precision"],
            "recall": results["overall_recall"],
            "f1": results["overall_f1"],
            "accuracy": results["overall_accuracy"],
        }

    # 3050 Ti VRAM Dostu Ayarlar
    # Batch size 8 ve fp16=True sayesinde 4GB VRAM'e sığacaktır.
    training_args = TrainingArguments(
        output_dir=output_dir,
        eval_strategy="epoch",
        learning_rate=2e-5,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        num_train_epochs=3,
        weight_decay=0.01,
        fp16=torch.cuda.is_available(), 
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1"
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=datasets["train"],
        eval_dataset=datasets["validation"],
        processing_class=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics
    )

    print("Eğitim (Fine-Tuning) başlatılıyor...")
    trainer.train()

    print(f"Eğitim tamamlandı! Model kaydediliyor: {output_dir}")
    trainer.save_model(output_dir)

if __name__ == "__main__":
    main()
