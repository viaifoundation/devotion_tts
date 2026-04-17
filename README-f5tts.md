# F5-TTS for Devotion TTS

F5-TTS — Flow-matching DiT for **zero-shot voice cloning**. No phoneme alignment needed.

## Performance Comparison

| Model | CER (ZH) ↓ | VRAM | Latency | Unique Features |
|-------|------------|------|---------|-----------------| 
| Fun-CosyVoice 3.0 | **0.81** | ~4-6GB | ~150ms | Best accuracy |
| GLM-TTS RL | 0.89 | ~8GB | Variable | GRPO emotion |
| **F5-TTS** | ~1.0 | ~4-6GB | Variable | Simplest pipeline, MIT license |
| Edge TTS | N/A | 0 | ~100ms | Fast/Free |

### F5-TTS Unique Features

1. **Zero-shot cloning** — ~10s reference audio, no training needed
2. **Simplest pipeline** — No phoneme alignment, no duration model
3. **pip installable** — `pip install f5-tts`
4. **MIT license** (code), Apache 2.0 (OpenF5-TTS weights)
5. **Bilingual** — Native Chinese + English support

## Quick Start

### 1. Run on NVIDIA DGX Spark

**Approach A: Base Image**

```bash
# On Host
docker run --gpus all -it --rm \
  -v ~/github:/workspace/github \
  -v ~/.cache:/root/.cache \
  -w /workspace/github/devotion_tts \
  nvcr.io/nvidia/pytorch:25.01-py3-igpu \
  bash

# Inside Container
source scripts/setup_f5tts_spark.sh  # Installs f5-tts (~5 mins)
python gen_verse_devotion_f5tts.py --input sample.txt -d 1
```

### 2. Run on Mac (CPU/MPS)

```bash
pip install f5-tts
python gen_verse_devotion_f5tts.py --input sample.txt -d 1
```

### 3. Generate Audio

```bash
# Basic usage
python gen_verse_devotion_f5tts.py --input sample.txt -d 1

# Custom voices
python gen_verse_devotion_f5tts.py --voices voice1.wav,voice2.wav --input sample.txt

# With BGM
python gen_verse_devotion_f5tts.py --input sample.txt --bgm
```

## CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `--input, -i` | Input text file | stdin |
| `--voices` | Comma-separated voice files | ref_female.wav,ref_male.wav |
| `--ref-text` | Reference text for cloning | Default Chinese text |
| `--no-rotate` | Use first voice only | False |
| `--bgm` | Enable background music | False |
| `--debug, -d` | Debug level (0-2) | 0 |

## References

- [F5-TTS GitHub](https://github.com/SWivid/F5-TTS)
- [F5-TTS Paper](https://arxiv.org/abs/2410.06885)
