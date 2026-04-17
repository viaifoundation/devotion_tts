# StepAudio TTS-3B for Devotion TTS

StepAudio TTS-3B — Dual-codebook TTS with **emotion, dialect, and speed control** by StepFun.

## Performance Comparison

| Model | CER (ZH) ↓ | VRAM | Unique Features |
|-------|------------|------|-----------------|
| Fun-CosyVoice 3.0 | **0.81** | ~4-6GB | Best accuracy |
| **StepAudio TTS-3B** | ~0.9 | ~8-12GB | Emotion + Dialect + Voice Cloning |
| GLM-TTS RL | 0.89 | ~8GB | GRPO emotion |
| Edge TTS | N/A | 0 | Fast/Free |

### StepAudio Unique Features

1. **Emotion control** — Happy, sad, angry, gentle, serious
2. **Dialect support** — Cantonese, Sichuanese, and more
3. **Speed control** — Natural language instructions
4. **Voice cloning** — Speaker dict with reference audio
5. **Rap & Singing** — Unique vocal synthesis modes
6. **Apache 2.0** (code), custom license (weights)

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
source scripts/setup_stepaudio_spark.sh
python gen_verse_devotion_stepaudio.py --input sample.txt -d 1
```

### 2. Generate Audio

```bash
# Voice cloning (default)
python gen_verse_devotion_stepaudio.py --input sample.txt -d 1

# With emotion
python gen_verse_devotion_stepaudio.py --input sample.txt --emotion gentle

# With Cantonese dialect
python gen_verse_devotion_stepaudio.py --input sample.txt --dialect cantonese

# Speed control
python gen_verse_devotion_stepaudio.py --input sample.txt --speed "speak slowly and gently"
```

## CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `--input, -i` | Input text file | stdin |
| `--voices` | Comma-separated voice files | ref_female.wav,ref_male.wav |
| `--emotion` | Emotion: happy, sad, angry, gentle, serious | None |
| `--dialect` | Dialect: cantonese, sichuanese | None |
| `--speed` | Speed instruction (natural language) | None |
| `--model-path` | Path to downloaded models | Auto-detect |
| `--bgm` | Enable background music | False |
| `--debug, -d` | Debug level (0-2) | 0 |

## References

- [Step-Audio GitHub](https://github.com/stepfun-ai/Step-Audio)
- [Step-Audio Paper](https://arxiv.org/abs/2502.11946)
- [Step-Audio TTS-3B on HuggingFace](https://huggingface.co/stepfun-ai/Step-Audio-TTS-3B)
