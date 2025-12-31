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

# Group 1: Utilities (Safe to install deps)
pip install -q --force-reinstall \
    gdown \
    hydra-core \
    inflect \
    omegaconf \
    pyworld \
    pydub \
    numpy \
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
    psutil

# Group 2: AI Core (Install with NO DEPS to prevent torch downgrade)
# We manually verified these need torch, and pip tries to reinstall torch if we let it resolve deps
pip install -q --no-deps --force-reinstall \
    "transformers>=4.40.0" \
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
    soundfile

# Ensure ruamel.yaml is downgraded if newer version exists (fixes max_depth error)
pip install -q "ruamel.yaml<0.18.0"

# Reinstall torchaudio if needed (sometimes pip breaks it)
pip install -q torchaudio --no-deps 2>/dev/null || true

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
