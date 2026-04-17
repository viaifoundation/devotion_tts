#!/bin/bash
# Setup StepAudio TTS-3B on NVIDIA DGX Spark
# Run: source scripts/setup_stepaudio_spark.sh

set -e

echo "=== Setting up StepAudio TTS-3B on DGX Spark ==="

# Clone Step-Audio repo if not present
STEPAUDIO_DIR="../Step-Audio"
if [ ! -d "$STEPAUDIO_DIR" ]; then
    echo "[1/5] Cloning Step-Audio..."
    git clone https://github.com/stepfun-ai/Step-Audio.git "$STEPAUDIO_DIR"
else
    echo "[1/5] Step-Audio repo already exists."
fi

# Create venv
VENV_DIR="envs/stepaudio"
if [ ! -d "$VENV_DIR" ]; then
    echo "[2/5] Creating virtual environment..."
    python -m venv "$VENV_DIR"
else
    echo "[2/5] Virtual environment already exists."
fi

source "$VENV_DIR/bin/activate"

# Install dependencies
echo "[3/5] Installing dependencies..."
pip install -q -r requirements-stepaudio.txt

# Download TTS-3B model
echo "[4/5] Downloading Step-Audio-TTS-3B model..."
cd "$STEPAUDIO_DIR"
git lfs install
if [ ! -d "Step-Audio-TTS-3B" ]; then
    git clone https://huggingface.co/stepfun-ai/Step-Audio-TTS-3B
fi

# Download Tokenizer
echo "[5/5] Downloading Step-Audio-Tokenizer..."
if [ ! -d "Step-Audio-Tokenizer" ]; then
    git clone https://huggingface.co/stepfun-ai/Step-Audio-Tokenizer
fi

cd -

echo ""
echo "=== StepAudio TTS-3B Setup Complete ==="
echo "Activate: source envs/stepaudio/bin/activate"
echo "Run:      python gen_verse_devotion_stepaudio.py --input sample.txt -d 1"
