# Performance Benchmarks

> **Status:** Skeleton — populated as models are trained and benchmarked.

All targets are CPU-baseline budgets from yol-haritasi §11.5. GPU numbers
(RTX 3050 Laptop 4GB) are tracked separately for training, not inference.

## CPU inference budgets (mandatory)

| Component | Target | Requirement |
|---|---|---|
| `trakad-ner-v1` | <500 ms / 512-token paragraph | R5.4 |
| `trakad-embed-v1` | <2 s / 32-batch | R7.5 |
| `trakad-summarizer-v1` | <10 s / 2000 words | R8.8 |
| `trakad-detector-v1` | <500 ms / paragraph | R16 (TBD) |
| RAG retrieval | <5 s / 500K-doc index | R9.7 |
| `trakad-reasoner-3b` (GGUF Q4) | <30 s / 512 tokens | R10.7 |
| HF Space PDF upload→summary | <60 s | R12.3 |
| SDK RAG init | <60 s / 10 PDF | R11.8 |

## How budgets are validated

`pytest -m perf` runs performance tests in CI on a standardized runner.
Each model has a corresponding `tests/performance/test_<model>_perf.py`
that fails if the budget is exceeded by more than 20% (CI variance buffer).

## Measured results (TBD)

Tables below are populated as models are released:

### NER (`trakad-ner-v1`)

| Hardware | Latency (p50) | Latency (p95) | Throughput |
|---|---|---|---|
| CPU (CI runner) | TBD | TBD | TBD |
| RTX 3050 Laptop 4GB | TBD | TBD | TBD |

### Embedder (`trakad-embed-v1`)

| Hardware | Latency (32-batch) | Throughput (sentences/sec) |
|---|---|---|
| CPU | TBD | TBD |
| RTX 3050 Laptop 4GB | TBD | TBD |

(Other models: same template.)

## Training compute log

Training jobs log to MLflow (per Requirement 15.7). A summary is added here
after each training run completes:

| Model | Training time | GPU peak VRAM | Dataset version | Final metric |
|---|---|---|---|---|
| TBD | TBD | TBD | TBD | TBD |

## Update policy

- Update budget tables on every release.
- Add a row to "Training compute log" after every training run.
- If a budget cannot be met, document the reason here and propose a remediation
  (quantization, distillation, batch tuning) before relaxing the target.
