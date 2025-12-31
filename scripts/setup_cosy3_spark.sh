#!/bin/bash
# setup_cosy3_spark.sh - Setup Fun-CosyVoice 3.0 in DGX Spark container
# Run this INSIDE the container after starting with:
#   docker run --gpus all -it --rm -v ~/github:/workspace/github -w /workspace/github/devotion_tts nvcr.io/nvidia/pytorch:25.11-py3

echo "=== Fun-CosyVoice 3.0 Setup for DGX Spark ==="

# Step 1: Install system dependencies (FFmpeg)
if ! command -v ffmpeg &> /dev/null; then
    echo "[1/4] Installing system dependencies..."
    apt-get update -qq && apt-get install -y -qq ffmpeg > /dev/null 2>&1
else
    echo "[1/4] System dependencies (ffmpeg) already installed."
fi

# Step 2: Install Python dependencies
echo "[2/4] Installing Python dependencies..."

# Explicitly uninstall conflicting packages that might be pre-installed in the container
# This is necessary because pip may skip downgrading some "satisfied" system packages
pip uninstall -y huggingface-hub transformers 2>/dev/null

# Group 1: Utilities & Sub-Dependencies (Safe to install deps)
# We strictly list ALL missing deps here because Group 2 uses --no-deps
pip install -q --force-reinstall \
    "numpy<2.0" \
    coloredlogs \
    flatbuffers \
    einx \
    loguru \
    tqdm \
    "typing-extensions" \
    PyYAML \
    nvidia-ml-py \
    "fsspec<=2025.10.0" \
    gdown \
    hydra-core \
    inflect \
    omegaconf \
    pyworld \
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
    tokenizers \
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
    HyperPyYAML \
    conformer \
    lightning \
    modelscope \
    openai-whisper \
    x-transformers \
    onnx \
    onnxruntime \
    librosa \
    soundfile || { echo "❌ Failed to install Group 2 dependencies"; return 1; }

# Ensure ruamel.yaml is downgraded if newer version exists (fixes max_depth error)
pip install -q "ruamel.yaml<0.18.0"

echo "✓ Python dependencies installed"

# Patch CosyVoice to use librosa (most robust for resampling/formats)
echo "[3/4] Patching CosyVoice..."
sed -i "s/speech, sample_rate = torchaudio.load(wav, backend='soundfile')/import librosa; speech, sample_rate = librosa.load(wav, sr=target_sr); speech = torch.from_numpy(speech); speech = speech.unsqueeze(0)/" /workspace/github/CosyVoice/cosyvoice/utils/file_utils.py

# FORCE FP32: Patch default fp16=True to fp16=False in source code
# This fixes the static noise issue on Blackwell/ARM64
sed -i "s/fp16: bool = True/fp16: bool = False/g" /workspace/github/CosyVoice/cosyvoice/cli/cosyvoice.py
echo "✓ Patched cosyvoice to force FP32 (fixes Spark noise)"
echo "✓ Patched cosyvoice/utils/file_utils.py"

# Set PYTHONPATH
echo "[4/4] Setting up environment..."
export PYTHONPATH=$PYTHONPATH:/workspace/github/CosyVoice:/workspace/github/CosyVoice/third_party/Matcha-TTS

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Run: python gen_verse_devotion_cosy3.py --input input.txt -d 1"
echo ""
