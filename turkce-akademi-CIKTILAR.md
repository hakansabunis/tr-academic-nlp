# tr-academic-nlp — Proje Çıktıları (Definition of Done)

> **Bu dokümanın amacı:** Proje bitiminde elimizde **somut olarak** olması
> gerekenleri tek bir tikleme listesi olarak vermek. Capstone savunma günü
> "neler hazır" sorusuna saniyeler içinde cevap verebileceğin checklist.
>
> **İlişkili dokümanlar:**
> - `turkce-akademi-YOL-HARITASI.md` (v2.3) — fazlar ve nasıl yapılacağı
> - `.kiro/specs/tr-academic-nlp/requirements.md` (v2.3) — EARS-formatlı kabul kriterleri
> - Bu dosya — **ne teslim edileceğinin somut listesi**
>
> **Sürüm:** v1.0 — 2026-04-30 (yol haritası v2.3 ile uyumlu)
> **Sahibi:** Hakan Sabunis (hakansabunis@gmail.com)

---

## 0. Üç Kanaldan Dağıtım Hedefi

Proje bittiğinde aşağıdaki **üç ayrı kanalda** ürün canlı olmalı:

```
🤗 HuggingFace Hub      📦 PyPI + GitHub        🎯 Anthropic Skills
6 model + 5 dataset     pip install +           5 sub-skill
+ 1 Space (Gradio)      Apache 2.0 source       Apache 2.0 reference impl
```

---

## 1. HuggingFace Hub Artifaktları

### 1.1 Modeller (6 toplam — 1 opsiyonel)

- [ ] **`hakansabunis/trakad-embed-v1`** — 768-dim akademik embedding (sentence-transformers + contrastive)
  - [ ] Model card: training data, eval, intended use, limitations
  - [ ] TR-MTEB akademik subset sonuçları model card'da
  - [ ] Apache 2.0 + dataset attribution (umutertugrul, TR-MTEB)
- [ ] **`hakansabunis/trakad-ner-v1`** — BERTurk fine-tune, 7 entity (YAZAR/KURUM/DERGİ/YIL/METODOLOJI/DATASET/METRİK)
  - [ ] Macro F1 ≥0.85 model card'da
  - [ ] Round-trip property test passing
- [ ] **`hakansabunis/trakad-citation-v1`** — APA/MLA/Chicago Türkçe parser + pretty-printer
  - [ ] Field-level accuracy ≥%95 APA TR
  - [ ] Round-trip property `parse(print(parse(s))) ≡ parse(s)` test passing
- [ ] **`hakansabunis/trakad-summarizer-v1`** — mT5 fine-tune Türkçe akademik özetleyici
  - [ ] ROUGE-L ≥0.35 model card'da
  - [ ] PDF→özet pipeline (header/footer/ref strip)
- [ ] **`hakansabunis/trakad-detector-v1`** — Türkçe akademik AI-yazımı detector (BERTurk classifier)
  - [ ] Binary AUC ≥0.90 (human vs AI)
  - [ ] 4-class macro F1 ≥0.75 (human/Claude/GPT/Gemini)
  - [ ] Calibration curve model card'da
- [ ] **`hakansabunis/trakad-reasoner-3b`** + **`trakad-reasoner-3b-gguf-q4`** (✨ opsiyonel — son faz)
  - [ ] Phi-3-mini QLoRA, base'den iyi 500-soru Türkçe Q&A eval
  - [ ] GGUF Q4 CPU <30s/512 tok
  - [ ] "Yeterli bilgim yok" fallback (no halüsinasyon)

### 1.2 Datasetler (5 toplam)

- [ ] **`hakansabunis/tr-thesis-academic-ready`** — umutertugrul derive, ~500K cleaned abstract
  - [ ] CC-BY-4.0 attribution dataset card'da (upstream link)
  - [ ] DERIVATION.md repo'da
  - [ ] Deterministic re-derivation (R2.9)
