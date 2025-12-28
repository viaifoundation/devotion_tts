#!/bin/bash
# setup_gptsovits.sh
# Runs the internal download.py to fetch pretrained models for GPT-SoVITS

echo "--- Setting up GPT-SoVITS Models ---"

# 1. Check if we are in the right place or find the file
DOWNLOAD_SCRIPT="/workspace/GPT-SoVITS/GPT_SoVITS/download.py"

if [ ! -f "$DOWNLOAD_SCRIPT" ]; then
    echo "❌ Could not find download.py at $DOWNLOAD_SCRIPT"
    echo "Searching..."
    DOWNLOAD_SCRIPT=$(find /workspace -name download.py | grep GPT-SoVITS | head -n 1)
fi

if [ -f "$DOWNLOAD_SCRIPT" ]; then
    echo "Found downloader: $DOWNLOAD_SCRIPT"
    echo "Running download (this may take a while)..."
    
    # We need to run it from the root of GPT-SoVITS usually, or where it expects
    cd $(dirname "$DOWNLOAD_SCRIPT")/..
    export PYTHONPATH=$PYTHONPATH:$(pwd)
    
    python "$DOWNLOAD_SCRIPT"
    
    echo "✅ Download complete (if no errors above)."
    echo "Checking pretrained_models..."
    ls -R GPT_SoVITS/pretrained_models
else
    echo "❌ Critical: download.py not found."
    exit 1
fi
