#!/bin/bash
# Setup Spark-TTS on NVIDIA DGX Spark
# Run: source scripts/setup_sparktts_spark.sh

set -e

echo "=== Setting up Spark-TTS on DGX Spark ==="

# Clone Spark-TTS repo if not present
SPARKTTS_DIR="/workspace/github/Spark-TTS"
if [ ! -d "$SPARKTTS_DIR" ]; then
    echo "Cloning Spark-TTS..."
    git clone https://github.com/SparkAudio/Spark-TTS.git "$SPARKTTS_DIR"
fi

cd "$SPARKTTS_DIR"

# Install dependencies
pip install -r requirements.txt
pip install pydub

# Download model
python -c "
from huggingface_hub import snapshot_download
snapshot_download('SparkAudio/Spark-TTS-0.5B', local_dir='pretrained_models/Spark-TTS-0.5B')
print('✅ Model downloaded successfully')
"

cd /workspace/github/devotion_tts

echo ""
echo "=== Spark-TTS Setup Complete ==="
echo "Run: python gen_verse_devotion_sparktts.py --input sample.txt -d 1"
