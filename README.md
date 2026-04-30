# tr-academic-nlp

> **Turkish Academic NLP Toolkit** — fine-tuned models, RAG, AI detection, and Anthropic Claude Skills for Turkish academic content.
>
> A **reference implementation for low-resource academic NLP skills**. Patterns
> (BERTurk fine-tune + ChromaDB local RAG + Apache 2.0 + Turkish I/O with English
> docs) are portable to any low-resource language.

[![CI](https://github.com/hakansabunis/tr-academic-nlp/actions/workflows/ci.yml/badge.svg)](https://github.com/hakansabunis/tr-academic-nlp/actions)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## Why this toolkit?

General-purpose LLMs (ChatGPT, Claude, Gemini) underperform on Turkish academic
text — they break terminology, mishandle citation conventions, and fail to match
academic register. This toolkit closes that quality gap with **6 Turkish-specific
fine-tuned models** plus a **reference Anthropic Skills package**.

### Sword & Shield

- **Sword** (better reading/writing): NER, citation parser, embedder,
  summarizer, reasoner — write and analyze Turkish academic text with
  domain-specialized models.
- **Shield** (defensive): AI-text detector for Turkish academic content —
  what Turnitin can't see in Turkish, this catches.

KVKK-compliant local mode optional (no third-party data sharing).

## Components

```
🤗 HuggingFace Hub          📦 PyPI + GitHub          🎯 Anthropic Skills
6 models + 5 datasets       pip install               5 sub-skills
+ 1 Gradio Space            + Apache 2.0 source       + Apache 2.0 reference
```

| Model | Purpose |
|---|---|
| [`trakad-embed-v1`](https://huggingface.co/hakansabunis/trakad-embed-v1) | 768-dim Turkish academic sentence embedding |
| [`trakad-ner-v1`](https://huggingface.co/hakansabunis/trakad-ner-v1) | 7-entity academic NER (BERTurk fine-tune) |
| [`trakad-citation-v1`](https://huggingface.co/hakansabunis/trakad-citation-v1) | APA / MLA / Chicago Turkish citation parser |
| [`trakad-summarizer-v1`](https://huggingface.co/hakansabunis/trakad-summarizer-v1) | Turkish academic summarizer (mT5) |
| [`trakad-detector-v1`](https://huggingface.co/hakansabunis/trakad-detector-v1) | Turkish academic AI-text detector |
| [`trakad-reasoner-3b`](https://huggingface.co/hakansabunis/trakad-reasoner-3b) | Phi-3-mini QLoRA Turkish academic Q&A (optional) |

## Quick start

```bash
pip install tr-academic-nlp
```

```python
from tr_academic_nlp import AcademicRAG, AIDetector

# Local Turkish academic RAG (web=False for KVKK compliance)
rag = AcademicRAG(corpus="yok-tez", web=False)
results = rag.search("derin öğrenme sel tahmini")

# AI text detection on Turkish academic text
det = AIDetector()
verdict = det.classify("Bu çalışmada derin öğrenme yöntemleri ile...")
# {"label": "AI", "confidence": 0.92, "likely_source": "Claude"}
```

## Benchmarks

See [`BENCHMARKS.md`](BENCHMARKS.md) — evaluated on TR-MTEB (Baysan & Güngör,
Findings of EMNLP 2025) and the project-internal Claude-alone vs Claude+Toolkit
comparison.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Performance benchmarks](docs/PERFORMANCE.md)
- [Privacy & KVKK](PRIVACY.md)
- [Dataset derivation](DERIVATION.md)
- [Extension to other low-resource languages](docs/EXTENSION.md)
- [Contributing](CONTRIBUTING.md)

## License

[Apache License 2.0](LICENSE) — chosen to align with the Anthropic
[`anthropics/skills`](https://github.com/anthropics/skills) ecosystem.

## Citation

If you use this toolkit, please cite both the upstream resources and this work:

- [`umutertugrul/turkish-academic-theses-dataset`](https://huggingface.co/datasets/umutertugrul/turkish-academic-theses-dataset) (CC-BY-4.0)
- TR-MTEB: Baysan & Güngör (Findings of EMNLP 2025)

## Author

Hakan Sabunis · [HuggingFace](https://huggingface.co/hakansabunis) · hakansabunis@gmail.com
