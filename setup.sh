#!/usr/bin/env bash
set -euo pipefail

# Confirm python3 exists
if ! command -v python3 >/dev/null 2>&1; then
    echo "[ERROR] python3 not found. Please install it before running this script."
    exit 1
fi

# Create venv if missing
if [ ! -d "venv" ]; then
    echo "[INFO] Creating virtual environment..."
    python3 -m venv venv
fi

echo "[INFO] Activating virtual environment..."
source venv/bin/activate

echo "[INFO] Upgrading pip..."
python3 -m pip install --upgrade pip

echo "[INFO] Installing dependencies from requirements.txt..."
python3 -m pip install -r requirements.txt

echo "[SUCCESS] Environment setup complete."
