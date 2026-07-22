---
license: apache-2.0
base_model: Qwen/Qwen2.5-0.5B-Instruct
library_name: peft
tags:
  - albanian
  - lora
  - peft
  - education
  - spelling
  - exercise-generation
  - text-generation
language:
  - sq
pipeline_tag: text-generation
---

# Albanian Spelling Exercise LoRA

LoRA adapter fine-tuned on top of [`Qwen/Qwen2.5-0.5B-Instruct`](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct) for **automatic Albanian spelling exercise generation** (fill-in-the-blank, find-the-error, explain-the-error).

This model is intended as a **standalone Python component** outside the AlbLingo web app, following the same publishing style as [`akadriu/albanian-news-llm`](https://huggingface.co/akadriu/albanian-news-llm).

## Intended use

| Task | Example |
|------|---------|
| Generate missing-letter exercises | seed word `mirë` → `Plotëso: m_rë` |
| Generate find-error exercises | seed word `shkollë` → incorrect form + correction |
| Propose child-friendly practice prompts | grade-aware short Albanian prompts |

### Safety policy (important)

- This LoRA **proposes** exercise text.
- For educational use with children, **final correctness must come from rules/database**, not from the LLM alone.
- Prefer teacher review before classroom deployment.

## How to use (standalone Python)

```bash
pip install torch transformers peft accelerate sentencepiece
```

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

BASE = "Qwen/Qwen2.5-0.5B-Instruct"
ADAPTER = "YOUR_HF_USERNAME/albanian-spelling-lora"  # or local folder path

tokenizer = AutoTokenizer.from_pretrained(ADAPTER, use_fast=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

base = AutoModelForCausalLM.from_pretrained(BASE)
model = PeftModel.from_pretrained(base, ADAPTER)
model.eval()

prompt = (
    "### Instruksion:\n"
    "Gjenero një ushtrim të sigurt për drejtshkrimin shqip. "
    "Kategoria: missing_letter. Klasa: 3. Vështirësia: easy. Fjala bazë: mirë.\n\n"
    "### Input:\n"
    "{\"seed_word\": \"mirë\", \"grade\": 3, \"difficulty\": \"easy\", "
    "\"exercise_type\": \"missing_letter\"}\n\n"
    "### Përgjigje:\n"
)

inputs = tokenizer(prompt, return_tensors="pt")
outputs = model.generate(
    **inputs,
    max_new_tokens=120,
    temperature=0.4,
    top_p=0.9,
    do_sample=True,
)
print(tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True))
```

Or use the helper script in this repository:

```bash
python generate_exercises.py --adapter . --seed-word mirë --grade 3 --type missing_letter
```

### Recommended sampling

- `temperature=0.3–0.5`
- `top_p=0.9`
- `max_new_tokens=80–160`

## Training details

| Field | Value |
|-------|-------|
| Base model | `Qwen/Qwen2.5-0.5B-Instruct` |
| Method | LoRA (PEFT) |
| LoRA rank / alpha | 16 / 32 |
| Target modules | `q_proj`, `k_proj`, `v_proj`, `o_proj` |
| Train examples | 763 instruction–output pairs from AlbLingo exercises |
| Related dataset | Controlled Albanian error-augmentation pairs (separate HF dataset) |

## Limitations

- Small educational adapter (smoke/research prototype scale).
- Can hallucinate answers; keep a rule/database authority layer.
- Best for short Albanian spelling prompts, not open-domain chat.

## Citation

```bibtex
@misc{albanian_spelling_lora_2026,
  title        = {Albanian Spelling Exercise LoRA},
  author       = {Ahma, Greta},
  year         = {2026},
  publisher    = {Hugging Face},
  note         = {PhD educational NLP prototype for Albanian spelling}
}
```

## License

Apache 2.0 (compatible with the base model terms). Users must also comply with the `Qwen2.5-0.5B-Instruct` license.
