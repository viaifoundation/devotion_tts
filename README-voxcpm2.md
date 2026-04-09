# VoxCPM2 for Devotion TTS

VoxCPM2 — Tokenizer-free, diffusion autoregressive TTS (2B parameters, 30 languages, 48kHz output).

## Performance Comparison

| Model | CER (ZH) ↓ | VRAM | Output | Use Case |
|-------|------------|------|--------|----------|
| Fun-CosyVoice 3.0 | **0.81** | ~4-6GB | 24kHz | Best accuracy |
| GLM-TTS RL | 0.89 | ~8GB | 24kHz | Emotion control |
| **VoxCPM2** | SOTA-level | ~8GB | **48kHz** | Voice Design + Cloning |
| Index-TTS2 | 1.03 | ~8GB | 24kHz | Duration + Emotion |
| Edge TTS | N/A | 0 | 24kHz | Fast/Free |

VoxCPM2 excels at **Voice Design** (create voices from text descriptions), **48kHz studio-quality output**, and **30-language multilingual** support without language tags.

## Supported Modes

| Mode | Description | Ref Audio Required? |
|------|-------------|---------------------|
| `clone` | Clone voice from short reference clip | ✅ Yes |
| `design` | Create voice from text description | ❌ No |
| `ultimate` | Highest fidelity cloning (ref audio + transcript) | ✅ Yes |

## Voice Design Presets

| Preset | Description |
|--------|-------------|
| `gentle_female` | A young woman, gentle and sweet voice, warm tone |
| `mature_male` | A middle-aged man, deep and steady voice, calm pace |
| `bright_female` | A young woman, bright and lively voice, slightly fast pace |
| `warm_male` | A young man, warm and clear voice, natural pace |
| `elder_male` | An elderly man, wise and gentle voice, slow pace |
| `cheerful_female` | A young woman, cheerful and energetic voice, upbeat tone |

Custom descriptions can also be passed directly (e.g., `--design "(A warm narrator, male, calm)"`)

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
source scripts/setup_voxcpm2_spark.sh  # Installs voxcpm, downloads model (~10 mins)
python gen_verse_devotion_voxcpm2.py --input sample.txt -d 1
```

### 2. Generate Audio

```bash
# Voice cloning (default, rotate male/female ref audio)
python gen_verse_devotion_voxcpm2.py --input sample.txt -d 1

# Voice design (no reference audio needed!)
python gen_verse_devotion_voxcpm2.py --input sample.txt --mode design --design gentle_female -d 1

# Voice design rotation (alternate 2 voices)
python gen_verse_devotion_voxcpm2.py --input sample.txt --mode design --designs "gentle_female,mature_male" -d 1

# Custom design description
python gen_verse_devotion_voxcpm2.py --input sample.txt --mode design \
  --design "(A warm narrator, male, calm and authoritative)"

# Ultimate cloning (highest fidelity)
python gen_verse_devotion_voxcpm2.py --input sample.txt --mode ultimate \
  --voices assets/ref_audio/ref_male.wav \
  --ref-text "然而，靠着爱我们的主，在这一切的事上已经得胜有余了。" -d 1

# With background music
python gen_verse_devotion_voxcpm2.py --input sample.txt --bgm --bgm-track AmazingGrace.MP3
```

## CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `--input, -i` | Input text file | stdin |
| `--mode` | TTS mode: clone, design, ultimate | clone |
| `--voices` | Comma-separated voice files | ref_female.wav,ref_male.wav |
| `--ref-text` | Reference text for voices | 然而，靠着... |
| `--design` | Voice design description or preset | None |
| `--designs` | Comma-separated designs for rotation | None |
| `--no-rotate` | Use first voice/design only | False |
| `--cfg` | CFG guidance value | 2.0 |
| `--steps` | Diffusion inference timesteps | 10 |
| `--bgm` | Enable background music | False |
| `--debug, -d` | Debug level (0-2) | 0 |

## Model Details

| Property | Value |
|----------|-------|
| Parameters | 2B |
| Languages | 30 (+ 9 Chinese dialects) |
| Output Quality | 48kHz |
| Architecture | Diffusion Autoregressive (MiniCPM-4 backbone) |
| Training Data | 2M+ hours multilingual speech |
| License | Apache-2.0 |
| HuggingFace | [openbmb/VoxCPM2](https://huggingface.co/openbmb/VoxCPM2) |

## References

- [VoxCPM GitHub](https://github.com/OpenBMB/VoxCPM)
- [VoxCPM2 HuggingFace](https://huggingface.co/openbmb/VoxCPM2)
- [VoxCPM Documentation](https://voxcpm.readthedocs.io/en/latest/)
- [VoxCPM Demo](https://huggingface.co/spaces/OpenBMB/VoxCPM-Demo)
