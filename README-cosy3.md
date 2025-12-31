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

```bash
# From HuggingFace
pip install -U huggingface_hub
huggingface-cli download FunAudioLLM/Fun-CosyVoice3-0.5B-2512 \
    --local-dir ~/github/CosyVoice/pretrained_models/Fun-CosyVoice3-0.5B

# Or from ModelScope (China)
pip install -U modelscope
modelscope download --model FunAudioLLM/Fun-CosyVoice3-0.5B-2512 \
    --local_dir ~/github/CosyVoice/pretrained_models/Fun-CosyVoice3-0.5B
```

### 3. Install Dependencies

```bash
cd ~/github/devotion_tts
pip install -r requirements-cosy.txt
pip install -r ../CosyVoice/requirements.txt
```

### NVIDIA DGX Spark Setup

**Option 1: Quick Interactive Run**
```bash
./scripts/run_spark_cosy3.sh my_verse.txt assets/ref_audio/speaker.wav
```

**Option 2: Build Custom Docker Image**
```bash
cd ~/github/devotion_tts
docker build -f docker/Dockerfile.spark.cosy3 -t cosy3-spark .
```

**Option 3: Manual Interactive**
```bash
docker run --gpus all -it --rm \
  -v ~/github:/workspace/github \
  -v ~/.cache:/root/.cache \
  -w /workspace/github/devotion_tts \
  nvcr.io/nvidia/pytorch:25.11-py3

# Inside container
apt-get update && apt-get install -y ffmpeg
pip install -r requirements-cosy.txt huggingface_hub

# Download model
huggingface-cli download FunAudioLLM/Fun-CosyVoice3-0.5B-2512 \
    --local-dir /workspace/github/CosyVoice/pretrained_models/Fun-CosyVoice3-0.5B

export PYTHONPATH=$PYTHONPATH:/workspace/github/CosyVoice:/workspace/github/CosyVoice/third_party/Matcha-TTS

python gen_verse_devotion_cosy3.py --input test.txt
```

## Docker Files

| File | Purpose |
|------|---------|
| `docker/Dockerfile.spark.cosy3` | Docker image for DGX Spark |
| `scripts/run_spark_cosy3.sh` | Quick-start run script |
| `setup_cosy3.sh` | One-time setup with model download |

## Usage

### Basic Usage (Without Voice Cloning)

```bash
# Verse Devotion
python gen_verse_devotion_cosy3.py --input my_verse.txt

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

### Audio Quality Issues
- Ensure reference audio is 3-10 seconds of clear speech
- Check that `--ref-text` matches what's spoken in the reference audio
- Try different reference audio samples

## References

- [Fun-CosyVoice 3.0 Paper](https://arxiv.org/pdf/2505.17589)
- [CosyVoice GitHub](https://github.com/FunAudioLLM/CosyVoice)
- [Model on HuggingFace](https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512)
- [Demo Page](https://funaudiollm.github.io/cosyvoice3/)
