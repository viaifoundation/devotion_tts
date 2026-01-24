#!/bin/bash
# run_spark_qwentts.sh - Run Qwen-TTS on NVIDIA DGX Spark
# Usage: ./scripts/run_spark_qwentts.sh [input_file]

set -e

# Configuration
GITHUB_DIR="${HOME}/github"
CACHE_DIR="${HOME}/.cache"
MODEL_DIR="${GITHUB_DIR}/devotion_tts/pretrained_models"
MODEL_NAME="Qwen/Qwen2.5-TTS" # Placeholder, update if specific Qwen3 path is known
# Allow IMAGE override, default to base pytorch image
IMAGE="${IMAGE:-nvcr.io/nvidia/pytorch:25.11-py3}"

# Parse arguments
INPUT_FILE="${1:-}"

echo "=========================================="
echo "Qwen-TTS on DGX Spark"
echo "=========================================="

mkdir -p "$MODEL_DIR"

# Check if model exists (Basic check, might need specific subdir logic)
# For now, we rely on standard HuggingFace caching inside the container or host cache text
echo "ℹ️  Model '$MODEL_NAME' will be loaded from cache or downloaded at runtime."

# Build command (mimicking run_spark_cosy3.sh)
CMD="cd /workspace/github/devotion_tts && "
# We set PYTHONPATH in setup script, but good to be explicit if needed
CMD+="export PYTHONPATH=\$PYTHONPATH:/workspace/github/devotion_tts && "

# Pass all arguments directly to the python script
if [ "$#" -eq 0 ]; then
    CMD+="bash" # Interactive if no args
else
    # If first arg is a file that exists, assume it's for --input (backward compatibility)
    if [ -f "$1" ]; then
        CMD+="python gen_verse_devotion_qwentts.py --input $1 --voice-prompt 'Reading in a clear, soothing voice.'"
    else
        CMD+="python gen_verse_devotion_qwentts.py $@"
    fi
fi

echo "🐳 Starting Docker container..."
echo "   Image: $IMAGE"
echo "   Input: ${INPUT_FILE:-interactive}"
echo ""

# Build the docker image locally to ensure deps are there
# This can be time consuming so better to use a named image if pre-built.
# We will use the 'devotion-qwen3-spark' tag.
docker build -t devotion-qwentts-spark -f docker/Dockerfile.spark.qwentts .

docker run --gpus all -it --rm \
    -v "${GITHUB_DIR}:/workspace/github" \
    -v "${CACHE_DIR}:/root/.cache" \
    -w /workspace/github/devotion_tts \
    "devotion-qwentts-spark" \
    bash -c "source scripts/setup_qwentts_spark.sh && \
             $CMD"
