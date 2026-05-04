import os
import pandas as pd
try:
    from sentence_transformers import SentenceTransformer, InputExample, losses
    from torch.utils.data import DataLoader
except ImportError:
    print("Kurulum yapılıyor: sentence-transformers")
    os.system("pip install sentence-transformers")
    from sentence_transformers import SentenceTransformer, InputExample, losses
    from torch.utils.data import DataLoader


def _find_latest_checkpoint(checkpoint_dir: str) -> str | None:
    """Return path of highest-step checkpoint subdir, or None.

    sentence-transformers writes checkpoints as `checkpoint-<step>/` or
    sometimes just `<step>/` depending on version — handle both.
    """
    if not os.path.isdir(checkpoint_dir):
        return None
    candidates = []
    for name in os.listdir(checkpoint_dir):
        full = os.path.join(checkpoint_dir, name)
        if not os.path.isdir(full):
            continue
        step_str = name.split("-")[-1] if "-" in name else name
        if step_str.isdigit():
            candidates.append((int(step_str), full))
    if not candidates:
        return None
    return max(candidates)[1]


def train_embedder(
    parquet_path: str,
    output_dir: str,
    base_model: str = "dbmdz/bert-base-turkish-cased",
    sample_size: int = 5000,
    batch_size: int = 8,
    checkpoint_save_steps: int = 25,
    checkpoint_save_total_limit: int = 2,
):
    """
    Unsupervised SimCSE fine-tuning, RTX 3050 Ti'da ~3.5h.

    Checkpoint stratejisi: her `checkpoint_save_steps` step'te bir snapshot
    `<output_dir>/checkpoints/<step>/` altına yazılır. Restart'ta en son
    checkpoint base model olarak yüklenir — kill -> resume = ağırlık kaybı yok.

    Not: Optimizer/scheduler state ST API'de checkpoint'e yazılmıyor, sadece
    model ağırlıkları. Kill sonrası restart "yeni bir mini-fine-tune" gibi
    devam eder; SimCSE tek epoch için bu kabul edilebilir.
    """
    if not os.path.exists(parquet_path):
        print(f"Veri bulunamadı: {parquet_path}. Lütfen önce Faz 1 (derive) scriptini çalıştırın.")
        return

    print(f"Veri yükleniyor: {parquet_path}")
    df = pd.read_parquet(parquet_path)

    sample_size = min(sample_size, len(df))
    df = df.dropna(subset=['abstract_tr']).sample(n=sample_size, random_state=42)
    sentences = df['abstract_tr'].tolist()

    print(f"Eğitim için {len(sentences)} adet tez özeti (abstract) seçildi.")

    train_examples = [InputExample(texts=[sent, sent]) for sent in sentences]
    train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=batch_size)

    checkpoint_dir = os.path.join(output_dir, "checkpoints")
    latest_ckpt = _find_latest_checkpoint(checkpoint_dir)

    if latest_ckpt:
        print(f"[RESUME] Son checkpoint bulundu, oradan devam: {latest_ckpt}")
        model = SentenceTransformer(latest_ckpt)
    else:
        print(f"[NEW] Taban model yükleniyor: {base_model}")
        model = SentenceTransformer(base_model)

    train_loss = losses.MultipleNegativesRankingLoss(model)

    total_steps = len(train_dataloader)
    eta_min = (total_steps * 20) // 60  # ~20s/step on RTX 3050 Ti
    ckpt_min = (checkpoint_save_steps * 20) // 60
    print(
        f"SimCSE Fine-Tuning başlatılıyor — {total_steps} step, "
        f"~{eta_min} dk total, checkpoint her {checkpoint_save_steps} step (~{ckpt_min} dk)"
    )

    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        epochs=1,
        warmup_steps=100,
        output_path=output_dir,
        checkpoint_path=checkpoint_dir,
        checkpoint_save_steps=checkpoint_save_steps,
        checkpoint_save_total_limit=checkpoint_save_total_limit,
        show_progress_bar=True,
    )

    print(f"Eğitim tamamlandı! Model kaydedildi: {output_dir}")
    print(f"Checkpoint klasörünü silebilirsiniz: {checkpoint_dir}")


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    parquet = os.path.join(base_dir, "data", "corpora", "full", "data.parquet")
    out = os.path.join(base_dir, "models", "embed", "trakad-embed-v1")

    train_embedder(parquet, out)
