# Devotion Audio TTS – GPT-SoVITS Guide

**GPT-SoVITS** is a state-of-the-art few-shot voice cloning engine capable of high-fidelity speech generation with minimal training data (3-10 seconds).

## 🚀 Quick Start (Spark/Docker)

### 1. Build & Enter Container
Run the wrapper script to build the image and enter the environment:
```bash
./scripts/run_spark_gptsovits.sh
```

### 2. Setup Models
Inside the container, run the one-time setup to download all required models:
```bash
python download_models.py
```

This downloads:
- GPT-SoVITS v2 pretrained models
- Chinese RoBERTa & HuBERT
- FastText language detection model
- NLTK data for English processing

---

## 🎙️ Reference Audio Preparation

GPT-SoVITS requires a **Reference Audio** (3-10 seconds) and its corresponding **Reference Text**.

### Option A: Generate a Starter Voice
Use the helper script to generate a high-quality starter voice using Edge TTS:
```bash
python gen_ref_audio.py --voice zh-CN-YunxiNeural
```
Output: `assets/ref_audio/ref.wav`

### Option B: Record Your Own
Record a 3-10 second clip and save it to `assets/ref_audio/`.

**Sample Texts to Read:**

| Style | Text |
|-------|------|
| Neutral | 大家好，这是一个参考音频，用于语音克隆模型的输入。 |
| Biblical | 起初，神创造天地。地是空虚混沌，渊面黑暗。 |
| Emotive | 然而，靠着爱我们的主，在这一切的事上已经得胜有余了。 |

> **Important:** Reference audio must be **3-10 seconds** long.

---

## 🎧 Generating Audio

```bash
python gen_verse_devotion_gptsovits.py \
  --input input.txt \
  --ref-audio assets/ref_audio/ref.wav \
  --ref-text "大家好，这是一个参考音频，用于语音克隆模型的输入。" \
  --ref-lang zh \
  --speed 1.0 \
  --bgm
```

### Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--input`, `-i` | Input text file | (stdin) |
| `--prefix` | Filename prefix | None |
| `--ref-audio` | Reference audio file (3-10s) | `assets/ref_audio/ref.wav` |
| `--ref-text` | Exact text of reference audio | Required |
| `--ref-lang` | Reference language: `zh`, `en`, `ja` | `zh` |
| `--speed` | Speed factor: `1.0`, `1.2`, `+20%`, `-10%` | `1.0` |
| `--bgm` | Enable background music | False |
| `--bgm-track` | BGM filename | `AmazingGrace.mp3` |
| `--bgm-volume` | BGM volume (dB) | `-20` |
| `--bgm-intro` | BGM intro delay (ms) | `4000` |

### Speed Examples
- `--speed 1.2` → 20% faster
- `--speed +20%` → 20% faster
- `--speed 0.8` → 20% slower
- `--speed -10%` → 10% slower

---

## 🎧 Generating SOH Prayer (Voice Clone)

For "Sound of Home" (SOH) prayer audio with consistent filename format `乡音情_{Date}.mp3`:

```bash
python gen_soh_prayer_gptsovits.py \
  --input input.txt \
  --ref-audio assets/ref_audio/soh_ref.wav \
  --ref-text "..." \
  --bgm
```

---

## 🔧 Troubleshooting

| Error | Solution |
|-------|----------|
| `Reference audio is outside the 3-10 second range` | Trim your reference audio to 3-10 seconds |
| `No module named 'ERes2NetV2'` | Re-run container build: `./scripts/run_spark_gptsovits.sh` |
| `fast-langdetect: Cache directory not found` | Run `python download_models.py` |
| `averaged_perceptron_tagger_eng not found` | Run `python download_models.py` |
