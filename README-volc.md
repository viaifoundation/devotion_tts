# Devotion Audio TTS – Volcengine (Doubao) Edition

Uses **ByteDance/Volcengine** (Doubao) TTS API for high-quality, expressive Chinese speech synthesis.

## Key Features
- **High Quality**: "Doubao" voices (e.g., Vivi, Yunzhou) are currently industry-leading for naturalness.
- **Cloud API**: Requires API Key (Paid service, but cheap/free tier available).
- **Fast**: Cloud-based generation is typically faster than local inference on older hardware.

## Files
- `gen_bread_audio_volc.py`: Daily Bread (2 voices)
- `gen_verse_devotion_volc.py`: Verse + Devotion + Prayer (Multi-voice)
- `requirements-volc.txt`: Dependencies

## Setup

### 1. Get Credentials
1. High to [Volcengine Console](https://console.volcengine.com/speech/app).
2. Create an App to get your **AppID**.
3. Create an Access Token to get your **Token**.
4. Standard Cluster ID is usually `volcano_tts`.

## Configuration
You need two environment variables:
`VOLC_APPID` and `VOLC_TOKEN`.
**(Do NOT use Access Key / Secret Key / AK / SK)**

### How to get credentials:
1.  Log in to [Volcengine Console](https://console.volcengine.com/speech/service).
2.  Go to **Speech Synthesis** > **Service Management**.
3.  Go to **Speech Synthesis** > **Token Management**.
    *   Create a token with correct permissions.
4.  **Note**: These scripts use the **HTTP V1 API** for maximum compatibility.

### Setup
```bash
export VOLC_APPID="your_appid_number"
export VOLC_TOKEN="your_access_token"
```

### 3. Installation
```bash
pip install -r requirements-volc.txt
```
(Requires `websockets` and `volcengine-python-sdk`)

## Usage

```bash
python gen_verse_devotion_volc.py --speed 1.2
```

### Arguments
- `--speed`: Speed ratio (0.8 - 2.0). Default `1.0`.
- `--bgm`: Enable background music.
# or
python gen_bread_audio_volc.py
```

## Voices
Configured to use "Doubao 2.0" voices:
- `zh_female_vv_uranus_bigtts` (Vivi - Warm/Affectionate)
- `zh_male_m191_uranus_bigtts` (Yunzhou - Mature/Storytelling)
- `zh_female_xiaohe_uranus_bigtts` (Xiaohe - Gentle)
- `zh_male_taocheng_uranus_bigtts` (Xiaotian - Clear)
