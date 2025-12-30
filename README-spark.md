# NVIDIA DGX Spark Guide (CosyVoice & GPT-SoVITS)

This guide details how to run AI audio workflows on the **NVIDIA DGX Spark** developer kit (utilizing the GB10 Grace Blackwell Superchip).

## 1. Why Specific Configuration?

The DGX Spark uses the **ARM64 (aarch64)** CPU architecture combined with NVIDIA GPUs.
*   **Standard x86 images fail**: You must use **ARM64-optimized containers**.
*   **Solution**: We use `nvcr.io/nvidia/pytorch:25.11-py3` which has pre-compiled PyTorch/CUDA for ARM64 and supports GB10.

## 2. Hardware Verification
Run these on your host machine to verify:
```bash
lscpu       # Should show "Architecture: aarch64"
nvidia-smi  # Should show GB10 GPU and CUDA version
```

---

## Workflow A: CosyVoice (TTS)
*Best for: High-quality zero-shot Chinese TTS using built-in voices.*

### Quick Start
```bash
./scripts/run_spark_cosy.sh
```

This script will:
1. Build the ARM64-optimized Docker image (`devotion-cosy-spark`)
2. Mount required directories
3. Drop you into an interactive shell

### Generate Audio
Inside the container:
```bash
python gen_verse_devotion_cosy.py -i input.txt --bgm
```

### Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--input`, `-i` | Input text file | (stdin) |
| `--prefix` | Filename prefix | None |
| `--bgm` | Enable background music | False |
| `--bgm-track` | BGM filename | `AmazingGrace.MP3` |
| `--bgm-volume` | BGM volume (dB) | `-20` |
| `--bgm-intro` | BGM intro delay (ms) | `4000` |
| `--debug`, `-d` | Debug level: 0, 1, 2 | `0` |

> [!TIP]
> Run `python gen_verse_devotion_cosy.py -?` for quick help.

---

## Workflow B: GPT-SoVITS (Voice Cloning)
*Best for: Cloning specific voices from 3-10 second reference audio.*

### Quick Start
```bash
./scripts/run_spark_gptsovits.sh
```

### First-Time Setup (Inside Container)
```bash
python download_models.py
```

### Generate Audio
```bash
python gen_verse_devotion_gptsovits.py \
  -i input.txt \
  --ref-audio assets/ref_audio/ref.wav \
  --ref-text "大家好，这是一个参考音频" \
  --speed 1.0 \
  --bgm
```

> [!TIP]
> See [README-sovits.md](README-sovits.md) for full documentation including reference audio preparation.

---

## Verification

```bash
# Check GPU Hardware
nvidia-smi

# Check PyTorch CUDA
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
```

## Rebuilding Images
If you changed requirements, force a rebuild:
```bash
./scripts/run_spark_cosy.sh --build
./scripts/run_spark_gptsovits.sh --build
```
