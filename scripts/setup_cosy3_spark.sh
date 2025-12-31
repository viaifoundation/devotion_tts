#!/bin/bash
# setup_cosy3_spark.sh - Setup Fun-CosyVoice 3.0 in DGX Spark container
# Run this INSIDE the container after starting with:
#   docker run --gpus all -it --rm -v ~/github:/workspace/github -w /workspace/github/devotion_tts nvcr.io/nvidia/pytorch:25.11-py3

echo "=== Fun-CosyVoice 3.0 Setup for DGX Spark ==="

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
