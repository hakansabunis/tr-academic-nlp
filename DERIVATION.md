# Dataset Derivation & Attribution

This document tracks every upstream dataset reused by `tr-academic-nlp`,
including source, license, transformation summary, and downstream artifact.
Required by [Requirement 17](../tools/.kiro/specs/tr-academic-nlp/requirements.md#requirement-17-upstream-dataset-attribution--derivation-compliance-new-v23)
of the project specification.

---

## 1. Turkish Academic Theses Corpus

| Field | Value |
|---|---|
| **Upstream identifier** | `umutertugrul/turkish-academic-theses-dataset` |
| **Upstream URL** | https://huggingface.co/datasets/umutertugrul/turkish-academic-theses-dataset |
| **Upstream license** | CC-BY-4.0 |
| **Upstream maintainer** | umutertugrul |
| **Date of access** | 2026-04-30 |
| **Total upstream records** | ~650,000 thesis abstracts (TR + EN parallel where available) |
| **Source of upstream data** | YÖK Ulusal Tez Merkezi (public records) |
| **Format** | Parquet (~1.56 GB) |
| **Downstream artifact** | `hakansabunis/tr-thesis-academic-ready` (planned) |

### Transformation summary

The derivation pipeline (`data/derive/load_umutertugrul.py` — to be implemented
in Faz 1) applies the following filters:

1. Drop records with empty `abstract_tr`.
2. Drop records with `abstract_tr` shorter than 50 words.
3. Drop exact duplicates by `tez_no`.
4. Normalize Turkish characters via Unicode NFC.
5. Compute a `quality_score` field (length, language consistency, abstract density).

**Target output:** ~500,000 quality-filtered abstracts (minimum 200,000 for
capstone scope).

**Preserved fields:** `tez_no`, `pdf_url`, `title_tr`, `title_en`, `author`,
`advisor`, `location`, `subject`, `index`, `degree`, `year`, `pages`,
`abstract_tr`, `abstract_en`.

**Added fields:** `quality_score`, `derived_at` (ISO-8601 timestamp).

### Reproducing locally

```bash
python data/derive/load_umutertugrul.py \
    --upstream umutertugrul/turkish-academic-theses-dataset \
    --output-dir data/corpora/tr-thesis-academic-ready \
    --min-abstract-words 50
```

The pipeline is deterministic: same upstream snapshot + same filter version
produce identical output (Requirement 2.9).

### License compliance

Per CC-BY-4.0, the derived dataset:
- Attributes the upstream maintainer in the dataset card.
- Links to the upstream dataset.
- States the license terms.
- Does NOT impose additional restrictions.

The derived dataset will be published under **CC-BY-4.0** (matching the
upstream license to honor the attribution chain).

### Upstream notification

The upstream maintainer (umutertugrul) will be notified of the derivative
work via HuggingFace discussion or community tab once the derived dataset
is published, in line with Requirement 17.7.

---

## 2. (placeholder) DergiPark Articles — optional

If the optional DergiPark fetcher is implemented (Requirement 3, marked
optional in v2.3), this section will document the source URL pattern,
rate-limit policy, public-metadata-only scope, and DOI deduplication.

---

## Future derivations

This file will be updated as new datasets are derived (e.g.,
`tr-academic-ner-corpus` from labeling `tr-thesis-academic-ready` paragraphs,
`tr-citation-pairs-tr` synthesis pipeline, `tr-ai-vs-human-academic` LLM
generation pipeline).

Each derivation entry must include: upstream source(s), license, transformation
description, downstream artifact name, and reproducibility instructions.
