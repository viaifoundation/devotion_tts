# gen_bread_audio_volc.py
# Volcengine (ByteDance/Doubao) TTS – Daily Bread Audio
# Uses HTTP V1 API for maximum compatibility.
# Requires VOLC_APPID and VOLC_TOKEN

import io
import os
import sys
import re
import uuid
import base64
import requests
from pydub import AudioSegment

from bible_parser import convert_bible_reference
from text_cleaner import clean_text
from datetime import datetime
import argparse
import filename_parser
import audio_mixer

# CLI Args
if "-?" in sys.argv:
    print(f"Usage: python {sys.argv[0]} [--input FILE] [--prefix PREFIX] [--speed SPEED] [--bgm] [--bgm-track TRACK] [--bgm-volume VOL] [--bgm-intro MS] [--help]")
    print ("\nOptions:")
    print("  --input FILE, -i     Text file to read input from")
    print("  --prefix PREFIX      Filename prefix (e.g. MyPrefix)")
    print("  --speed SPEED        Speech speed adjustment (e.g. +20, -10, or 1.2)")
    print("  --bgm                Enable background music (Default: False)")
    print("  --bgm-track TRACK    Specific BGM filename (Default: AmazingGrace.MP3)")
    print("  --bgm-volume VOL     BGM volume adjustment in dB (Default: -20)")
    print("  --bgm-intro MS       BGM intro delay in ms (Default: 4000)")
    print("  --help, -h           Show this help")
    print("\n  (Note: You can also add 'FilenamePrefix: <Prefix>' in the input TEXT)")
    sys.exit(0)

parser = argparse.ArgumentParser()
parser.add_argument("--input", "-i", type=str, help="Input text file")
parser.add_argument("--prefix", type=str, default=None, help="Filename prefix (e.g. MyPrefix)")
parser.add_argument("--speed", type=str, default=None, help="Speech speed adjustment (e.g. +20)")
parser.add_argument("--bgm", action="store_true", help="Enable background music (Default: False)")
parser.add_argument("--bgm-track", type=str, default="AmazingGrace.MP3", help="Specific BGM filename (Default: AmazingGrace.MP3)")
parser.add_argument("--bgm-volume", type=int, default=-20, help="BGM volume adjustment in dB (Default: -20)")
parser.add_argument("--bgm-intro", type=int, default=4000, help="BGM intro delay in ms (Default: 4000)")

args, unknown = parser.parse_known_args()
CLI_PREFIX = args.prefix
ENABLE_BGM = args.bgm
BGM_FILE = args.bgm_track
BGM_VOLUME = args.bgm_volume
BGM_INTRO_DELAY = args.bgm_intro

# Calculate Speed Ratio
SPEED_RATIO = 1.0
if args.speed:
    val_str = args.speed.replace("%", "")
    try:
        if val_str.startswith("+") or val_str.startswith("-"):
            # e.g. +20 -> 1.2, -10 -> 0.9
            SPEED_RATIO = 1.0 + (float(val_str) / 100.0)
        else:
            # e.g. 1.2 or 0.9 directly
            SPEED_RATIO = float(val_str)
    except ValueError:
        print(f"⚠️ Invalid speed format '{args.speed}', using default 1.0")
        SPEED_RATIO = 1.0

# 1. Try --input argument
if args.input:
    print(f"Reading text from file: {args.input}")
    with open(args.input, "r", encoding="utf-8") as f:
        TEXT = f.read()

# 2. Try Stdin (Piped)
elif not sys.stdin.isatty():
    print("Reading text from Stdin...")
    TEXT = sys.stdin.read()

# 3. Fallback
else:
    TEXT = """
“　神爱世人，甚至将他的独生子赐给他们，叫一切信他的，不至灭亡，反得永生。因为　神差他的儿子降世，不是要定世人的罪，乃是要叫世人因他得救。信他的人，不被定罪；不信的人，罪已经定了，因为他不信　神独生子的名。
(约翰福音 3:16-18)
"""



# Configuration
APPID = os.getenv("VOLC_APPID", "")
TOKEN = os.getenv("VOLC_TOKEN", "")
CLUSTER = "volcano_tts"

HOST = "openspeech.bytedance.com"
API_URL = f"https://{HOST}/api/v1/tts"

