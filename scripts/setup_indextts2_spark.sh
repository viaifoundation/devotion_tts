#!/bin/bash
# setup_indextts2_spark.sh
# Setup Index-TTS2 for NVIDIA DGX Spark
# Based on: https://github.com/index-tts/index-tts

set -e

echo "=== Index-TTS2 Setup for DGX Spark ==="

# [1/5] System dependencies
echo "[1/5] Installing system dependencies..."
apt-get update -qq && apt-get install -y -qq ffmpeg git-lfs || { echo "❌ Failed to install system deps"; return 1; }
git lfs install || true

# [2/5] Clone Index-TTS2 if not present
INDEXTTS_PATH="/workspace/github/index-tts"
if [ ! -d "$INDEXTTS_PATH" ]; then
    echo "[2/5] Cloning Index-TTS2 repository..."
    git clone https://github.com/index-tts/index-tts.git "$INDEXTTS_PATH" || { echo "❌ Failed to clone Index-TTS2"; return 1; }
    cd "$INDEXTTS_PATH"
    git lfs pull
else
    echo "[2/5] Index-TTS2 repository already exists."
    cd "$INDEXTTS_PATH"
fi

# [3/5] Install Python dependencies
echo "[3/5] Installing Python dependencies..."

# Forcefully remove conflicting pre-installed versions
pip uninstall -y huggingface-hub transformers 2>/dev/null || true

# Group 1: Utilities & Sub-Dependencies (Safe to install deps)
pip install -q --force-reinstall \
    "numpy<2.0" \
    coloredlogs \
    einx \
    loguru \
    tqdm \
    "typing-extensions" \
    PyYAML \
    nvidia-ml-py \
    "fsspec<=2025.10.0" \
    pydub \
    matplotlib \
    protobuf \
    rich \
    tiktoken \
    pydantic \
    wget \
    mutagen \
    packaging \
    regex \
    safetensors \
    "tokenizers>=0.20,<0.21" \
    psutil \
    deepspeed \
    gradio || { echo "❌ Failed to install Group 1 dependencies"; return 1; }

# Group 2: AI Core (Install with NO DEPS to prevent torch downgrade)
pip install -q --no-deps --force-reinstall \
    "transformers==4.46.3" \
    "huggingface-hub<1.0" \
    "pytorch-lightning>=2.0.0" \
    "torchmetrics>=0.7.0" \
    torchaudio \
    accelerate \
    diffusers \
    lightning \
    modelscope \
    onnx \
    onnxruntime \
    librosa \
    soundfile || { echo "❌ Failed to install Group 2 dependencies"; return 1; }

# Install Index-TTS2 specific requirements
if [ -f "$INDEXTTS_PATH/requirements.txt" ]; then
    pip install -q -r "$INDEXTTS_PATH/requirements.txt" --no-deps 2>/dev/null || true
fi
echo "✓ Python dependencies installed"

# [4/5] Download pre-trained models
CKPT_PATH="$INDEXTTS_PATH/checkpoints"
if [ ! -d "$CKPT_PATH" ] || [ -z "$(ls -A $CKPT_PATH 2>/dev/null)" ]; then
    echo "[4/5] Downloading Index-TTS2 models from HuggingFace..."
    mkdir -p "$CKPT_PATH"
    huggingface-cli download IndexTeam/IndexTTS-2 --local-dir "$CKPT_PATH" || { echo "❌ Failed to download models"; return 1; }
    echo "✓ Models downloaded to $CKPT_PATH"
else
    echo "[4/5] Index-TTS2 models already present."
fi

# [5/5] Setup environment
echo "[5/5] Setting up environment..."
export PYTHONPATH="$INDEXTTS_PATH:/workspace/github/devotion_tts:$PYTHONPATH"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Run: python gen_verse_devotion_indextts2.py --input input.txt -d 1"
echo ""
