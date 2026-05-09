## Table I. Overall CER and WER by configuration across all document categories

| Configuration | CER (%) | WER (%) | DER (%) |
|---|---:|---:|---:|
| A - Tesseract sqi | 76.37 | 113.01 | 25.13 |
| B - Tesseract fallback | 82.66 | 103.33 | 83.33 |
| C - Best-of multi-pass fusion | 76.37 | 113.01 | 25.13 |
| D - Fusion + heuristics | 76.09 | 113.01 | 18.35 |
| E - Full pipeline | 77.16 | 113.01 | 23.94 |

## Table II. CER (%) by document category and layout complexity

| Category | Layout | Config A | Config B | Config C | Config D | Config E |
|---|---|---:|---:|---:|---:|---:|
| Administrative | Complex | 72.73 | 72.73 | 72.73 | 71.72 | 71.72 |
| Administrative | Simple | 76.92 | 82.42 | 76.92 | 75.82 | 75.82 |
| Educational | Complex | 75.38 | 75.38 | 75.38 | 72.31 | 78.46 |
| Educational | Simple | 76.55 | 89.58 | 76.55 | 78.50 | 77.85 |
| Literary | Complex | 85.90 | 87.18 | 85.90 | 85.90 | 85.90 |
| Literary | Simple | 70.76 | 88.70 | 70.76 | 72.31 | 73.20 |

## Table III. Proposed row for comparison table

| System | Language | CER (%) | WER (%) | Method |
|---|---|---:|---:|---|
| Proposed (Config E) | Albanian | 77.16 | 113.01 | Tesseract-based hybrid + Albanian-specific PP |
