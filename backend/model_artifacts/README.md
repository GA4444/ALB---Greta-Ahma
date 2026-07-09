# Model Artifacts

This folder is the integration point between the AlbLingo application and the
doctoral-level AI experiments.

Training should be performed on a GPU/Colab machine, then the generated artifacts
should be copied here. Render should load trained artifacts only.

## LoRA/QLoRA

Expected files:

```text
model_artifacts/lora_qlora/adapter/training_manifest.json
model_artifacts/lora_qlora/adapter/adapter_config.json
model_artifacts/lora_qlora/adapter/adapter_model.*
```

Commands:

```bash
pip install -r backend/requirements-training.txt
cd backend
python scripts/export_lora_dataset.py
python scripts/train_lora_qlora.py --model Qwen/Qwen2.5-0.5B-Instruct --qlora
```

## Deep-IRT / DKT

Expected files:

```text
model_artifacts/deep_irt_dkt/training_manifest.json
model_artifacts/deep_irt_dkt/dkt_model.pt
```

Command:

```bash
cd backend
python scripts/train_deep_irt_dkt.py --epochs 30
```

## ERRANT/GLEU Benchmark

Expected file:

```text
model_artifacts/benchmarks/errant_gleu_results.json
```

Command:

```bash
cd backend
python scripts/run_errant_gleu_benchmark.py --input model_artifacts/benchmarks/test_corrections.jsonl
```

For Albanian, if official ERRANT preprocessing is not available, report the
included metric as ERRANT-inspired F0.5 and GLEU-like unless an Albanian-specific
official evaluation setup is documented.
