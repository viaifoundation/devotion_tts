#!/bin/bash
# Setup F5-TTS on NVIDIA DGX Spark
# Run: source scripts/setup_f5tts_spark.sh

set -e

echo "=== Setting up F5-TTS on DGX Spark ==="

# Create venv
VENV_DIR="envs/f5tts"
if [ ! -d "$VENV_DIR" ]; then
    echo "[1/2] Creating virtual environment..."
    python -m venv "$VENV_DIR"
else
    echo "[1/2] Virtual environment already exists."
fi

source "$VENV_DIR/bin/activate"

# Install dependencies
echo "[2/2] Installing dependencies..."
pip install -q -r requirements-f5tts.txt

echo ""
echo "=== F5-TTS Setup Complete ==="
echo "Activate: source envs/f5tts/bin/activate"
echo "Run:      python gen_verse_devotion_f5tts.py --input sample.txt -d 1"
