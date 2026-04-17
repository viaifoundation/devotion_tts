#!/bin/bash
# sync_to_spark.sh - Rsync devotion_tts assets to NVIDIA DGX Spark
#
# Usage:
#   ./scripts/sync_to_spark.sh                  # Uses default SPARK_HOST
#   SPARK_HOST=192.168.1.100 ./scripts/sync_to_spark.sh
#   ./scripts/sync_to_spark.sh user@hostname
#
# What gets synced:
#   - assets/ref_audio/*.wav    (Voice reference files for cloning)
#   - assets/bgm/               (Background music tracks)
#   - assets/bible/db/           (bible.sqlite)
#   - assets/bible/audio/        (Chapter audio files)

set -e

# ─── Configuration ───
SPARK_HOST="${1:-${SPARK_HOST:-spark}}"
LOCAL_DIR="$HOME/github/devotion_tts"
REMOTE_DIR="~/github/devotion_tts"

echo "═══════════════════════════════════════════════"
echo "  Syncing devotion_tts assets → DGX Spark"
echo "  Host: $SPARK_HOST"
echo "═══════════════════════════════════════════════"
echo ""

# ─── 1. Reference Audio (voice cloning) ───
echo "📦 [1/4] Syncing reference audio..."
rsync -avz --progress \
    "$LOCAL_DIR/assets/ref_audio/" \
    "$SPARK_HOST:$REMOTE_DIR/assets/ref_audio/"
echo "✅ Reference audio synced"
echo ""

# ─── 2. BGM (background music) ───
echo "📦 [2/4] Syncing BGM tracks..."
rsync -avz --progress \
    "$LOCAL_DIR/assets/bgm/" \
    "$SPARK_HOST:$REMOTE_DIR/assets/bgm/"
echo "✅ BGM synced"
echo ""

# ─── 3. Bible DB ───
echo "📦 [3/4] Syncing Bible database..."
rsync -avz --progress \
    "$LOCAL_DIR/assets/bible/db/" \
    "$SPARK_HOST:$REMOTE_DIR/assets/bible/db/"
echo "✅ Bible DB synced"
echo ""

# ─── 4. Chapter Audio ───
echo "📦 [4/4] Syncing Bible chapter audio (1189 files)..."
rsync -avz --progress \
    "$LOCAL_DIR/assets/bible/audio/" \
    "$SPARK_HOST:$REMOTE_DIR/assets/bible/audio/"
echo "✅ Chapter audio synced"
echo ""

echo "═══════════════════════════════════════════════"
echo "  ✅ All assets synced to $SPARK_HOST"
echo ""
echo "  On Spark, run:"
echo "    docker run --gpus all -it --rm \\"
echo "      -v ~/github:/workspace/github \\"
echo "      -w /workspace/github/devotion_tts \\"
echo "      nvcr.io/nvidia/pytorch:25.01-py3-igpu bash"
echo ""
echo "    source scripts/setup_cosy3_spark.sh"
echo "    python gen_votd_cosy3.py -i input.txt --voice six"
echo "═══════════════════════════════════════════════"
