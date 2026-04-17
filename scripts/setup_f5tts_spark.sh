#!/bin/bash
# Setup F5-TTS on NVIDIA DGX Spark
# Run: source scripts/setup_f5tts_spark.sh

set -e

echo "=== Setting up F5-TTS on DGX Spark ==="

# Install F5-TTS
pip install f5-tts

# Install pydub for audio processing
pip install pydub

echo ""
echo "=== F5-TTS Setup Complete ==="
echo "Run: python gen_verse_devotion_f5tts.py --input sample.txt -d 1"