- [ ] **`hakansabunis/tr-thesis-embeddings-v1`** — ~500K × 768-d pre-computed FAISS-ready
- [ ] **`hakansabunis/tr-academic-ner-corpus`** — 30K CoNLL BIO etiketli paragraph
  - [ ] Cohen κ ≥0.80 (500-örnek validation)
  - [ ] 80/10/10 stratified split
- [ ] **`hakansabunis/tr-citation-pairs-tr`** — 100K APA/MLA/Chicago Türkçe parse pair
- [ ] **`hakansabunis/tr-ai-vs-human-academic`** — 20K+ 4-sınıf paragraph (human/Claude/GPT/Gemini)

### 1.3 Space

- [ ] **`hakansabunis/tr-academic-asistan`** — Gradio, **6 sekme**:
  - [ ] 📚 Literatür Tara (RAG, opsiyonel web search)
  - [ ] 📑 Makaleyi Özetle (PDF upload <60s)
  - [ ] 🔗 Atıf Düzelt (raw → APA/MLA/Chicago)
  - [ ] ✍️ Akademik Tona Çevir
  - [ ] 🛡️ AI Yazımı Tespit
  - [ ] 🧠 Konu Sor (Reasoner — opsiyonel)
  - [ ] CPU-only quantize (GGUF Q4 / INT8)
  - [ ] Türkçe error msg (no stack trace)

---

## 2. Python SDK (PyPI)

- [ ] **`pip install tr-academic-nlp`** PyPI'da yayında (Python 3.11+)
- [ ] **7 public class** import edilir:
  - [ ] `AcademicEmbedder`
  - [ ] `AcademicNER`
  - [ ] `AcademicSummarizer`
  - [ ] `CitationParser`
  - [ ] `AcademicRAG`
  - [ ] `AcademicWriter`
  - [ ] `AIDetector`
- [ ] Auto HF download + lokal cache; `ModelDownloadError` descriptive
- [ ] ChromaDB default backend + FAISS opt (`backend="faiss"`)
- [ ] `web=True` default + `web=False` KVKK modu (Brave/SearXNG adapter)
- [ ] Type annotations tüm public method/class'larda (`mypy --strict` geçer)
- [ ] **≥%80 test coverage** (`pytest-cov`)
- [ ] `pyproject.toml` pinned deps
- [ ] PyPI sayfası: README rendered, classifiers, license=Apache 2.0

---

## 3. Claude Skills (5 sub-skill)

Her skill klasöründe **mutlaka** olması gerekenler (12-madde Pre-Flight):

- [ ] `SKILL.md` — YAML frontmatter (`name` lowercase-hyphen, `description` when-to-use + when-NOT-to-use)
- [ ] `README.md` — English; reference impl pitch + performance bench + honest limitations
- [ ] `LICENSE` — **Apache 2.0**
- [ ] `EXTENSION.md` — low-resource lang port pattern (HF model swap + corpus swap rehberi)
- [ ] `scripts/` — skill'in core mantığı
- [ ] `examples/` — **≥5 working example**
- [ ] `tests/` — pytest **≥10 test case**
- [ ] `demo.gif` — README'de görsel demo
- [ ] Türkçe structured error msg (yetersiz veri/desteksiz input)
- [ ] GH Actions CI yeşil (ruff + mypy --strict + pytest)

5 skill:
- [ ] **`turkish-academic-search`** (YÖK Tez + DergiPark RAG, opt. web search)
- [ ] **`turkish-citation-parser`** (APA/MLA/Chicago)
- [ ] **`turkish-academic-summarizer`** (PDF → akademik özet)
- [ ] **`turkish-academic-writer`** (informal TR → akademik ton)
- [ ] **`turkish-academic-ai-detector`** (TR akademik AI tespit)

---

## 4. GitHub Repo

### 4.1 Root dokümanlar
- [ ] `README.md` — sword & shield + reference impl pitch + benchmark sonuçları + 3-kanal kurulum
- [ ] `LICENSE` — **Apache 2.0**
- [ ] `PRIVACY.md` — KVKK statement + lokal mod opsiyonu
- [ ] `CONTRIBUTING.md` — dev setup + test + PR rehberi
- [ ] `CHANGELOG.md` — SemVer, her release'de güncel
- [ ] `DERIVATION.md` — umutertugrul attribution + filtering kuralları + reproducibility
- [ ] `BENCHMARKS.md` — TR-MTEB attribution + sonuçlar + reproducibility script

