#!/bin/bash
# setup_cosy3_spark.sh - Setup Fun-CosyVoice 3.0 in DGX Spark container
# Run this INSIDE the container after starting with:
#   docker run --gpus all -it --rm -v ~/github:/workspace/github -w /workspace/github/devotion_tts nvcr.io/nvidia/pytorch:25.11-py3

echo "=== Fun-CosyVoice 3.0 Setup for DGX Spark ==="

# Install system dependencies
echo "[1/3] Installing system dependencies..."
apt-get update -qq && apt-get install -y -qq ffmpeg > /dev/null 2>&1
echo "✓ ffmpeg installed"

# Install Python dependencies (skip grpcio - not needed for inference)
echo "[2/3] Installing Python dependencies..."
pip install -q \
    HyperPyYAML \
    conformer \
    diffusers \
    gdown \
    hydra-core \
    inflect \
    lightning \
    modelscope \
    omegaconf \
    openai-whisper \
    pyworld \
    transformers \
    x-transformers \
    onnx \
    onnxruntime \
    librosa \
    soundfile \
    pydub \
    numpy \
    matplotlib \
    protobuf \
    rich \
    ruamel.yaml \
    tiktoken \
    pydantic \
    wget \
    mutagen

# Reinstall torchaudio if needed (sometimes pip breaks it)
pip install -q torchaudio --no-deps 2>/dev/null || true

echo "✓ Python dependencies installed"

# Patch CosyVoice to use soundfile instead of torchaudio (avoid torchcodec issues)
echo "[3/4] Patching CosyVoice..."
sed -i "s/speech, sample_rate = torchaudio.load(wav, backend='soundfile')/import soundfile as sf; data, sample_rate = sf.read(wav); speech = torch.from_numpy(data).float(); speech = speech.mean(dim=-1, keepdim=True).T if len(speech.shape) > 1 else speech.unsqueeze(0)/" /workspace/github/CosyVoice/cosyvoice/utils/file_utils.py
echo "✓ Patched cosyvoice/utils/file_utils.py"

# Set PYTHONPATH
echo "[4/4] Setting up environment..."
export PYTHONPATH=$PYTHONPATH:/workspace/github/CosyVoice:/workspace/github/CosyVoice/third_party/Matcha-TTS

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Run: python gen_verse_devotion_cosy3.py --input input.txt -d 1"
echo ""
