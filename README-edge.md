# Devotion Audio TTS – Edge TTS Edition (Microsoft Edge Online TTS)

Uses Microsoft Edge's online text-to-speech service (via `edge-tts` library) for high-quality multi-voice audio generation. Free and no API key required.

## Files
- `gen_bread_audio_edge.py`: Daily Bread (2 voices)
- `gen_verse_devotion_edge.py`: Verse + Devotion + Prayer (5 voices)
- `requirements-edge.txt`: Dependencies

## Setup

1. **Environment**:
   ```bash
   pyenv activate tts-venv-edge  # Recommended
   pip install -r requirements-edge.txt
   ```

## Usage

Run the script:
```bash
python gen_bread_audio_edge.py       # ~5-10 seconds
python gen_verse_devotion_edge.py --speed +10%
```

### Arguments
- `--speed`: Speech rate adjustment (e.g. `+10%`, `-5%`, `1.1`). Default `+0%`.
- `--bgm`: Enable background music.

Output will be saved to `~/Downloads/*.mp3`.

## Voices
Configured to use Microsoft Edge Neural voices (e.g., `zh-CN-YunxiNeural`, `zh-CN-XiaoyiNeural`, `zh-CN-YunyangNeural`).
