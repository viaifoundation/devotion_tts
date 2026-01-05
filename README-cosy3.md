# Devotion Audio TTS – Fun-CosyVoice 3.0 Edition

**Model:** Fun-CosyVoice 3.0 (0.5B) by FunAudioLLM Team (Alibaba)

This is the **upgraded** version of CosyVoice with significantly better quality through RLHF training.

## Key Improvements over CosyVoice-300M (cosy)

| Feature | CosyVoice-300M (cosy) | Fun-CosyVoice 3.0 (cosy3) |
|---------|----------------------|---------------------------|
| **Parameters** | 300M | 500M |
| **CER (accuracy)** | ~1.45% | **0.81%** (2x better) |
| **Voice Cloning** | Limited | **Zero-shot with 3-10s audio** |
| **Prosody** | SFT | **RLHF-trained** (more natural) |
| **Languages** | 5 | 9+ languages, 18+ dialects |
| **VRAM** | 4-6GB | 8-10GB |

## Key Features

- **🎙️ Zero-Shot Voice Cloning**: Clone any voice with just 3-10 seconds of reference audio
- **🎭 Natural Prosody**: RLHF-trained for human-like intonation
- **🌐 Multilingual**: Chinese, English, Japanese, Korean, Cantonese, and more
- **⚡ Low Latency**: Bi-streaming support with ~150ms latency
- **📊 Best-in-Class Accuracy**: 0.81% CER (ranked #1 in 2025 TTS benchmarks)

## Files

| Script | Purpose |
|--------|---------|
| `gen_verse_devotion_cosy3.py` | Verse + Devotion with voice cloning |
| `gen_bread_audio_cosy3.py` | Daily Bread with voice cloning |
| `gen_prayer_cosy3.py` | Prayer with voice cloning |
| `gen_soh_prayer_cosy3.py` | SOH Prayer with voice cloning |

## Setup

### Prerequisites
- **Python 3.10+** (Recommended: 3.12)
- **Disk Space**: ~10GB for model weights
- **VRAM**: 8-10GB (NVIDIA GPU recommended)
- **DGX Spark**: Fully supported (128GB unified memory)

### 1. Clone CosyVoice Repository

```bash
cd ~/github
git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git
```

### 2. Download Fun-CosyVoice 3.0 Model

**For local Mac/Linux (with virtual environment):**
```bash
pip install -U huggingface_hub
huggingface-cli download FunAudioLLM/Fun-CosyVoice3-0.5B-2512 \
    --local-dir ~/github/CosyVoice/pretrained_models/Fun-CosyVoice3-0.5B
```

**For DGX Spark:** See [NVIDIA DGX Spark Setup](#nvidia-dgx-spark-setup) below.

### 3. Install Dependencies (Local Mac/Linux)

```bash
cd ~/github/devotion_tts
pip install -r requirements-cosy.txt
pip install -r ../CosyVoice/requirements.txt
```

### NVIDIA DGX Spark Setup

> **Note:** If you already have `~/github/CosyVoice` from using CosyVoice v1, **keep it** - the same repo supports all versions (1.0, 2.0, 3.0). Just download the new model.

#### Step 1: Update CosyVoice Repo (on Spark host)
```bash
cd ~/github/CosyVoice
git pull
git submodule update --init --recursive
```

#### Step 2: Download Fun-CosyVoice 3.0 Model

> **Important:** Download to the **host filesystem** so it persists and is shared across containers.

Use a temporary container to download (avoids host pip installation issues):

```bash
docker run --rm \
  -v ~/github:/workspace/github \
  python:3.12-slim \
  bash -c "pip install -q huggingface_hub && \
    python -c \"from huggingface_hub import snapshot_download; \
    snapshot_download('FunAudioLLM/Fun-CosyVoice3-0.5B-2512', \
    local_dir='/workspace/github/CosyVoice/pretrained_models/Fun-CosyVoice3-0.5B')\""

# Verify on host
ls ~/github/CosyVoice/pretrained_models/Fun-CosyVoice3-0.5B/
```

### 3. Run on NVIDIA DGX Spark

There are two ways to run: **Custom Image** (Recommended, fast startup) or **Base Image** (No build needed, slower startup).

#### Approach A: Built Custom Image (Recommended)
Build the image once on the host, then reuse it for instant startup.

**1. Build Image (Host):**
```bash
git pull
docker build -t viaifoundation/cosy3-spark:latest -f docker/Dockerfile.spark.cosy3 .
```

**2. Run Container:**
```bash
docker run --gpus all -it --rm \
  -v ~/github:/workspace/github \
  -v ~/.cache:/root/.cache \
  -w /workspace/github/devotion_tts \
  viaifoundation/cosy3-spark:latest \
  bash
```

**3. Generate Audio (Inside Container):**
```bash
source scripts/setup_cosy3_spark.sh  # Initial patches only
python gen_verse_devotion_cosy3.py --input sample.txt -d 1
```

#### Approach B: Base Image (One-off)
Use the standard NVIDIA image. Downloads/installs dependencies every time.

**1. Run Container:**
```bash
docker run --gpus all -it --rm \
  -v ~/github:/workspace/github \
  -v ~/.cache:/root/.cache \
  -w /workspace/github/devotion_tts \
  nvcr.io/nvidia/pytorch:25.11-py3 \
  bash
```

**2. Setup & Run (Inside Container):**
```bash
source scripts/setup_cosy3_spark.sh  # Installs ALL deps (~2 mins)
python gen_verse_devotion_cosy3.py --input sample.txt -d 1
```

## Quick Start Examples

```bash
# Default (rotate male/female voices)
python gen_verse_devotion_cosy3.py -i input.txt

# Male voice only
python gen_verse_devotion_cosy3.py -i input.txt --voice male

# Female voice only with BGM
python gen_verse_devotion_cosy3.py -i input.txt --voice female --bgm

# Rotate voices with speed adjustment
python gen_verse_devotion_cosy3.py -i input.txt --voice rotate --speed 1.1

# Daily Bread
python gen_bread_audio_cosy3.py -i my_bread.txt --voice male

# Prayer with BGM
python gen_prayer_cosy3.py -i my_prayer.txt --voice female --bgm
```


### Voice Cloning

CosyVoice 3.0 uses **zero-shot voice cloning** with reference audio files.

#### Generate Voice Samples with Edge TTS

Use `gen_voice_samples_edge.py` to create voice samples using Edge TTS:

```bash
# List available voices
python gen_voice_samples_edge.py --list

# Generate default male/female samples
python gen_voice_samples_edge.py

# Generate all 10 Chinese voices
python gen_voice_samples_edge.py --all

# Custom reference text
python gen_voice_samples_edge.py --text "你好，欢迎收听今天的节目。"
```

**Output:** `assets/ref_audio/ref_edge_zh_female_warm.wav`, etc. (16kHz mono WAV)

#### Using Custom Voices

Pass voices via `--voices` (comma-separated list):

```bash
# Using Edge-generated voices
python gen_verse_devotion_cosy3.py \
    --voices assets/ref_audio/ref_edge_zh_female_warm.wav,assets/ref_audio/ref_edge_zh_male_sunshine.wav \
    --input my_verse.txt

# Multiple voices (rotation enabled by default)
python gen_verse_devotion_cosy3.py \
    --voices voice1.wav,voice2.wav,voice3.wav,voice4.wav \
    --input my_verse.txt

# Single voice (no rotation)
python gen_verse_devotion_cosy3.py \
    --voices my_voice.wav \
    --no-rotate \
    --input my_verse.txt
```

**Voice Reference Requirements:**
- Duration: 3-10 seconds
- Format: WAV (16-bit, mono recommended)
- Quality: Clear speech, no background noise
- Content: Should match the language of your output text


### With Background Music

```bash
python gen_verse_devotion_cosy3.py \
    --input my_verse.txt \
    --ref-audio assets/ref_audio/speaker.wav \
    --bgm \
    --bgm-track AmazingGrace.MP3 \
    --bgm-volume -20
```

## Command Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--input`, `-i` | Input text file | (stdin) |
| `--voice` | Voice mode: `male`, `female`, `rotate` | `rotate` |
| `--voices` | Custom comma-separated voice files | (see --voice) |
| `--ref-text` | Reference text for voice cloning | (preset) |
| `--no-rotate` | Disable voice rotation | False |
| `--speed` | Speed factor: `1.0`, `1.2`, `+20%`, `--speed=-10%` | `1.0` |
| `--prefix` | Output filename prefix | (from text) |
| `--bgm` | Enable background music | False |
| `--bgm-track` | BGM filename | `AmazingGrace.MP3` |
| `--bgm-volume` | BGM volume in dB | -20 |
| `--bgm-intro` | BGM intro delay in ms | 4000 |
| `--debug`, `-d` | Debug level (0-2) | 0 |

**Quick Help:** Run `python gen_verse_devotion_cosy3.py -?` or `-h` or `--help`.

## Comparison with Other TTS Engines

| Engine | Quality | Voice Cloning | Offline | Speed |
|--------|---------|---------------|---------|-------|
| **cosy3** | ⭐⭐⭐⭐⭐ | ✅ Zero-shot | ✅ | Fast |
| cosy | ⭐⭐⭐⭐ | ❌ | ✅ | Fast |
| gptsovits | ⭐⭐⭐ | ✅ Fine-tune | ✅ | Medium |
| edge | ⭐⭐⭐ | ❌ | ❌ | Fast |
| qwen | ⭐⭐⭐⭐ | ❌ | ❌ | Medium |

## Troubleshooting

### Model Not Found
```
❌ Error loading Fun-CosyVoice 3.0: [model not found]
```
**Solution:** Ensure you've downloaded the model:
```bash
huggingface-cli download FunAudioLLM/Fun-CosyVoice3-0.5B-2512 \
    --local-dir pretrained_models/Fun-CosyVoice3-0.5B
```

### CUDA Out of Memory
Fun-CosyVoice 3.0 requires ~8-10GB VRAM. If you're running out of memory:
- Close other GPU applications
- Use CPU mode (slower but works): Set `CUDA_VISIBLE_DEVICES=""`
- Use the smaller CosyVoice-300M (`gen_*_cosy.py` scripts)

### Audio Quality Issues (Noise/Static)
If you hear static noise:
1. **Sample Rate Mismatch:** Ensure your reference audio is **16kHz mono WAV**.
    ```bash
    ffmpeg -y -i input.m4a -acodec pcm_s16le -ar 16000 -ac 1 output.wav
    ```
2. **FP16 Instability (Spark/ARM64):** The scripts automatically force **FP32** on Spark to prevent this. 
   - If using custom code, ensure `cosyvoice.fp16 = False`.

## References

- [Fun-CosyVoice 3.0 Paper](https://arxiv.org/pdf/2505.17589)
- [CosyVoice GitHub](https://github.com/FunAudioLLM/CosyVoice)
- [Model on HuggingFace](https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512)
- [Demo Page](https://funaudiollm.github.io/cosyvoice3/)
