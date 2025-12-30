# System76 Pop!_OS Guide (CosyVoice & GPT-SoVITS)

This guide details how to run AI audio workflows on a **System76 Pop!_OS** laptop with an NVIDIA GPU.

## 1. Why Specific Configuration?
Pop!_OS (x86_64) makes NVIDIA driver management easy. We recommend running **directly on the host** for simplicity and performance.

## 2. Hardware Verification
```bash
nvidia-smi  # Confirm RTX GPU is active
```

---

## Workflow A: CosyVoice (TTS)

### 1. Setup
```bash
# System Deps
sudo apt update && sudo apt install -y git ffmpeg build-essential system76-cuda-latest

# Python Env
python3 -m venv tts-venv-pop
source tts-venv-pop/bin/activate

# Install PyTorch (CUDA 12.1)
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install Deps
cd ~/github/devotion_audio_tts
pip install -r requirements-cosy.txt
pip install -r ../CosyVoice/requirements.txt
```

### 2. Generate
```bash
python gen_verse_devotion_pop.py
python gen_verse_devotion_pop.py --speed 1.0
```

### Arguments
- `--speed`: Speed adjustment placeholder (not supported yet).
- `--bgm`: Enable background music.

---

## Workflow B: GPT-SoVITS (Voice Cloning)

### 1. Setup
```bash
# Environment
conda create -n gptsovits python=3.10
conda activate gptsovits

# Clone
git clone https://github.com/RVC-Boss/GPT-SoVITS
cd GPT-SoVITS

# Install Deps
pip install -r requirements.txt
pip install -r extra-req.txt --no-deps
sudo apt install ffmpeg

# Download Models
# Place v2Pro models in GPT_SoVITS/pretrained_models/
```

### 2. Run
```bash
python webui.py
```
Open `http://localhost:9874`.
