# Benchmarks & Evaluation

This document tracks every external benchmark used to evaluate models in this
toolkit. Required by [Requirement 17](../tools/.kiro/specs/tr-academic-nlp/requirements.md#requirement-17-upstream-dataset-attribution--derivation-compliance-new-v23).

---

## 1. TR-MTEB — Turkish Massive Text Embedding Benchmark

| Field | Value |
|---|---|
| **Benchmark identifier** | TR-MTEB |
| **Original publication** | Baysan, M. S., & Güngör, T. (2025). TR-MTEB: A Comprehensive Benchmark and Embedding Model Suite for Turkish Sentence Representations. In Findings of the Association for Computational Linguistics: EMNLP 2025. |
| **Paper URL** | https://aclanthology.org/2025.findings-emnlp.471/ |
| **Official pipeline** | https://github.com/selmanbaysan/mteb_tr |
| **HuggingFace org** | https://huggingface.co/trmteb |
| **Task categories** | classification, clustering, pair classification, retrieval, bitext mining, semantic textual similarity (6 total) |
| **Datasets** | 26 |
| **Used by** | `trakad-embed-v1` evaluation (Faz 5) |

### Citation

```bibtex
@inproceedings{baysan-gungor-2025-tr-mteb,
    title = {TR-MTEB: A Comprehensive Benchmark and Embedding Model Suite for Turkish Sentence Representations},
    author = {Baysan, Mehmet Selman and G{\"u}ng{\"o}r, Tunga},
    booktitle = {Findings of the Association for Computational Linguistics: EMNLP 2025},
    year = {2025},
    url = {https://aclanthology.org/2025.findings-emnlp.471/}
}
```

### Evaluation targets for `trakad-embed-v1`

- Academic-domain task subset: **top-3** (competitive with `mursit` and Baysan & Güngör reference models)
- Overall TR-MTEB leaderboard: **top-10**

Results will be populated in this file once Faz 5 evaluation is complete.

### Reproducing the evaluation

```bash
git clone https://github.com/selmanbaysan/mteb_tr.git
cd mteb_tr
# Run TR-MTEB pipeline against hakansabunis/trakad-embed-v1
python evaluate.py --model hakansabunis/trakad-embed-v1
```

### Potential upstream contribution

The toolkit may contribute an **academic-domain task subset** back to TR-MTEB
v2 as a community PR to the upstream `selmanbaysan/mteb_tr` repository
(Requirement 17.7).

---

## 2. Internal — Claude alone vs Claude + Toolkit (R16)

A project-internal benchmark suite (defined in Requirement 16) measures the
toolkit's value-add over Claude API alone on 4 task categories:

| Task | Metric |
|---|---|
| Literature retrieval | Precision@5, Recall@10, hallucination rate |
| Citation parsing | Field-level accuracy |
| Summarization | ROUGE-L, factual consistency |
| Entity extraction | Macro-averaged F1 |

- 100 test questions per category (sourced from YÖK / DergiPark records not used in training)
- Two conditions: **Baseline** (Claude API only) vs **Augmented** (Claude API + toolkit)
- Reproducible via `benchmarks/run_benchmark.py`
- Public test set published as `hakansabunis/tr-academic-benchmark` on HuggingFace

Results will be populated in `docs/BENCHMARK.md` (a separate report file)
during Faz 10 (final evaluation).

---

## 3. Per-model intrinsic metrics

| Model | Metric | Target |
|---|---|---|
| `trakad-ner-v1` | macro-F1 | ≥0.85 |
| `trakad-citation-v1` | field-level accuracy (APA TR) | ≥95% |
| `trakad-embed-v1` | TR-MTEB academic subset | top-3 |
| `trakad-summarizer-v1` | ROUGE-L | ≥0.35 |
| `trakad-detector-v1` | binary AUC | ≥0.90 |
| `trakad-detector-v1` | 4-class macro-F1 | ≥0.75 |
| `trakad-reasoner-3b` (optional) | Turkish academic Q&A accuracy | better than Phi-3-mini base |

---

## Update policy

This file is updated every time:
- A new external benchmark is added to evaluation.
- An evaluation is re-run on a new model version.
- Upstream benchmark releases a new version (we re-evaluate).

Per Requirement 17.4, all citations follow the canonical form provided by
the upstream authors.