### 4.2 docs/
- [ ] `docs/ARCHITECTURE.md` — sistem diagram + design decision rationale
- [ ] `docs/PERFORMANCE.md` — CPU + RTX 3050 4GB benchmark tablosu
- [ ] `docs/learning-log.md` — Faz 0 12 başlık × min 200 kelime özet (kronolojik)
- [ ] `docs/EXTENSION.md` — low-resource lang reference implementation rehberi

### 4.3 CI/CD
- [ ] `.github/workflows/ci.yml` — `ruff` + `mypy --strict` + `pytest` gate
- [ ] `.github/workflows/train.yml` — model retraining pipeline (opsiyonel scheduled)
- [ ] `.github/workflows/publish.yml` — PyPI release

### 4.4 Test
- [ ] `tests/unit/` — her SDK modülü
- [ ] `tests/integration/` — RAG end-to-end, skill end-to-end
- [ ] `tests/property/` — `hypothesis` ile round-trip fuzz (NER preservation, citation round-trip, embedder determinism, detector calibration)

### 4.5 Experiment tracking
- [ ] `mlruns/` (gitignore'da) — MLflow aktif, her model run'unda training params + dataset version + metrics + hardware loglu

---

## 5. Benchmark & Eval Sonuçları

### 5.1 Standart benchmark'larda yer
- [ ] **TR-MTEB akademik task subset**: top-3 (Mursit / Baysan & Güngör'e karşı competitive) — `BENCHMARKS.md` tablo
- [ ] **TR-MTEB genel leaderboard**: top-10 — `BENCHMARKS.md` tablo

### 5.2 Tek-model metrikleri
- [ ] NER macro-F1 ≥0.85 (held-out test)
- [ ] Citation parser field-level accuracy ≥%95 APA TR
- [ ] Summarizer ROUGE-L ≥0.35
- [ ] AI Detector binary AUC ≥0.90
- [ ] AI Detector 4-class macro F1 ≥0.75
- [ ] (Opsiyonel) Reasoner Türkçe Q&A: base Phi-3-mini'den iyi (500-soru eval)

### 5.3 Karşılaştırmalı (R16)
- [ ] **Claude alone vs Claude + Toolkit** — 4 task × 100 soru, BENCHMARK.md raporu
  - [ ] Literature retrieval Precision@5, Recall@10, hallucination rate
  - [ ] Citation parsing field accuracy
  - [ ] Summarization ROUGE-L + factual consistency
  - [ ] Entity extraction macro-F1
- [ ] Toolkit ≥3/4 task'ta baseline'ı geçer
- [ ] **General LLM kıyas:** GPT-4o-mini & Claude Haiku Türkçe akademik benchmark'larda kıyaslandı (NER F1, ROUGE-L, citation accuracy)

### 5.4 Eşlik kalitesi
- [ ] Inter-annotator κ ≥0.80 (NER labeling validation)

---

## 6. Performance Bütçesi (CPU baseline doğrulanmış)

- [ ] NER <500 ms / 512-token paragraph
- [ ] Embedder <2 s / 32-batch
- [ ] Summarizer <10 s / 2000 kelime
- [ ] AI Detector <500 ms / paragraph
- [ ] RAG retrieval <5 s / ~500K-doc query
- [ ] Reasoner GGUF Q4 <30 s / 512 token (opsiyonel)
- [ ] HF Space <60 s / PDF upload
- [ ] SDK RAG init <60 s / 10 PDF
- [ ] `pytest -m perf` CI'de yeşil

---

## 7. Yayım & Görünürlük

### 7.1 Garantili (A-D fazları, %95+ olasılık)
- [ ] **GitHub repo public** + ≥100 stars
- [ ] **PyPI** ≥200 haftalık install
- [ ] **HF Hub** 6 model + 5 dataset + 1 Space yayında; ≥5K aylık toplam download
- [ ] **`awesome-claude-skills`** topluluk listesinde
- [ ] **Twitter/X launch tweet** + Anthropic team etiket
- [ ] HF Space ziyaretçi 1K-10K/ay

### 7.2 Bonus (E-F fazları, %20-30 olasılık)
- [ ] (Bonus) Plugin marketplace kabul
- [ ] (Bonus) Anthropic blog feature
- [ ] (Bonus) Resmi `anthropics/skills` repo PR merge
- [ ] (Bonus) TR-MTEB v2'ye akademik subset PR (Baysan & Güngör'e)

---

## 8. Etik & Compliance

- [ ] **Apache 2.0** license (root + her skill)
- [ ] umutertugrul **CC-BY-4.0 attribution** DERIVATION.md + dataset card'larda
- [ ] **TR-MTEB citation** (Baysan & Güngör, EMNLP 2025) BENCHMARKS.md'de
- [ ] **KVKK statement** PRIVACY.md'de net
- [ ] **Honest limitations** her model card + her SKILL.md'de
- [ ] **AI Humanizer EKLENMEDİ** — etik karar tablosunda (§15) dokümante (academic dishonesty bypass)
- [ ] Anthropic Usage Policy uyumu (Skills marketplace submit edilebilir)

---

## 9. Capstone Savunma Hazırlığı

- [ ] **Pitch versiyonları** hazır:
  - [ ] 30-saniye elevator pitch
  - [ ] 2-dakika mülakat hikayesi (sword & shield + reference impl + ekosistem genişletme)
  - [ ] 5-dakika capstone sunum açılışı
- [ ] **Canlı demo:** HF Space üstünden 6 sekmenin hepsi çalışır gösterim
- [ ] **Architecture diagram:** sunum slide + ARCHITECTURE.md figure (aynı görsel)
- [ ] **Benchmark tablosu:** TR-MTEB sonuçları + R16 Baseline vs Augmented + general LLM kıyas
- [ ] **Q&A hazırlığı:**
  - [ ] "Niye humanizer yapmadın?" → §EK B etik karar
  - [ ] "Niye scraper yazmadın?" → §15 wheel reinvention reddi + umutertugrul derive
  - [ ] "Niye TR-MTEB?" → peer-reviewed standard, kendi metriği zayıf
  - [ ] "Niye Apache 2.0, MIT değil?" → Anthropic ekosistem uyumu
  - [ ] "Reasoner niye opsiyonel?" → en riskli/uzun, portfolyo bütünlüğü öncelik
- [ ] **HF profil sayfası temiz:** 6 model + 5 dataset + 1 Space + 1 önceki (turkish-flood-news-bert) — toplam 7+ artifact

---

## 10. Süreklilik

Capstone bitince proje bakımı için:

- [ ] **Quarterly retraining plan** (özellikle AI detector — yeni LLM'ler için)
- [ ] **Issue tracker** açık, label'lı (bug, enhancement, good-first-issue)
- [ ] **Roadmap** GitHub Discussions'da paylaşılmış (community input)
- [ ] **Anthropic Skills standard tracking** — agentskills.io spec değişirse uyumluluk

---

## Hızlı Özet — Tek Cümlede Ne Teslim Ediliyor

> *"6 Türkçe-özel ince ayarlı model + 5 dataset (1'i türetilmiş) + 1 Gradio Space + 1 Python SDK (PyPI) + 5 Anthropic Skill (Apache 2.0 reference impl) + TR-MTEB EMNLP 2025 standart benchmark sonuçları + Claude vs Claude+Toolkit karşılaştırma raporu + 80%+ test coverage + CC-BY-4.0/Apache 2.0 compliance — capstone savunmada üç kanaldan canlı dağıtımla gösterilebilir bir proje."*

---

**Çıktılar dosyası:** `Desktop/turkce-akademi-CIKTILAR.md`
**Sürüm:** v1.0 — 2026-04-30 (yol haritası v2.3 + requirements.md v2.3 ile uyumlu)
**Sahibi:** Hakan Sabunis (hakansabunis@gmail.com)
