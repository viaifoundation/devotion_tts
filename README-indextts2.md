# Index-TTS2 for Devotion TTS

Index-TTS2 - Zero-shot voice cloning with **duration control** and **emotion disentanglement**.

## Performance Comparison

| Model | CER (ZH) ↓ | VRAM | Latency | Unique Features |
|-------|------------|------|---------|-----------------|
| Fun-CosyVoice 3.0 | **0.81** | ~4-6GB | ~150ms | Best accuracy |
| GLM-TTS RL | 0.89 | ~8GB | Variable | GRPO emotion |
| **Index-TTS2** | 1.03 | ~8GB | Variable | Duration + Emotion control |
| Edge TTS | N/A | 0 | ~100ms | Fast/Free |
| Gemini TTS | N/A | 0 (API) | ~200ms | Google API |

### Index-TTS2 Unique Features

1. **Duration Control** – Precise token-count for video dubbing sync
2. **Emotion Disentanglement** – Separate timbre from emotion
3. **Text-Based Emotion** – Natural language prompts via Qwen3

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
source scripts/setup_indextts2_spark.sh  # Clones repo, installs deps (~10 mins)
python gen_verse_devotion_indextts2.py --input sample.txt -d 1
```

**Approach B: Custom Image**

```bash
# Build (includes model download)
docker build -t viaifoundation/indextts2-spark:latest -f docker/Dockerfile.spark.indextts2 .

# Run
docker run --gpus all -it --rm \
  -v ~/github:/workspace/github \
  -w /workspace/github/devotion_tts \
  viaifoundation/indextts2-spark:latest bash
```

### 2. Generate Audio

```bash
# Basic usage
python gen_verse_devotion_indextts2.py --input sample.txt -d 1

# With emotion control
python gen_verse_devotion_indextts2.py --input sample.txt --emotion happy

# Custom voices
python gen_verse_devotion_indextts2.py --voices voice1.wav,voice2.wav --input sample.txt
```

## CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `--input, -i` | Input text file | stdin |
| `--voices` | Comma-separated voice files | ref_female.wav,ref_male.wav |
| `--emotion` | Emotion prompt (happy, sad, angry) | None |
| `--no-rotate` | Use first voice only | False |
| `--bgm` | Enable background music | False |
| `--debug, -d` | Debug level (0-2) | 0 |

## References

- [Index-TTS2 GitHub](https://github.com/index-tts/index-tts)
- [Index-TTS2 Paper](https://index-tts.github.io/index-tts2.github.io/)
- [Architecture Analysis](docs/arch.md)
