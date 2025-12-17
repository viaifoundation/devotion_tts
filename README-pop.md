# System76 Pop!_OS CosyVoice Guide

This guide details how to run CosyVoice on a **System76 Pop!_OS** laptop with an NVIDIA GPU.

## 1. Why Specific Configuration?
Pop!_OS is an x86_64 Linux distribution that makes NVIDIA drivers exceptionally easy to manage. Unlike the Spark (ARM64), you have two great choices here:
1.  **Host Run (Recommended)**: Run directly on your laptop. Fastest setup, no Docker overhead.
2.  **Docker (Optional)**: If you prefer isolation.

## 2. Hardware Verification

Verify your NVIDIA GPU is active:
```bash
nvidia-smi
# Should show your GPU (e.g., RTX 4060/3070) and CUDA Version (e.g., 12.x).
```

## 3. Host Installation (Recommended)

Run these commands in your terminal.

### Step 1: System Dependencies
Pop!_OS usually comes with drivers, but ensure you have the CUDA toolkit:
```bash
sudo apt update
sudo apt install -y git ffmpeg build-essential system76-cuda-latest
```

### Step 2: Python Environment
Use `pyenv` or `venv` to keep things clean.
```bash
python3 -m venv tts-venv-pop
source tts-venv-pop/bin/activate
```

### Step 3: Install PyTorch (CUDA Version)
*CRITICAL*: Do not just `pip install torch`. You must specify the CUDA index URL.
```bash
# Install PyTorch with CUDA 12.1 support
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### Step 4: Install Project Dependencies
```bash
cd ~/github/devotion_audio_tts
pip install -r requirements-cosy.txt
pip install -r ../CosyVoice/requirements.txt
```

## 4. How to Run

Use the Pop!_OS specific scripts:

```bash
python gen_verse_devotion_pop.py
# Output: [Verse]_[Date]_pop.mp3
```

You should see:
> `Loading CosyVoice-300M-Instruct... [CUDA=True, FP16=True]`

## 5. (Alternative) Docker Run
If you prefer Docker:
```bash
# Use standard NVIDIA PyTorch image (x86_64)
docker run --gpus all -it --rm \
  -v ~/github:/workspace/github \
  -v ~/.cache/modelscope:/root/.cache/modelscope \
  -w /workspace/github/devotion_tts \
  nvcr.io/nvidia/pytorch:24.01-py3  # Works for x86 too
```
*Follow the "Manual Run" steps in README-spark.md inside the container, but skip the 'sed' command for onnxruntime-gpu (since x86 wheels exist).*
