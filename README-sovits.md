# Devotion Audio TTS – GPT-SoVITS Guide

**GPT-SoVITS** is a state-of-the-art few-shot voice cloning engine capable of high-fidelity speech generation with minimal training data (5-10 seconds).

## 🚀 Quick Start (Spark/Docker)

### 1. Build & Enter Container
Run the wrapper script to build the image and enter the environment:
```bash
./scripts/run_spark_gptsovits.sh
```

### 2. Setup Models
Inside the container, run the one-time setup script to download required models (GPT-SoVITS Base, Chinese Roberta, etc.):
```bash
./setup_gptsovits.sh
```
*Note: If you encounter errors, ensure you have pulled the latest code with `git pull` on the host.*

---

## 🎙️ Reference Audio Preparation

GPT-SoVITS requires a **Reference Audio** (the voice to clone) and its corresponding **Reference Text** (what is being said).

### Option A: Generate a Starter Voice (Recommended)
If you don't have a recording, use the helper script to generate a high-quality starter voice using Edge TTS:
```bash
# Generates assets/ref_audio/ref.wav
python gen_ref_audio.py --voice zh-CN-YunxiNeural
```

### Option B: Record Your Own (Sample Texts)
Record a 3-10 second clip (WAV/MP3) and save it to `assets/ref_audio/ref.wav`.

**Sample Texts to Read:**

1.  **Standard (Neutral)**
    > "大家好，这是一个参考音频，用于语音克隆模型的输入。"
    > *(Dàjiā hǎo, zhè shì yīgè cānkǎo yīnpín, yòng yú yǔyīn kèlóng móxíng de shūrù.)*

2.  **Biblical (Devotional)**
    > "起初，神创造天地。地是空虚混沌，渊面黑暗。"
    > *(Qǐchū, Shén chuàngzào tiāndì. Dì shì kōngxū hùndùn, yuānmiàn hēi'àn.)*

3.  **Emotive (Warm)**
    > "然而，靠着爱我们的主，在这一切的事上已经得胜有余了。"
    > *(Rán'ér, kàozhe ài wǒmen de Zhǔ, zài zhè yīqiè de shì shàng yǐjīng déshèng yǒuyú le.)*

---

## 🎧 Generating Audio

Run the generation script with your input file and reference settings:

```bash
python gen_verse_devotion_gptsovits.py \
  --input input.txt \
  --ref-audio assets/ref_audio/ref.wav \
  --ref-text "大家好，这是一个参考音频，用于语音克隆模型的输入。" \
  --ref-lang zh \
  --bgm \
  --bgm-track AmazingGrace.mp3
```

### Arguments
*   `--input`: Path to input text file.
*   `--ref-audio`: Path to the 3-10s reference audio clip.
*   `--ref-text`: Exact content of the reference audio.
*   `--ref-lang`: Language of reference audio (`zh`, `en`, `ja`).
*   `--bgm`: Enable background music mixing.
