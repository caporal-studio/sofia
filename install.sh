#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "Preparing SOFIA..."

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 was not found. Install Python 3.11+ first."
  exit 1
fi

if [ ! -d "venv" ]; then
  python3 -m venv venv
fi

source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r app/install/requirements.txt

python app/scripts/setup_inicial.py

python -m streamlit run app/Home.py
