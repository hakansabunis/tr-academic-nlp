# Extension Guide — Porting to Other Low-Resource Languages

> **Status:** Skeleton — written in full once the Turkish reference
> implementation is complete and patterns are validated.
>
> **Goal:** Make `tr-academic-nlp` a **reference implementation** that
> someone working in another low-resource academic language (Greek, Persian,
> Indonesian, etc.) can port with minimal friction.

## Why this guide exists

The patterns used here generalize:
- Domain-fine-tuned BERT family model + 7-entity academic NER schema
- Sentence-transformers contrastive training on academic abstract pairs
- mT5 fine-tuning for academic summarization
- AI-text detector trained on language-specific human↔LLM paired data
- Local RAG with ChromaDB on pre-computed embeddings
- Anthropic Skills package wrapping each capability

What changes from language to language:
- Base model (BERTurk → AraBERT / mBERT / etc.)
- Source corpus (umutertugrul → equivalent academic theses dataset)
- Tokenization edge cases (Turkish has agglutinative morphology; others differ)
- Citation format conventions (APA TR vs APA EN — author name order, etc.)
- Standard benchmark to align with (TR-MTEB vs MTEB / language-specific equivalent)

## Porting checklist

When porting to language `X`:

1. **Base model selection**
   - Find a publicly available BERT-family model fine-tuned on language X.
   - Document selection rationale in your fork's `learning-log.md`.

2. **Source corpus**
   - Find or build a CC-BY (or similarly permissive) academic corpus.
   - Avoid scraping if a community-published dataset already exists.
   - Document license + attribution in `DERIVATION.md`.

3. **NER schema**
   - The 7-entity schema (YAZAR/KURUM/DERGİ/YIL/METODOLOJI/DATASET/METRİK)
     is language-agnostic in concept.
   - Check whether your language adds entities (e.g., Greek: kingdom, classical-era markers).

4. **Embedding evaluation**
   - Find your language's MTEB-equivalent benchmark (or contribute one).
   - Aim for top-3 in academic subset, top-10 overall — the same pattern as `trakad-embed-v1`.

5. **AI detector training data**
   - Generate human↔LLM paired paragraphs in language X.
   - Use Claude API + GPT-4o + Gemini API for the synthetic AI side.
   - Keep license + cost discipline (~$50-100 per language for ~5K paragraphs/source).

6. **Skills package**
   - 5 sub-skills, single-focus, Apache 2.0, English README + language-X I/O.
   - Reuse the pre-flight checklist (`turkce-akademi-YOL-HARITASI.md` §11.8).

7. **Documentation**
   - English README with the same "low-resource lang reference" pitch.
   - Language-X examples and error messages.

## Reference issues to coordinate ports

If you are porting this toolkit:
- Open a discussion at https://github.com/hakansabunis/tr-academic-nlp/discussions
- Tag with `port:<language>` so contributors can find each other.
- Cross-link your fork in this guide via PR.

## Known unknowns

- **Tokenization for non-Latin scripts:** Subword vocabularies may need
  retraining for Arabic, Devanagari, etc. Not validated yet.
- **Citation parsers:** APA / MLA / Chicago apply broadly, but local
  conventions (e.g., Cyrillic alphabetization) may need additional rules.
- **Web search providers:** Brave / SearXNG may have weaker coverage
  in certain languages — alternatives to be documented per port.

This guide is updated as ports are completed; if you ship a working
port, please contribute back a section under "Reference ports".
