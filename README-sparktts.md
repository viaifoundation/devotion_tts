# Spark-TTS for Devotion TTS

Spark-TTS — LLM-based (Qwen2.5) BiCodec TTS with **controllable pitch, speed, and gender**.

> ⚠️ Not to be confused with `gen_*_spark.py` (DGX Spark TTS via API). This is `gen_*_sparktts.py`.

## Performance Comparison

| Model | CER (ZH) ↓ | VRAM | Unique Features |
|-------|------------|------|-----------------|
| Fun-CosyVoice 3.0 | **0.81** | ~4-6GB | Best accuracy |
| **Spark-TTS** | ~1.0 | ~4-8GB | Pitch/Speed/Gender control, BiCodec |
| Edge TTS | N/A | 0 | Fast/Free |

### Spark-TTS Unique Features

1. **Controllable** — Fine-grained pitch, speed, gender via chain-of-thought
2. **Zero-shot cloning** — ~5s reference audio
3. **Bilingual** — Native Chinese + English, cross-lingual code-switching
4. **Efficient** — 0.5B model, no external vocoder needed
5. **Apache 2.0** license

## Quick Start

### 1. Run on NVIDIA DGX Spark

```bash
docker run --gpus all -it --rm \
  -v ~/github:/workspace/github \
  -v ~/.cache:/root/.cache \
  -w /workspace/github/devotion_tts \
  nvcr.io/nvidia/pytorch:25.01-py3-igpu \
  bash

# Inside Container
source scripts/setup_sparktts_spark.sh
python gen_verse_devotion_sparktts.py --input sample.txt -d 1
```

### 2. Generate Audio

```bash
# Voice cloning (default)
python gen_verse_devotion_sparktts.py --input sample.txt -d 1

# Controllable mode (no reference audio needed)
python gen_verse_devotion_sparktts.py --input sample.txt --gender female --pitch high --speed moderate

# Custom voices
python gen_verse_devotion_sparktts.py --voices voice1.wav,voice2.wav --input sample.txt
```

## CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `--input, -i` | Input text file | stdin |
| `--voices` | Comma-separated voice files | ref_female.wav,ref_male.wav |
| `--gender` | Gender: male, female | None (clone mode) |
| `--pitch` | Pitch: very_low, low, moderate, high, very_high | moderate |
| `--speed` | Speed: very_slow, slow, moderate, fast, very_fast | moderate |
| `--model-dir` | Model directory | ../Spark-TTS/pretrained_models/Spark-TTS-0.5B |
| `--bgm` | Enable background music | False |
| `--debug, -d` | Debug level (0-2) | 0 |

## References

- [Spark-TTS GitHub](https://github.com/SparkAudio/Spark-TTS)
- [Spark-TTS Paper](https://arxiv.org/abs/2503.01710)
