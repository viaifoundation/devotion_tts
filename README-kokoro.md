# Kokoro TTS for Devotion TTS

Kokoro TTS — Ultra-lightweight **82M parameter** TTS that runs on **CPU**. No GPU required!

## Performance Comparison

| Model | Params | VRAM | CPU? | Unique Features |
|-------|--------|------|------|-----------------|
| **Kokoro** | **82M** | **~0.5GB** | ✅ Yes | Lightest, fastest |
| Fun-CosyVoice 3.0 | ~1B+ | ~4-6GB | ❌ | Best accuracy |
| Edge TTS | N/A | 0 | N/A | Cloud, free |

### Kokoro Unique Features

1. **Ultra-lightweight** — Only 82M parameters
2. **CPU-friendly** — Runs on Mac CPU/MPS, no GPU needed
3. **Fast** — Real-time or faster inference
4. **Chinese voicepacks** — `Kokoro-82M-v1.1-zh` with 100 Chinese speakers
5. **Apache 2.0** license
6. **No voice cloning** — Uses pre-trained voicepacks only

## Quick Start

### 1. Mac Local (Recommended)

```bash
pip install kokoro "misaki[zh]"
python gen_verse_devotion_kokoro.py --input sample.txt -d 1
```

### 2. DGX Spark

```bash
pip install kokoro "misaki[zh]"
python gen_verse_devotion_kokoro.py --input sample.txt -d 1
```

### 3. Generate Audio

```bash
# Default (rotate female/male voices)
python gen_verse_devotion_kokoro.py --input sample.txt -d 1

# Specific voice
python gen_verse_devotion_kokoro.py --input sample.txt --voice zf_001

# Slow reading
python gen_verse_devotion_kokoro.py --input sample.txt --speed 0.8

# Multiple voices rotation
python gen_verse_devotion_kokoro.py --input sample.txt --voices zf_001,zm_001,zf_002

# With BGM
python gen_verse_devotion_kokoro.py --input sample.txt --bgm
```

## CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `--input, -i` | Input text file | stdin |
| `--voice` | Single voice ID | zf_001 |
| `--voices` | Comma-separated voice IDs for rotation | zf_001,zm_001 |
| `--speed` | Speech speed (0.5-2.0) | 1.0 |
| `--no-rotate` | Use single voice only | False |
| `--bgm` | Enable background music | False |
| `--debug, -d` | Debug level (0-2) | 0 |

## Voice IDs

| ID | Description |
|----|-------------|
| `zf_001` | Chinese female 1 |
| `zm_001` | Chinese male 1 |
| `zf_002` | Chinese female 2 |
| `zm_002` | Chinese male 2 |

> Note: Voice IDs depend on the installed voicepack. Check `hexgrad/Kokoro-82M-v1.1-zh` on HuggingFace for the full list.

## References

- [Kokoro GitHub](https://github.com/hexgrad/kokoro)
- [Kokoro Chinese Model](https://huggingface.co/hexgrad/Kokoro-82M-v1.1-zh)
