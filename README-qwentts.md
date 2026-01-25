# Devotion Audio TTS – Qwen-TTS Local Edition (DGX Spark)

Uses Alibaba's **Qwen-TTS model** running locally on the DGX Spark GPU for high-fidelity synthesis.

> [!NOTE]
> For **cloud API** usage (Dashscope), see [README-qwen.md](README-qwen.md).

## Files
- `gen_verse_devotion_qwentts.py` → Verse + Devotion + Prayer
- `scripts/run_spark_qwentts.sh` → Docker launch script
- `docker/Dockerfile.spark.qwentts` → Container definition

## Quick Start
```bash
# On DGX Spark host
./scripts/run_spark_qwentts.sh

# Inside container
python gen_verse_devotion_qwentts.py -i input.txt --voice two --bgm
```

### Arguments
| Argument | Description | Default |
|----------|-------------|---------|
| `--voice` | Voice mode: `male`, `female`, `two`, `four`, `six` | `six` |
| `--voices` | Custom voices (comma-separated, overrides --voice) | None |
| `--prefix` | Filename prefix | None |
| `--bgm` | Enable background music | False |

### Voice Modes
| Mode | Voices | Description |
|------|--------|-------------|
| `male` | Dylan | Single youthful male voice |
| `female` | Serena | Single warm female voice |
| `two` | Dylan, Serena | 1 male + 1 female (rotating) |
| `four` | Dylan, Serena, Aiden, Vivian | 2 male + 2 female (rotating) |
| `six` | Dylan, Serena, Aiden, Vivian, Ryan, Chelsie | 3 male + 3 female (rotating) **[Default]** |

### Voice Cloning
To clone a voice, provide a reference audio file (3-10s) and its transcript. This automatically switches to the `Base` model.

**Single Voice Cloning:**
```bash
python gen_verse_devotion_qwentts.py -i input.txt \
  --ref-audio "ref.wav" \
  --ref-text "Transcript of ref audio"
```

**Multi-Voice Cloning (Rotation):**
Separate multiple reference files with comma `,` and transcripts with pipe `|`.
```bash
python gen_verse_devotion_qwentts.py -i input.txt \
  --ref-audio "male.wav,female.wav" \
  --ref-text "Male transcript|Female transcript"
```

Output → `output/*.mp3`

## Requirements
- ~10GB for model weights (auto-downloaded)

## Troubleshooting

### 1. No Sound (Silent Audio)
If the output audio is silent (all zeros), check the logs for:
`⚠️ Running in MOCK mode for structure verification.`
This means the model failed to load. Use `--debug` to see why.

### 2. "Torch not compiled with CUDA enabled"
This happens if `pip install` downgrades PyTorch to a CPU version.
**Fix:** Run the setup script which compiles `torchaudio` from source to match the NVIDIA container:
```bash
source scripts/setup_qwentts_spark.sh
```

### 3. "Transformers does not recognize this architecture"
This means the `qwen_tts` package is missing or imports failed.
**Fix:** Run the setup script (above) which installs `qwen_tts` from GitHub.

### 4. "RuntimeError: operator torchvision::nms does not exist"
The `torchvision` package is broken due to version mismatch.
**Fix:** Uninstall it (not needed for TTS):
```bash
pip uninstall -y torchvision
```

