# Türkçe Akademik NLP Toolkit — Proje Yol Haritası v3.0

> **Bu dokümanın amacı:** Yeni bir Claude sohbetine veya Claude Code agent'ına
> devredilebilen, sıfırdan projeyi anlatan ve uygulanmaya başlanabilecek tek
> dosyalık brief. Hakan Sabunis'in HuggingFace portfolyo + Anthropic Skill
> ekosistemi hedefli capstone-yan projesi.
>
> **Kaynak gerçek (single source of truth):** EARS-formatlı resmi gereksinimler
> için bkz. `.kiro/specs/tr-academic-nlp/requirements.md`. Bu dosya yol haritası —
> onun yürütme planı; çelişki olursa **requirements.md kazanır**.
>
> **v2.1 değişiklikleri:** (a) Tez yeniden çerçevelendi (kalite boşluğu öncelikli),
> (b) AI Detector modeli + skill eklendi (toplam 6 model + 5 skill), (c) §9.5 veri
> mimarisi bölümü eklendi, (d) Web search opsiyonel modül olarak default açık.
>
> **v2.2 değişiklikleri (Anthropic submission optimizasyonu):**
> (a) **License: MIT → Apache 2.0** (Anthropic ekosistem standardı uyumu),
> (b) Yeni §11.8 "Anthropic Pre-Flight Checklist" (12 madde),
> (c) §11 MUST HAVE'e "Reference implementation pitch" + "Demo GIF" eklendi,
> (d) §14 submission tablosu probabilistik kıyaslama (düşük kalite vs iyi mimari),
> (e) §13 mülakat hikayesine "first Turkish reference implementation" cümlesi,
> (f) §16 Faz 0'a `anthropics/skills` repo audit + agentskills.io spec çalışması.
>
> **v2.3 değişiklikleri (mevcut ekosistem entegrasyonu — wheel reinvention'dan kaçınma):**
> (a) Faz 1 scraper → **`umutertugrul/turkish-academic-theses-dataset`** doğrudan kullan
>     (650K abstract, CC-BY-4.0, TR+EN, Parquet); DergiPark scraper'ı opsiyonel ek,
> (b) Faz 5 embedder eval → **TR-MTEB (EMNLP 2025 Findings)** standart benchmark
>     entegrasyonu; kendi STS bench'i kaldırıldı,
> (c) §13 mülakat hikayesi "veri topladım" → "ekosistemi genişlettim" (NER ile zenginleştirme + akademik subset),
> (d) §18'den YÖK scraping yasal riski kaldırıldı (CC-BY-4.0 attribution yeterli),
> (e) Yeni R17 (requirements.md) — dataset attribution & derivation compliance.
>
> **v2.4 değişiklikleri (Ollama → Claude Haiku + human-in-the-loop):**
> (a) **Ollama tamamen kapsam dışı** — tüm LLM-as-labeler işleri Anthropic API üstünden
>     (Claude Haiku 3.5 NER labeling için, Sonnet AI-detector data + Reasoner CoT için),
> (b) Faz 2 NER labeling pipeline'ı **distant supervision via Claude Haiku + 100 saat
>     human review** (UniversalNER NeurIPS 2023 pattern — Türkçe akademik domain transfer),
> (c) §15 karar tablosu "Ollama qwen2.5:7b" → "Claude Haiku 3.5 + human-in-loop";
>     §17 donanım & ortam Ollama satırı kaldırıldı, Anthropic API key eklendi,
> (d) §13 mülakat hikayesine "UniversalNER pattern Türkçe akademik domain'e taşındı + human review disiplini" cümlesi,
> (e) Toplam Claude API maliyeti netleştirildi: ~$75-145 (Faz 2: ~$10-20, Faz 6.5: ~$50-100, Faz 7 opsiyonel: ~$15-25),
> (f) requirements.md R4.3/R4.4/R10.4 güncellendi + yeni R4.8 (human-in-loop discipline).
>
> **v3.0 değişiklikleri (BÜYÜK PİVOT — Secure Academic Middleware):**
> Mevcut iş kaybolmaz: Faz 0/1/2/3 ✅ tamam ve **anonymizer için kritik**. Aşağıdakiler
> middleware mimarisine geçişi tanımlar.
>
> (a) **Tez yeniden çerçevelendi:** "6 Türkçe-özel model + 1 detector ile yarış" yerine
>     "Yerel KVKK shield + Türkçe akademik prompt engine + Frontier/local LLM köprüsü";
> (b) **Mimari değişti** (§6 + ARCHITECTURE.md): kullanıcı verisi → Anonymizer → PromptEngine →
>     Ollama qwen2.5:7b (lokal, ücretsiz) → De-anonymizer → kullanıcı. Hiçbir veri makineden çıkmaz;
> (c) **Kaldırılan modeller:** `trakad-summarizer-v1` (mT5), `trakad-detector-v1` (etik —
>     false-positive akademik metinde sistematik), `trakad-reasoner-3b` (Phi-3 QLoRA);
>     gerekçe: Frontier/local LLM'ler bu görevleri prompt-engineering ile çok daha iyi yapacak;
> (d) **Korunan modeller (3):** `trakad-ner-v1` (anonymizer), `trakad-embed-v1` (RAG),
>     `trakad-citation-v1` (atıf parser — Frontier'ler hala Türkçe atıfta zayıf);
> (e) **%100 yerel + ücretsiz:** Faz 8'in LLM motoru Ollama qwen2.5:7b
>     (RTX 3050 Ti 4GB GPU dostu, ~4.7GB Q4); kullanıcı için API ücreti yok;
> (f) **Skills 5 → 4:** academic-search (RAG), citation-parser, **academic-anonymizer (yeni)**,
>     **academic-pipeline (yeni — full middleware)**;
> (g) **§10 fazları kısaltıldı:** eski Faz 6/6.5/7 kaldırıldı; yeni Faz 6 (Anonymizer modülü),
>     Faz 7 (Türkçe akademik prompt library), Faz 8 (AcademicPipeline orchestrator);
> (h) **Mülakat hikayesi (§13)** "Sword & Shield" → "Secure Academic Middleware" pivot;
> (i) **Toplam süre:** 12-13 hafta → **6-8 hafta** (capstone deadline güvenli);
> (j) **MVP çalışıyor (2026-05-01):** trakad-ner-v1 HF'de canlı, pipeline.py + Ollama
>     qwen2.5:7b ile end-to-end Türkçe akademik özetleme test edildi (analyze_and_rewrite).

---

## 0. Bu Dokümanı Nasıl Kullan (Claude'la Çalışırken)

Bu dosyayı yeni bir Claude sohbetine yapıştırınca:

1. **Faz seç** (§10 tablosundan). Bağımlılık zinciri:
   `0 → 1 → 2 → (3, 5, 6 paralel) → 4 → 6.5 → 8 → 9.5 → 9.7 → 7 (opsiyonel) → 10`
2. **Her fazda Claude'a §21 görev kartı şablonunu doldur:**
   - **Hedef:** §10'daki o fazın çıktı satırı
   - **Acceptance criteria:** §10 kabul kriteri sütunu + `requirements.md` Requirement N
   - **Donanım kısıtı:** §17 (RTX 3050 4GB / Windows + WSL2 / CPU baseline)
3. **Bitince:** §11 Anthropic-grade kontrol listesi + §20 sayısal başarı kriterleri
   + ilgili requirement'ın acceptance criteria'larını tikle.

> **Not (v2.1):** AI Detector (Faz 6.5) ve veri-mimarisi detayları için requirements.md'ye
> R16 (AI Detection) eklenmesi gerekir; mevcut sürümde yol haritası tek başına
> implementasyon için yeterli detayda.

---

## 1. Tek Cümlelik Tez (v3.0 — Secure Academic Middleware)

> *"Genel-amaçlı LLM'ler (Claude, GPT-4, Qwen, Llama) güçlü, ama Türk akademisyenler
> tezini ChatGPT'ye yükleyemiyor — KVKK riski + Türkçe akademik üslup zayıflığı
> sorun. Çözüm: **yerel KVKK shield (NER anonymizer) + Türkçe akademik prompt engine
> + yerel Ollama LLM** üçlüsü ile akademisyene 'GPT-4 kalitesi, KVKK uyumlu, ücretsiz'
> diyebilen `tr-academic-nlp` middleware'i."*

**Değer önerisi:**
- **Yerel KVKK shield:** Hassas entity'ler (yazar, kurum, yıl vb.) lokal NER ile
  maskelenir; LLM sadece anonim formla çalışır
- **Türkçe akademik prompt engine:** Pasif çatı, üçüncü tekil şahıs, akademik
  terminoloji, APA atıf — Frontier modelinin Türkçe akademik üslup zayıflığını kapatır
- **Yerel LLM (Ollama qwen2.5:7b):** %100 ücretsiz, makinede kalır, RTX 3050 Ti 4GB
  GPU yeter; istenirse Frontier API moduna da geçilebilir
- **Capstone savunma cümlesi:** *"Akademisyen tezini ChatGPT'ye yükleyemiyor; biz
  yerel kalkanla Frontier kalitesini KVKK uyumlu sunuyoruz."*

**v3.0 öncesi tez (v2.4):** "6 Türkçe-özel model eğitiyorum" idi — Frontier modellerle
yarışmak yerine onları wrap etmek daha realistik + future-proof + capstone scope için
güvenli (12-13 hafta → 6-8 hafta).

## 2. Hedef Kitle

| Kitle | Sayı | Niye kullanır |
|---|---|---|
| Türk lisansüstü öğrenciler | 200K+ | Tez yazımı + literatür taraması (kalite) |
| Türk akademisyenler | 100K+ | Makale review, atıf yönetimi, AI tespit (kalite + savunma) |
| Türk lisans öğrencileri | 5M+ (kısmi) | Bitirme projesi yardımı |
| Türkçe AI geliştiren şirketler | KOBİ + kurumsal | KVKK uyumlu lokal NLP altyapısı |
| **Üniversite kurulları, dergi editörleri, jüriler** | **Akademi** | **AI-yazılı metin tespiti (detector)** |
| Türkçe NLP araştırmacıları | Akademi | Baseline modeller |

## 3. Pazar Boşluğu (Nisan 2026 araştırma sonucu)

### 3a. Kalite boşluğu (birincil — v2.1 yeni)

Genel-amaçlı LLM'ler Türkçe akademik dilde ölçülebilir şekilde zayıf:
- **ChatGPT/Claude Türkçe özet:** Akademik terminolojiyi popülerleştiriyor, "şudur ki" gibi anti-akademik kalıplar üretiyor
- **Atıf parse:** Genel LLM'ler "Yılmaz, A.M. (2023)" formatını parse edebilir ama Türkçe-spesifik "Soyadı, Adı" sıralamasını tutarsız bırakıyor
- **NER:** Generic "person/org" tanır ama akademik METODOLOJI/DATASET/METRİK ayrımı yok
- **ROUGE-L on Turkish thesis abstracts (mevcut benchmark'lar):** Genel LLM'ler ~0.25-0.30; Türkçe-özel mT5 fine-tune ile 0.35+ hedef

### 3b. Ekosistem boşluğu (HuggingFace)
- **Mevcut Türkçe LLM'ler:** Trendyol-LLM (~30-50K/ay), ytu-cosmos (~10-20K), Kanarya, WiroAI, BERTurk (~200K/ay)
- **Türkçe akademik özel model:** ❌ YOK
- **Türkçe akademik NER:** ❌ Yok (sadece generic person/org/location)
- **Türkçe atıf parser:** ❌ Yok
- **Türkçe akademik özetleyici:** ❌ Yetersiz (mukayese-tr <5K/ay)
- **Türkçe akademik embedding:** ❌ multilingual-e5 hâlâ standart, Türkçe-özel yok
- **YÖK Tez RAG sistemi:** ❌ Yok
- **Türkçe akademik AI detector:** ❌ **YOK** (Turnitin İngilizce, GPTZero/ZeroGPT İngilizce only)

### 3c. Mevcut benzer toolkit'ler
- **VNGRS-AI/vnlp** (en yakın) — tokenizer + NER + sentiment, LLM/embedding/summarization yok, 2024'ten beri durağan
- **zemberek-nlp** — Java, klasik morfoloji, 2020'den durağan
- **mukayese** — toolkit değil benchmark
- **feynman.is** (uluslararası emsal) — İngilizce arXiv için research agent; Türkçe/YÖK yok
- **Awesome listeler** — sadece dağınık link koleksiyonu

### 3d. Anthropic Claude Skills ekosistemi
- Anthropic resmi `anthropics/skills` repo: 4 kategori (Creative, Dev, Enterprise, Document)
- Türkçe skill: ❌ 0 | Akademik skill: ❌ 0 | NLP skill: ❌ 0

**Boşluk gerçek ve dar:** Türkçe akademik domain için **birleşik, kalite-odaklı, ek olarak KVKK opsiyonlu** altyapı yok.

## 4. Proje Adı

Repo/paket adı: **`tr-academic-nlp`** (HF aramasında bulunabilirlik için).

## 5. Üçlü Dağıtım Stratejisi

```
              🏛️ Çekirdek: 6 model + 4 dataset
                      (HuggingFace)
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
  🤗 HF Space      📦 GitHub Repo    🎯 Claude Skills
  (Gradio demo)    (Python SDK)      (5 sub-skill)
```

Her ayak farklı bir kitleye ulaşır:
- **HF Space** → Capstone jürisi, ML camiası, son kullanıcı (kurulum yok)
- **GitHub repo** → Geliştiriciler, işverenler (`pip install tr-academic-nlp`)
- **Claude Skills** → Anthropic ekosistemi, early adopter farklılaştırıcı

## 6. Teknik Mimari

```
┌──────────────────────────────────────────────────────────┐
│  Kullanıcı arayüzleri:                                    │
│  ┌──────────┐  ┌──────────┐  ┌─────────────┐            │
│  │ HF Space │  │ Python   │  │ Claude      │            │
│  │ (Gradio) │  │ SDK      │  │ Skills (×5) │            │
│  └─────┬────┘  └─────┬────┘  └─────┬───────┘            │
│        └─────────────┼────────────┘                      │
└──────────────────────┼───────────────────────────────────┘
                       │
        ┌──────────────┼──────────────────┐
        ▼              ▼                   ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────────┐
│ Çekirdek      │ │ Veri Katmanı  │ │ Web Search        │
│ Modeller (6)  │ │               │ │ (opsiyonel modül) │
│               │ │ • YÖK Tez     │ │                   │
│ • Embedding   │ │ • DergiPark   │ │ • Brave / SearXNG │
│ • Domain NER  │ │ • Atıf parser │ │ • default: AÇIK   │
│ • Citation    │ │ • FAISS /     │ │ • web=False ile   │
│ • Summarizer  │ │   ChromaDB    │ │   tam lokal mod   │
│ • Reasoner    │ │ • Pre-emb HF  │ │   (KVKK)          │
│ • AI Detector │ │   datasets    │ │                   │
└───────────────┘ └───────────────┘ └───────────────────┘
```

## 7. HuggingFace Artifaktları (v2.1 — 6 model + 4 dataset)

```
huggingface.co/hakansabunis/

📦 Modeller (6)
├── trakad-embed-v1            ← Türkçe akademik sentence embedding (768-dim)
├── trakad-ner-v1              ← Akademik NER (7 entity, BERTurk fine-tune)
├── trakad-citation-v1         ← Türkçe atıf parser (APA/MLA/Chicago)
├── trakad-summarizer-v1       ← Türkçe akademik özetleyici (mT5 fine-tune)
├── trakad-detector-v1         ← ✨ YENİ: Türkçe akademik AI-yazımı detector (BERTurk classifier)
└── trakad-reasoner-3b         ← Phi-3-mini QLoRA Türkçe akademik Q&A (opsiyonel son faz)
   └── trakad-reasoner-3b-gguf-q4  ← CPU için quantize edilmiş (~2GB)

📊 Datasetler (4 + 1 derive — v2.3)
├── tr-thesis-academic-ready   ← ✨ v2.3: umutertugrul/turkish-academic-theses-dataset'ten derive (filtered/cleaned, 650K → ~500K kullanılabilir abstract)
├── tr-thesis-embeddings-v1    ← v2.1: ~500K × 768-d pre-computed FAISS-ready embeddings (umutertugrul derive üzerinde)
├── tr-academic-ner-corpus     ← 30K akademik entity etiketli paragraph (CoNLL BIO) — umutertugrul abstract'lerinden örneklenir
├── tr-citation-pairs-tr       ← 100K atıf parse örneği (APA/MLA/Chicago Türkçe)
└── tr-ai-vs-human-academic    ← v2.1: 20K+ insan/AI eşleşmiş akademik paragraph (4 sınıf: human/Claude/GPT/Gemini)

ℹ️ Üst-kaynak attribution (v2.3):
   • umutertugrul/turkish-academic-theses-dataset (CC-BY-4.0) → tr-thesis-academic-ready
   • TR-MTEB (Baysan & Güngör, EMNLP 2025 Findings) → embedder eval pipeline

🤗 Space (1)
└── tr-academic-asistan        ← Tüm modeller tek arayüzde (6 sekme)
```

## 8. Claude Skills Paketi (v2.1 — 5 sub-skill)

5 ayrı sub-skill (Anthropic'in "tek odaklı" prensibine uygun):

```
.claude/skills/
├── turkish-academic-search/         (YÖK Tez + DergiPark RAG, opt. web search)
│   ├── SKILL.md                     (name + when-to-use + when-NOT-to-use + 5+ example)
│   ├── README.md                    (English)
│   ├── LICENSE                      (MIT)
│   ├── scripts/
│   ├── examples/                    (≥5)
│   └── tests/                       (pytest, ≥10 case)
├── turkish-citation-parser/         (Atıf parse + format)
├── turkish-academic-summarizer/     (PDF → akademik özet)
├── turkish-academic-writer/         (Akademik tona dönüştürme)
└── turkish-academic-ai-detector/    ← ✨ YENİ: AI-yazılı metin tespiti (TR akademik)
```

## 9. Kullanım Örnekleri (Son Ürün)

### Web UI (HuggingFace Space)
```
🌐 huggingface.co/spaces/hakansabunis/tr-academic-asistan

Sekmeler (v2.1 — 6 sekme):
📚 Literatür Tara         (YÖK + DergiPark RAG, opsiyonel web search)
📑 Makaleyi Özetle        (PDF upload → akademik özet)
🔗 Atıf Düzelt            (raw text → APA/MLA/Chicago)
✍️ Akademik Tona Çevir    (informal Türkçe → akademik)
🛡️ AI Yazımı Tespit       (✨ YENİ: metin → human/AI olasılığı + hangi LLM)
🧠 Konu Sor               (Reasoner Q&A, kaynaklı — opsiyonel)
```

### Python SDK
```python
from tr_academic_nlp import (
    AcademicEmbedder, AcademicNER, AcademicSummarizer,
    CitationParser, AcademicRAG, AcademicWriter,
    AIDetector,  # ✨ YENİ
)

# Literatür tarama (default: web=True; KVKK için web=False)
rag = AcademicRAG(corpus="yok-tez", web=False)
results = rag.search("derin öğrenme sel tahmini")

# AI detector
det = AIDetector()
verdict = det.classify("Bu çalışmada derin öğrenme yöntemleri ile...")
# → {"label": "AI", "confidence": 0.92, "likely_source": "Claude"}

# Diğer örnekler aynı (NER, citation, summarizer, RAG)
```

### Claude Skill
```
Kullanıcı: "Bu paragrafı AI mı yazmış?"
↓
Claude → turkish-academic-ai-detector skill tetiklenir
↓
Claude → "AI yazımı tespit edildi (güven: %92, muhtemel kaynak: Claude). Sebep: ..."
```

## 9.5. Veri Mimarisi & Lokal RAG (v2.3 — umutertugrul entegrasyonu)

**Load-derive-distribute, run-locally** modeli — scrape yok, mevcut dataset üzerinde derive:

```
┌─────────────────────────────────────────────────────────┐
│  BUILD-TIME (bir kez, biz yapıyoruz)                     │
│                                                          │
│  umutertugrul/turkish-academic-theses-dataset (HF)      │
│  650K abstract, TR+EN, CC-BY-4.0                        │
│         ↓ load + filter + clean + sub-sample            │
│  tr-thesis-academic-ready (derived, ~500K)              │
│         ↓ trakad-embed v1 ile encode                    │
│  HuggingFace Hub'a 5 dataset yükle:                     │
│  • tr-thesis-academic-ready   (~1.2 GB cleaned Parquet) │
│  • tr-thesis-embeddings-v1    (~1.5 GB ~500K×768d)      │
│  • tr-academic-ner-corpus     (~50 MB CoNLL BIO)        │
│  • tr-citation-pairs-tr       (~30 MB JSONL)            │
│  • tr-ai-vs-human-academic    (~40 MB 4-class JSONL)    │
└─────────────────────────────────────────────────────────┘
                         ↓ (pip install + first run)
┌─────────────────────────────────────────────────────────┐
│  RUN-TIME (her kullanıcı kendi makinesinde)              │
│                                                          │
│  HF download (~380 MB, bir kez, otomatik cache)         │
│         ↓                                                │
│  Lokal ChromaDB index build (saniyeler)                 │
│         ↓                                                │
│  Sorgu → trakad-embed lokalde encode → retrieve         │
│         ↓                                                │
│  (Opsiyonel) web=True → Brave/SearXNG augment           │
│         ↓                                                │
│  Cevap + inline citation                                │
│                                                          │
│  Kullanıcı kendi PDF'lerini incremental ekleyebilir     │
└─────────────────────────────────────────────────────────┘
```

### Telif & KVKK kararları

| Veri | Nerede | Sebep |
|---|---|---|
| Tez metadata (başlık, yazar, kurum, yıl) | HF Hub ✓ | Public, KVKK temiz |
| Tez abstract'ı | HF Hub ✓ | YÖK zaten public |
| **Tez tam metni** | **HF Hub ✗** | Telif belirsiz; her tez yazar izni farklı |
| Tam metin URL'si | HF Hub ✓ | Sadece pointer |
| Pre-computed embeddings | HF Hub ✓ | Tersine çevrilemez (lossy) |
| Kullanıcı PDF | **Sadece kullanıcı diski** | `cache=True` opt-in olmadan persist edilmez |

### Boyut & performans (CPU baseline — v2.3 güncel)

| Kalem | Boyut | Not |
|---|---|---|
| ~500K cleaned abstract (Parquet) | ~1.2 GB | umutertugrul derive |
| ~500K × 768-d float32 embedding | ~1.5 GB | FAISS-ready |
| ChromaDB index (HNSW, k=5) | ~150 MB | overhead + graph |
| **Toplam ilk indirme** | **~2.8 GB** | bir kez, HF cache'lenir |
| Kullanıcı tarafı RAM | ~3-4 GB | embeddings + index in-memory |
| Query latency | <5 s/500K doc CPU | R9.7 — daha büyük corpus, sliding window aynı |
| **Quick-start opsiyonu** | **~380 MB** | İsteyene 50K alt-örneklenmiş "lite" sürüm (CPU-first laptops) |

### Index store kararı: **ChromaDB** (default)

ChromaDB seçildi çünkü kullanıcı kendi PDF'ini ekleyince incremental gerekiyor + metadata filter ("yıl=2023, alan=mühendislik") native destekli. FAISS opsiyonel hız modu (`backend="faiss"`).

### Web search opsiyonel modülü

- **Default:** `web=True` (genel kullanıcı için zenginleşmiş cevap)
- **KVKK modu:** `web=False` (sorgu hiçbir yere gitmez)
- **Sağlayıcı seçimi:** Brave Search API veya SearXNG (privacy-first); Perplexity/Gemini de opsiyonel
- **Disclaimer:** SDK init'te `web=True` ise log'a "Web search açık — sorgu üçüncü tarafa gidiyor" satırı düşürülür

## 10. Faz Planı (v3.0 — Secure Academic Middleware, 6-8 hafta)

> **NOT:** Eski (v2.4) faz tablosu aşağıda olduğu gibi korundu (history için). v3.0
> pivot ile **gerçek ilerleme + kalan iş** aşağıdaki "Mevcut Durum" tablosunda. Kaldırılan fazlar (Faz 6 mT5, Faz 6.5 detector, Faz 7 reasoner) ❌ ile işaretli; eklenen fazlar (yeni 6 anonymizer, 7 prompts, 8 pipeline) ✅ ile.

### v3.0 Mevcut Durum (2026-05-01)

| # | Faz | Durum | Kanıt |
|---|---|---|---|
| 0 | Repo + araştırma altyapısı | ✅ tamam | git history, learning-log.md |
| 1 | Dataset preparation (umutertugrul → 1986) | ✅ tamam | data/corpora/smoke-2k/ |
| 2 | NER labeling (Sonnet + offset fix + temizlik) | ✅ tamam | docs/labeler-eval/api-sonnet-2k-fixed.jsonl |
| 3 | trakad-ner-v1 BERTurk fine-tune | ✅ HF'de canlı | https://huggingface.co/hakansabunis/trakad-ner-v1 |
| 4 | Atıf parser (`trakad-citation-v1`) | ⏳ planlanan | — |
| 5 | Embedder + ChromaDB local RAG | ⏳ planlanan | — |
| ~~6~~ | ~~mT5 summarizer~~ | ❌ KALDIRILDI v3.0 | Frontier/local LLM yapacak |
| ~~6.5~~ | ~~AI detector~~ | ❌ KALDIRILDI v3.0 | Etik (false positive) |
| ~~7~~ | ~~Phi-3 reasoner~~ | ❌ KALDIRILDI v3.0 | Ollama qwen2.5:7b yeter |
| **6** | **Anonymizer (KVKK shield)** | ✅ tamam | sdk/tr_academic_nlp/anonymizer.py |
| **7** | **Türkçe akademik prompt library** | ✅ iskelet | sdk/tr_academic_nlp/prompts/system_prompts.py |
| **8** | **AcademicPipeline + Ollama** | ✅ MVP çalışıyor | sdk/tr_academic_nlp/pipeline.py — analyze_and_rewrite() canlı |
| 9.5 | HF Space (Gradio demo) | ⏳ planlanan | — |
| 9.7 | Claude Skills (4 sub-skill) | ⏳ planlanan | — |
| 10 | Docker + CI/CD + docs | ⏳ kısmi | .github/workflows/ci.yml var |

**Kalan ana iş:** Faz 4 (atıf parser, 1 hafta) + Faz 5 (embedder + RAG, 1.5 hafta) + Faz 9.5 (Gradio Space, 5 gün) + Faz 9.7 (4 Skill, 1 hafta) ≈ **4-5 hafta** kapanış için.

### Eski (v2.4) tablo — history için

## 10b. Faz Planı (eski v2.4, history)

| # | Faz | Süre | Çıktı | Kabul kriteri özet (Requirement N) |
|---|---|---|---|---|
| **0** | **Araştırma + Öğrenme Altyapısı** | **5-7 gün** | `docs/learning-log.md` + paper/tutorial özetleri | 9 konu × min 200 kelime özet (scraping, BERTurk FT, sentence-transformers, mT5, QLoRA, FAISS/Chroma, Gradio, packaging, Skills spec) + seçim/red gerekçeleri + RTX 3050 4GB için quantization stratejisi (**R1**) |
| 1 | **Dataset preparation (v2.3 — scraper yok)** | **3-4 gün** | `tr-thesis-academic-ready` derive dataset + opsiyonel DergiPark zenginleştirme | umutertugrul/turkish-academic-theses-dataset (650K) load → filter (boş abstract, kısa metin, tekrar) → clean (Unicode normalize, Türkçe karakter) → sub-sample (~500K kullanılabilir) → CC-BY-4.0 attribution + DERIVATION.md; opsiyonel DergiPark fetcher (1s rate, DOI dedup, 5 alan) ek alanlar için (**R2 revize, R3 opsiyonel, R14.2, R17 yeni**) |
| 2 | Akademik NER veri etiketleme (LLM + human-in-loop) | 2-4 hafta (~100h human review) | 30K etiketli paragraph (CoNLL BIO) | Tam 7 entity; regex high-conf pre-pass + **Claude Haiku 3.5 full annotation** + tüm 30K human review (Hakan); 500-örnek 2nd-annotator κ ≥0.80; 80/10/10 stratified split; **UniversalNER (NeurIPS 2023) pattern Türkçe akademik domain'e adapt** (**R4 v2.4**) |
| 3 | Akademik NER fine-tune (BERTurk) | 1 hafta | `hakansabunis/trakad-ner-v1` HF | Macro F1 ≥0.85; CPU <500ms/512-tok; sliding window 50-tok overlap; round-trip property (**R5**) |
| 4 | Atıf parser (regex + LLM verify) | 1 hafta | `hakansabunis/trakad-citation-v1` HF + 100K dataset | Field accuracy ≥%95 APA TR; auto-detect; round-trip parse↔print; Türkçe karakter + "Soyadı, Adı" desteği (**R6**) |
| 5 | **Akademik embedding fine-tune + TR-MTEB eval (v2.3)** | **1-1.5 hafta** | `hakansabunis/trakad-embed-v1` HF + `tr-thesis-embeddings-v1` (~500K pre-computed) | 768-dim; deterministic output; CPU 32-batch <2s; **TR-MTEB (EMNLP 2025) full pipeline'da değerlendirildi**: akademik task subset'inde top-3 (Mursit / Baysan & Güngör'e karşı competitive), genel TR-MTEB'de top-10; semantik eşit ≥0.85, alakasız <0.50 (**R7 revize**) |
| 6 | Akademik özetleyici (mT5 fine-tune) | 1 hafta | `hakansabunis/trakad-summarizer-v1` HF | ROUGE-L ≥0.35; PDF→özet (header/footer/ref strip); 150-300 kelime default; CPU <10s/2000 kelime (**R8**) |
| **6.5** | **AI Detector (Türkçe akademik)** ✨ YENİ | **1 hafta** | **`hakansabunis/trakad-detector-v1` HF + `tr-ai-vs-human-academic` dataset** | **Binary AUC ≥0.90 (human/AI); 4-class macro F1 ≥0.75 (human/Claude/GPT/Gemini); 20K+ eşleşmiş çift; "düşük güven" fallback; CPU <500ms/paragraph (TBD: requirements.md R16)** |
| 8 | SDK + RAG packaging | 1 hafta | `pip install tr-academic-nlp` (PyPI) | 7 public class (Embedder/NER/Summarizer/CitationParser/RAG/Writer/**AIDetector**); Python 3.11+; auto HF download + cache; pyproject.toml pinned; type annotations; ≥%80 test coverage; ChromaDB default + FAISS opt; `web=True` default + `web=False` KVKK modu (**R9, R11**) |
| 9.5 | HF Space (Gradio demo) | 5 gün | `hf.co/spaces/hakansabunis/tr-academic-asistan` | **6 sekme** (5 + AI Detector); PDF<60s; CPU-only quantize; RAG'da kaynak göster; Türkçe error msg (**R12**) |
| **9.7** | **Claude Skills paketi (×5) + Anthropic-grade** | **7-10 gün** | 5 spec-compliant sub-skill | Tam 5 sub-skill; tek odak; her SKILL.md when-to-use + when-NOT-to-use + 5+ example; English doc + Türkçe I/O; MIT LICENSE/skill; structured Türkçe error msg; pytest 10+ test/skill; GH Actions CI (**R13**) |
| 7 | Reasoner LLM (Phi-3 QLoRA) — **opsiyonel son** | 2-3 hafta | `hakansabunis/trakad-reasoner-3b` + GGUF Q4 | Base Phi-3-mini'den iyi; QLoRA 4-bit, GPU <3.8GB; "yeterli bilgim yok" fallback; GGUF Q4 CPU <30s/512 tok (**R10**) |
| 10 | Docker + CI/CD + MLflow + docs | 1 hafta | Production-ready | ruff + mypy + pytest CI gate; semver + CHANGELOG; ARCHITECTURE/PERFORMANCE/PRIVACY/CONTRIBUTING; MLflow run history (**R15**) |

**Bağımlılık zinciri:** `0 → 1 → 2 → (3, 5, 6 paralel) → 4 → 6.5 → 8 → 9.5 → 9.7 → [7 opsiyonel] → 10`

**Toplam:** ~12-14 hafta (Faz 6.5 dahil); reasoner opsiyonel olduğu için minimum savunulabilir sürüm ~10-11 hafta.

## 11. Anthropic-Grade Skill Kriterleri

### 🟢 MUST HAVE (Requirement 13.1-13.5)
1. **Spec-compliant SKILL.md** — `name` (lowercase-hyphen), `description` (when-to-use + when-NOT-to-use)
2. **Tek odaklı scope** — kitchen sink yok, ayrı sub-skill'ler (tam 5), bundle gibi sunma
3. **Standalone çalışır** — minimal external deps
4. **Apache 2.0 license** her sub-skill'de (v2.2: Anthropic ekosistem standardı; eski MIT karar revize)
5. **İngilizce dokümantasyon** (input/output Türkçe)
6. **Reference implementation pitch** (✨ v2.2) — README başında "low-resource lang reference impl" pitch + EXTENSION.md
7. **Demo GIF** her skill için (✨ v2.2) — README'de görsel doğrulama

### 🟡 SHOULD HAVE (Requirement 13.6-13.8)
8. **Reference implementation pattern** — başkası kendi diline port edebilsin (EXTENSION.md zorunlu, MUST'a alındı)
9. **Net invocation triggers** ("Use when...", "DO NOT use when...")
10. **5+ working example** her skill için
11. **Pytest + GitHub Actions CI** — ≥10 test/skill
12. **Performance benchmarks** README'de
13. **Structured Türkçe error msg** (yetersiz veri/desteksiz input)

### 🔵 NICE TO HAVE
14. Bench/eval data, ARCHITECTURE.md, CHANGELOG.md, CITATION.cff

### 🟣 ANTHROPIC-SPECIFIC
15. **Honest limitations** — overclaim yok
16. **Harm mitigation** — halüsinasyon guard, "I don't know" cevap modu
17. **Helpfulness signals** — açık hata mesajları, alternatif önerme

## 11.8. Anthropic Submission Pre-Flight Checklist (✨ v2.2)

`anthropics/skills` repo'ya / awesome-claude-skills'a / marketplace'e PR atmadan
önce **her skill için** tek tek tikle (12 madde):

- [ ] **License:** Apache 2.0 + LICENSE dosyası skill klasöründe
- [ ] **SKILL.md frontmatter:** YAML `name` (lowercase-hyphen) + `description` (when-to-use + when-NOT-to-use)
- [ ] **Examples:** ≥5 working usage örneği SKILL.md veya `examples/` altında
- [ ] **Tests:** Pytest ≥10 test case `tests/` altında, hepsi yeşil
- [ ] **EXTENSION.md:** Low-resource lang port pattern dokümante (HF model swap + corpus swap rehberi)
- [ ] **Demo GIF:** README'de skill kullanımının görsel demo'su
- [ ] **Reference impl pitch:** README başında "low-resource academic NLP reference" cümle
- [ ] **Honest limitations:** README'de "Bu skill X yapmaz, Y için uygun değil" bölümü
- [ ] **Türkçe error msg:** Structured error formatı (yetersiz veri/desteksiz input için Türkçe açıklama)
- [ ] **English docs:** README + ARCHITECTURE İngilizce (input/output Türkçe)
- [ ] **Performance bench:** README'de CPU latency tablosu (§11.5'tan)
- [ ] **CI green:** GH Actions ruff + mypy --strict + pytest yeşil son commit'te

## 11.5. Performance Bütçesi (CPU Baseline)

| Bileşen | Hedef | Donanım | Requirement |
|---|---|---|---|
| NER (`trakad-ner-v1`) | <500 ms/paragraph (≤512 tok) | CPU | R5.4 |
| Embedder (`trakad-embed-v1`) | <2 s/32-batch | CPU | R7.5 |
| Summarizer (`trakad-summarizer-v1`) | <10 s/2000 kelime | CPU | R8.8 |
| **Detector (`trakad-detector-v1`)** | **<500 ms/paragraph** | CPU | TBD R16 |
| RAG retrieval | <5 s/query, 100K-doc index | CPU | R9.7 |
| Reasoner GGUF Q4 | <30 s/512 tok | CPU | R10.7 |
| HF Space | <60 s/PDF upload | HF free CPU | R12.3 |
| SDK RAG init | <60 s/10 PDF | CPU | R11.8 |

## 11.7. Doğruluk / Round-trip Garantileri (Property Tests)

| Property | Açıklama | Requirement |
|---|---|---|
| NER preservation | Extract→re-insert tüm span'leri korur | R5.8 |
| Citation round-trip | `parse(print(parse(s))) ≡ parse(s)` | R6.6 |
| Embedder determinism | İki ardışık `embed(s)` bit-identik | R7.8 |
| Reasoner non-hallucination | Düşük confidence → "yeterli bilgim yok" | R10.5 |
| Citation auto-detect | Format belirtmeden ID'lenir | R6.3 |
| NER empty input safety | Tanınan entity yok → `[]` | R5.5 |
| **Detector calibration** | **Sıcaklık skalasında kalibre; reported confidence ≈ ampirik accuracy** | **TBD R16** |

## 12. İlan Maddesi → Proje Bileşeni Eşleştirmesi

| İlan maddesi | Karşılayan bileşen |
|---|---|
| Transformer LLM eğitimi | Phi-3-mini QLoRA fine-tune |
| RAG mimarisi | LangChain + ChromaDB + Türkçe embedder |
| Vektör DB / embedding | ChromaDB (default) + FAISS (opt) |
| Sınıflandırma | **AI detector + belge tipi sınıflandırıcı** |
| NER | Akademik domain NER |
| Özetleme | Türkçe akademik summarizer |
| Soru-cevap | RAG + reasoner LLM |
| Çıkarım optimizasyonu | GGUF Q4 quantization |
| LLMOps | MLflow + HF model versions |
| HF/LangChain/LlamaIndex | LangChain native |
| FAISS/Chroma | İkisi de |
| LoRA/QLoRA/PEFT | QLoRA |
| PyTorch | Tüm eğitim |
| Docker/CI-CD | Dockerfile + GH Actions |
| Linux/bash | Mac/WSL |
| XAI / halüsinasyon | RAG citation + Turk-LettuceDetect entegrasyonu + AI detector calibration |

**14/14 madde karşılanır + AI detection bonus.** RLHF/DPO/PPO opsiyonel.

## 13. Mülakat Hikayesi (v3.0 — Secure Academic Middleware)

> *"Türk akademisyenler GPT-4 / Claude'a teze dair veri yükleyemiyor — KVKK riski
> + Türkçe akademik üslup zayıflığı. Çözüm: yerel KVKK shield + Türkçe akademik
> prompt engine + yerel Ollama LLM köprüsü. Kendi eğittiğim BERTurk NER (`trakad-ner-v1`)
> hassas entity'leri lokalde maskeliyor; akademik prompt library Türkçe pasif çatı
> + APA atıf zorluyor; Ollama qwen2.5:7b yerelde inference yapıyor — hiçbir veri
> makineden çıkmıyor. **'GPT-4 kalitesi, KVKK uyumlu, ücretsiz' diyebiliyorum.**
> Mimari Frontier modeller gelişince otomatik daha akıllanır — small custom
> model'leri devlerle yarıştırmak yerine onları akıllıca paketledim. v3.0 pivot:
> 6 ayrı model eğitmek yerine (mT5 summarizer, Phi-3 reasoner, AI detector
> deprecate ettim) 3 utility model + middleware pattern; capstone scope 12-13
> haftadan 6-8 haftaya indirildi. Anthropic Skills ekosisteminde ilk Türkçe
> akademik 'KVKK shield + LLM gateway' paketi olarak yayınladım."*

**v3.0 öncesi hikaye (v2.4 — history):**

## 13b. Mülakat Hikayesi (eski v2.4 — Sword & Shield + Reference Impl + Ekosistem Genişletme + Disiplinli Annotation)

> *"Genel-amaçlı LLM'ler Türkçe akademik dilde zayıf — terminoloji bozuyor, atıf
> yapısını anlamıyor, akademik tonu yakalayamıyor. Bu kalite boşluğunu
> Türkçe-özel modellerle kapattım: NER + atıf parser + embedding + özetleyici +
> reasoning LLM (sword — Türkçe akademiyi daha iyi okuyup yazıyor). Üstüne bir
> de Türkçe akademik AI detector eğittim — Turnitin'in Türkçe'de göremediğini
> görüyor (shield — AI yazılı metni tespit ediyor). **NER training data için
> UniversalNER (NeurIPS 2023) distillation pattern'ini Türkçe akademik domain'e
> taşıdım — Claude Haiku 3.5 ile 30K paragraph pre-label, sonra her birini elle
> review ettim (~100 saat); 500-sample subset için bir 2. annotator ile κ ≥0.80
> doğruladım. Bu LLM-assisted human-in-the-loop disiplini olmadan tek annotator
> bir capstone scope'unda 30K manual etiketleme imkânsızdı; sadece Claude da yine
> bırakırsam paper-quality reviewer kabul etmezdi — hibrit doğru denge.**
> **Mühendislik kararı olarak
> tekerleği yeniden icat etmedim:** YÖK abstract'leri için zaten umutertugrul'un
> 650K'lık CC-BY-4.0 dataset'i vardı — onu akademik NER ile zenginleştirip
> derive ettim. Türkçe embedding değerlendirmesi için Baysan & Güngör'ün
> EMNLP 2025'te yayınladığı TR-MTEB benchmark'ı vardı — kendi metriğimi
> yazmak yerine onu standardize ettim ve akademik-domain alt-subset ekledim.
> Aynı altyapı KVKK isteyen kurumlar için lokal modda da çalışıyor.
> **Anthropic Skills ekosisteminde mevcut non-English skill yoktu — bu paketi
> `low-resource academic NLP skills` için reference implementation olarak
> Apache 2.0 lisansla yayınladım; başka diller aynı pattern'i kendi dillerine
> port edebilir.** `pip install tr-academic-nlp`, Anthropic Skills paketi,
> HF Space — üç kanaldan dağıtım."*

**Sword & Shield + Reference Impl + Ekosistem Genişletme çerçevesi:** Kalite (writer/summarizer/embedder) + savunma (detector) + topluluk katkısı (low-resource lang reference) + olgun mühendislik (mevcut varlıkları derive et, yeniden icat etme). Dördü birlikte etik + ölçülebilir + savunulabilir.

## 14. Anthropic Submission Stratejisi (v2.2 — probabilistik kıyas)

İki kolon: **Düşük kalite** (spec'e uyulmuyor, MIT, demo yok) vs **İyi mimari**
(§11.8 Pre-Flight Checklist tüm 12 madde tikli, Apache 2.0, EXTENSION.md, demo GIF):

| Faz | Aksiyon | Düşük kalite | **İyi mimari (hedef)** | Açıklama |
|---|---|---|---|---|
| A | GitHub repo + yıldız | %100 | **%100** | Self-serve, kapı yok |
| B | `awesome-claude-skills` (topluluk) PR | %70 | **%95** | Spec compliant + 5 örnek + test → kabul filtresi düşük |
| C | Plugin marketplace (Anthropic-hosted) | %30 | **%75** | Document-type reference impl Anthropic favori; Türkçe niş bonus |
| D | Twitter/X + Anthropic team etiket | bonus | **bonus+** | "First Turkish skill" + "low-resource lang reference" tweet'lenebilir |
| E | Anthropic blog featured | %5 | **%20** | Capstone öğrenci + multi-platform + reference pattern → blog narrative güçlü |
| F | Resmi `anthropics/skills` PR merge | %5 | **%30** | Apache 2.0 + spec + reference → red bar düşer; ana risk: Türkçe ICP-dışı |

**Realistik beklenti (iyi mimari ile):**
- **A-D %95+ başarı** — bunu garantiye al, mülakat/portfolyo için yeterli
- **E-F %20-30** — hedefle ama bağımlılık olarak alma
- **Asıl ödül:** capstone savunma + iş başvurusu (Anthropic ekosistem sinyali)

**Submission sırası:** Önce A (2+ hafta soak), sonra B → C, paralel D. F için fork'ta tek skill draft PR ile maintainer reaction'ı oku, olumluysa tüm 5 skill ekle.

**Ek outreach kanalları (v2.3):**
- **TR-MTEB yazarlarına PR:** Baysan & Güngör'ün `selmanbaysan/mteb_tr` repo'suna **akademik-domain task subset** PR'ı — kabul edilirse TR-MTEB v2'ye katkı, capstone'da güçlü "peer-reviewed venue contribution" hikayesi.
- **umutertugrul'a notify:** Derive dataset'ini yayınlarken upstream'i bilgilendir, dataset card'da çift yönlü link.

## 15. Karar Verilen Şeyler (devre dışı bırakılan alternatifler)

| Karar | Devredışı bırakılan | Sebep |
|---|---|---|
| **Kalite-first pivot (v2.1)** | KVKK-first | Asıl USP Türkçe-özel modellerin dil kalitesi; KVKK ikincil/opsiyonel özellik |
| Akademik domain | Hukuk, sağlık, finans | Hukuk kapalı kaynak rakipler dolu, sağlık veri zor, akademik niş daha boş |
| **AI Detector EVET, Humanizer HAYIR** | "Turnitin pass humanizer" | **Etik ihlali (akademik dolandırıcılık) + Anthropic policy + capstone savunulamaz; Detector tam tersine etik defansif ürün** |
| Phi-3-mini-3.8B baz model | Llama-7B, Trendyol-LLM-7b | RTX 3050 4GB sığar |
| QLoRA fine-tune | Full fine-tune, RLHF | Donanım sınırı + capstone scope |
| 5 ayrı Claude Skill | Tek mega skill | Anthropic "tek odaklı" prensibi |
| **Apache 2.0 license (v2.2)** | MIT, GPL | Anthropic ekosistem standardı (mevcut anthropics/skills repo Apache 2.0); MIT eşit permissive ama uyum sinyali zayıf |
| İngilizce doküman, Türkçe I/O | Türkçe-only doküman | Uluslararası audience + Anthropic uyumu |
| Reasoner Faz 7 (opsiyonel son) | Reasoner Faz 3 (erken) | En riskli/uzun; portfolyo bütünlüğü için son |
| EARS-formatlı requirements.md | Free-form spec | Acceptance criteria test edilebilir |
| **ChromaDB default + FAISS opt** | FAISS-only | Kullanıcı incremental PDF eklemesi + metadata filter native |
| **Web search default AÇIK** | Default kapalı (KVKK-first) | Genel kullanıcı için zenginleşmiş cevap; KVKK isteyen `web=False` ile kapatabilir |
| **Claude Haiku 3.5 + 100h human review (v2.4)** | Ollama qwen2.5:7b (lokal) | (a) Türkçe akademikte Claude > Ollama kalitesi, (b) 30K paragraph Ollama'da seri 28+ gün vs Claude 1-2 saat, (c) maliyet $10-20 makul, (d) human review olmazsa paper-quality reviewer reddeder, (e) UniversalNER (NeurIPS 2023) pattern aynı yaklaşımı kanıtladı |
| **Tüm LLM-as-labeler işleri Anthropic API (v2.4)** | Ollama lokal LLM | Lokal LLM yalnızca **kullanıcı runtime'ı** için (web=False mode); **bizim training pipeline'ımız** public veriyi işliyor, kullanıcı verisi değil — KVKK iddiası ayakta |

## 15.5. KVKK & Veri Gizliliği (Detay — Requirement 14, opsiyonel mod)

- **Lokal-only mod (`web=False`)** (R14.1): Kullanıcı metni hiçbir external API'ye gitmez.
- **Scraping kapsamı** (R14.2): Yalnızca public metadata + abstract; kişisel iletişim hariç.
- **Cache opt-in** (R14.3): SDK belge içeriğini sadece `cache=True` ile diske yazar.
- **Embedding storage** (R14.5): Kullanıcı RAG cache açtıysa, embedding'ler lokal klasörde.
- **`PRIVACY.md` zorunlu içerikleri** (R14.4): Hangi veri toplanır, hangi veri lokal işlenir, cache nasıl silinir.
- **Web search disclaimer:** SDK `web=True` init'te log'a uyarı düşürür.
- **Doküman compliance statement** (R14.6): README + PRIVACY'de "lokal mod cloud çağrısı içermez" net cümle.

## 15.7. Kalite Altyapısı (Requirement 15)

- **Test coverage:** ≥%80 SDK genelinde (`pytest-cov`, CI gate).
- **CI gate:** PR'da `ruff` + `mypy` + `pytest`, üçü yeşil → merge.
- **Versioning:** SemVer + `CHANGELOG.md` her release'de güncellenir.
- **Experiment tracking:** MLflow — params + dataset version + eval metrics + hardware.
- **Dokümantasyon:** ARCHITECTURE.md + PERFORMANCE.md + PRIVACY.md + CONTRIBUTING.md + learning-log.md.
- **Type annotations:** Tüm public method ve class (`mypy --strict`).
- **Repo yapısı:** Data scripts, model training, SDK, HF Space, Skills, docs, tests ayrı dizinlerde.

## 16. İlk Somut Adımlar (Yeni Sohbet Başlangıcı)

### Faz 0 (5-7 gün) — Araştırma + Öğrenme Altyapısı
```bash
mkdir tr-academic-nlp && cd tr-academic-nlp
git init
mkdir -p docs
touch docs/learning-log.md
```

`docs/learning-log.md`'ye 9+1 başlık için min 200-kelime özet:
1. Web scraping with rate limiting
2. BERTurk fine-tuning for token classification (NER + classifier — Faz 6.5'te yine kullanılacak)
3. sentence-transformers contrastive training
4. mT5 abstractive summarization fine-tuning
5. QLoRA / PEFT (BitsAndBytes 4-bit)
6. **ChromaDB vs FAISS** (incremental, persistence, metadata filter)
7. Gradio Space (CPU-free tier limitations + quantized model loading)
8. Python packaging (pyproject.toml + PyPI publish)
9. Anthropic Skills spec format (SKILL.md schema, when-to-use convention) + **`anthropics/skills` repo audit** (mevcut document skill'lerin yapısını 1:1 incele) + **agentskills.io** standard spec (✨ v2.2)
10. **AI text detection** (✨ v2.1: GPTZero/DetectGPT yaklaşımları, perplexity-based vs classifier-based, kalibrasyon)
11. **TR-MTEB paper okuma + reproduction** (✨ v2.3: Baysan & Güngör EMNLP 2025 Findings; mteb_tr repo'sunu klonla, kendi BERTurk fine-tune'undan ön baseline al, akademik subset kapsamını netleştir)
12. **umutertugrul dataset audit** (✨ v2.3: 650K abstract'i load et, alan dağılımı + kalite metriği + boş/duplicate oranı çıkar; filtering threshold'larını kararlaştır)

Her başlık altında: **Seçilen yaklaşım** + **Reddedilen alternatif(ler)** + **Gerekçe** + **RTX 3050 4GB için memory budget** (gerekirse).

### Faz 1 — Dataset preparation (v2.3 — scraper yok)
```bash
mkdir -p data/derive data/labeling data/corpora data/scrapers
mkdir -p models sdk space skills tests notebooks
mkdir -p .github/workflows
touch README.md LICENSE PRIVACY.md CONTRIBUTING.md CHANGELOG.md DERIVATION.md pyproject.toml requirements.txt
```

Birincil script: `data/derive/load_umutertugrul.py`
- HF'den `umutertugrul/turkish-academic-theses-dataset` load (datasets lib)
- Filtering: boş abstract drop, <50 kelime drop, exact duplicate drop, kalite skoru
- Output: `tr-thesis-academic-ready` Parquet, ~500K kullanılabilir abstract
- Attribution: DERIVATION.md'de CC-BY-4.0 + upstream link

Opsiyonel script: `data/scrapers/dergipark_fetcher.py` (1s rate, 5 alan, DOI dedup)
- Capstone scope minimum'u için zorunlu değil; thesis+article hibridi isteyenler için

## 17. Donanım & Ortam

| Bileşen | Notlar |
|---|---|
| Geliştirme makinası | Mac M4 (önerilen) veya Windows + WSL2 |
| GPU | RTX 3050 Laptop 4GB — QLoRA için yeterli |
| Python | 3.11+ |
| **Anthropic API key (v2.4)** | **Faz 2 NER labeling (Claude Haiku 3.5), Faz 7 reasoner CoT (Claude Sonnet)** — lokal Ollama yerine resmi araç. ENV: `ANTHROPIC_API_KEY` |
| Bulut LLM (data gen) | Claude API + GPT-4o + Gemini API (AI-vs-human dataset için synthetic — Faz 6.5) |
| HF auth | `hakansabunis` — write token |
| Toplam Claude API maliyet (tüm proje) | **~$75-145** (Faz 2: ~$10-20, Faz 6.5: ~$50-100, Faz 7 opsiyonel: ~$15-25) |

## 18. Risk Notları

| Risk | Etki | Mitigasyon |
|---|---|---|
| YÖK Tez tam metin izinli | Veri kısıtlı | Sadece public abstract + metadata (R14.2) |
| HF Space CPU only (free tier) | LLM yavaş | GGUF Q4 quantize (R12.4) |
| Phi-3 Türkçe baseline zayıf | Reasoner kalite | Ollama qwen2.5:7b'den synthetic CoT augment |
| Anthropic Skills ekosistemi gömülürse | Skills ayağı boşa | HF + GitHub ayakları zaten ayakta |
| ~~Telif - DergiPark/YÖK~~ (v2.3 kaldırıldı) | ~~Yasal~~ | umutertugrul CC-BY-4.0 dataset kullanımı + attribution → telif riski yok; DergiPark opsiyonel ve sadece public metadata |
| **TR-MTEB akademik subset baseline yetersizliği (v2.3)** | **Eval kalitesi düşer** | Akademik subset için yeterli data yoksa biz oluşturup TR-MTEB v2'ye PR atabiliriz; mevcut general subset hala competitive baseline |
| **umutertugrul dataset kalite drift'i (v2.3)** | **Filtering sonrası 500K hedefine ulaşılamayabilir** | Quality filter threshold'u kademeli (strict/medium/loose); minimum 200K ile capstone savunulabilir |
| Faz 0 atlanır → ad-hoc kod | Yeniden yazım | Faz 0 zorunlu (R1.2) |
| RTX 3050 4GB OOM | Train fail | gradient checkpointing + batch=1 + max_len kısıt |
| **AI detector Claude/GPT/Gemini API maliyeti** | **Synthetic data üretimi pahalı** | **Bütçe limit + cache + her LLM'den 5K paragraph (toplam ~$50-100)** |
| **AI detector "model arms race" zayıflığı** | **Yeni LLM çıkınca güncel kalmaz** | **Quarterly retraining; CHANGELOG.md'de model versions** |
| Web search API maliyeti | Brave/Perplexity ücretli | SearXNG self-hosted opsiyonu, default sınırlı sorgu |

## 19. Dosya Yapısı

```
tr-academic-nlp/
├── README.md                    # Reference impl pitch + sword&shield + benchmarks
├── LICENSE                      # Apache 2.0 (v2.2)
├── PRIVACY.md                   # KVKK + opsiyonel lokal mod statement
├── CONTRIBUTING.md
├── CHANGELOG.md                 # SemVer
├── pyproject.toml               # pinned deps
├── requirements.txt
├── .github/
│   └── workflows/
│       ├── ci.yml               # ruff + mypy + pytest gate
│       ├── train.yml
│       └── publish.yml          # PyPI release
├── data/
│   ├── scrapers/
│   │   ├── yok_tez_scraper.py
│   │   └── dergipark_fetcher.py
│   ├── labeling/
│   │   ├── semi_auto_label.py     # NER labeling
│   │   └── ai_human_pair_gen.py   # ✨ AI detector dataset (Claude/GPT/Gemini API)
│   └── corpora/                   # gitignore
├── models/
│   ├── ner/
│   ├── embedder/
│   ├── summarizer/
│   ├── citation/
│   ├── detector/                  # ✨ YENİ: BERTurk classifier
│   └── reasoner/
├── sdk/
│   └── tr_academic_nlp/
│       ├── __init__.py
│       ├── embedder.py
│       ├── ner.py
│       ├── summarizer.py
│       ├── citation.py
│       ├── rag.py                 # ChromaDB default + FAISS opt + web search opt
│       ├── writer.py
│       ├── detector.py            # ✨ AIDetector
│       ├── reasoner.py
│       ├── _hf_download.py
│       └── _web_search.py         # ✨ Brave/SearXNG adapter
├── space/
│   └── app.py                     # Gradio (6 sekme)
├── skills/                        # Claude Skills (×5) — her skill'de SKILL.md + README + LICENSE (Apache 2.0) + EXTENSION.md + demo.gif + scripts/ + examples/ + tests/
│   ├── turkish-academic-search/
│   ├── turkish-citation-parser/
│   ├── turkish-academic-summarizer/
│   ├── turkish-academic-writer/
│   └── turkish-academic-ai-detector/   # ✨ v2.1
├── docs/
│   ├── learning-log.md
│   ├── ARCHITECTURE.md
│   ├── PERFORMANCE.md             # CPU + RTX 3050 4GB benchmark + general LLM kıyas
│   └── EXTENSION.md
├── tests/
│   ├── unit/
│   ├── integration/
│   └── property/
├── notebooks/
└── mlruns/                        # gitignore
```

## 20. Başarı Kriterleri (Capstone Savunmada Savunulabilir) — v2.1 Sayısal

| Metrik | Hedef | Kaynak | Requirement |
|---|---|---|---|
| HF aylık toplam indirme | 5K-20K | downloads counter | — |
| GitHub stars | 100-500 | github | — |
| `pip` haftalık install | 200+ | pypistats | — |
| **Akademik NER macro-F1** | **≥0.85** | held-out test | R5.2 |
| **Atıf parser field accuracy (APA TR)** | **≥%95** | held-out test | R6.2 |
| **Embedder TR-MTEB akademik subset (v2.3)** | **top-3 (Mursit/Baysan'a karşı competitive)** | TR-MTEB EMNLP 2025 pipeline | R7.2 revize |
| **Embedder TR-MTEB genel** | **top-10** | TR-MTEB pipeline | R7.2 revize |
| **Summarizer ROUGE-L** | **≥0.35** | held-out test | R8.2 |
| **AI Detector binary AUC** | **≥0.90** | held-out test | TBD R16 |
| **AI Detector 4-class macro F1** | **≥0.75** (human/Claude/GPT/Gemini) | held-out test | TBD R16 |
| **Reasoner Türkçe Q&A accuracy** | **base Phi-3 mini'den iyi** | 500-soru eval | R10.4 |
| **Genel LLM kıyaslama (✨ v2.1)** | **GPT-4o-mini & Claude Haiku'dan iyi** (NER F1, ROUGE-L, citation accuracy) | comparison table | — |
| **Inter-annotator κ (NER labeling)** | **≥0.80** | 500-örnek validation | R4.4 |
| **SDK test coverage** | **≥%80** | pytest-cov | R11.7, R15.2 |
| HF Space ziyaretçi | 1K-10K/ay | HF analytics | — |
| Claude Skill awesome lists | ≥1 listede | github search | — |
| GH Actions CI | yeşil ✓ | actions | R15.3 |

## 21. Claude Code İş Akışı (Spec-Driven Görev Kartı)

```markdown
## GÖREV: [§10 tablosundan faz adı, ör. "Faz 6.5 — AI Detector"]

## KAYNAK DOKÜMANLAR
- Yol haritası: `turkce-akademi-YOL-HARITASI.md` (bu dosya — §10 ilgili satır)
- Resmi spec: `.kiro/specs/tr-academic-nlp/requirements.md`, **Requirement N**
- Donanım kısıtı: §17 (RTX 3050 4GB / Windows + WSL2 / CPU baseline)
- Önceki faz çıktıları: [yol/dosya yolları]

## HEDEF
[§10 satırının "Çıktı" sütunu]

## ZORUNLU ACCEPTANCE CRITERIA
[§10 "Kabul kriteri özet" sütunu — copy/paste, requirement numaraları dahil]

## ÇIKTI DOSYALARI
[§19 dosya yapısına göre nereye ne yazılacak]

## TESTING
- Unit test: [her major function için]
- Property test: [§11.7'den uygulanabilir]
- Performance test: [§11.5 bütçesi — pytest -m perf]
- MLflow log: [training params + dataset version + eval metrics + hardware]

## TAMAMLANDI SİNYALİ (Definition of Done)
- [ ] Acceptance criteria checklist tikli
- [ ] README.md / model card güncellenmiş
- [ ] CHANGELOG.md'de bir satır
- [ ] CI yeşil (ruff + mypy + pytest)
- [ ] Test coverage ≥%80 (etkilenen modüllerde)
- [ ] (Model fazlarında) HF push'lanmış, model card complete
- [ ] (Skill fazında) SKILL.md + 5 example + 10 test + LICENSE
```

### Faz 0 hızlı başlangıç komutu

> Bu yol haritasını ve `.kiro/specs/tr-academic-nlp/requirements.md`'yi oku.
> Faz 0 (Araştırma + Öğrenme Altyapısı) görev kartını uygula:
> 1. Repo iskeletini kur (§19'daki tüm dizinler)
> 2. `docs/learning-log.md`'yi oluştur ve §16'daki 10 başlık için iskeleti yaz
> 3. `pyproject.toml`'da pinned deps + Python 3.11 minimum + ruff/mypy/pytest dev deps
> 4. `.github/workflows/ci.yml` (ruff + mypy + pytest)
> 5. `LICENSE` (MIT), `PRIVACY.md` (KVKK opsiyonel mod statement template), `CONTRIBUTING.md` taslağı
>
> Bitince §20 başarı kriterlerinden Faz 0'a uygulanan'lar tikli + commit "feat: Faz 0 araştırma altyapısı".

---

## EK A: Mevcut Durum (Hakan'ın Devam Eden İşleri)

Bu projeden **bağımsız** olarak Hakan'ın paralel ilerleyen iki işi var:

1. **FloodGuard capstone** (`Guard/floodguard_env`) — TFT-LSTM sel tahmin modeli,
   v5 cascade enriched, AUC=0.992. Bitirme tezi.
2. **disaster_news pipeline** (`Guard/v3/disaster_news`) — 7 afet tipi haber takip
   + Kandilli deprem entegrasyonu, dashboard. Capstone'a yardımcı.
3. **Yayında olan ilk HF model:** `huggingface.co/hakansabunis/turkish-flood-news-bert`.

`tr-academic-nlp` projesi bunlardan **bağımsız** — Guard klasörüne dokunmadan
ayrı bir repo olarak geliştirilecek. Capstone bittiğinde HF profilinde 1 mevcut
sel BERT + 6 yeni akademik model = toplam 7+ model olur.

## EK B: Reddedilen Özellik — AI Humanizer (Turnitin Bypass)

**Talep:** "Turnitin/AI detector'dan geçecek bir Türkçe humanizer."

**Karar:** **Yapılmayacak.** Üç gerekçe:

1. **Akademik etik:** YÖK + uluslararası akademik etik kuralları "AI yazımı kendi yazımı gibi sunmayı" plagiat sayıyor — yakalanırsa tez/diploma iptali.
2. **Anthropic Usage Policy:** "Academic dishonesty" araçları açıkça yasak; Skills marketplace'e gönderilse reddedilir.
3. **Portfolyo riski:** Capstone savunmada "humanizer yazdım" demek savunulamaz; HF model card yasal açıklaması imkânsız.

**Yerine:** Tam karşıtı — `trakad-detector-v1` + `turkish-academic-ai-detector` skill (Faz 6.5). Defansif/koruyucu, etik, savunulması kolay, mülakatta güçlü.

---

**Yol haritası dosyası:** `Desktop/turkce-akademi-YOL-HARITASI.md`
**Resmi spec:** `.kiro/specs/tr-academic-nlp/requirements.md` (R16 AI Detector + R13.5 Apache 2.0 güncellenecek)
**Sürüm:** v3.0 — 2026-05-01 (BÜYÜK PİVOT: Secure Academic Middleware; 6 model → 3 utility model + middleware; mT5 summarizer + Phi-3 reasoner + AI detector kaldırıldı; %100 yerel Ollama qwen2.5:7b; MVP canlı)
**Sahibi:** Hakan Sabunis (hakansabunis@gmail.com)
**Lisans:** Bu doküman serbest kullanım için (proje kendisi **Apache 2.0** olacak)
