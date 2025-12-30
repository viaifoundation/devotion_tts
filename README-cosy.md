# Devotion Audio TTS – CosyVoice Edition (Local Offline)

**Developed by:** FunAudioLLM Team (SpeechLab@Tongyi, Alibaba Group).
It is a state-of-the-art offline Chinese TTS model comparable to GPT-4o voice capabilities.

Uses Alibaba's **CosyVoice-300M** (Instruct) model.
These scripts run **locally** on your machine.

## Key Features
- **Offline**: No internet required after initial model download.
- **High Quality**: Neural quality comparable to ElevenLabs/OpenAI.
- **Instructable**: Supports various voice timbres.

## Files
- `gen_bread_audio_cosy.py`: Daily Bread (2 voices)
- `gen_verse_devotion_cosy.py`: Verse + Devotion + Prayer (Multi-voice)
- `requirements-cosy.txt`: Dependencies

## Setup

### 1. Prerequisites
- **Python 3.10+** (Recommended: 3.12)
- **Disk Space**: ~5GB for model weights.
- **Hardware**:
    - **Mac**: M-series (MPS) recommended (Verified on MacBook Pro M5).
    - **Linux**: NVIDIA GPU (CUDA 11.8+) recommended.

### 2. Environment & Installation

#### A. Directory Structure
Since `CosyVoice` is not a pip package, you must clone it as a "sibling" repository.
```
~/github/
  ├── devotion_tts/  (This repo)
  └── CosyVoice/           (Clone this)
```

#### B. Installation Steps

**Step 1: Clone CosyVoice (Recursive)**
```bash
cd ~/github
git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git
# If you already cloned it without --recursive:
# cd CosyVoice && git submodule update --init --recursive
```

**Step 2: Install Dependencies**

**macOS:**
```bash
cd ~/github/devotion_tts

# Create/Activate environment
pyenv virtualenv 3.12.12 tts-venv-cosy
pyenv activate tts-venv-cosy

# Install requirement for this project + CosyVoice dependencies
pip install -r requirements-cosy.txt
pip install -r ../CosyVoice/requirements.txt
```

**Linux (System76 Pop!_OS / Ubuntu with NVIDIA):**
Ensure you have NVIDIA drivers and CUDA toolkit installed.
```bash
# 1. System Dependencies (Pop!_OS/Ubuntu)
sudo apt-get update && sudo apt-get install -y git ffmpeg build-essential

# 2. Python Environment
pyenv virtualenv 3.12.12 tts-venv-cosy
pyenv activate tts-venv-cosy

# 3. Install Torch with CUDA support (Important for speed)
# Check https://pytorch.org/get-started/locally/ for your CUDA version
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121

# 4. Install Project Requirements
cd ~/github/devotion_tts
pip install -r requirements-cosy.txt
pip install -r ../CosyVoice/requirements.txt
```

**NVIDIA DGX / NGX Spark (Data Center / Appliance):**
If running on a DGX appliance or Spark cluster node:
1.  **CUDA**: Likely pre-installed (e.g., CUDA 12.x or 13.x). Use `nvidia-smi` to check.
2.  **Environment**:
    ```bash
    # Ensure you are on a GPU node
    nvidia-smi  # Should list A100/H100 GPUs
    
    # Create Environment (standard python venv or conda)
    python3 -m venv tts-env
    source tts-env/bin/activate
    
    # Install dependencies (same as Linux above)
    pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
    pip install -r requirements-cosy.txt
    pip install -r ../CosyVoice/requirements.txt
    ```
3.  **Running**:
    ```bash
    # If multiple GPUs, select one (e.g., GPU 0)
**NVIDIA DGX Spark Manual Run (Interactive):**
Faster approach using the pre-built NVIDIA image directly. Ensure your repos are at `~/github/CosyVoice` and `~/github/devotion_tts`.

1.  **Launch Container**:
    Mounts your code into `/workspace` and caches models to your host `~/.cache` so you don't re-download them.
    ```bash
    docker run --gpus all -it --rm \
      -v ~/github:/workspace/github \
      -v ~/.cache/modelscope:/root/.cache/modelscope \
      -w /workspace/github/devotion_audio_tts \
      nvcr.io/nvidia/pytorch:24.01-py3
    ```

2.  **Setup Environment (Inside Container)**:
    Only needed the first time you start the container.
    ```bash
    # 1. Install System Deps
    apt-get update && apt-get install -y ffmpeg

    # grep -v "torch" requirements-cosy.txt | pip install -r /dev/stdin
    # 2.A Install CosyVoice repo deps (Fixing onnxruntime for ARM64)
    # onnxruntime-gpu is not on PyPI for aarch64, but onnxruntime (CPU) works fine for frontend
    sed 's/onnxruntime-gpu/onnxruntime/g' ../CosyVoice/requirements.txt | grep -v "torch" | pip install -r /dev/stdin

    # 2.B Install Devotion TTS deps
    grep -v "torch" requirements-cosy.txt | pip install -r /dev/stdin
    
    # 3. Setup Paths
    export PYTHONPATH=$PYTHONPATH:/workspace/github/CosyVoice:/workspace/github/CosyVoice/third_party/Matcha-TTS
    ```

3.  **Run**:
    ```bash
    python gen_verse_devotion_cosy.py
    ```

### 3. Troubleshooting Installation

**If you see `Failed to build grpcio` errors:**
The pinned version of grpcio in CosyVoice is too old for Python 3.12 on Mac. Run this to unpin it and allow a newer version:

```bash
# Modify CosyVoice requirements to allow newer grpcio
sed -i '' 's/grpcio==1.57.0/grpcio/g' ../CosyVoice/requirements.txt
sed -i '' 's/grpcio-tools==1.57.0/grpcio-tools/g' ../CosyVoice/requirements.txt

# Try installing again
pip install -r ../CosyVoice/requirements.txt
```

**Note**: If `requirements.txt` in CosyVoice fails on some specific versions, focus on installing `torch`, `torchaudio`, `modelscope`, `hyperpyyaml`, `onnxruntime` manually.

## Usage

Run the scripts:
```bash
python gen_verse_devotion_cosy.py
# or
python gen_verse_devotion_cosy.py --speed 1.0
# or
python gen_bread_audio_cosy.py
```

### Arguments (CosyVoice Scripts)
- `--speed`: Speed factor. **Note:** Currently a placeholder (not supported by CosyVoice engine yet). Default `1.0`.
- `--bgm`: Enable background music.

*First run will download the model automatically via ModelScope.*

## Voices
Scripts use built-in SFT speaker names:
- `中文女` (Chinese Female)
- `中文男` (Chinese Male)
- `英文女` (English Female)
- `英文男` (English Male)
