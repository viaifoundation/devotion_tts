# Devotion Audio TTS – Qwen API Edition

Uses Alibaba's **Dashscope API** for cloud-based Qwen TTS synthesis.

> [!NOTE]
> For **local GPU inference** on DGX Spark, see [README-spark.md](README-spark.md) → Workflow C (Qwen-TTS Local).

## Files
- `gen_bread_audio_qwen.py` → Daily Bread (2 voices)
- `gen_verse_devotion_qwen.py` → Verse + Devotion + Prayer (5 voices)
- `gen_prayer_qwen.py` → Prayer audio
- `requirements-qwen.txt` → Dependencies

## Setup
```bash
# Install dependencies
pip install -r requirements-qwen.txt

# Set API key
export DASHSCOPE_API_KEY="your-key-here"
```

## Daily Use
```bash
python gen_bread_audio_qwen.py
python gen_verse_devotion_qwen.py --speed 1.2
```

### Arguments
| Argument | Description | Default |
|----------|-------------|---------|
| `--speed` | Speed adjustment (e.g. `1.2` or `+20%`) | `1.0` |
| `--bgm` | Enable background music | False |
| `--input`, `-i` | Input text file | stdin |

Output → `output/*.mp3`
