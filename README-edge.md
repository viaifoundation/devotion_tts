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
| `--mp4` | Generate MP4 video from audio | False |
| `--mp4-bg` | Background image for MP4 | `assets/background/background.jpg` |
| `--mp4-res` | MP4 resolution | `1920x1080` |

## MP4 Video Generation

Generate YouTube-ready MP4 videos with a static background image:

```bash
# Generate MP4 with default background
python gen_verse_devotion_edge.py -i input.txt --mp4

# Custom background and resolution
python gen_verse_devotion_edge.py -i input.txt --mp4 --mp4-bg ~/imgs/banner.jpg --mp4-res 1280x720

# Full pipeline: audio with BGM + MP4 video
python gen_verse_devotion_edge.py -i input.txt --bgm --mp4
```

> [!NOTE]
> Requires `ffmpeg` installed. The MP4 file is created alongside the MP3 with the same name.

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
