# Standalone Albanian Spelling LoRA (outside the web app)

This folder packages:

1. **LoRA model** for Albanian spelling exercise generation
2. **Controlled error-augmentation dataset**
3. **Python-only usage script** (no FastAPI / no frontend)

It follows the publishing style of the professor's example:
https://huggingface.co/akadriu/albanian-news-llm

## Local folders

| Path | Content |
|------|---------|
| `albanian-spelling-lora/` | LoRA adapter + tokenizer + model card |
| `dataset_albanian_error_augmentation/` | `train.jsonl`, `train.csv`, dataset card |
| `standalone/generate_exercises.py` | Independent inference script |

## Install (Python only)

```bash
pip install torch transformers peft accelerate sentencepiece datasets huggingface_hub
```

## Use the model without the app

```bash
cd backend/huggingface_publish
python standalone/generate_exercises.py \
  --adapter ./albanian-spelling-lora \
  --seed-word mirë \
  --grade 3 \
  --type missing_letter
```

Other exercise types:

```bash
python standalone/generate_exercises.py --adapter ./albanian-spelling-lora --seed-word shkollë --type find_error
python standalone/generate_exercises.py --adapter ./albanian-spelling-lora --seed-word fëmijë --type explain_error
```

## Inspect the augmentation dataset

```bash
python - <<'PY'
import json
from collections import Counter
rows=[json.loads(l) for l in open('dataset_albanian_error_augmentation/train.jsonl',encoding='utf-8')]
print('records', len(rows))
print(Counter(r['error_type'] for r in rows))
print(rows[0])
PY
```

## Upload to Hugging Face

1. Create a free account at https://huggingface.co/join
2. Create a token at https://huggingface.co/settings/tokens (Write access)
3. Run:

```bash
export HF_TOKEN="hf_xxxxxxxx"
export HF_USERNAME="your-username"   # e.g. gretaahma
cd backend
python scripts/publish_to_huggingface.py
```

This creates two public repos:

- `https://huggingface.co/$HF_USERNAME/albanian-spelling-lora`
- `https://huggingface.co/datasets/$HF_USERNAME/albanian-error-augmentation`

## What to send the professor

1. Model link (Hugging Face)
2. Dataset link (Hugging Face)
3. The short usage instructions from `albanian-spelling-lora/README.md`
4. Note that correctness for children remains rule/database-based (safety layer)
