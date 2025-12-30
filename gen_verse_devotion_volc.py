# gen_verse_devotion_volc.py
# Volcengine (ByteDance/Doubao) TTS
# Uses HTTP V1 API for maximum compatibility. 
# Requires VOLC_APPID and VOLC_TOKEN

import io
import os
import re
import uuid
import json
import base64
import requests
from pydub import AudioSegment
from datetime import datetime

from bible_parser import convert_bible_reference
from date_parser import convert_dates_in_text
from text_cleaner import clean_text
import filename_parser
import argparse
import sys

# CLI Args
parser = argparse.ArgumentParser()
parser.add_argument("--input", "-i", type=str, help="Input text file")
parser.add_argument("--prefix", type=str, default=None, help="Filename prefix")
parser.add_argument("--speed", type=str, default="1.0", help="Speed ratio (0.8-2.0, default 1.0)")

args, unknown = parser.parse_known_args()
CLI_PREFIX = args.prefix

# Parse speed value
def parse_speed(speed_str):
    if not speed_str: return 1.0
    try:
        # Handle percentage "+10%"
        if "%" in speed_str:
            val = float(speed_str.replace("%", ""))
            return 1.0 + (val / 100.0)
        return float(speed_str)
    except ValueError:
        return 1.0

TTS_SPEED = max(0.8, min(2.0, parse_speed(args.speed)))


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

# API Endpoint (HTTP V1)
HOST = "openspeech.bytedance.com"
API_URL = f"https://{HOST}/api/v1/tts"

# Voices
VOICES = [
    "zh_female_vv_uranus_bigtts",       # Vivi
    "zh_male_m191_uranus_bigtts",       # Yunzhou
    "zh_female_xiaohe_uranus_bigtts",   # Xiaohe
    "zh_male_taocheng_uranus_bigtts",   # Xiaotian
    "zh_female_sister_uranus_bigtts"    # ZhiXin Jiejie
]

def check_auth():
    if not APPID or not TOKEN:
        print("❌ Error: Missing VOLC_APPID or VOLC_TOKEN.")
        return False
    return True

def speak(text: str, voice: str) -> AudioSegment:
    """Synthesize text using Volcengine HTTP API"""
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
            "speed_ratio": TTS_SPEED,
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
        # print(f"DEBUG: Sending to {API_URL} with voice {voice}...")
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



if __name__ == "__main__":
    if not check_auth():
        exit(1)

    # Generate filename dynamically
    # 1. Extract Date
    TEXT = clean_text(TEXT)
    first_line = TEXT.strip().split('\n')[0]
    date_match = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", first_line)
    if date_match:
        m, d, y = date_match.groups()
        date_str = f"{y}-{int(m):02d}-{int(d):02d}"
    else:
        # Try YYYY-MM-DD
        date_match = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", first_line)
        if date_match:
            y, m, d = date_match.groups()
            date_str = f"{y}-{int(m):02d}-{int(d):02d}"
        else:
            date_str = datetime.today().strftime("%Y-%m-%d")

# 2. Extract Verse Reference (for metadata only)
    verse_ref = filename_parser.extract_verse_from_text(TEXT)

    # 3. Generate Filename (Standardized V2)
    extracted_prefix = CLI_PREFIX if CLI_PREFIX else filename_parser.extract_filename_prefix(TEXT)
    filename = filename_parser.generate_filename_v2(
        title=first_line, 
        date=date_str, 
        prefix=extracted_prefix,
        ext=".mp3"
    ).replace(".mp3", "_volc.mp3")
    OUTPUT_DIR = os.path.join(os.getcwd(), "output")
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    OUTPUT_PATH = os.path.join(OUTPUT_DIR, filename)
    print(f"Target Output: {OUTPUT_PATH}")

    # Process Text
    TEXT = convert_bible_reference(TEXT)
    TEXT = convert_dates_in_text(TEXT)
    TEXT = clean_text(TEXT)

    paragraphs = [p.strip() for p in re.split(r'\n{2,}', TEXT.strip()) if p.strip()]

    # Group paragraphs
    if len(paragraphs) < 5:
        logical_sections = [[p] for p in paragraphs]
    else:
        logical_sections = [
            [paragraphs[0]],              # Intro
            [paragraphs[1]],              # Scripture 1
            [paragraphs[2]],              # Scripture 2
            paragraphs[3:-1],             # Main Body
            [paragraphs[-1]]              # Prayer
        ]

    print(f"Processing {len(logical_sections)} logical sections...")
    section_titles = ["Intro", "Scripture 1", "Scripture 2", "Main Body", "Prayer"]

    final_segments = []
    global_p_index = 0
    
    for i, section_paras in enumerate(logical_sections):
        title = section_titles[i] if i < len(section_titles) else f"Section {i+1}"
        print(f"--- Section {i+1}: {title} ---")
        
        section_audio = AudioSegment.empty()
        silence_between_paras = AudioSegment.silent(duration=700, frame_rate=24000)

        for j, para in enumerate(section_paras):
            # Rotate voices
            voice = VOICES[global_p_index % len(VOICES)]
            print(f"  > Part {i+1}.{j+1} - {voice}")
            global_p_index += 1
            
            # Simple synchronous call
            current_segment = speak(para, voice)
            section_audio += current_segment
            
            if j < len(section_paras) - 1:
                section_audio += silence_between_paras
                
        final_segments.append(section_audio)

    final = AudioSegment.empty()
    silence_between_sections = AudioSegment.silent(duration=1000, frame_rate=24000)

    for i, seg in enumerate(final_segments):
        final += seg
        if i < len(final_segments) - 1:
            final += silence_between_sections

    final = final.set_frame_rate(24000)
    # Metadata extraction
    PRODUCER = "VI AI Foundation"
    TITLE = TEXT.strip().split('\n')[0]
    ALBUM = "Devotion"
    COMMENTS = f"Verse: {verse_ref}"

    final.export(OUTPUT_PATH, format="mp3", bitrate="192k", tags={
        'title': TITLE, 
        'artist': PRODUCER,
        'album': ALBUM,
        'comments': COMMENTS
    })
    print(f"Success! Saved → {OUTPUT_PATH}")
