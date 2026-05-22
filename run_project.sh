#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "=========================================="
echo "Qu2016 precipitation method reproduction"
echo "Running with real Open-Meteo data"
echo "=========================================="

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python scripts/00_run_all.py --force-download
