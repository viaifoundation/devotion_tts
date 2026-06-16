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

| Engine | Provider | CER (ZH) ↓ | VRAM | Type | Best For |
|--------|----------|------------|------|------|----------|
| **Fun-CosyVoice 3.0** | Alibaba (FunAudioLLM) | **0.81** ✅ | ~4-6GB | Zero-shot | Best accuracy (SOTA) |
| GLM-TTS RL | Zhipu AI (GLM) | 0.89 | ~8GB | Zero-shot | GRPO emotion |
| StepAudio TTS-3B | StepFun (阶跃星辰) | ~0.9 | ~8-12GB | Zero-shot | Emotion + Dialect control |
| VoxCPM2 | OpenBMB (Tsinghua) | SOTA-level | ~8GB | Zero-shot | Voice Design + 48kHz |
| F5-TTS | SJTU X-LANCE Lab | ~1.0 | ~4-6GB | Zero-shot | Simplest pipeline (MIT) |
| Spark-TTS | SparkAudio (HKUST) | ~1.0 | ~4-8GB | Zero-shot | Pitch/Speed/Gender control |
| Index-TTS2 | Bilibili | 1.03 | ~8GB | Zero-shot | Duration + Emotion control |
| GPT-SoVITS | RVC-Boss | N/A | ~6GB | Fine-tune | Custom voice training |
| Qwen-TTS (Local) | Alibaba (Qwen) | N/A | ~10GB | Zero-shot | Voice Design / DGX Spark |
| Qwen TTS (API) | Alibaba (Dashscope) | N/A | API | Cloud | Dashscope multi-voice |
| Kokoro | hexgrad | N/A | ~0.5GB | Voicepack | Ultra-lightweight (82M, CPU) |
| Vibe | Vibe | N/A | ~4GB | Voice | Voice cloning |
| Volc (Volcengine) | ByteDance | N/A | API | Cloud | ByteDance API |
| Edge TTS | Microsoft | N/A | 0 | Cloud | Fast/Free |
| Gemini TTS | Google | N/A | API | Cloud | Google API |

### Quick Reference

| Provider | Script Prefix | Setup | Documentation |
| :--- | :--- | :--- | :--- |
| **Fun-CosyVoice 3.0** | `gen_*_cosy3.py` | DGX Spark / Docker | [README-cosy3.md](README-cosy3.md) |
| **GLM-TTS** | `gen_*_glmtts.py` | DGX Spark / Docker | [README-glmtts.md](README-glmtts.md) |
| **StepAudio TTS-3B** | `gen_*_stepaudio.py` | DGX Spark / Docker | [README-stepaudio.md](README-stepaudio.md) |
| **VoxCPM2** | `gen_*_voxcpm2.py` | `pip install voxcpm` | [README-voxcpm2.md](README-voxcpm2.md) |
| **F5-TTS** | `gen_*_f5tts.py` | `pip install f5-tts` | [README-f5tts.md](README-f5tts.md) |
| **Spark-TTS** | `gen_*_sparktts.py` | DGX Spark / Docker | [README-sparktts.md](README-sparktts.md) |
| **Index-TTS2** | `gen_*_indextts2.py` | DGX Spark / Docker | [README-indextts2.md](README-indextts2.md) |
| **GPT-SoVITS** | `gen_*_gptsovits.py` | DGX Spark / Docker | [README-gptsovits.md](README-gptsovits.md) |
| **Qwen-TTS (Local)** | `gen_*_qwentts.py` | DGX Spark / Docker | [README-qwentts.md](README-qwentts.md) |
| **Qwen TTS (API)** | `gen_*_qwen.py` | `DASHSCOPE_API_KEY` | [README-qwen.md](README-qwen.md) |
| **Kokoro** | `gen_*_kokoro.py` | `pip install kokoro` | [README-kokoro.md](README-kokoro.md) |
| **Vibe** | `gen_*_vibe.py` | Local | [README-vibe.md](README-vibe.md) |
| **Volc** | `gen_*_volc.py` | Volcengine API | [README-volc.md](README-volc.md) |
| **Edge TTS** | `gen_*_edge.py` | `pip install edge-tts` | [README-edge.md](README-edge.md) |
| **Gemini TTS** | `gen_*_gemini.py` | `gcloud auth` | [README-gemini.md](README-gemini.md) |
| **CosyVoice (Mac)** | `gen_*_cosy.py` | Offline (CPU/MPS) | [README-cosy.md](README-cosy.md) |

