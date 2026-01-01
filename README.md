# Devotion TTS



## Overview

This project provides Python scripts to generate high-quality audio for:
- Daily Devotionals
- Verse of the Day (VOTD)
- "Bread" Audio (Daily portion)
- **Prayer Audio**

It supports automatic filename generation based on the Bible verse and date found in the text.

## Supported TTS Engines

### Performance Comparison

| Engine | CER (ZH) ↓ | VRAM | Type | Best For |
|--------|------------|------|------|----------|
| **Fun-CosyVoice 3.0** | **0.81** ✅ | ~4-6GB | Zero-shot | Best accuracy (SOTA) |
| GLM-TTS RL | 0.89 | ~8GB | Zero-shot | GRPO emotion |
| Index-TTS2 | 1.03 | ~8GB | Zero-shot | Duration + Emotion control |
| GPT-SoVITS | N/A | ~6GB | Fine-tune | Custom voice training |
| Qwen TTS | N/A | ~4GB | Neural | Local multi-voice |
| Vibe | N/A | ~4GB | Voice | Voice cloning |
| Volc (Volcengine) | N/A | API | Cloud | ByteDance API |
| Edge TTS | N/A | 0 | Cloud | Fast/Free |
| Gemini TTS | N/A | API | Cloud | Google API |

### Quick Reference

| Provider | Script Prefix | Setup | Documentation |
| :--- | :--- | :--- | :--- |
| **Fun-CosyVoice 3.0** | `gen_*_cosy3.py` | DGX Spark / Docker | [README-cosy3.md](README-cosy3.md) |
| **GLM-TTS** | `gen_*_glmtts.py` | DGX Spark / Docker | [README-glmtts.md](README-glmtts.md) |
| **Index-TTS2** | `gen_*_indextts2.py` | DGX Spark / Docker | [README-indextts2.md](README-indextts2.md) |
| **GPT-SoVITS** | `gen_*_gptsovits.py` | DGX Spark / Docker | [README-gptsovits.md](README-gptsovits.md) |
| **Qwen TTS** | `gen_*_qwen.py` | `DASHSCOPE_API_KEY` | [README-qwen.md](README-qwen.md) |
| **Vibe** | `gen_*_vibe.py` | Local | [README-vibe.md](README-vibe.md) |
| **Volc** | `gen_*_volc.py` | Volcengine API | [README-volc.md](README-volc.md) |
| **Edge TTS** | `gen_*_edge.py` | `pip install edge-tts` | [README-edge.md](README-edge.md) |
| **Gemini TTS** | `gen_*_gemini.py` | `gcloud auth` | [README-gemini.md](README-gemini.md) |
| **CosyVoice (Mac)** | `gen_*_cosy.py` | Offline (CPU/MPS) | [README-cosy.md](README-cosy.md) |


## Environment Setup (Recommended)

It is highly recommended to use `pyenv` to manage Python versions and virtual environments to avoid conflicts.

### A. macOS Setup Guide

1.  **Install Prerequisites (Pyenv & FFmpeg)**:
    ```bash
    brew update
    brew install pyenv pyenv-virtualenv ffmpeg
    ```
    *Follow the instructions printed in your terminal to add pyenv to your shell profile (e.g., `~/.zshrc` or `~/.bash_profile`).*

2.  **Install Python 3.12.12**:
    ```bash
    pyenv install 3.12.12
    ```

3.  **Create & Activate Virtual Environment**:
    ```bash
    # Create virtual env named "tts-venv-qwen"
    pyenv virtualenv 3.12.12 tts-venv-qwen
    
    # Activate it
    pyenv activate tts-venv-qwen
    
    # (Optional) Auto-activate when entering folder
    pyenv local tts-venv-qwen
    ```

4.  **Confirm Activation**:
    You should see `(tts-venv-qwen)` in your prompt.

### B. Linux Setup Guide

1.  **Install Prerequisites**:
    ```bash
    # Install build dependencies & ffmpeg
    sudo apt-get update; sudo apt-get install make build-essential libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
    libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev ffmpeg
    ```

