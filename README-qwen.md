# Devotion Audio TTS – Qwen3-TTS Edition (Offline · Best Chinese Quality)

Uses Alibaba's official Qwen3-TTS model (Nov 2025) with PyTorch + MPS → runs blazing fast on M1–M4 Macs.

## Files
- `gen_bread_audio_qwen.py`      → Daily Bread (2 voices)
- `gen_verse_devotion_qwen.py`    → Verse + Devotion + Prayer (5 voices)
- `requirements-qwen.txt`         → install once

## One-time setup (already done)
```bash
pip install -r requirements-qwen.txt
```

## Daily use
```
source ~/.pyenv/versions/3.12.12/envs/tts-venv-qwen/bin/activate
python gen_bread_audio_qwen.py        # ~1.5 seconds
python gen_verse_devotion_qwen.py --speed 1.2
```

### Arguments
- `--speed`: Speed adjustment (e.g. `1.2` or `+20%`). Default `1.0`.
- `--bgm`: Enable background music.
Output → ~/Downloads/*.mp3

First run downloads model (~1.8 GB), then cached forever).
Enjoy the highest-quality offline Chinese devotional audio in 2025 — completely free.