def speak(text: str, voice: str = "zh_female_vv_uranus_bigtts") -> AudioSegment:
    print(f"DEBUG: Text to read: {text[:100]}...")
    if not text.strip():
        return AudioSegment.empty()

    headers = {
        "Authorization": f"Bearer;{TOKEN}",
        "Content-Type": "application/json"
    }

    request_json = {
        "app": {
            "appid": APPID,
            "token": TOKEN,
            "cluster": CLUSTER
        },
        "user": {
            "uid": str(uuid.uuid4())
        },
        "audio": {
            "voice_type": voice,
            "encoding": "mp3",
            "speed_ratio": SPEED_RATIO,
            "volume_ratio": 1.0,
            "pitch_ratio": 1.0,
        },
        "request": {
            "reqid": str(uuid.uuid4()),
            "text": text,
            "text_type": "plain",
            "operation": "query",
            "with_frontend": 1,
            "frontend_type": "unitTson"
        }
    }

    try:
        resp = requests.post(API_URL, json=request_json, headers=headers)
        if resp.status_code == 200:
            resp_data = resp.json()
            if "data" in resp_data and resp_data["data"]:
                audio_bytes = base64.b64decode(resp_data["data"])
                return AudioSegment.from_mp3(io.BytesIO(audio_bytes))
            else:
                print(f"⚠️ API Error: {resp.text}")
                return AudioSegment.silent(duration=500)
        else:
            print(f"❌ HTTP Error {resp.status_code}: {resp.text}")
            return AudioSegment.silent(duration=500)
    except Exception as e:
        print(f"❌ Request Failed: {e}")
        return AudioSegment.silent(duration=500)

def check_auth():
    if not APPID or not TOKEN:
        print("❌ Error: Missing VOLC_APPID or VOLC_TOKEN.")
        return False
    return True

# Configuration Check
if not APPID or not TOKEN:
    print("❌ Error: Missing VOLC_APPID or VOLC_TOKEN.")
    sys.exit(1)

OUTPUT_DIR = os.path.join(os.getcwd(), "output")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
# Generate filename dynamically
# 1. Try to find date in text like "12月15日" or "12/15"
TEXT = clean_text(TEXT)
date_match = re.search(r"(\d{1,2})月(\d{1,2})日", TEXT)
if date_match:
    m, d = date_match.groups()
    current_year = datetime.now().year
    date_str = f"{current_year}{int(m):02d}{int(d):02d}"
else:
    # 2. Fallback to script modification time
    try:
        mod_timestamp = os.path.getmtime(__file__)
        date_str = datetime.fromtimestamp(mod_timestamp).strftime("%Y%m%d")
        print(f"⚠️ Date not found in text. Using script modification date: {date_str}")
    except:
        # 3. Fallback to today
        date_str = datetime.today().strftime("%Y%m%d")

extracted_prefix = CLI_PREFIX if CLI_PREFIX else filename_parser.extract_filename_prefix(TEXT)

basename = f"Bread_{date_str}_volc.mp3"
if extracted_prefix:
    filename = f"{extracted_prefix}_{basename}"
else:
    filename = basename

if ENABLE_BGM and BGM_FILE:
    bgm_base = os.path.splitext(os.path.basename(BGM_FILE))[0]
    filename = filename.replace(".mp3", f"_bgm_{bgm_base}.mp3")

OUTPUT_PATH = os.path.join(OUTPUT_DIR, filename)



if __name__ == "__main__":
    if not check_auth():
        exit(1)

    TEXT = convert_bible_reference(TEXT)
    TEXT = clean_text(TEXT)

    paragraphs = [p.strip() for p in re.split(r'\n{2,}', TEXT.strip()) if p.strip()]
    intro = paragraphs[0] if paragraphs else ""
    main = "\n".join(paragraphs[1:]) if len(paragraphs) > 1 else ""

    print("Generating introduction (Vivi)…")
    # Vivi (zh_female_vv_uranus_bigtts)
    seg_intro = speak(intro, "zh_female_vv_uranus_bigtts")

    print("Generating main content (Yunzhou)…")
    # Yunzhou (zh_male_m191_uranus_bigtts)
    seg_main = speak(main, "zh_male_m191_uranus_bigtts")

    final = seg_intro + AudioSegment.silent(duration=600) + seg_main
    final = final.set_frame_rate(24000)

    # Add Background Music (Optional)
    if ENABLE_BGM:
        print(f"🎵 Mixing Background Music (Vol={BGM_VOLUME}dB, Intro={BGM_INTRO_DELAY}ms)...")
        final = audio_mixer.mix_bgm(
            final, 
            specific_filename=BGM_FILE,
            volume_db=BGM_VOLUME,
            intro_delay_ms=BGM_INTRO_DELAY
        )

# Metadata extraction
PRODUCER = "VI AI Foundation"
TITLE = TEXT.strip().split('\n')[0]

final.export(OUTPUT_PATH, format="mp3", bitrate="192k", tags={'title': TITLE, 'artist': PRODUCER})
print(f"Success! Saved → {OUTPUT_PATH}")

