#!/bin/bash
# run_spark_cosy3.sh - Run Fun-CosyVoice 3.0 on NVIDIA DGX Spark
# Usage: ./scripts/run_spark_cosy3.sh [input_file] [ref_audio]

set -e

# Configuration
GITHUB_DIR="${HOME}/github"
CACHE_DIR="${HOME}/.cache"
MODEL_DIR="${GITHUB_DIR}/CosyVoice/pretrained_models/Fun-CosyVoice3-0.5B"
IMAGE="nvcr.io/nvidia/pytorch:25.11-py3"

# Parse arguments
INPUT_FILE="${1:-}"
REF_AUDIO="${2:-assets/ref_audio/ref.wav}"
REF_TEXT="${3:-你好，我是可以在本地运行的语音生成模型。}"

echo "=========================================="
echo "Fun-CosyVoice 3.0 on DGX Spark"
echo "=========================================="

# Check if model exists
if [ ! -d "$MODEL_DIR" ] || [ -z "$(ls -A $MODEL_DIR 2>/dev/null)" ]; then
    echo "⚠️  Fun-CosyVoice 3.0 model not found at: $MODEL_DIR"
    echo "📥 Downloading model from HuggingFace..."
    
    pip install -U huggingface_hub 2>/dev/null || true
    huggingface-cli download FunAudioLLM/Fun-CosyVoice3-0.5B-2512 \
        --local-dir "$MODEL_DIR"
    
    echo "✅ Model downloaded successfully"
fi

# Build command
CMD="cd /workspace/github/devotion_tts && "
CMD+="export PYTHONPATH=\$PYTHONPATH:/workspace/github/CosyVoice:/workspace/github/CosyVoice/third_party/Matcha-TTS && "

if [ -n "$INPUT_FILE" ]; then
    CMD+="python gen_verse_devotion_cosy3.py --input $INPUT_FILE --ref-audio $REF_AUDIO --ref-text '$REF_TEXT'"
else
    CMD+="bash"
fi

echo "🐳 Starting Docker container..."
echo "   Image: $IMAGE"
echo "   Input: ${INPUT_FILE:-interactive}"
echo ""

docker run --gpus all -it --rm \
    -v "${GITHUB_DIR}:/workspace/github" \
    -v "${CACHE_DIR}:/root/.cache" \
    -w /workspace/github/devotion_tts \
    "$IMAGE" \
    bash -c "apt-get update -qq && apt-get install -y -qq ffmpeg > /dev/null 2>&1 && \
             pip install -q pydub mutagen 2>/dev/null && \
             $CMD"
