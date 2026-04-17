#!/bin/bash
# Setup Spark-TTS on NVIDIA DGX Spark
# Run: source scripts/setup_sparktts_spark.sh

set -e

echo "=== Setting up Spark-TTS on DGX Spark ==="

# Clone Spark-TTS repo if not present
SPARKTTS_DIR="../Spark-TTS"
if [ ! -d "$SPARKTTS_DIR" ]; then
    echo "[1/4] Cloning Spark-TTS..."
    git clone https://github.com/SparkAudio/Spark-TTS.git "$SPARKTTS_DIR"
else
    echo "[1/4] Spark-TTS repo already exists."
fi

# Create venv
VENV_DIR="envs/sparktts"
if [ ! -d "$VENV_DIR" ]; then
    echo "[2/4] Creating virtual environment..."
    python -m venv "$VENV_DIR"
else
    echo "[2/4] Virtual environment already exists."
fi

source "$VENV_DIR/bin/activate"

# Install dependencies
echo "[3/4] Installing dependencies..."
pip install -q -r requirements-sparktts.txt

# Download model
echo "[4/4] Downloading Spark-TTS-0.5B model..."
python -c "
from huggingface_hub import snapshot_download
snapshot_download('SparkAudio/Spark-TTS-0.5B', local_dir='$SPARKTTS_DIR/pretrained_models/Spark-TTS-0.5B')
print('✅ Model downloaded successfully')
"

echo ""
echo "=== Spark-TTS Setup Complete ==="
echo "Activate: source envs/sparktts/bin/activate"
echo "Run:      python gen_verse_devotion_sparktts.py --input sample.txt -d 1"
