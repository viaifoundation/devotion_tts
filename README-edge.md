# Devotion Audio TTS – Edge TTS Edition (Microsoft Edge Online TTS)

Uses Microsoft Edge's online text-to-speech service (via `edge-tts` library) for high-quality multi-voice audio generation. Free and no API key required.

## Files

| Script | Purpose | Default Voice Mode |
|--------|---------|-------------------|
| `gen_verse_devotion_edge.py` | Verse + Devotion + Prayer | `six` |
| `gen_prayer_edge.py` | Prayer | `six` |
| `gen_prayer_soh.py` | SOH Prayer | `two` |
| `gen_bread_audio_edge.py` | Daily Bread | `two` |

## Setup

```bash
pip install -r requirements-edge.txt
```

## Usage

```bash
# Default (6 voices rotation)
python gen_verse_devotion_edge.py -i input.txt

# Male voice only
python gen_verse_devotion_edge.py -i input.txt --voice male

# Female voice only with BGM
python gen_prayer_edge.py -i input.txt --voice female --bgm

# Two voices (1 male + 1 female)
python gen_bread_audio_edge.py -i input.txt --voice two

# Four voices with speed adjustment
python gen_verse_devotion_edge.py -i input.txt --voice four --speed +10%

# Custom voices (CSV format)
python gen_verse_devotion_edge.py -i input.txt --voices "zh-CN-YunyangNeural,zh-CN-XiaoyiNeural"
```

## Command Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--input`, `-i` | Input text file | (stdin) |
| `--voice` | Voice mode: `male`, `female`, `two`, `four`, `six` | varies by script |
| `--voices` | Custom voices (CSV, overrides --voice) | (none) |
| `--speed` | Speech rate: `+10%`, `--speed=-10%` | `+0%` |
| `--prefix` | Output filename prefix | (from text) |
| `--bgm` | Enable background music | False |
| `--bgm-track` | BGM filename | `AmazingGrace.MP3` |
| `--bgm-volume` | BGM volume in dB | -20 |
| `--bgm-intro` | BGM intro delay in ms | 4000 |
| `--mp4` | Generate MP4 video from audio (both short and long versions) | False |
| `--mp4-bg` | Background image for MP4 (auto-searches `assets/background/` and `assets/bgm/`) | `assets/background/background_soh.jpg` for SOH (fallback: `background.jpg`) |
| `--mp4-res` | MP4 resolution | `1920x1080` |
| `--caption` | Enable burned-in hard captions on MP4 (`true`/`false`) | `true` |
| `--no-caption` | Disable burned-in captions on MP4 video | False |
| `--caption-scale` | Caption font scale multiplier (`1x`, `2x`, `3x`, `4x`, etc.) | `2x` |
| `--caption-large` | Shortcut for 3x caption font size for mobile/social screens (`true`/`false`) | `false` |
| `--caption-file` | Explicit SRT/VTT caption file (auto-detects if omitted) | (none) |

## MP4 Video Generation & Captions

Generate YouTube- and WeChat-ready MP4 videos with a static background image and burned-in subtitles (on by default, 2x font):

```bash
# Generate MP4 with default 2x burned-in captions (108px font - ideal for WeChat / mobile)
python gen_prayer_soh.py -i input.txt --mp4

# Generate MP4 without captions
python gen_prayer_soh.py -i input.txt --mp4 --no-caption

# Custom caption sizes
python gen_prayer_soh.py -i input.txt --mp4 --caption-scale 1x   # Standard 54px font
python gen_prayer_soh.py -i input.txt --mp4 --caption-scale 3x   # 3x font (or: --caption-large)
python gen_prayer_soh.py -i input.txt --mp4 --caption-scale 0.5  # Compact font

# Specify background image by filename (searched in assets/background/ and assets/bgm/) or full path
python gen_prayer_soh.py -i input.txt --mp4 --mp4-bg background_soh.jpg
python gen_prayer_soh.py -i input.txt --mp4 --mp4-bg background.jpg
python gen_prayer_soh.py -i input.txt --mp4 --mp4-bg ~/imgs/banner.jpg --mp4-res 1280x720

# Full pipeline: audio with BGM + MP4 video with 2x burned-in captions
python gen_prayer_soh.py -i input.txt --bgm --mp4 --caption true --caption-scale 2x
```

> [!NOTE]
> Captions are hard-coded (burned-in) onto the video frames inside a modern semi-transparent dark rounded pill box. This ensures full visual compatibility across YouTube, WeChat, and native mobile players where soft subtitle tracks are often stripped or ignored. Requires `ffmpeg` and `pillow`.

## Voice Modes

| Mode | Voices |
|------|--------|
| `male` | YunyangNeural (Professional, Reliable) |
| `female` | XiaoxiaoNeural (Warm) |
| `two` | Yunyang + Xiaoxiao |
| `four` | Yunyang, Xiaoxiao, Yunxi, Xiaoyi |
| `six` | All 6 zh-CN voices |

## Available zh-CN Voices

| Voice | Gender | Personality |
|-------|--------|-------------|
| `zh-CN-YunyangNeural` | Male | Professional, Reliable |
| `zh-CN-YunxiNeural` | Male | Lively, Sunshine |
| `zh-CN-YunjianNeural` | Male | Passion |
| `zh-CN-XiaoxiaoNeural` | Female | Warm |
| `zh-CN-XiaoyiNeural` | Female | Lively |
| `zh-CN-YunxiaNeural` | Male | Cute |

**Quick Help:** Run `python gen_verse_devotion_edge.py -h` for help.
