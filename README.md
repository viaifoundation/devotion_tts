# Devotion Audio TTS

A unified toolset for generating Chinese Bible devotional audio using state-of-the-art TTS providers: **Microsoft Edge TTS**, **Google Gemini/Cloud TTS**, **Alibaba Qwen TTS**, and **CosyVoice**.

## Overview

This project provides Python scripts to generate high-quality audio for:
- Daily Devotionals
- Verse of the Day (VOTD)
- "Bread" Audio (Daily portion)

It supports automatic filename generation based on the Bible verse and date found in the text.

## Supported Providers

| Provider | Script Prefix | Key Features | Setup |
| :--- | :--- | :--- | :--- |
| **Edge TTS** | `gen_*_edge.py` | **Free**, High Quality, No API Key | `pip install edge-tts` |
| **Google Gemini** | `gen_*_gemini.py` | Professional, Google Cloud | `gcloud auth application-default login` |
| **Alibaba Qwen** | `gen_*_qwen.py` | Concise, Neural | `DASHSCOPE_API_KEY` env var |
| **CosyVoice** | `gen_*_cosy.py` | Offline/Local capable (300M model) | `torch`, `modelscope` |

## Quick Start

### 1. Installation

Clone the repo and install dependencies:

```bash
git clone https://github.com/viaifoundation/devotion_audio_tts.git
cd devotion_audio_tts
pip install -r requirements.txt
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

## Project Utilities

- `daily_devotional_filenames_v2.py`: Handles dynamic parsing of dates and verses to generate consistent filenames.
- `bible_parser.py`: Normalizes Chinese Bible references for better TTS pronunciation (e.g., "3:16" -> "3章16节").
- `text_cleaner.py`: Formats text, adding ensuring spacing around "God" (神).

## Requirements

Global requirements are listed in `requirements.txt`. Specific providers may have additional needs:
- **Edge**: `requirements-edge.txt`
- **Gemini**: `requirements-gemini.txt`
- **Qwen**: `requirements-qwen.txt`
- **CosyVoice**: `requirements-cosy.txt`

## License

MIT License
