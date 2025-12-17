# NVIDIA DGX Spark (GB10) CosyVoice Guide

This guide details how to run CosyVoice on the **NVIDIA DGX Spark** developer kit (utilizing the GB10 Grace Blackwell Superchip).

## 1. Why Specific Configuration?

The DGX Spark uses the **ARM64 (aarch64)** CPU architecture combined with NVIDIA GPUs.
*   **Standard Python/Ubuntu images failure**: They often install CPU-only PyTorch for ARM64, or lack the necessary CUDA libraries.
*   **`nvcr.io` Solution**: The official NVIDIA container (`nvcr.io/nvidia/pytorch:24.01-py3`) comes **pre-compiled** with PyTorch + CUDA + cuDNN optimized specifically for this architecture. This is the only reliable way to get GPU acceleration.

## 2. Hardware Verification

Before running, verify your system sees the hardware correctly.

### Check CPU Architecture
Run this on your host machine:
```bash
lscpu
# Look for "Architecture: aarch64"
```

### Check GPU Status
Run this to see your GB10 GPU:
```bash
nvidia-smi
# You should see your GPU listed with Driver Version and CUDA Version.
```

## 3. Docker Configuration

We use an interactive Docker container to run the scripts.

*   **Base Image**: `nvcr.io/nvidia/pytorch:24.01-py3` (Optimized for ARM64)
*   **GPU Access**: `--gpus all` (Vital! Passes the GPU to the container)
*   **Volume Mounts**:
    *   `-v ~/github:/workspace/github`: Maps your host code to the container so you can edit locally and run inside.
    *   `-v ~/.cache/modelscope:/root/.cache/modelscope`: Persists downloaded models to your host disk (saves 4GB+ redownloads).

## 4. How to Run (Manual Interactive Mode)

### Step 1: Launch Container
Run this from your Spark terminal:

```bash
docker run --gpus all -it --rm \
  -v ~/github:/workspace/github \
  -v ~/.cache/modelscope:/root/.cache/modelscope \
  -w /workspace/github/devotion_tts \
  nvcr.io/nvidia/pytorch:24.01-py3
```

### Step 2: Setup Environment (Inside Container)
*Run these commands once you are inside the container prompt (`root@...`).*

1.  **Install System Dependencies**:
    ```bash
    apt-get update && apt-get install -y ffmpeg
    ```

2.  **Verify/Clone CosyVoice Repo**:
    ```bash
    # Ensure backend repo exists
    ls -d ../CosyVoice
    # If missing: git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git ../CosyVoice
    ```

3.  **Install Python Dependencies**:
    *CRITICAL: We filter out `torch` requirements to protect the pre-installed optimized PyTorch.*
    ```bash
    # 1. Install CosyVoice backend deps (swapping missing ARM64 packages)
    sed 's/onnxruntime-gpu/onnxruntime/g' ../CosyVoice/requirements.txt | grep -v "torch" | pip install -r /dev/stdin

    # 2. Install Project deps
    grep -v "torch" requirements-cosy.txt | pip install -r /dev/stdin
    ```

4.  **Configure Paths**:
    ```bash
    export PYTHONPATH=$PYTHONPATH:/workspace/github/CosyVoice:/workspace/github/CosyVoice/third_party/Matcha-TTS
    ```

### Step 3: Run Generation
Now you can generate audio using the Spark-specific scripts:

```bash
python gen_verse_devotion_spark.py
# Output: [Verse]_[Date]_spark.mp3
```

You should see:
> `Loading CosyVoice-300M-Instruct... [CUDA=True, FP16=True]`

This confirms the GPU is active and running in half-precision mode (2x speed).
