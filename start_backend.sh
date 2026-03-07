#!/bin/bash
cd "$(dirname "$0")/backend"
# Ensure venv
source venv/bin/activate 2>/dev/null || python3 -m venv venv && source venv/bin/activate
# Install deps (quiet)
pip install -q -r requirements.txt

# Set Tesseract data path if not already set (Homebrew default on macOS)
export TESSDATA_PREFIX="${TESSDATA_PREFIX:-/opt/homebrew/share/tessdata}"

uvicorn app.main:app --reload --host 0.0.0.0 --port 8001


