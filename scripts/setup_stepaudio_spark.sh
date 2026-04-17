#!/bin/bash
# Setup StepAudio TTS-3B on NVIDIA DGX Spark
# Run: source scripts/setup_stepaudio_spark.sh

set -e

echo "=== Setting up StepAudio TTS-3B on DGX Spark ==="

# Clone Step-Audio repo if not present
STEPAUDIO_DIR="/workspace/github/Step-Audio"
if [ ! -d "$STEPAUDIO_DIR" ]; then
    echo "Cloning Step-Audio..."
    git clone https://github.com/stepfun-ai/Step-Audio.git "$STEPAUDIO_DIR"
fi

cd "$STEPAUDIO_DIR"

# Install dependencies
pip install -r requirements.txt
pip install pydub

# Download TTS-3B model (smaller than the full 130B chat model)
echo "Downloading Step-Audio-TTS-3B model..."
git lfs install
if [ ! -d "Step-Audio-TTS-3B" ]; then
    git clone https://huggingface.co/stepfun-ai/Step-Audio-TTS-3B
fi

# Download Tokenizer
if [ ! -d "Step-Audio-Tokenizer" ]; then
    git clone https://huggingface.co/stepfun-ai/Step-Audio-Tokenizer
fi

cd /workspace/github/devotion_tts

echo ""
echo "=== StepAudio TTS-3B Setup Complete ==="
echo "Run: python gen_verse_devotion_stepaudio.py --input sample.txt -d 1"
