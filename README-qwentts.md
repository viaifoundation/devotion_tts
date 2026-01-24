# Devotion Audio TTS – Qwen-TTS Local Edition (DGX Spark)

Uses Alibaba's **Qwen-TTS model** running locally on the DGX Spark GPU for high-fidelity synthesis.

> [!NOTE]
> For **cloud API** usage (Dashscope), see [README-qwen.md](README-qwen.md).

## Files
- `gen_verse_devotion_qwentts.py` → Verse + Devotion + Prayer
- `scripts/run_spark_qwentts.sh` → Docker launch script
- `docker/Dockerfile.spark.qwentts` → Container definition

## Quick Start
```bash
# On DGX Spark host
./scripts/run_spark_qwentts.sh

# Inside container
python gen_verse_devotion_qwentts.py -i input.txt --bgm
```

### Arguments
| Argument | Description | Default |
|----------|-------------|---------|
| `--voice-prompt` | Natural language voice description | "A clear, soothing..." |
| `--prefix` | Filename prefix | None |
| `--bgm` | Enable background music | False |

Output → `output/*.mp3`

## Requirements
- NVIDIA DGX Spark (ARM64 + Blackwell GPU)
- Docker with GPU support
- ~10GB for model weights (auto-downloaded)
