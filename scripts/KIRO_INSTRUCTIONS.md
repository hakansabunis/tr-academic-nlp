# Instructions for Kiro - Batch Labeling with Claude Haiku

You have Claude Haiku access. This script will help you process the Turkish academic NER labeling task while respecting Claude Pro tier rate limits.

## Quick Start

### Option 1: Batch Script (Simpler)
```bash
cd C:\Users\SABUNIS\OneDrive\Desktop\tr-academic-nlp

# Run batch 1 (first 45 paragraphs)
scripts\run_labeling_for_kiro.bat 1

# After ~5 hours, run batch 2 (next 45 paragraphs)
scripts\run_labeling_for_kiro.bat 2
```

### Option 2: Python Script (More Control)
```bash
cd C:\Users\SABUNIS\OneDrive\Desktop\tr-academic-nlp

# Run batch 1
python scripts/run_labeling_for_kiro.py 1

# After ~5 hours, run batch 2
python scripts/run_labeling_for_kiro.py 2
```

## How It Works

- **Batch size**: 15 paragraphs per Claude call
- **Pause**: 300 seconds (5 minutes) between batches
- **Rate limit**: Stays within Claude Pro tier (~45 messages/5 hours)
- **Resume-safe**: Script skips already-labeled paragraphs, so you can interrupt and resume anytime

## What to Expect

Each batch (45 paragraphs) takes approximately **45-60 minutes** to complete:
- 3 subprocess calls × 15 paragraphs each
- ~2.8 seconds per paragraph (from previous runs)
- 5-minute pauses between calls
- Real time: ~12-15 minutes actual processing + 10 minutes pause = ~25 minutes total

## Rate Limits Explained

**Claude Pro Tier**: ~45 messages per 5-hour window

With our settings:
- 3 batches per window (3 × 15 = 45 messages)
- Each batch = 45 paragraphs labeled
- Total throughput: **45 paragraphs per 5 hours**

To label all 993 paragraphs:
- ~22 batches needed
- ~110 hours wall-clock time (spread over multiple days)

## Troubleshooting

### If you hit rate limits again
- You're on Pro tier already
- Wait the full 5 hours before running the next batch
- Cannot process faster without upgrading to Max tier

### If script fails
- Check your Claude CLI is installed: `where claude`
- Verify path exists: `C:\Users\SABUNIS\OneDrive\Desktop\tr-academic-nlp`
- Review error messages in console output

### To check progress
```bash
# See how many have been labeled so far
python -c "
import json
with open('docs/labeler-eval/cli-haiku-B.jsonl', 'r', encoding='utf-8') as f:
    count = sum(1 for line in f if json.loads(line).get('succeeded'))
    print(f'Labeled so far: {count} paragraphs')
"
```

## When You're Done

Once all batches complete, the output will be in:
```
docs/labeler-eval/cli-haiku-B.jsonl
```

Each line is a JSON record with labeled entities.

---

**Questions?** Check `scripts/batch_label_via_claude_cli.py` for advanced options like custom timeouts, different models, etc.
