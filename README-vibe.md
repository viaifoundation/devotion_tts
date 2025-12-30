# VibeVoice TTS Setup

This workflow uses the Microsoft VibeVoice model (Open Source) for high-quality, expressive TTS.

## 1. Setup VibeVoice Repository

You need to clone the VibeVoice repository as a sibling to this one:

```bash
cd ..
git clone https://github.com/microsoft/VibeVoice
cd VibeVoice
# Optional: Setup their environment if you want to run their demos
# but for our script, we just need the code and models.
```

## 2. Install Dependencies

Install the Python requirements:

```bash
pip install -r requirements-vibe.txt
```

## 3. Run the Script

The script `gen_verse_devotion_vibe.py` wraps VibeVoice for our workflow.

```bash
python gen_verse_devotion_vibe.py
python gen_verse_devotion_vibe.py --speed 1.0
```

### Arguments
- `--speed`: Speed factor. **Note:** Currently only a placeholder. Default `1.0`.
- `--bgm`: Enable background music.

## Troubleshooting

- **MPS (Mac)**: The script attempts to use MPS acceleration. If it fails, it falls back to CPU.
- **CUDA (Linux/Spark)**: Automatically used if available.
- **Model Download**: The script will download `microsoft/VibeVoice-Realtime-0.5B` from Hugging Face on the first run. Ensure you have internet access.
- **Voices**: The script looks for voice prompts in `../VibeVoice/demo/voices/streaming_model`. If you want new voices, add `.pt` files there.