### Utility Tools

| Tool | Purpose | Usage |
|------|---------|-------|
| `gen_votd*.py` | VOTD audio: Short + Long (multi-translation Bible audio + **recorded** CUV chapters). See **Recorded chapter audio** below. | `python gen_votd_edge.py -i input.txt` |
| `chapter_narration_gain.py` | Shared dB offsets for **Everest vs David Yen** chapter MP3s (aligned with [ting](https://github.com/viaifoundation/ting) `concat_daily.py`). | Imported by `gen_votd_*.py` |
| `votd_narration_chapter.py` | Loads narration chapters, rotation index only advances after a **successful** decode; fallback if one source missing. | Used by `gen_votd_edge.py`, `gen_votd_cosy3.py`, `gen_votd_qwen.py` |
| `mp3_to_mp4.py` | Convert MP3 to MP4 for YouTube | `python mp3_to_mp4.py audio.mp3 --bg image.jpg` |
| `gen_voice_samples_edge.py` | Generate voice samples for CosyVoice 3.0 | `python gen_voice_samples_edge.py --all` |

#### Recorded chapter audio (`gen_votd_edge.py`, `gen_votd_cosy3.py`, `gen_votd_qwen.py`)

Full-chapter MP3s come from `assets/bible/audio/chapters/` (Everest, female) and `assets/bible/audio/chapters_davidyen/` (David Yen, male). Per-source gain matches ting’s plan pipeline; extra boost: `--speech-volume` (default 4).

`--chapter-voice` options:

| Value | Behavior |
|--------|-----------|
| `everest` | Female (Everest) only |
| `davidyen` | Male (David Yen) only |
| `rotate` | Alternate male/female by chapter (male first); same as `rotate_male_first` |
| `rotate_male_first` | Same as `rotate` |
| `rotate_female_first` | Alternate with female first |

## Environment Setup (Recommended)

To avoid Python version and package dependency conflicts, we recommend using **Mise** (a modern, fast tool manager) and **uv** (an extremely fast virtual environment and package manager).

### A. macOS Setup Guide

1.  **Install Prerequisites (Mise, uv, & FFmpeg)**:
    ```bash
    brew update
    brew install mise uv ffmpeg
    ```
    *Make sure to add `eval "$(mise activate zsh)"` to your `~/.zshrc` (or equivalent shell profile).*

2.  **Install Python 3.12**:
    ```bash
    mise use --global python@3.12
    ```

3.  **Create & Activate Virtual Environment**:
    Inside the repository directory, run:
    ```bash
    # Create virtual env named ".venv" using uv (takes ~10ms)
    uv venv
    
    # Activate it
    source .venv/bin/activate
    ```

### B. Traditional Setup Guide (Alternative)

If you prefer using traditional tools (`pyenv` + `venv`):

1.  **Install Pyenv & FFmpeg**:
    ```bash
    brew install pyenv ffmpeg
    ```
    *Follow instructions to add pyenv hooks to your shell profile.*

2.  **Install & Set Python**:
    ```bash
    pyenv install 3.12.12
    pyenv local 3.12.12
    ```

3.  **Create & Activate Virtual Environment**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

### C. Helpful Commands

```bash
# Deactivate virtual env
deactivate

# Install dependencies quickly with uv
uv pip install -r requirements.txt

# Remove the virtual env
rm -rf .venv
```

## Quick Start

### 1. Installation

Clone the repo and install dependencies:

```bash
git clone https://github.com/viaifoundation/devotion_tts.git
cd devotion_tts
# Install core dependencies (includes Edge TTS & Google)
uv pip install -r requirements.txt

# OR install provider-specific requirements as needed:
# uv pip install -r requirements-qwen.txt
# uv pip install -r requirements-cosy.txt
# uv pip install -r requirements-volc.txt
# uv pip install -r requirements-vibe.txt

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
