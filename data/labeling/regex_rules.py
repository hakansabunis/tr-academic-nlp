"""Regex-based first-pass entity extraction for academic Turkish text.

Step 1 of the semi-automatic labeling pipeline (Requirement 4.3): apply
regex rules, then route uncertain matches to a local LLM for verification.

Each rule returns a list of ``(start, end, entity_type, confidence)`` spans.
High-confidence regex matches go straight to the labeled output; low-confidence
matches are accumulated for the Ollama verification pass.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from re import Pattern

from .entity_types import ENTITY_TYPES


@dataclass(frozen=True)
class Span:
    start: int
    end: int
    entity: str
    confidence: float
    text: str


# ---------------------------------------------------------------------------
# YIL — 4-digit year, 1900-2030 (academic paper publication range)
# ---------------------------------------------------------------------------
_YEAR_RE: Pattern[str] = re.compile(r"\b(19[0-9]{2}|20[0-2][0-9]|2030)\b")


def find_years(text: str) -> list[Span]:
    return [
        Span(m.start(), m.end(), "YIL", 0.99, m.group())
        for m in _YEAR_RE.finditer(text)
    ]


# ---------------------------------------------------------------------------
# KURUM — Turkish institution names (heuristic suffix-based)
# ---------------------------------------------------------------------------
# Capitalized noun phrase ending with one of these keywords
_INSTITUTION_SUFFIXES = (
    "Üniversitesi",
    "Universitesi",
    "Enstitüsü",
    "Enstitusu",
    "Fakültesi",
    "Fakultesi",
    "Akademisi",
    "Yüksek Okulu",
    "Yuksek Okulu",
)
_INSTITUTION_RE: Pattern[str] = re.compile(
    r"(?:[A-ZÇĞİÖŞÜ][a-zçğıöşüA-ZÇĞİÖŞÜ\.\-]*\s+){0,4}"
    r"(?:" + "|".join(re.escape(s) for s in _INSTITUTION_SUFFIXES) + r")"
)


def find_institutions(text: str) -> list[Span]:
    spans: list[Span] = []
    for match in _INSTITUTION_RE.finditer(text):
        # Trim leading lowercase noise (e.g., 'de Boğaziçi Üniversitesi')
        captured = match.group().strip()
        if not captured or not captured[0].isupper():
            continue
        spans.append(
            Span(match.start(), match.end(), "KURUM", 0.85, captured)
        )
    return spans


# ---------------------------------------------------------------------------
# METODOLOJI — known ML/NLP methodology terms
# ---------------------------------------------------------------------------
# Curated whitelist; the LLM verify pass extends coverage.
_METHODOLOGY_TERMS = (
    "CNN", "RNN", "LSTM", "GRU", "BERT", "BERTurk", "GPT", "Transformer",
    "Random Forest", "XGBoost", "SVM", "Logistic Regression", "k-NN",
    "Decision Tree", "Naive Bayes", "Gradient Boosting",
    "K-Means", "DBSCAN", "PCA", "t-SNE", "UMAP",
    "Word2Vec", "GloVe", "FastText", "ELMo", "RoBERTa", "DistilBERT",
    "ResNet", "VGG", "AlexNet", "Inception", "U-Net", "YOLO",
    "Reinforcement Learning", "Q-Learning", "Policy Gradient",
    "Attention Mechanism", "Self-Attention", "Multi-Head Attention",
    "Encoder-Decoder", "Seq2Seq", "GAN", "VAE", "Autoencoder",
    "Derin Öğrenme", "Makine Öğrenmesi", "Doğal Dil İşleme",
)
_METHODOLOGY_RE: Pattern[str] = re.compile(
    r"\b("
    + "|".join(re.escape(t) for t in sorted(_METHODOLOGY_TERMS, key=len, reverse=True))
    + r")\b",
    re.IGNORECASE,
)


def find_methodologies(text: str) -> list[Span]:
    spans: list[Span] = []
    for match in _METHODOLOGY_RE.finditer(text):
        spans.append(
            Span(match.start(), match.end(), "METODOLOJI", 0.95, match.group())
        )
    return spans


# ---------------------------------------------------------------------------
# DATASET — known dataset names + 'veri seti' / 'dataset' suffix patterns
# ---------------------------------------------------------------------------
_DATASET_NAMES = (
    "MNIST", "CIFAR-10", "CIFAR-100", "ImageNet", "COCO", "Pascal VOC",
    "IMDB", "SST", "GLUE", "SuperGLUE", "SQuAD", "MS MARCO",
    "WikiText", "Common Crawl", "OSCAR",
    "TR-MTEB", "Mukayese", "BOUN-PARS", "TS Corpus",
    "YÖK Tez", "DergiPark",
)
_DATASET_NAMED_RE: Pattern[str] = re.compile(
    r"\b("
    + "|".join(re.escape(n) for n in sorted(_DATASET_NAMES, key=len, reverse=True))
    + r")\b"
)
# "Foo veri seti" / "Foo dataset" pattern
_DATASET_SUFFIX_RE: Pattern[str] = re.compile(
    r"\b([A-ZÇĞİÖŞÜ][\w\-]*(?:\s+[A-ZÇĞİÖŞÜ][\w\-]*){0,3})"
    r"\s+(?:veri seti|dataseti|dataset)\b",
    re.IGNORECASE,
)


def find_datasets(text: str) -> list[Span]:
    spans: list[Span] = []
    for match in _DATASET_NAMED_RE.finditer(text):
        spans.append(
            Span(match.start(), match.end(), "DATASET", 0.95, match.group())
        )
    for match in _DATASET_SUFFIX_RE.finditer(text):
        # Capture group 1 = the named dataset prefix only
        spans.append(
            Span(match.start(1), match.end(1), "DATASET", 0.75, match.group(1))
        )
    return spans


# ---------------------------------------------------------------------------
# METRİK — academic evaluation metrics
# ---------------------------------------------------------------------------
_METRIC_TERMS = (
    "F1", "F1-score", "F1 skoru", "F-skoru",
    "Accuracy", "Doğruluk", "Hassasiyet", "Precision",
    "Recall", "Geri Çağırma", "Duyarlılık",
    "AUC", "ROC", "AP", "mAP",
    "ROUGE", "ROUGE-1", "ROUGE-2", "ROUGE-L",
    "BLEU", "METEOR", "CIDEr", "WER",
    "Spearman", "Pearson", "Cohen Kappa", "Kappa",
    "MSE", "RMSE", "MAE", "R-squared", "R²",
    "Perplexity",
)
# Sort longest-first so multi-token / hyphenated forms (ROUGE-L) win over
# their prefixes (ROUGE) in alternation.
_METRIC_RE: Pattern[str] = re.compile(
    r"\b(" + "|".join(re.escape(t) for t in sorted(_METRIC_TERMS, key=len, reverse=True)) + r")\b"
)


def find_metrics(text: str) -> list[Span]:
    spans: list[Span] = []
    for match in _METRIC_RE.finditer(text):
        spans.append(
            Span(match.start(), match.end(), "METRİK", 0.95, match.group())
        )
    return spans


# ---------------------------------------------------------------------------
# YAZAR — author name pattern (Turkish reversed: "Soyadı, Adı")
# ---------------------------------------------------------------------------
# E.g., "Yılmaz, A.M." or "Sabunis, Hakan" or "Y. Demir"
# Two passes: explicit reversed format + initial-Lastname format
_AUTHOR_REVERSED_RE: Pattern[str] = re.compile(
    r"\b([A-ZÇĞİÖŞÜ][a-zçğıöşü]+),\s+"
    r"([A-ZÇĞİÖŞÜ][a-zçğıöşü]*\.?(?:\s*[A-ZÇĞİÖŞÜ]\.?)*)"
)
_AUTHOR_INITIAL_RE: Pattern[str] = re.compile(
    r"\b([A-ZÇĞİÖŞÜ]\.\s*(?:[A-ZÇĞİÖŞÜ]\.\s*)*"
    r"[A-ZÇĞİÖŞÜ][a-zçğıöşü]+)\b"
)


def find_authors(text: str) -> list[Span]:
    spans: list[Span] = []
    for match in _AUTHOR_REVERSED_RE.finditer(text):
        spans.append(
            Span(match.start(), match.end(), "YAZAR", 0.85, match.group())
        )
    for match in _AUTHOR_INITIAL_RE.finditer(text):
        spans.append(
            Span(match.start(), match.end(), "YAZAR", 0.70, match.group())
        )
    return spans


# ---------------------------------------------------------------------------
# DERGİ — journals are hard to detect via regex alone (LLM verify-heavy).
# We catch a few canonical patterns; rest is LLM's job.
# ---------------------------------------------------------------------------
_JOURNAL_HINTS_RE: Pattern[str] = re.compile(
    r"\b("
    r"Nature|Science|Cell|Lancet|JAMA|"
    r"IEEE\s+Transactions[\w\s]*|"
    r"ACM\s+Transactions[\w\s]*|"
    r"(?:Journal\s+of\s+|Dergisi\s+)[\w\s]+"
    r")\b"
)


def find_journals(text: str) -> list[Span]:
    return [
        Span(m.start(), m.end(), "DERGİ", 0.70, m.group())
        for m in _JOURNAL_HINTS_RE.finditer(text)
    ]


# ---------------------------------------------------------------------------
# Unified extraction
# ---------------------------------------------------------------------------
def extract_all(text: str) -> list[Span]:
    """Run every regex extractor and return spans sorted by ``start``."""
    spans: list[Span] = []
    spans.extend(find_years(text))
    spans.extend(find_institutions(text))
    spans.extend(find_methodologies(text))
    spans.extend(find_datasets(text))
    spans.extend(find_metrics(text))
    spans.extend(find_authors(text))
    spans.extend(find_journals(text))
    return sorted(spans, key=lambda s: (s.start, s.end))


def resolve_overlaps(spans: list[Span]) -> list[Span]:
    """When two spans overlap, keep the one with higher confidence.

    Required because a token like 'BERT' could match both METODOLOJI and
    (rarely) DATASET patterns. Greedy left-to-right resolution preserves
    determinism.
    """
    spans = sorted(spans, key=lambda s: (s.start, -s.confidence, s.end))
    kept: list[Span] = []
    for span in spans:
        # Skip if it overlaps a previously-kept higher-confidence span
        overlaps_higher = any(
            not (span.end <= k.start or span.start >= k.end)
            and k.confidence >= span.confidence
            for k in kept
        )
        if not overlaps_higher:
            kept.append(span)
    return kept


__all__ = [
    "ENTITY_TYPES",
    "Span",
    "extract_all",
    "find_authors",
    "find_datasets",
    "find_institutions",
    "find_journals",
    "find_methodologies",
    "find_metrics",
    "find_years",
    "resolve_overlaps",
]
