#!/usr/bin/env python3
"""Publish LoRA adapter + augmentation dataset to Hugging Face Hub."""

from __future__ import annotations

import os
import sys


def main() -> None:
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_HUB_TOKEN")
    username = os.environ.get("HF_USERNAME")
    if not token:
        raise SystemExit("Set HF_TOKEN (Hugging Face write token).")
    if not username:
        raise SystemExit("Set HF_USERNAME (your Hugging Face username).")

    from huggingface_hub import HfApi, create_repo

    backend = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    model_dir = os.path.join(backend, "huggingface_publish", "albanian-spelling-lora")
    dataset_dir = os.path.join(backend, "huggingface_publish", "dataset_albanian_error_augmentation")
    generate_script = os.path.join(backend, "huggingface_publish", "standalone", "generate_exercises.py")

    api = HfApi(token=token)

    model_repo = f"{username}/albanian-spelling-lora"
    dataset_repo = f"{username}/albanian-error-augmentation"

    create_repo(model_repo, repo_type="model", exist_ok=True, private=False, token=token)
    create_repo(dataset_repo, repo_type="dataset", exist_ok=True, private=False, token=token)

    # Include standalone script inside the model repo for convenience.
    api.upload_file(
        path_or_fileobj=generate_script,
        path_in_repo="generate_exercises.py",
        repo_id=model_repo,
        repo_type="model",
        token=token,
    )
    api.upload_folder(
        folder_path=model_dir,
        repo_id=model_repo,
        repo_type="model",
        token=token,
    )
    api.upload_folder(
        folder_path=dataset_dir,
        repo_id=dataset_repo,
        repo_type="dataset",
        token=token,
    )

    print("Published successfully:")
    print(f"  Model:   https://huggingface.co/{model_repo}")
    print(f"  Dataset: https://huggingface.co/datasets/{dataset_repo}")


if __name__ == "__main__":
    main()
