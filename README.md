# Devotion TTS



## Overview

This project provides Python scripts to generate high-quality audio for:
- Daily Devotionals
- Verse of the Day (VOTD)
- "Bread" Audio (Daily portion)
- **Prayer Audio**

It supports automatic filename generation based on the Bible verse and date found in the text.

## Supported Providers

| Provider | Script Prefix | Key Features | Setup |
| :--- | :--- | :--- | :--- |
| **Edge TTS** | `gen_*_edge.py` | **Free**, High Quality, No API Key | `pip install edge-tts` |
| **Google Gemini** | `gen_*_gemini.py` | Professional, Google Cloud | `gcloud auth application-default login` |
| **Alibaba Qwen** | `gen_*_qwen.py` | Concise, Neural | `DASHSCOPE_API_KEY` env var |
| **CosyVoice (Mac)** | `gen_*_cosy.py` | Offline/Local (CPU/MPS), 300M Model | [README-cosy.md](README-cosy.md) |
| **CosyVoice (Spark)** | `gen_*_spark.py` | **NVIDIA DGX Spark** (ARM64 Docker), GPU Accel | [README-spark.md](README-spark.md) |
| **CosyVoice (Pop!_OS)** | `gen_*_pop.py` | **System76 Laptop** (Host/x86), Native speed | [README-pop.md](README-pop.md) |

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
python gen_verse_devotion_edge.py
```

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
