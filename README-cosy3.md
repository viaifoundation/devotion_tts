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

#### Step 3: Run in Container

**Option A: Quick Run Script (on host)**
```bash
cd ~/github/devotion_tts
./scripts/run_spark_cosy3.sh my_verse.txt
```

**Option B: Interactive Container (Manual)**
Best for debugging or custom runs.

1. **Launch Container:**
```bash
docker run --gpus all -it --rm \
  -v ~/github:/workspace/github \
  -v ~/.cache:/root/.cache \
  -w /workspace/github/devotion_tts \
  nvcr.io/nvidia/pytorch:25.11-py3 \
  bash
```

2. **Initialize Environment (Important):**
```bash
# Patches CosyVoice & Installs Deps
source scripts/setup_cosy3_spark.sh
```

3. **Run Generation:**
```bash
python gen_verse_devotion_cosy3.py --input sample.txt -d 1
```

## Docker Files

| File | Purpose |
|------|---------|
| `docker/Dockerfile.spark.cosy3` | Docker image for DGX Spark |
| `scripts/run_spark_cosy3.sh` | Quick-start run script |
### 3. Run Generation

**Option A: Quick Start (Auto-setup)**
This runs the setup script every time (installing dependencies takes ~1 min).
```bash
# On Host
./scripts/run_spark_cosy3.sh sample.txt
```

**Option B: Faster Startup (Build Image)**
Build the image once to bake in dependencies.
```bash
# 1. Build Image (Run once)
docker build -t viaifoundation/cosy3-spark -f docker/Dockerfile.spark.cosy3 .

# 2. Run (Instant start)
# Edit scripts/run_spark_cosy3.sh to use IMAGE="viaifoundation/cosy3-spark"
./scripts/run_spark_cosy3.sh sample.txt
```

> [!IMPORTANT]
> **Audio Quality Note:** We force **FP32** inference on Spark DGX to prevent static noise issues caused by FP16 instability on some GPU architectures. This is handled automatically in the scripts.

# Daily Bread
python gen_bread_audio_cosy3.py --input my_bread.txt

# Prayer
python gen_prayer_cosy3.py --input my_prayer.txt
```

### Voice Cloning

Clone a specific voice using 3-10 seconds of reference audio:

```bash
python gen_verse_devotion_cosy3.py \
    --input my_verse.txt \
    --ref-audio assets/ref_audio/speaker.wav \
    --ref-text "这是参考音频中说的话"
```

**Reference Audio Requirements:**
- Duration: 3-10 seconds
- Format: WAV (16-bit, mono recommended)
- Quality: Clear speech, no background noise
- Content: Should match the language of your output text

### Voice Rotation (Without Personal Cloning)

Fun-CosyVoice 3.0 doesn't have built-in SFT voices like CosyVoice-300M. However, you can rotate through **preset reference audio files**:

**Default preset voices (already configured):**
- `ref_female.m4a` - Female voice
- `ref_male.m4a` - Male voice

**Run with rotation:**
```bash
python gen_verse_devotion_cosy3.py --input my_text.txt --rotate
```

**Preset voice configuration** (in script):
```python
PRESET_VOICES = [
    {"audio": "assets/ref_audio/ref_female.m4a", "text": "然而，靠着爱我们的主，在这一切的事上已经得胜有余了。"},
    {"audio": "assets/ref_audio/ref_male.m4a", "text": "然而，靠着爱我们的主，在这一切的事上已经得胜有余了。"},
    # Add more voices as needed...
]
```

> **Note:** To add more voices, just record 3-10 seconds of clear speech and add to `assets/ref_audio/`.

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
| `--ref-audio` | Reference audio for voice cloning | `ref_female.m4a` |
| `--ref-text` | Text spoken in reference audio | (preset) |
| `--rotate` | Rotate between ref_female.m4a and ref_male.m4a | False |
| `--prefix` | Output filename prefix | (from text) |
| `--bgm` | Enable background music | False |
| `--bgm-track` | BGM filename | `AmazingGrace.MP3` |
| `--bgm-volume` | BGM volume in dB | -20 |
| `--bgm-intro` | BGM intro delay in ms | 4000 |
| `--debug`, `-d` | Debug level (0-2) | 0 |

**Quick Help:** Run `python gen_verse_devotion_cosy3.py -?` for help.

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
