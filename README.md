# tr-academic-nlp

> **Turkish Academic NLP Toolkit** — A secure middleware and prompt engine for processing Turkish academic content with frontier LLMs (Claude, GPT).
>
> A **reference implementation for low-resource academic NLP skills**. Provides local KVKK-compliant data anonymization and domain-specialized prompts to bridge the gap between Turkish academic register and general-purpose LLMs.

[![CI](https://github.com/hakansabunis/tr-academic-nlp/actions/workflows/ci.yml/badge.svg)](https://github.com/hakansabunis/tr-academic-nlp/actions)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## Why this toolkit?

General-purpose LLMs (ChatGPT, Claude, Gemini) are incredibly powerful, but they often struggle with Turkish academic terminology, mishandle citation conventions, and fail to match the passive academic register. 

Instead of training small custom models that quickly become obsolete, `tr-academic-nlp` acts as a **Secure Academic Middleware**. It wraps frontier models with robust Turkish academic prompt engineering and a local anonymization layer, giving you GPT-4/Claude 3.5 quality **without compromising KVKK (data privacy) or academic integrity.**

## Core Components

```
1. Local RAG -> 2. Anonymizer -> 3. Prompt Engine -> 4. Frontier API
```

| Component | Purpose |
|---|---|
| **Local RAG (ChromaDB)** | Retrieves relevant context from local academic papers using `trakad-embed-v1` without uploading your entire library to the cloud. |
| **Local Anonymizer** | Repurposes `trakad-ner-v1` to mask sensitive entities (e.g., `Dr. Ahmet` -> `[KİŞİ_1]`) before sending data to external APIs (KVKK Shield). |
| **Academic Prompt Engine** | A library of meticulously crafted system prompts that force LLMs to output perfect Turkish academic register, passive voice, and correct citations. |
| **De-anonymizer** | Restores the original sensitive entities into the LLM's response locally before presenting it to the user. |

*(Note: The previously planned `trakad-detector-v1` AI text detector is deprecated due to high false-positive rates inherent to AI detection in academic texts.)*

## Quick start

```bash
pip install tr-academic-nlp
```

```python
from tr_academic_nlp import AcademicPipeline

# Initialize the secure middleware
pipeline = AcademicPipeline(llm_provider="claude-3-5-sonnet")

# Analyze text securely (Entities are masked locally -> Claude -> Unmasked locally)
text = "Prof. Dr. Ayşe Yılmaz'ın Hacettepe Üniversitesi'nde yaptığı araştırma..."
result = pipeline.analyze_and_rewrite(text, task="summarize")

print(result)
```

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

## Author

Hakan Sabunis · [HuggingFace](https://huggingface.co/hakansabunis) · hakansabunis@gmail.com
