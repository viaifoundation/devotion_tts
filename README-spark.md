# NVIDIA DGX Spark Guide (CosyVoice & GPT-SoVITS)

This guide details how to run AI audio workflows on the **NVIDIA DGX Spark** developer kit (utilizing the GB10 Grace Blackwell Superchip).

## 1. Why Specific Configuration?

The DGX Spark uses the **ARM64 (aarch64)** CPU architecture combined with NVIDIA GPUs.
*   **Standard x86 images fail**: You must use **ARM64-optimized containers**.
*   **Solution**: We use `nvcr.io/nvidia/pytorch:24.01-py3` which has pre-compiled PyTorch/CUDA for ARM64.

## 2. Hardware Verification
Run these on your host machine to verify:
```bash
lscpu       # Should show "Architecture: aarch64"
nvidia-smi  # Should show GB10 GPU and CUDA version
```

---

## Workflow A: CosyVoice (Tts)
*Best for: High-quality zero-shot Chinese TTS.*

### 1. Run (Easy Mode)
We provide a helper script to build and run the environment automatically.

```bash
./scripts/run_spark_cosy.sh
```

*This script will:*
1. Build the ARM64-optimized Docker image (`devotion-cosy-spark`).
2. Mount your `~/github/CosyVoice` and `~/github/devotion_tts` directories.
3. Drop you into an interactive shell inside the container.

### 2. Generate
Inside the container, run:

```bash
python gen_verse_devotion_cosy.py
```

---

## Workflow B: GPT-SoVITS (Voice Cloning)
*Best for: Cloning specific characters (e.g., Sun Wukong) and training.*

### 1. Docker Run
Launch the container (mounting your models folder):

```bash
docker run --gpus all -it --rm \
  --net=host \
  --shm-size=16g \
  -v ~/github:/workspace/github \
  -v ~/GPT-SoVITS-Models:/workspace/models \
  -w /workspace/github/GPT-SoVITS \
  nvcr.io/nvidia/pytorch:24.01-py3
```

### 2. Setup (Inside Container)
```bash
# Install ffmpeg
apt-get update && apt-get install -y ffmpeg

# Install Deps
pip install -r requirements.txt
pip install -r extra-req.txt --no-deps

# Start WebUI
python webui.py
```
Open `http://localhost:9874` on your host machine.
