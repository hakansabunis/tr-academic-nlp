# Learning Log — Faz 0 Research Notes

> **Purpose:** Per Requirement 1 (Faz 0 — Research & Learning Infrastructure),
> every technical component must be researched before implementation begins.
> Each topic below requires a minimum 200-word summary covering:
> - **Selected approach** + rationale
> - **Rejected alternatives** + why
> - **Hardware budget** for RTX 3050 Laptop 4GB GPU (where applicable)
>
> Entries are recorded in chronological order. Add the date when you start a
> topic and the date when you finish.

---

## Topic 1 — Web scraping with rate limiting

**Status:** Deprioritized — Faz 1 v2.3 `umutertugrul/turkish-academic-theses-dataset` üstüne derive ediyor; scraping yalnız DergiPark için opsiyonel ek (R3 → optional).
**Started:** 2026-04-30
**Completed:** 2026-04-30 (kapsam minimum'u; opsiyonel DergiPark için detay)

### Selected approach

DergiPark fetcher'ı opsiyonel kalıyor (Faz 1 minimum scope için zorunlu değil). Eğer yapılırsa minimum spec:

- **Library:** `httpx` (async-uyumlu, modern) + `tenacity` retry decorators veya manuel exponential backoff (3x retry, 2^n saniye delay)
- **Rate limit:** 1 saniye/istek (R3.2 default)
- **Error handling:** HTTP 429 / 5xx → log + retry; 4xx (404, 403) → log + skip; network error → retry
- **Storage:** JSONL stream-write (her record bir satır), `source_url` + `scraped_at` ISO-8601 timestamp
- **Deduplication:** DOI bazlı, ÖNCE save'den
- **KVKK:** Yalnız public metadata (title, author name, journal, year, DOI, abstract); kişisel iletişim hariç (R14.2)
- **Etik:** `robots.txt` kontrol + User-Agent string ("tr-academic-nlp/0.x.x; capstone-research; hakansabunis@gmail.com")

### Rejected alternatives

1. **Scrapy:** Reddedildi. Tek-sayfa fetcher için overkill; `httpx` + manuel queue yeterli.
2. **Selenium / Playwright headless browser:** Reddedildi. JavaScript rendering DergiPark'ın açık API'sinde gereksiz; static API + meta endpoint ile çalış.
3. **YÖK Tez Merkezi scraping:** Reddedildi (yol haritası v2.3 kararı). umutertugrul derive birincil kaynak.

### Hardware budget

- Inference yok — disk + network bound.
- ~10K-50K article × ~10 KB/article = 100-500 MB JSONL output
- 1s rate limit × 50K request = ~14 saat ardı ardına çalıştırma; gerçekçi: gece + bir gün
- Disk: <1 GB, RAM <500 MB


---

## Topic 2 — BERTurk fine-tuning for token classification

**Used in:** Faz 3 (NER `trakad-ner-v1`), Faz 6.5 (AI detector `trakad-detector-v1`).
**Started:** 2026-04-30
**Completed:** 2026-04-30

### Selected approach

**Base model:** `dbmdz/bert-base-turkish-cased` (BERTurk vanilla, 110M parametre, ~440 MB FP32). Türkçe için en yaygın baseline; aylık ~200K indirme, geniş downstream fine-tune literatürü mevcut.

**Pipeline:** HuggingFace `Trainer` + `AutoModelForTokenClassification` (NER için BIO scheme) ve `AutoModelForSequenceClassification` (detector için binary + 4-class). Standart `TrainingArguments` ile fp16 mixed precision + gradient accumulation. Tokenizer alignment'i için `tokenize_and_align_labels` helper (HF token-classification cookbook'undaki referans).

**NER (Faz 3) konfigürasyon:**
- 7 entity × 2 (B-/I-) + O = 15 etiket
- Sliding window 512-token max_length, 50-token overlap (Requirement 5.3)
- 3 epoch, learning rate 2e-5, warmup 10%, weight decay 0.01
- Eval: macro-F1 her epoch sonu, en iyi checkpoint kaydedilir
- Round-trip property test (R5.8) post-training pytest'te doğrulanır

