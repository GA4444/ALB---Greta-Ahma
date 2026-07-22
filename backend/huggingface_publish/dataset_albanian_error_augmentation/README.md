---
license: apache-2.0
language:
  - sq
task_categories:
  - text-generation
  - text2text-generation
pretty_name: Albanian Controlled Error Augmentation
tags:
  - albanian
  - spelling
  - data-augmentation
  - gec
  - education
  - orthography
size_categories:
  - 1K<n<10K
---

# Albanian Controlled Error Augmentation Dataset

Dataset of **controlled Albanian orthographic errors** created for PhD research on Albanian spelling education and automatic exercise generation.

Each row is an `(incorrect → correct)` pair with an explicit `error_type` label.

## Error types

| error_type | Description |
|------------|-------------|
| `missing_diacritic` | Missing `ë` / `ç` |
| `c_q_confusion` | Confusion between `ç` / `q` / `c` |
| `digraph_reduction` | Digraph loss (`sh`, `dh`, `th`, `gj`, `nj`, `ll`, `rr`, `xh`, `zh`) |
| `case_ending_error` | Wrong Albanian case ending / morphological suffix |
| `letter_transposition` | Swapped adjacent letters |
| `missing_letter` | Deleted letter |
| `extra_letter` | Inserted letter |
| `drop_final_vowel` | Dropped final vowel |

## Files

- `train.jsonl` — full records (instruction format + labels)
- `train.csv` — compact table for quick inspection
- `dataset_manifest.json` — counts and coverage summary

## Example

```json
{
  "incorrect": "mire",
  "correct": "mirë",
  "error_type": "missing_diacritic",
  "language": "sq",
  "task": "albanian_spelling_correction",
  "instruction": "Korrigjo fjalën e gabuar në shqip. Kthe vetëm formën e saktë.",
  "input": "mire",
  "output": "mirë"
}
```

## How it was created

Source Albanian lemmas were taken from:

1. curated educational seed vocabulary, and
2. answers/prompts from AlbLingo exercise instruction pairs.

Errors were injected **deterministically / controlled** (not scraped noisy web text), so each pair has a known linguistic category useful for:

- data augmentation for GEC / spelling models
- ERRANT-style evaluation preparation
- pedagogical feedback examples for children

## Load with Datasets

```python
from datasets import load_dataset

ds = load_dataset("YOUR_HF_USERNAME/albanian-error-augmentation")
print(ds["train"][0])
```

## Intended research use

Educational NLP for Albanian spelling, especially primary-school orthography. Not a general web corpus.

## License

Apache 2.0
