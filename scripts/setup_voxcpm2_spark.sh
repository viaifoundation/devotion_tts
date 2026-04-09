#!/bin/bash
# setup_voxcpm2_spark.sh
# Setup VoxCPM2 for NVIDIA DGX Spark
# Based on: https://github.com/OpenBMB/VoxCPM

set -e

echo "=== VoxCPM2 Setup for DGX Spark ==="

# [1/4] System dependencies
if ! command -v ffmpeg &> /dev/null; then
    echo "[1/4] Installing ffmpeg..."
    apt-get update -qq && apt-get install -y -qq ffmpeg || { echo "❌ Failed to install ffmpeg"; return 1; }
else
    echo "[1/4] System dependencies (ffmpeg) already installed."
fi

# [2/4] Install voxcpm package
echo "[2/4] Installing voxcpm package..."

# Forcefully remove conflicting pre-installed versions
pip uninstall -y huggingface-hub transformers 2>/dev/null || true

# Group 1: Core voxcpm package
pip install -q voxcpm || { echo "❌ Failed to install voxcpm"; return 1; }

# Group 2: Additional utilities (install with no-deps to prevent torch downgrade)
pip install -q --no-deps --force-reinstall \
    pydub \
    mutagen \
    soundfile || { echo "❌ Failed to install utility dependencies"; return 1; }

echo "✓ voxcpm package installed"

# [3/4] Download model weights (pre-cache for faster inference)
echo "[3/4] Pre-downloading VoxCPM2 model weights..."
python3 -c "
from voxcpm import VoxCPM
print('Downloading VoxCPM2 model...')
model = VoxCPM.from_pretrained('openbmb/VoxCPM2', load_denoiser=False)
print('✅ Model downloaded and cached.')
del model
" || { echo "⚠️ Model pre-download failed. Will download on first run."; }

# [4/4] Setup environment
echo "[4/4] Setting up environment..."
export PYTHONPATH="/workspace/github/devotion_tts:$PYTHONPATH"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Modes:"
echo "  Clone:    python gen_verse_devotion_voxcpm2.py --input input.txt -d 1"
echo "  Design:   python gen_verse_devotion_voxcpm2.py --input input.txt --mode design --design gentle_female -d 1"
echo "  Ultimate: python gen_verse_devotion_voxcpm2.py --input input.txt --mode ultimate --voices ref.wav --ref-text '...' -d 1"
echo ""
