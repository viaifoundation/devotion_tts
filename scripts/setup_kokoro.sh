#!/bin/bash
# Setup Kokoro TTS (ultra-lightweight, CPU-friendly)
# Run: source scripts/setup_kokoro.sh

set -e

echo "=== Setting up Kokoro TTS ==="

# Create venv
VENV_DIR="envs/kokoro"
if [ ! -d "$VENV_DIR" ]; then
    echo "[1/2] Creating virtual environment..."
    python -m venv "$VENV_DIR"
else
    echo "[1/2] Virtual environment already exists."
fi

source "$VENV_DIR/bin/activate"

# Install dependencies
echo "[2/2] Installing dependencies..."
pip install -q -r requirements-kokoro.txt

echo ""
echo "=== Kokoro TTS Setup Complete ==="
echo "Activate: source envs/kokoro/bin/activate"
echo "Run:      python gen_verse_devotion_kokoro.py --input sample.txt -d 1"
