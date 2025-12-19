#!/bin/bash
set -e

# Configuration
IMAGE_NAME="devotion-cosy-spark"
DOCKERFILE="docker/Dockerfile.spark.cosy"
CONTAINER_NAME="devotion_cosy_runner"

# Check if we are in the root of the repo
if [ ! -f "gen_verse_devotion_cosy.py" ]; then
    echo "Error: Please run this script from the root of the devotion_tts repository."
    echo "Usage: ./scripts/run_spark_cosy.sh"
    exit 1
fi

# Build the image if it doesn't exist or if forced
if [[ "$(docker images -q $IMAGE_NAME 2> /dev/null)" == "" ]] || [[ "$1" == "--build" ]]; then
    echo "Building Docker image $IMAGE_NAME..."
    docker build -t $IMAGE_NAME -f $DOCKERFILE .
fi

# Check for CosyVoice directory
COSY_DIR="../CosyVoice"
if [ ! -d "$COSY_DIR" ]; then
    echo "Warning: CosyVoice directory not found at $COSY_DIR"
    echo "Please ensure you have cloned CosyVoice as a sibling directory:"
    echo "  git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git ../CosyVoice"
    read -p "Press Enter to continue anyway (or Ctrl+C to abort)..."
fi

echo "Starting container..."
echo "Mounting $(pwd) -> /workspace/github/devotion_tts"
echo "Mounting $(realpath $COSY_DIR) -> /workspace/github/CosyVoice"

# Run the container
# We map the modelscope cache so downloads persist
docker run --gpus all -it --rm \
    --name $CONTAINER_NAME \
    --net=host \
    --shm-size=16g \
    -v "$(pwd)":/workspace/github/devotion_tts \
    -v "$(realpath $COSY_DIR)":/workspace/github/CosyVoice \
    -v "$HOME/.cache/modelscope":/root/.cache/modelscope \
    -w /workspace/github/devotion_tts \
    $IMAGE_NAME
