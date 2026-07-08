#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -f "venv/bin/activate" ]; then
  echo "ERROR: virtual environment not found. Run ./install.sh first."
  exit 1
fi

source venv/bin/activate
python -m streamlit run app/Home.py