2.  **Install Pyenv**:
    ```bash
    curl https://pyenv.run | bash
    ```
    *Follow the on-screen instructions to add pyenv to your shell configuration.*

3.  **Install Python & Create Environment**:
    ```bash
    # Install Python 3.12.12
    pyenv install 3.12.12
    
    # Create virtual env
    pyenv virtualenv 3.12.12 tts-venv-qwen
    
    # Activate
    pyenv activate tts-venv-qwen
    ```

### C. Helpful Commands

```bash
# Deactivate virtual env
pyenv deactivate

# List all versions
pyenv versions

# List virtual envs
pyenv virtualenvs

# Delete virtual env
pyenv uninstall tts-venv-qwen

# Check current python path
which python
```

## Quick Start

### 1. Installation

Clone the repo and install dependencies:

```bash
git clone https://github.com/viaifoundation/devotion_tts.git
cd devotion_tts
# Install core dependencies (includes Edge TTS & Google)
pip install -r requirements.txt

# OR install provider-specific requirements as needed:
# pip install -r requirements-qwen.txt
# pip install -r requirements-cosy.txt
# pip install -r requirements-volc.txt
# pip install -r requirements-vibe.txt

```

### 2. Generate Verse of the Day (VOTD)

Choose your preferred provider script (e.g., Edge TTS):

1.  Open `gen_verse_devotion_edge.py`
2.  Update the `TEXT` variable with your devotional content.
3.  Run the script:

```bash
python gen_verse_devotion_edge.py --speed +10%
```

### Arguments
| Argument | Description | Default |
|----------|-------------|---------|
| `--input`, `-i` | Input text file | (stdin) |
| `--prefix` | Filename prefix | None |
| `--speed` | Speed factor (e.g. `+10%`, `1.1`) | `+0%` |
| `--bgm` | Enable background music | False |

The audio will be generated in your `~/Downloads` folder with a filename like:
`VOTD_John-3-16_2025-12-09_edge.mp3`

### 3. Usage for Other Scripts

- **Daily Devotion**: `gen_devotion_audio_edge.py`
- **Bread Audio**: `gen_bread_audio_edge.py`
- **Prayer Audio**: `gen_prayer_edge.py`

## Project Utilities

- `filename_parser.py`: Handles dynamic parsing of dates and verses to generate consistent filenames.
- `bible_parser.py`: Normalizes Chinese Bible references for better TTS pronunciation (e.g., "3:16" -> "3章16节").
- `text_cleaner.py`: Formats text, adding ensuring spacing around "God" (神).

## Standalone Utilities

### Background Music Mixer (`mix_bgm.py`)
A robust CLI tool to mix background music with any existing speech audio file.

**Usage:**
```bash
python mix_bgm.py --input speech.mp3 [OPTIONS]
```

**Parameters & Defaults:**
| Argument | Description | Default Value |
| :--- | :--- | :--- |
| `--input`, `-i` | Input speech file (Required) | N/A |
| `--bgm-track` | Specific BGM filename in `assets/bgm` | `AmazingGrace.mp3` |
| `--bgm-volume` | Volume adjustment for BGM (dB) | `-15` |
| `--bgm-intro` | Delay before speech starts (ms) | `5000` |
| `--bgm-tail` | Delay after speech ends (fades out) (ms) | `4000` |

**Example:**
```bash
python mix_bgm.py --input output/my_audio.mp3 --bgm-track OHolyNight.mp3 --bgm-volume -10
```

## Requirements

Global requirements are listed in `requirements.txt`. Specific providers may have additional needs:
- **Edge**: `requirements-edge.txt`
- **Gemini**: `requirements-gemini.txt`
- **Qwen**: `requirements-qwen.txt`
- **CosyVoice**: `requirements-cosy.txt`



This project is licensed under a custom **Non-Commercial / Proprietary** license.

*   ✅ **Allowed:** Personal, Educational, and Non-Profit use.
*   ❌ **Prohibited:** Commercial use without written permission.
*   ℹ️ **Requirement:** You must provide clear credit to **VI AI Foundation**.

See the [LICENSE](LICENSE) file for full details.
