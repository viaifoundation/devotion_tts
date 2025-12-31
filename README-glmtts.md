# GLM-TTS for Devotion TTS

GLM-TTS with Reinforcement Learning (GLM-TTS RL) - Zero-shot voice cloning with RL-enhanced emotion control.

## Performance Comparison

| Model | CER (ZH) ↓ | VRAM | Latency | Use Case |
|-------|------------|------|---------|----------|
| Fun-CosyVoice 3.0 | **0.81** | ~4-6GB | ~150ms | Best accuracy |
| **GLM-TTS RL** | 0.89 | ~8GB | Variable | Emotion control |
| GPT-SoVITS | N/A | ~6GB | ~300ms | Custom training |
| Edge TTS | N/A | 0 | ~100ms | Fast/Free |
| Gemini TTS | N/A | 0 (API) | ~200ms | Google API |

GLM-TTS excels at **emotional expressiveness** via GRPO reinforcement learning.


## Quick Start

### 1. Run on NVIDIA DGX Spark

**Approach A: Base Image (First-time Setup)**

```bash
# On Host
docker run --gpus all -it --rm \
  -v ~/github:/workspace/github \
  -v ~/.cache:/root/.cache \
  -w /workspace/github/devotion_tts \
  nvcr.io/nvidia/pytorch:25.01-py3-igpu \
  bash

# Inside Container
source scripts/setup_glmtts_spark.sh  # Clones repo, installs deps, downloads models (~10 mins)
python gen_verse_devotion_glmtts.py --input sample.txt -d 1
```

**Approach B: Custom Image (Recommended for Repeated Use)**

```bash
# On Host - Build image (includes model download)
docker build -t viaifoundation/glmtts-spark:latest -f docker/Dockerfile.spark.glmtts .

# Run container
docker run --gpus all -it --rm \
  -v ~/github:/workspace/github \
  -v ~/.cache:/root/.cache \
  -w /workspace/github/devotion_tts \
  viaifoundation/glmtts-spark:latest \
  bash
```

### 2. Generate Audio

```bash
# Basic usage (voice rotation enabled by default)
python gen_verse_devotion_glmtts.py --input sample.txt -d 1

# Custom voices
python gen_verse_devotion_glmtts.py --voices voice1.wav,voice2.wav --input sample.txt

# With background music
python gen_verse_devotion_glmtts.py --input sample.txt --bgm --bgm-track AmazingGrace.MP3
```

## CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `--input, -i` | Input text file | stdin |
| `--voices` | Comma-separated voice files | ref_female.wav,ref_male.wav |
| `--ref-text` | Reference text for voices | 然而，靠着... |
| `--no-rotate` | Use first voice only | False |
| `--bgm` | Enable background music | False |
| `--debug, -d` | Debug level (0-2) | 0 |

## References

- [GLM-TTS GitHub](https://github.com/zai-org/GLM-TTS)
- [GLM-TTS HuggingFace](https://huggingface.co/zai-org/GLM-TTS)
- [Architecture Analysis](docs/arch.md)
