#!/bin/bash
# setup_qwentts_spark.sh - Setup Qwen-TTS in DGX Spark container
# Run this INSIDE the container

echo "=== Qwen-TTS Setup for DGX Spark ==="

# Step 1: Install system dependencies (FFmpeg)
if ! command -v ffmpeg &> /dev/null; then
    echo "[1/3] Installing system dependencies..."
    apt-get update -qq && apt-get install -y -qq ffmpeg libsndfile1 > /dev/null 2>&1
else
    echo "[1/3] System dependencies (ffmpeg) already installed."
fi

# Step 2: Install Python dependencies
echo "[2/3] Verifying/Installing Python dependencies..."

# Install core utilities
pip install -q \
    numpy \
    scipy \
    soundfile \
    librosa \
    pydub \
    inflect \
    tqdm \
    loguru \
    "typing-extensions" \
    accelerate \
    einops \
    transformers_stream_generator \
    tiktoken \
    "gradio<4.0" || echo "⚠️ Minor dep install issues"

# Install AI Core with --no-deps to protect torch
pip install -q --no-deps \
    "transformers>=4.40.0" \
    "huggingface-hub" \
    "torchaudio" || echo "⚠️ AI Core install issues"

# Install Qwen3-TTS package
echo "[2.5/3] Installing Qwen3-TTS package..."
pip install -q git+https://github.com/QwenLM/Qwen3-TTS.git || echo "⚠️ Qwen-TTS install failed"


# Step 3: Flash Attention Check
if python -c "import flash_attn" &> /dev/null; then
    echo "✅ Flash Attention is installed."
else
    echo "⚠️ Flash Attention NOT found. Attempting install..."
    pip install ninja
    pip install flash-attn --no-build-isolation || echo "❌ Flash Attention build failed. Will run in standard mode (slower)."
fi

echo "[3/3] Setting up environment..."
export PYTHONPATH=$PYTHONPATH:/workspace/github/devotion_tts

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Run: python gen_verse_devotion_qwentts.py --input input.txt"
echo ""
