#!/bin/bash
# setup_cosy3.sh - Setup Fun-CosyVoice 3.0 environment
# Run this once to download the model and verify installation

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COSYVOICE_DIR="${SCRIPT_DIR}/../CosyVoice"
MODEL_DIR="${COSYVOICE_DIR}/pretrained_models/Fun-CosyVoice3-0.5B"

echo "=========================================="
echo "Fun-CosyVoice 3.0 Setup"
echo "=========================================="

# Step 1: Check CosyVoice repo
echo ""
echo "Step 1: Checking CosyVoice repository..."
if [ ! -d "$COSYVOICE_DIR" ]; then
    echo "📥 Cloning CosyVoice repository..."
    git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git "$COSYVOICE_DIR"
else
    echo "✅ CosyVoice repository found at: $COSYVOICE_DIR"
fi

# Step 2: Check/Update submodules
echo ""
echo "Step 2: Updating submodules..."
cd "$COSYVOICE_DIR"
git submodule update --init --recursive
cd "$SCRIPT_DIR"

# Step 3: Install huggingface_hub
echo ""
echo "Step 3: Installing huggingface_hub..."
pip install -U huggingface_hub

# Step 4: Download Fun-CosyVoice 3.0 model
echo ""
echo "Step 4: Downloading Fun-CosyVoice 3.0 model..."
if [ -d "$MODEL_DIR" ] && [ -n "$(ls -A $MODEL_DIR 2>/dev/null)" ]; then
    echo "✅ Model already exists at: $MODEL_DIR"
    echo "   To re-download, delete the directory first."
else
    echo "📥 Downloading from HuggingFace (this may take a while, ~10GB)..."
    mkdir -p "$MODEL_DIR"
    huggingface-cli download FunAudioLLM/Fun-CosyVoice3-0.5B-2512 \
        --local-dir "$MODEL_DIR"
    echo "✅ Model downloaded successfully"
fi

# Step 5: Verify
echo ""
echo "Step 5: Verifying installation..."
if [ -f "${MODEL_DIR}/flow.pt" ] || [ -f "${MODEL_DIR}/llm.pt" ]; then
    echo "✅ Fun-CosyVoice 3.0 model files found"
else
    echo "⚠️  Model files may be incomplete. Check $MODEL_DIR"
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "To run Fun-CosyVoice 3.0:"
echo "  python gen_verse_devotion_cosy3.py --input your_text.txt --ref-audio assets/ref_audio/speaker.wav"
echo ""
echo "For DGX Spark:"
echo "  ./scripts/run_spark_cosy3.sh your_text.txt"
echo ""
