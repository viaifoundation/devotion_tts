#!/bin/bash
# setup_glmtts_spark.sh
# Setup GLM-TTS for NVIDIA DGX Spark
# Based on: https://github.com/zai-org/GLM-TTS

set -e

echo "=== GLM-TTS Setup for DGX Spark ==="

# [1/5] System dependencies
if ! command -v ffmpeg &> /dev/null; then
    echo "[1/5] Installing ffmpeg..."
    apt-get update -qq && apt-get install -y -qq ffmpeg || { echo "❌ Failed to install ffmpeg"; return 1; }
else
    echo "[1/5] System dependencies (ffmpeg) already installed."
fi

# [2/5] Clone GLM-TTS if not present
GLMTTS_PATH="/workspace/github/GLM-TTS"
if [ ! -d "$GLMTTS_PATH" ]; then
    echo "[2/5] Cloning GLM-TTS repository..."
    git clone https://github.com/zai-org/GLM-TTS.git "$GLMTTS_PATH" || { echo "❌ Failed to clone GLM-TTS"; return 1; }
else
    echo "[2/5] GLM-TTS repository already exists."
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
    gdown \
    hydra-core \
    omegaconf \
    pydub \
    matplotlib \
    protobuf \
    rich \
    "ruamel.yaml<0.18.0" \
    tiktoken \
    pydantic \
    wget \
    mutagen \
    packaging \
    regex \
    safetensors \
    "tokenizers>=0.20,<0.21" \
    psutil || { echo "❌ Failed to install Group 1 dependencies"; return 1; }

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

# Group 3: GLM-TTS specific dependencies
cd "$GLMTTS_PATH"
pip install -q -r requirements.txt --no-deps 2>/dev/null || true
echo "✓ Python dependencies installed"

# [4/5] Download pre-trained models
CKPT_PATH="$GLMTTS_PATH/ckpt"
if [ ! -d "$CKPT_PATH" ] || [ -z "$(ls -A $CKPT_PATH 2>/dev/null)" ]; then
    echo "[4/5] Downloading GLM-TTS models from HuggingFace..."
    mkdir -p "$CKPT_PATH"
    huggingface-cli download zai-org/GLM-TTS --local-dir "$CKPT_PATH" || { echo "❌ Failed to download models"; return 1; }
    echo "✓ Models downloaded to $CKPT_PATH"
else
    echo "[4/5] GLM-TTS models already present."
fi

# [5/5] Setup environment
echo "[5/5] Setting up environment..."
export PYTHONPATH="$GLMTTS_PATH:/workspace/github/devotion_tts:$PYTHONPATH"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Run: python gen_verse_devotion_glmtts.py --input input.txt -d 1"
echo ""