**Detector (Faz 6.5) konfigürasyon:**
- 2-class (human/AI) ve 4-class (human/Claude/GPT/Gemini) ayrı head'ler
- 5 epoch, learning rate 3e-5
- Class imbalance varsa `WeightedRandomSampler`
- Calibration: training sonrası temperature scaling (validation set'te NLL minimize)

### Rejected alternatives

1. **SetFit (few-shot embedding-based):** Reddedildi. Bizde 30K etiketli paragraph var — few-shot avantajı yok. Trainer-based fine-tune daha iyi F1 verir.
2. **BiLSTM-CRF:** Reddedildi. 2018 öncesi standard; transformer-based F1'e kıyasla 5-10 puan geride. Türkçe akademik domain'de yeterli değil.
3. **Full continual pretraining (BERTurk üstüne MLM):** Reddedildi. Faz 0 önce; capstone scope dışı. Vanilla BERTurk fine-tune yeterli (R5.2 F1 ≥0.85 hedefi karşılanabilir, paper benchmark'ları gösteriyor).
4. **mDeBERTa-v3 multilingual:** Düşünüldü, reddedildi. Türkçe-spesifik tokenizer BERTurk'te daha iyi (subword bölünmesi tutarsız değil); akademik terminoloji koruması daha sağlam.
5. **xlm-roberta-base:** Reddedildi. 0.27B parametre — daha büyük ama Türkçe-only fine-tune coverage sınırlı; BERTurk benchmark'larda Türkçe NER için competitive.

### Hardware budget

- **Train:** RTX 3050 Laptop 4GB. BERTurk-base FP16 + batch=16 ≈ 2.8 GB VRAM (token classification). Gradient checkpointing açıkken batch=32'ye çıkabilir; gerekirse.
- **Time:** 30K paragraph × 3 epoch ≈ 90K step / batch 16 = ~5,600 step. RTX 3050 ~1.5-2 saat tek epoch; toplam ~5-6 saat NER training.
- **Detector:** Daha küçük dataset (20K paragraph × 5 epoch); ~3-4 saat.
- **Eval inference:** CPU baseline <500ms/512-tok paragraph (R5.4); VRAM ~1 GB. Kabul kriterinin altında çalışacak.
- **Disk:** Checkpoint'ler ~440 MB × her save. `save_total_limit=2` ile disk taşmasını önle.


---

## Topic 3 — sentence-transformers contrastive training

**Used in:** Faz 5 (embedder `trakad-embed-v1`).
**Started:** 2026-04-30
**Completed:** 2026-04-30

### Selected approach

**Framework:** `sentence-transformers` (UKPLab) v3.x. Trainer API ile training loop standardize, MTEB ile out-of-the-box uyumlu — TR-MTEB değerlendirmesini doğrudan destekliyor (Topic 11).

**Base model:** `dbmdz/bert-base-turkish-cased` (BERTurk vanilla) + mean pooling. 768-dim default output (Requirement 7.1). `trmteb/turkish-embedding-model` aynı yaklaşımı kullanmış — kıyaslama anlamlı.

**Loss:** `MultipleNegativesRankingLoss` (MNRL). Pair-based, simetrik, batch içindeki diğer örnekleri otomatik negatif olarak kullanır. Akademik domain'de etiketli triplet zor — pair üretmek daha kolay.

**Pair üretim stratejisi (~500K abstract'ten):**
1. **Title ↔ Abstract** çiftleri: aynı tezin başlığı + abstract = pozitif. ~500K pozitif pair.
2. **Abstract ↔ Same-author abstract:** aynı yazarın iki tezi = orta-sıkı pozitif. ~50K-100K pair (her yazarın birden fazla tezi varsa).
3. **Abstract ↔ Same-subject abstract (same year):** aynı alan + yıl = zayıf pozitif. Sample ile 200K pair.
4. **Hard negative mining:** TR-MTEB scidocs-tr / scifact-tr sample'ları üstünde BM25 hard negatives (opsiyonel, eval öncesi).

**Training:**
- Batch 64-128 (MNRL'de büyük batch = daha çok in-batch negative = daha iyi performans)
- 3-5 epoch, learning rate 2e-5
- Warmup 10%, fp16 mixed precision
- Eval set: TR-MTEB scidocs-tr + scifact-tr (akademik), her epoch sonu Spearman/NDCG@10

### Rejected alternatives

1. **SimCSE (self-supervised, single sentence):** Reddedildi. Domain-spesifik etiketli pair'imiz var — supervised contrastive daha iyi performans. Ek olarak SimCSE Türkçe akademik için kalibrasyon veri yokluğunda risk.
2. **TSDAE (denoising):** Reddedildi. STS benchmark'larda MNRL'den ~3-5 puan zayıf (sentence-transformers paper). Domain transfer için iyi ama biz domain-target'lı eğitiyoruz.
3. **`intfloat/multilingual-e5-base` üstüne fine-tune:** Düşünüldü, ileride v1.1 candidate. v1.0'da BERTurk-base seçildi çünkü tek-dil ekosistem (TR-MTEB authors da aynı yolu seçti, kıyas adil).
4. **Triplet loss + hard negative mining baştan:** Reddedildi. MNRL daha basit + büyük batch'te in-batch negative + benchmark'ta competitive. Triplet'i v1.1'de hard negative pass olarak ekleriz.
5. **Bigger model (`xlm-roberta-large` 0.55B):** Reddedildi. RTX 3050 4GB sığar ama batch küçülür → in-batch negative azalır → MNRL etkinliği düşer. Trade-off karlı değil.

### Hardware budget

- **Train:** BERTurk-base FP16 + batch 64 ≈ 2.5-3 GB VRAM. Gradient accumulation ile batch 128'e effective çıkar.
- **Time:** ~500K pair × 3 epoch / batch 64 ≈ 23,000 step. RTX 3050 ~3-4 saat 1 epoch; toplam ~10-12 saat training. Overnight run.
- **Eval (TR-MTEB akademik subset, her epoch sonu):** scidocs-tr (56K) + scifact-tr (7.5K) — encode + Spearman compute, ~10-15 dakika.
- **Final TR-MTEB tam değerlendirme (training sonrası):** 26 dataset, ~2-4 saat (Topic 11 hardware budget'te dokümante).
- **Disk:** Pair Parquet'leri ~3-5 GB; final model ~440 MB; intermediate checkpoint'ler `save_total_limit=2`.
- **Risk:** RAM peak (eski sentence-transformers v2 eval'de >8 GB olabilir). v3.x'te streaming + dataloader chunking ile çözülür; learning-log'a not.


---

## Topic 4 — mT5 abstractive summarization fine-tuning

**Used in:** Faz 6 (summarizer `trakad-summarizer-v1`).
**Started:** 2026-04-30
**Completed:** 2026-04-30

### Selected approach

**Base model:** `google/mt5-small` (300M params, ~1.2 GB FP32) **veya** `google/mt5-base` (580M, ~2.3 GB) — RTX 3050 4GB GPU constraint'i belirleyici. İlk denemede mt5-small'la baseline çıkar; ROUGE-L ≥0.35 hedefi (R8.2) karşılanmazsa mt5-base'e gradient checkpointing + fp16 ile geçiş.

**Pipeline:** HF `Seq2SeqTrainer` + `DataCollatorForSeq2Seq` + `generate()` w/ beam search. Tokenizer aynı mT5 multilingual SentencePiece — Türkçe karakterler doğal olarak destekleniyor.

**Training data (umutertugrul derive'den):**
- **Source:** Tezin "Giriş" + "Sonuç" bölümleri (eğer ayrılabilirse) — yoksa abstract'ın genişletilmiş versiyonu (full thesis intro + conclusion). Ancak full thesis text yoktu (sadece abstract var); bu durumda alternatif strategy:
- **Pratik strateji:** Abstract'ı "uzun input" olarak kullan, ilk N kelime → kalan abstract = source/target değil, başka bir yaklaşım gerekiyor.
- **Final pair üretimi:** İki yön:
  1. `(title + index_keywords) → abstract_tr` (compression)
  2. Sentetik: Claude API ile abstract'lardan "extended pre-summary" üret, sonra abstract → bu extended versiyonu reverse-eğitim. Maliyet ~$30-50 (5K pair). Bu hibrit yaklaşım Faz 6 başlangıcında karara bağlı.

**Inference config:**
- max_length 300, min_length 100 (akademik özet bandı 150-300 kelime — R8.1)
- num_beams 4, length_penalty 1.0, no_repeat_ngram_size 3
- 100 kelimeden kısa input → bypass + flag (R8.4)
- PDF input: header/footer/references stripping (`pypdf` + heuristic regex), sonra section detection, sonra summarize

### Rejected alternatives

1. **`facebook/bart-large` (English only):** Reddedildi. Türkçe değil. Multilingual BART'lar (mbart-50) deneme yapılabilir ama mT5 STS/summarization Türkçe benchmark'larda daha tutarlı.
2. **`google/pegasus-xsum`:** Reddedildi. Türkçe coverage zayıf, fine-tune cost yüksek. mT5 Türkçe-yetkin out-of-the-box.
3. **mT0-small (instruction-tuned):** Düşünüldü; RAM/VRAM uyumlu ama instruction-tuning bias özetlemede istenmedik shorthand çıkartabilir. mT5 vanilla daha temiz baseline.
4. **Extractive summarization (TextRank, BertSumExt):** Reddedildi. Akademik özet için abstractive zorunlu (R8.1) — extractive cümleleri kelimesi kelimesine kopyalar, yeniden yazma yok.
5. **GPT-4 / Claude API ile zero-shot summarization (no fine-tune):** Reddedildi. (a) Local inference iddiamızı bozar, (b) maliyet runtime'da kullanıcıya yansır, (c) Türkçe academik tone tutarlılığı API responses'ta dalgalı. Kendi model fine-tune deterministic.

### Hardware budget

- **Train (mt5-small öncelik):** 300M parametre + fp16 + batch 4 + gradient accumulation 8 (effective batch 32) ≈ 3.0-3.5 GB VRAM. RTX 3050 4GB sınırda; gradient checkpointing açık.
- **Time:** ~50K (source, target) pair × 3 epoch / effective batch 32 ≈ 4,700 step. RTX 3050 ~4-6 saat tek epoch (mT5 inference yavaş); toplam ~12-18 saat. Overnight + bir gün.
- **Plan B (mt5-base):** 580M, fp16 + batch 2 + accumulation 16 → effective batch 32. VRAM ~3.7 GB, sınırı zorlar. Time ~24-36 saat. Sadece mt5-small ROUGE-L < 0.30 ise denenir.
- **Eval (ROUGE-L):** Held-out 5K test set; her epoch sonu beam search ile generate (~1-2 saat). Validate edip best checkpoint seç.
- **Inference (CPU baseline):** R8.8 hedefi <10s/2000 kelime input. mt5-small + beam=4 ~7-9 saniye, sınırı geçer. mt5-base ~15-20 saniye → quantize gerekebilir (INT8 ONNX), Faz 9.5 öncesi optimize.


---

## Topic 5 — QLoRA / PEFT (BitsAndBytes 4-bit)

**Used in:** Faz 7 (reasoner `trakad-reasoner-3b`, optional final phase).
**Started:** 2026-04-30
**Completed:** 2026-04-30 (theory; implementation deferred — Faz 7 opsiyonel)

### Selected approach

**Base model:** `microsoft/Phi-3-mini-4k-instruct` (3.8B parametre). RTX 3050 4GB GPU üstünde QLoRA (4-bit NF4 quantization + LoRA adapter) ile fine-tune edilebilir tek aday. Llama-3-8B sığmaz, daha küçük modeller (Phi-2 2.7B) Türkçe baseline'da Phi-3-mini'den zayıf.

**Stack:**
- `transformers` + `peft` (HuggingFace) + `bitsandbytes` (4-bit quantization)
- `BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.float16)`
- LoRA: r=16, alpha=32, target_modules=`["q_proj","k_proj","v_proj","o_proj"]`, dropout=0.05
- Gradient checkpointing zorunlu (batch=1 + accumulation 16)
- TRL (`SFTTrainer`) instruction-following fine-tune için

**Training data (synthetic CoT):**
- Ollama qwen2.5:7b ile umutertugrul abstract'lerinden Q&A çiftleri üret (~5K-10K)
- "Bu tezde hangi metodoloji kullanılmış?" / "Sonuçlar ne gösteriyor?" gibi akademik sorular
- Cevaplar grounded: abstract'tan extracted + chain-of-thought reasoning

**Output:**
- Adapter weights HF'e push (~50 MB; full model değil)
- Inference için: base + adapter merge → GGUF Q4 quantize (`llama.cpp` ile) → ~2 GB CPU inference dosyası (R10.6)

### Rejected alternatives

1. **Full fine-tune (no LoRA):** Reddedildi. RTX 3050 4GB sığmaz; Phi-3-mini full FP32 ~15 GB, FP16 ~7.6 GB. Donanım çıkmazı.
2. **Llama-3-8B QLoRA:** Reddedildi. 4-bit quantize edilse bile ~5 GB; gradient + optimizer state ile RTX 3050 4GB sığmaz.
3. **Phi-2 (2.7B) QLoRA:** Reddedildi. Türkçe baseline performansı Phi-3-mini'den belirgin zayıf (Phi-3 mini Türkçe 4-shot eval'lerde ~15 puan üstünde).
4. **DeepSpeed ZeRO-3 offload:** Reddedildi. CPU offload eğitimi 5-10× yavaşlatır; capstone scope için imkânsız (300+ saat).
5. **RLHF / DPO:** Reddedildi. Capstone scope dışı; QLoRA SFT yeterli baseline'ı geçmek için (R10.4).

### Hardware budget

- **Train:** 4-bit quantize Phi-3-mini ≈ 2.0 GB VRAM + LoRA adapters ~500 MB + gradient + optimizer ~1 GB → toplam **~3.8 GB peak**, RTX 3050 4GB sınırda (R10.3 kabul kriteri "GPU usage <3.8GB").
- **Time:** 5-10K Q&A pair × 3 epoch / batch 1 + accum 16 = ~1,800 step. RTX 3050 ~15-20 saat training. Multi-night run.
- **GGUF Q4 quantize (post-training):** llama.cpp `convert.py` + `quantize` ~30 dakika. Output ~2 GB.
- **Inference (CPU GGUF Q4):** 4-8 GB RAM kullanır. R10.7 hedefi <30s/512 tok — `llama-cpp-python` thread sayısı ile optimize edilir.
- **Risk:** OOM eğer model loader 4-bit quantize bypass ederse. `accelerate` ile device_map="auto" zorunlu.


---

## Topic 6 — ChromaDB vs FAISS

**Used in:** Faz 8 (RAG in SDK).
**Started:** 2026-04-30
**Completed:** 2026-04-30

### Selected approach

**Default backend: ChromaDB** (v0.5.x). FAISS opsiyonel ek olarak kullanıcıya `backend="faiss"` parametresi ile expose edilir. Üç gerekçe:

1. **Incremental add native:** Kullanıcı kendi PDF'lerini RAG index'ine ekleyince (R9.6) ChromaDB out-of-the-box destekler. FAISS index rebuild gerektirir veya manuel manifest yönetimi.
2. **Metadata filtering native:** "yıl=2023 AND alan=mühendislik" gibi compound filter ChromaDB'de SQL-vari syntax'la mümkün. FAISS pure vector search; metadata layer ekstra kod yazmak gerekir.
3. **Persistence kolay:** ChromaDB PersistentClient + tek bir DB klasörü. FAISS `index.write_index` + manifest JSON + metadata pickle = 3 dosya yönetimi.

**ChromaDB konfigürasyonu (Faz 8):**
- `chromadb.PersistentClient(path="~/.cache/tr_academic_nlp/chroma")`
- HNSW indexing default (`hnsw:space="cosine"`)
- Embedding function: `trakad-embed-v1` (custom sentence-transformers wrapper)
- Document ID: `tez_no` (umutertugrul) veya UUID4 (kullanıcı PDF)
- Metadata fields: title, author, year, subject, source_url

**FAISS opt-in (`backend="faiss"`):**
- `faiss-cpu` extra dep (`pip install tr-academic-nlp[faiss]`)
- Static index için preferable: kullanıcı kendi PDF eklemeyecekse + sub-millisecond retrieval ister
- Persistence: `faiss.write_index` + `manifest.json` (id↔metadata)

### Rejected alternatives

1. **Pinecone / Weaviate cloud:** Reddedildi. KVKK lokal mod bozulur; license + hosting maliyet capstone scope dışı.
2. **Qdrant:** Düşünüldü; ChromaDB'ye benzer feature set ama topluluk + Türkçe ekosistem'de daha az yaygın. ChromaDB'nin embedding function abstraction'ı sentence-transformers ile daha temiz entegre.
3. **PostgreSQL + pgvector:** Reddedildi. Kullanıcının extra service kurması gerekir; "pip install + çalıştır" UX'i bozulur.
4. **In-memory dict + numpy linear search:** Reddedildi. 500K embedding × 768d brute-force ~5 saniye/query (CPU) — R9.7 hedefini geçer ama incremental add efficient değil.
5. **FAISS-only (no ChromaDB):** Reddedildi yukarıda. v1.0'da default değişimi karmaşık.

### Hardware budget

- ChromaDB persistent: ~150 MB on-disk for 500K × 768d HNSW index
- RAM peak: ~3 GB (full corpus + index in-memory). Stream mode opsiyonu yok ChromaDB'de; kullanıcı 8 GB+ RAM.
- Query latency: HNSW <100 ms / query. 500K-doc retrieval (top-5) <5 s CPU (R9.7) rahat sığar.
- Lite mode (50K subset): ~30 MB index, ~600 MB RAM, query <50 ms.


---

## Topic 7 — Gradio Space (CPU-free tier limitations + quantized loading)

**Used in:** Faz 9.5 (HF Space).
**Started:** 2026-04-30
**Completed:** 2026-04-30

### Selected approach

**Stack:** `gradio==5.x` + HF Space free tier (CPU only, 16 GB RAM, 50 GB disk). 6-sekme `gr.Tabs` layout (R12.2): Literatür Tara / Makaleyi Özetle / Atıf Düzelt / Akademik Tona Çevir / AI Yazımı Tespit / Konu Sor.

**CPU-only constraint mitigations:**
- **Quantize all models:** mt5-small INT8 ONNX (~150 MB, 3-5× faster CPU), BERTurk fine-tune INT8, reasoner GGUF Q4 (~2 GB)
- **Lazy load:** Her sekme ilk kullanıldığında model yüklenir; önceden hepsini yüklemek RAM peak'i tepeler
- **Lite RAG corpus:** Space üstünde tüm 500K corpus değil, 50K alt-örneklenmiş "lite" sürüm (~380 MB) — query latency hedefini tutar
- **Streaming response:** Reasoner ve summarizer çıktılarında `yield` ile incremental output (Gradio streaming)

**Caching:**
- `@spaces.GPU` dekoratörü kullanmayız (CPU-only); ama `gr.cache_examples=True` ile demo örnekleri pre-compute edilir
- Same-input cache (`@functools.lru_cache`) basit textual operasyonlar için (citation parse vb.)

**Error handling:**
- Türkçe error messages (R12.7) — no stack trace
- "Bu işlem yaklaşık X saniye sürebilir, lütfen bekleyin" type indicator
- Timeout: 120 sn/request (PDF upload <60s hedef, R12.3)

**About section:** README anchor + KVKK statement + GitHub/HF link (R12.6)

### Rejected alternatives

1. **Streamlit:** Reddedildi. Gradio HF Space ile tight integration; auto-deploy, Spaces leaderboard görünürlük.
2. **Native React frontend:** Reddedildi. UI yazma yükü Faz 9.5'i 5 günden 2-3 haftaya çıkarır. Gradio "low-code, high-yield" choice.
3. **HF Inference API on Space:** Reddedildi. Inference API token-based ücretli; KVKK iddiamızı bozar (third-party cloud).
4. **GPU paid tier ($0.05/saat veya ZeroGPU):** Düşünüldü; v1.0 demo için CPU yeterli. ZeroGPU başvurusu ileride v1.1 candidate.
5. **Static Hugging Face Demo Space (no backend):** Reddedildi. RAG + LLM çalıştırmak gerekiyor, statik mümkün değil.

### Hardware budget

- **HF Space CPU free tier:** 2 vCPU, 16 GB RAM, 50 GB disk
- **RAM allocation:**
  - Embedder + ChromaDB lite (50K) ~1.5 GB
  - Summarizer (mt5-small INT8) ~200 MB
  - NER (BERTurk INT8) ~150 MB
  - Citation parser (BERTurk INT8) ~150 MB
  - AI detector (BERTurk INT8) ~150 MB
  - Reasoner (GGUF Q4 4-bit) ~2.5 GB → opsiyonel; eğer açıksa toplam ~5 GB
  - Gradio + Python overhead ~1 GB
  - **Toplam peak: ~6.5 GB / 16 GB tavanı altında ✓**
- **Disk:** Tüm modeller + lite corpus ~3 GB / 50 GB tavanı altında.
- **Cold start:** İlk model load ~30-60 sn (HF Hub'dan indirme). Subsequent invocations cached, hızlı.
- **Concurrency:** Gradio default queue (max 1 concurrent inference); dağıtık trafik için sıraya alır. Throughput düşük ama R12.4 budget içinde.


---

## Topic 8 — Python packaging (pyproject.toml + PyPI publish)

**Used in:** Faz 8 (SDK release).
**Started:** 2026-04-30
**Completed:** 2026-04-30

### Selected approach

**Build system:** `setuptools>=68` + `wheel` (zaten `pyproject.toml`'da konfigüre, repo skeleton'da). PEP 621 metadata, `[project]` table tek source-of-truth.

**Dependency strategy:**
- **Core deps:** Pinned major + minor (örn. `transformers>=4.45,<5.0`, `chromadb>=0.5,<1.0`) — breaking change'lerden korur.
- **Optional extras:** `[faiss]` (FAISS backend), `[web]` (httpx + beautifulsoup4), `[quantize]` (bitsandbytes + accelerate), `[dev]` (pytest, ruff, mypy, pre-commit).
- **Avoid `==` exact pins:** Solver hell yaratır ve user'ın diğer paketleriyle çakışır. Range pinning yeterli.

**Versioning:** SemVer (R15.5). Faz 0: `0.0.1` (pre-alpha). PyPI release Faz 8 sonrası `0.1.0` (alpha public). Capstone savunma sonrası `1.0.0` (stable, üç kanal canlı).

**Publishing flow:**
- `python -m build` (sdist + wheel)
- Test PyPI'da deneme: `twine upload --repository testpypi dist/*`
- Smoke test: temiz venv'de `pip install -i https://test.pypi.org/simple/ tr-academic-nlp`
- Production: `gh release create vX.Y.Z` → `.github/workflows/publish.yml` PyPI'ya push (trusted publishers / OIDC, no token-in-secret)

**Distribution discipline:**
- Wheel'in içine **model weights gömme** — sadece kod. Models HF Hub'dan auto-download (`huggingface_hub.snapshot_download`).
- Datasets de gömme. SDK runtime'da `datasets.load_dataset` ile çağırır.
- LICENSE + README rendered PyPI sayfasında.

### Rejected alternatives

1. **Poetry:** Düşünüldü, reddedildi. setuptools + pyproject.toml standartlaştı; Poetry ekstra abstraction değer katmıyor (build hız, dep management farkı küçük).
2. **flit:** Reddedildi. setuptools'tan minimal; bizim build pipeline'ında ek özellik gerekmiyor.
3. **hatchling:** Düşünüldü; setuptools daha eski + daha geniş ekosistem entegrasyon. Risk minimization.
4. **Lockfile (`requirements.txt` pinned):** Hem core hem dev için lockfile yok; `pyproject.toml` range yeterli. Reproducibility için CI'da pip resolver kullanılır.
5. **Conda packaging:** Reddedildi. PyPI öncelik; conda ek eforlu, kullanıcı tabanı PyPI'a göre küçük.

### Hardware budget

- Build host: Herhangi (CI runner, local dev makinesi). 2 GB RAM yeterli.
- `python -m build` ~30 saniye sdist + wheel üretir.
- PyPI hesabı + TestPyPI hesabı (zaten hakansabunis için ayarlanacak).
- Trusted publishers (OIDC): GitHub Actions üzerinden token-less publish — daha güvenli, secret yönetimi yok.


---

## Topic 9 — Anthropic Skills spec format

Subtopics:
- SKILL.md schema (YAML frontmatter: name, description with when-to-use + when-NOT-to-use)
- `anthropics/skills` repo audit — read existing Document skills (pdf, docx, pptx, xlsx) and identify common patterns
- agentskills.io standard spec

**Used in:** Faz 9.7 (Claude Skills package).
**Started:** 2026-04-30
**Completed:** 2026-04-30 (initial audit; deep audit in Faz 9.7)

### Selected approach

**Audit bulguları (`anthropics/skills` repo'sundan):**
- 4 kategori: Creative, Development, Enterprise, **Document** (PDF/DOCX/PPTX/XLSX)
- License standart: **Apache 2.0** (most skills)
- "Document skills" pozisyonlanması: **production reference implementations**
- Non-English skill: **0** (boşluk + filtre riski)
- Stack: Python %84, HTML/Shell/JS yardımcı

**Bizim Türkçe akademik 5 skill için strateji:** Kendi pozisyonumuzu **document skills'in non-English reference implementation'ı** olarak konumlandır. README başında "low-resource academic NLP reference implementation" pitch (yol haritası v2.2).

**SKILL.md spec:**
```yaml
---
name: turkish-academic-summarizer
description: |
  Use when summarizing Turkish academic text (theses, journal articles, conference papers).
  Input: Turkish PDF or raw text. Output: 150-300 word academic-tone summary preserving
  research objective, methodology, findings, conclusions.
  DO NOT use when: input is non-Turkish, non-academic genre (news/blog), shorter than 100 words,
  or when verbatim quotation is required (this skill paraphrases).
---

# Turkish Academic Summarizer

[Skill instructions in English; Turkish I/O]

## Examples
[≥5 working examples — Pre-Flight Checklist madde 3]

## Guidelines
[Honest limitations, performance bench, etc.]
```

**Per-skill yapı (Pre-Flight Checklist 12 madde — yol haritası §11.8):**
1. SKILL.md — frontmatter + when-to-use + when-NOT-to-use
2. README.md — English; reference impl pitch + benchmarks
3. LICENSE — Apache 2.0
4. EXTENSION.md — low-resource lang port pattern
5. scripts/ — core implementation
6. examples/ — ≥5 working examples
7. tests/ — pytest ≥10 case
8. demo.gif
9. Türkçe error messages
10. CI green (ruff + mypy --strict + pytest)

**Submission stratejisi (yol haritası §14):**
- **Faz A:** GitHub repo public, ≥2 hafta soak, dış kullanıcı feedback
- **Faz B:** awesome-claude-skills topluluk PR (high accept rate)
- **Faz C:** Plugin marketplace (Anthropic-hosted) submission
- **Faz D:** Twitter/X paylaşım, Anthropic team etiket
- **Faz E (bonus):** Anthropic blog feature
- **Faz F (bonus):** Resmi `anthropics/skills` repo PR (fork'ta tek skill draft → maintainer reaction → all 5 PR)

### Rejected alternatives

1. **Tek mega-skill:** Reddedildi (R13.1 = "exactly 5 separate sub-skills"). Anthropic "tek odak" prensibi.
2. **MIT license (eski v2.1 kararı):** Reddedildi v2.2'de. Apache 2.0 Anthropic ekosistem standardı; submission filtresinde uyum sinyali güçlü.
3. **Sadece Türkçe doküman:** Reddedildi. README + ARCHITECTURE İngilizce; Türkçe yalnız I/O ve error message'lar. Uluslararası audience + Anthropic uyumu.
4. **Skill bundling (single repo, multi-skill folder):** Yapıyoruz ama "her skill standalone" disiplin: ayrı LICENSE, ayrı SKILL.md, ayrı tests. Bundle gibi sunmuyoruz.
5. **agentskills.io spec'ten sapmak:** Reddedildi. Spec'e bağlı kalmak community uyum + future migration (yeni spec versions) için kolay.

### Hardware budget

- Yok — bu topic doküman + spec compliance. Inference yok.
- Demo GIF üretimi: OBS Studio veya `ffmpeg` ile, lokal makinede. Her skill için ~30-60 saniyelik 1 GIF. ~5 MB/skill × 5 = ~25 MB toplam.
- Test infrastructure: pytest standart, repo'da zaten konfigüre.


---

## Topic 10b — LLM-as-labeler reading list (added v2.4)

**Note:** Faz 2 NER labeling pipeline shifted from Ollama (lokal qwen2.5:7b verify) to Claude Haiku 3.5 (full annotation) + 100h human review (~12 sec/paragraph). Pattern grounded in:

- **UniversalNER** (Zhou et al., NeurIPS 2023, [arXiv:2308.03279](https://arxiv.org/abs/2308.03279)) — ChatGPT used as labeler for open-domain NER, distilled into specialized student model. 45K input-output pairs, 240K entities.
- **NuNER** ([arXiv:2402.15343](https://arxiv.org/html/2402.15343v1), 2024) — encoder pre-trained on LLM-annotated data; demonstrates LLM-as-labeler at scale.
- **Astronomical NER** (RAA 2024) — GPT-4 vs Claude 2 head-to-head on scientific text. Claude 2 operationally functional but GPT-4 stronger; Claude Haiku 3.5 sits between these two in capability.
- **Biomedical NER instruction tuning** (Bioinformatics 2024) — instruction-tuned models +5-30% F1 vs few-shot GPT-4 on disease/chemical/gene NER. Validates that fine-tuned BERT family on LLM-annotated data outperforms raw LLM zero-shot.

**Cost ledger update:**
- Faz 2 (NER labeling): Claude Haiku 3.5 × ~30K paragraphs × ~500 tokens I/O each ≈ **~$10-20**
- Faz 6.5 (AI detector data): Claude Sonnet + GPT-4o + Gemini × ~5K paragraphs each ≈ **~$50-100**
- Faz 7 (reasoner CoT, optional): Claude Sonnet × ~5K-10K Q&A pairs ≈ **~$15-25**
- **Total Claude API cost (whole project): ~$75-145**

**Ollama removed from project scope.** Local LLM inference is reserved for **end-user** runtime (`web=False` KVKK mode); the project's training pipeline handles upstream public datasets and uses cloud LLM APIs — not user data, so KVKK posture is unaffected.

---

## Topic 10 — AI text detection

Subtopics:
- GPTZero / DetectGPT approaches
- Perplexity-based vs classifier-based methods
- Calibration (temperature scaling, isotonic regression)

**Used in:** Faz 6.5 (AI detector `trakad-detector-v1`).
**Started:** 2026-04-30
**Completed:** 2026-04-30

### Selected approach

**Yaklaşım:** Classifier-based fine-tuned BERTurk (Topic 2 ile ortak altyapı). İki head birden:
1. **Binary** (human vs AI) — ana metric, AUC ≥0.90 hedef (R20)
2. **4-class** (human / Claude / GPT / Gemini) — ikincil; hangi LLM yazdığını tespit, macro-F1 ≥0.75

**Training data (`tr-ai-vs-human-academic` dataset):**
- 5K human paragraph (umutertugrul abstract'lerinden örnekleme — gerçek Türkçe akademik insan yazımı)
- 5K Claude paragraph (API ile aynı konularda akademik paragraph yazdırma — system prompt: "akademik tonda, terminoloji koruyarak")
- 5K GPT-4o paragraph (API ile aynı şekilde)
- 5K Gemini paragraph (API ile aynı şekilde)
- Toplam ~20K, 80/10/10 stratified split
- Maliyet: ~$50-100 toplam (3 LLM × 5K paragraph, ortalama 200 token/paragraph)

**Konstrüksiyon detayları:**
- Topic seed'leri umutertugrul subject alanlarından alınır (mühendislik, sosyal bilim, sağlık, vb.) — coverage tutarlılığı
- Her LLM'e aynı topic listesinden eşit dağıtım — leakage'i önler
- Versioning: `tr-ai-vs-human-academic-v1` (LLM model versiyonları YYYY-MM-DD ile sabit), her yeni LLM sürümü için v2 retraining (Faz 18 risk satırı)

**Calibration:**
- Training sonrası temperature scaling (Platt'tan basit, NLL minimize) validation set'te
- Reported confidence ≈ ampirik accuracy (R11.7 detector calibration property test)
- Düşük confidence threshold (örn. 0.55-0.65) → "uncertain" label döndür ("AI/human kararı için yetersiz veri")

### Rejected alternatives

1. **Perplexity-based (DetectGPT, GPTZero):** Reddedildi tek başına. Türkçe için kalibre LM gerekli; bu LM'in yine fine-tune edilmesi gerekir → classifier yapmak daha basit. Future: ensemble (perplexity + classifier) v1.1'de denenebilir.
2. **Zero-shot detector (sadece prompting):** Reddedildi. Türkçe akademik dilde Claude/GPT'nin self-detection performansı kalibre değil; sayısal güven veremez. Production-ready değil.
3. **Watermark-based detection:** Reddedildi. Anthropic/OpenAI watermark'ı yayınlamış değil (şu anlık); Gemini watermark'ı bilinmiyor. Watermark-agnostic classifier daha sağlam.
4. **Tek-LLM detection (yalnız ChatGPT vs human):** Reddedildi. Türkiye'de Claude + Gemini de yaygın; üç sınıf birden eğitmek anlamlı. 4-class ek detail bonus.
5. **Stylometric features (POS distribution, sentence length, vocabulary diversity) + Random Forest:** Reddedildi. Modern LLM'ler stylometric "human-like" çıktılar üretebiliyor; classifier-based BERT representation daha sağlam.

### Hardware budget

- **Train:** Topic 2 ile aynı (BERTurk-base FP16 batch 16). 20K paragraph × 5 epoch / batch 16 = 6,250 step. RTX 3050 ~2-3 saat training.
- **Calibration pass:** 5 dakika, validation set üstünde temperature optimize.
- **API cost (one-time data generation):** $50-100. Çoğu zaman cache + rate limit yönetimi. Ollama qwen2.5:7b veya yerel modeller ile augment etmek mümkün ama çıktı kalitesi düşer (target dağılımdan saparız) — opsiyonel ek class olarak değil.
- **Inference (CPU):** <500 ms/paragraph (R11.5 budget). BERTurk-base classification head'i hızlı, hedef altında.
- **Disk:** Detector model ~440 MB; dataset ~40 MB JSONL.
- **Risk: model arms race.** Yeni LLM çıkınca veya mevcutlar sürüm atınca detector'ın 4-class accuracy'si düşer. Mitigasyon: quarterly retraining + dataset versioning + model card'da "tested against [model versions YYYY-MM]" disclaimer.


---

## Topic 11 — TR-MTEB paper reading + reproduction

Reference: Baysan & Güngör, Findings of EMNLP 2025.
- Read the paper end-to-end.
- Clone `selmanbaysan/mteb_tr` and run baseline against an off-the-shelf BERTurk model.
- Identify the academic-domain task subset (or note its absence and plan to contribute one).

**Used in:** Faz 5 (embedder evaluation).
**Started:** 2026-04-30
**Completed:** 2026-04-30 (initial — re-run after first eval)

### Selected approach

TR-MTEB'i `trakad-embed-v1` için **birincil değerlendirme standardı** olarak benimsedim. Üç gerekçe:

1. **Peer-reviewed venue:** Findings of EMNLP 2025'te yayınlandı (Baysan & Güngör, ITÜ). Self-authored bir benchmark capstone savunmada zayıf bir kanıttır; standart benchmark'a göre sıralama kıyaslanabilir + tartışılamaz.
2. **Kapsam:** 6 task kategorisi (classification, clustering, pair classification, retrieval, bitext mining, STS), 26 dataset. Tek metrik (Spearman) yerine çok-boyutlu performans gösterir.
3. **Reference altyapı hazır:** `selmanbaysan/mteb_tr` repo'sunda CLI mevcut (`./mteb_tr_cli.py "model_name"`). Yeni eval pipeline yazma yükü yok; bizim modeli HF'e push edip CLI'ı çalıştırmak yeterli.

**Kritik bulgu — fırsat alanı:** TR-MTEB'in 26 dataset'inden yalnızca **2 tanesi akademik domain'e yakın** (`trmteb/scifact-tr` — bilimsel fact verification, `trmteb/scidocs-tr` — bilimsel doküman benzerliği). Bu, hem stratejik avantaj hem topluluk katkısı fırsatı:

- **Avantaj:** `trakad-embed-v1` Türkçe akademik corpus'una (umutertugrul derive) fine-tune edildiği için bu 2 task'ta dominant olma şansı yüksek.
- **Topluluk katkısı:** TR-MTEB v2'ye **Türkçe thesis-retrieval ve academic-NLI** task'ları PR olarak gönderilebilir. Bu PR kabul edilirse hem capstone'da güçlü "peer-reviewed venue contribution" anlatısı hem ekosistem değeri.

**Hedef kombinasyonu:**
- Akademik subset'te (scifact-tr + scidocs-tr): **top-3** (`mursit` ve `trmteb/turkish-embedding-model`'a karşı competitive)
- Genel 26-dataset leaderboard: **top-10**
- Bonus: TR-MTEB v2'ye 2 yeni academic task PR

**Reference modeller (kıyas hedefleri):**
- `trmteb/turkish-embedding-model` (0.1B parametre, BERTurk-base boyutunda) — yazarların ana modeli
- `trmteb/turkish-embedding-model-fine-tuned` (0.1B) — yazarların fine-tune varyantı
- `trmteb/bert-base-turkish-cased-mean-nli-stsb-tr_contrastive_loss_training` (0.1B, 325 indirme) — repo'daki en popüler
- Multilingual baseline: `intfloat/multilingual-e5-base` (0.3B)

**Yazarların training corpus'u:** `trmteb/cleaned_turkish_embedding_model_training_data_colab` ~61.9M sentence pair (paper'da 34.2M, repo'da güncel sürüm 61.9M). Bizim training corpus'umuz ~500K abstract'ten türetilen pair'ler olacak — yazarlardan daha küçük, ama domain-specialized; trade-off bilinçli.

### Rejected alternatives

1. **Kendi STS benchmark'ımı yazmak (eski R7.2):** Reddedildi. Self-authored metrik zayıf savunma, peer-review yokluğu, kıyaslama eksikliği. Capstone jürisi "kendi sınavını kendin yapmışsın" eleştirisini haklı yapardı.

2. **MTEB (English) doğrudan kullanmak:** Reddedildi. Multilingual modellerin Türkçe performansını ölçmek için yeterli değil — TR-MTEB Türkçe-spesifik contrastive eğitilmiş modelleri ve Türkçe domain task'larını içeriyor.

3. **Yalnız Mursit modeline karşı kıyas:** Reddedildi. Tek baseline = weak comparison. TR-MTEB ile 26 dataset × birden çok reference model = sağlam çapraz-doğrulama.

4. **TR-MTEB'in yalnız STS subset'ini kullanmak:** Reddedildi. Tek task'ta iyi olmak embedding kalitesinin tamamını yansıtmaz; retrieval + clustering + classification de gerekli (Türkçe akademik RAG için kritik).

5. **TR-MTEB v2'ye yeni academic task'ları PR atmadan önce yayınlamak:** Reddedildi. Capstone bittikten sonra (v1.0 stabilize) akademik subset PR ile zaman çakışması riski. Yeni task PR'ı v1.1 fazına bırakıldı; ilk hedef mevcut subset'te top-3 + genel top-10.

### Hardware budget

**Inference-only (eval) yükü:**
- `trakad-embed-v1` (0.1B BERTurk-base boyutu) FP32 inference: ~400 MB VRAM batch=32
- 26 dataset × ~10K pair ortalama = ~260K embedding hesabı
- RTX 3050 Laptop 4GB GPU: rahat sığar; tahmini eval süresi 2-4 saat tüm benchmark için
- CPU fallback (HF Space veya CI runner): ~6-10 saat — kabul edilebilir ama yavaş

**Yazarların reference training corpus'una ulaşmak:** 61.9M pair, ~10-15 GB indirme. Disk space OK; bizim training pipeline için sadece referans olarak kullanılır, biz kendi pair corpus'umuzu üreteceğiz (umutertugrul derive'den).

**Risk:** TR-MTEB'in büyük retrieval task'ları (msmarco-tr 1.75M, quora-tr 561K) eval sırasında VRAM stress yapabilir. Mitigasyon: eval batch size'ı 16'ya düşür, gerekirse CPU'da uzun çalıştır.

**Kalibrasyon:** İlk eval'i `dbmdz/bert-base-turkish-cased` (BERTurk vanilla, 0.1B) üstünde sanity-check için yap. Beklenen: weak baseline (Spearman ~0.50-0.60). Sonra `trakad-embed-v1` fine-tune sonrası gerçek hedeflere bak.


---

## Topic 12 — umutertugrul dataset audit

- Load `umutertugrul/turkish-academic-theses-dataset` with `datasets` lib.
- Compute basic stats: discipline distribution, year range, abstract length distribution, empty/duplicate rate.
- Decide filter thresholds (target: ~500K usable abstracts after filtering).

**Used in:** Faz 1 (dataset derivation).
**Started:** 2026-04-30
**Completed:** 2026-04-30 (initial schema review — full audit deferred to Faz 1 implementation)

### Selected approach

`umutertugrul/turkish-academic-theses-dataset`'i `tr-academic-nlp`'nin **birincil thesis corpus kaynağı** olarak benimsedim ve scraper yazma planını iptal ettim. Üç gerekçe:

1. **Ölçek:** 650K abstract — bizim orijinal hedef olan 50K'nın **13×'i**. Daha geniş corpus, embedding fine-tune ve domain coverage için daha sağlam temel.
2. **Lisans temizliği:** CC-BY-4.0. Attribution + upstream link ile koşulsuz kullanım hakkı; YÖK doğrudan scraping'in yasal/etik gri alanı yok.
3. **Wheel reinvention'dan kaçınma:** Aynı veriyi yeniden scrape etmek mühendislik değil tekrar; capstone savunmada "mevcut topluluk varlıklarını derive ettim, üstüne özgün katkı (NER + AI detector + akademik subset) ekledim" anlatısı çok daha güçlü.

**Dataset şeması (16 alan):**
- Anahtarlar: `tez_no` (stable key), `pdf_url` (YÖK handle page)
- Çift dil: `title_tr` / `title_en`, `abstract_tr` / `abstract_en`
- Kişi/Kurum: `author`, `advisor`, `location` (üniversite/enstitü/bölüm yolu)
- Sınıflama: `subject` (alan), `index` (anahtar kelime), `degree` (Yüksek Lisans/Doktora), `language` (Türkçe), `status` (Onaylandı vb.)
- Sayısal: `year`, `pages`

**Filtering stratejisi (Faz 1'de uygulanacak):**

| Filtre | Eşik | Gerekçe |
|---|---|---|
| `abstract_tr` boş/null | DROP | Birincil hedef Türkçe abstract; yokluğu kaydı kullanılamaz hale getirir |
| `abstract_tr` < 50 kelime | DROP | Çok kısa = anlamlı semantic content yok; quality-over-quantity |
| `tez_no` exact duplicate | DROP (keep first) | Schema integrity |
| Unicode normalize (NFC) | TRANSFORM | Türkçe karakterlerin (ç, ğ, ı, ö, ş, ü) tutarlılığı için |
| `degree` whitelist | DROP others | Yüksek Lisans + Doktora yeterli; non-thesis records dışla |

**Beklenen çıktı:** 650K → ~500K (loose filter) ya da ~300K (strict filter). Capstone minimum'u 200K (Requirement 2.2).

**Erişim notu:** HF dataset card'ı "Users must agree to share contact information to access dataset files" diyor. Pratikte HF account ile login + dataset acceptance flow gerekiyor; CI'da yeniden derive için secret olarak HF_TOKEN gerekecek.

**Veri kapsamı eksiği:** Tam tez metni dataset'te YOK — yalnız abstract. Bu bizim için yeterli (RAG + embedding + summarization için abstract ölçeği uygun); reasoner Q&A'da daha derin context istenirse kullanıcının PDF yüklemesi planlandı (cache=True opt-in).

### Rejected alternatives

1. **Kendi YÖK scraper'ımı yazmak:** Reddedildi. (a) 1 hafta gereksiz iş, (b) 13× daha küçük corpus, (c) yasal/etik gri alan, (d) wheel reinvention anti-pattern. Yol haritası v2.3'te bu karar dokümante edildi.

2. **DergiPark'ı birincil kaynak yapmak:** Reddedildi. DergiPark journal article odaklı; tez ölçeği daha büyük + akademik dil tutarlılığı tezlerde daha yüksek. DergiPark opsiyonel ek (Requirement 3 → optional).

3. **mukayese-tr veya başka Türkçe akademik dataset:** İncelendi, reddedildi. mukayese-tr summarization odaklı, küçük (<5K download/ay), corpus boyutu yetersiz. umutertugrul tek atıfta hem corpus hem schema zenginliği veriyor.

4. **Raw upstream'i derivasyon yapmadan kullanmak:** Reddedildi. (a) Filtering yapılmamış raw dataset 650K abstract'in tamamı kullanılabilir değil (kısa/boş/dil tutarsız), (b) downstream training'in deterministic olması için filter version'lı derive shipped olmalı, (c) DERIVATION.md compliance Requirement 17.

5. **HF Hub yerine dataset'i lokal Parquet'te tutmak:** Reddedildi. Kullanıcı "lokal RAG" derken kullanıcının kendi makinesini kastediyor — biz publish'leyen tarafız, HF Hub doğru kanal. Lokal kopya kullanıcının `datasets.load_dataset` cache'inde otomatik oluşur.

### Hardware budget

**Load + filter pipeline:**
- Parquet upstream 1.56 GB indirme — tek seferlik, HF cache'lenir
- RAM peak: ~4-6 GB (tüm 650K record + abstract + metadata in-memory). RTX 3050 Laptop 4GB GPU üstünde değil, sistem RAM'inde tutulur (Windows + WSL2 16 GB minimum öneri).
- Streaming mode opsiyonu (`load_dataset(..., streaming=True)`) RAM <1 GB'ye düşer; filter sırasında preferable.
- Disk: 1.56 GB upstream + 1.2 GB filtered output + 1.5 GB embeddings (Topic 11 / Faz 5 sonrası) = ~5 GB toplam yer.

**Quality scoring (opsiyonel ek pass):**
- Sentence-level Türkçe language detection (`fasttext` lid.176.bin ~125 MB) — abstract içinde gizli İngilizce/karışık dil tespit
- Bu yalnız strict filter için; loose filter sırasında atlanabilir. RAM <500 MB.

**Determinism garantisi (Requirement 2.9):**
- `datasets` lib aynı upstream snapshot + aynı filter version → bit-identik output
- Reproducibility için `derived_at` ISO-8601 timestamp + filter version string output schema'sında tutulur

**Backup planı:** Eğer upstream HF'den çekilirse veya lisansı değiştirilirse: alt ay yedek dosyamız Faz 1 tamamlandıktan sonra `data/corpora/upstream-snapshot-YYYY-MM-DD/` altında local-only (gitignore'lu) tutulacak. Yeniden publish hakkımız yok ama derive pipeline'ı çalıştırabilmemiz için snapshot zorunlu.


---

## Notes

- Each topic must be completed before starting any code in the corresponding phase.
- Rejected alternatives are as important as the selected approach — they show the reasoning trail.
- Hardware budgets matter most for Topics 2, 3, 4, 5 (fine-tuning) and Topic 7 (Space deployment).
- This log is permanent; when revising approaches later, add a new dated entry rather than overwriting.
