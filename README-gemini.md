# Devotion Audio TTS – Gemini Edition (Google Cloud TTS)

Uses Google Cloud Text-to-Speech (Gemini voices) for high-quality multi-voice audio generation.

## Files
- `gen_verse_devotion_gemini.py`: Main script for generating Verse + Devotion + Prayer audio.
- `requirements-gemini.txt`: Dependencies.

## Setup

1. **Environment**:
   ```bash
   pyenv activate tts-venv-gemini
   pip install -r requirements-gemini.txt
   ```

2. **Google Cloud Credentials**:
   You must have a Google Cloud Service Account key to use this API.
   
   Export the path to your key file:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"
   ```

## Usage

Run the script:
```bash
python gen_verse_devotion_gemini.py --speed 1.2
```

### Arguments
| Argument | Description | Default |
|----------|-------------|---------|
| `--input`, `-i` | Input text file | (stdin) |
| `--prefix` | Filename prefix | None |
| `--speed` | Speed factor (e.g. `1.1`, `+10%`) | `1.0` |
| `--bgm` | Enable background music | False |

Output will be saved to `~/Downloads/verse_gemini.mp3`.

## Voices
Configured to valid "Gemini" voices (e.g., Charon, Kore, Fenrir, Aoede, Puck).
