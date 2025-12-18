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
if "-?" in sys.argv:
    print(f"Usage: python {sys.argv[0]} [--prefix PREFIX] [--help]")
    print("Options:")
    print("  --prefix PREFIX      Filename prefix (overrides 'FilenamePrefix' in text)")
    print("  --help, -h           Show this help")
    print("\n  (Note: You can also add 'FilenamePrefix: <Prefix>' in the input TEXT)")
    sys.exit(0)

parser = argparse.ArgumentParser()
parser.add_argument("--prefix", type=str, default=None, help="Filename prefix")
args, unknown = parser.parse_known_args()
CLI_PREFIX = args.prefix


TEXT = """
住在神的爱里面 (约翰一书 4:16) 12/13/2025

及至时候满足，　神就差遣他的儿子，为女子所生，且生在律法以下，要把律法以下的人赎出来，叫我们得着儿子的名分。你们既为儿子，　神就差他儿子的灵进入你们（原文是我们）的心，呼叫：“阿爸！父！”可见，从此以后，你不是奴仆，乃是儿子了；既是儿子，就靠着　神为后嗣。
(加拉太书 4:4-7 和合本)
但到了时机成熟，　神就差遣他的儿子，由女人所生，而且生在律法之下，要把律法之下的人救赎出来，好让我们得着嗣子的名分。
(加拉太书 4:4-5 新译本)
所以，你们要自卑，服在　神大能的手下，到了时候，他必叫你们升高。你们要将一切的忧虑卸给　神，因为他顾念你们。
(彼得前书 5:6-7)


　神爱我们的心，我们也知道也信。
　神就是爱；住在爱里面的，就是住在　神里面，　神也住在他里面。
(约翰一书 4:16 和合本)
　神对我们的爱，我们已经明白了，而且相信了。
　神就是爱；住在爱里面的，就住在　神里面，　神也住在他里面。
(约翰壹书 4:16 新译本)
这样，我们已经认识并相信了神对我们所怀的爱。神就是爱；那住在爱里面的，就住在神里面，神也住在他里面。
(约翰一书 4:16 标准译本)

住在神的爱里面

你曾遇到过特别善良和体贴的人吗？好朋友就是这样——平易近人、热心想知道你过得怎么样、心无旁骛地倾听你。好朋友会使我们记起我们是谁。他们怀着仁慈与爱来倾听你所说的一切，无论是喜还是忧。

神就是这样的朋友。他倾听；他感同身受。他非常关心你，并且仁慈地回应你。事实上，神所做的不仅仅是展示爱——他就是爱。他不可能不爱，因为爱就是他的本质。他的爱是纯洁的；不自私、不脱节、不苦涩、不怨恨，也不消极。我们可以信靠这种爱；我们可以信靠神。

在约翰一书 4:16 中，我们看到了一个美好的提醒，让我们知道与神同在的生活是什么样的：“神爱我们的心，我们也知道也信。神就是爱；住在爱里面的，就是住在神里面，神也住在他里面。”

和好朋友共度时光后，你感觉如何？也许你会觉得心情安逸、步履轻快，或者你发现自己有了勇气继续前行。你甚至可能发现自己因为感受到被爱而更加爱别人。这就是住在神的爱中产生的连锁反应。当你知道并体验到神多么爱你时，你就会情不自禁地爱别人。

这就是我们被邀请去过的生活。一种了解并依赖神对我们的爱，然后因此而爱他人的生活。今天，你将如何找到神对你的爱？在你认识并体验到神对你的爱之后，一切都会改变。

祷告：
神啊，你的爱对我来说太奇妙了。我需要更加理解你的爱。我想感受被爱和被重视；我想经历你对我何等的眷顾。请你今天就帮助我更深入认识你的爱。奉耶稣的名，阿们。
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
            "speed_ratio": 1.0,
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

    # 2. Extract Verse
    verse_ref = filename_parser.extract_verse_from_text(TEXT)

    if verse_ref:
        extracted_prefix = CLI_PREFIX if CLI_PREFIX else filename_parser.extract_filename_prefix(TEXT)
        filename = filename_parser.generate_filename(verse_ref, date_str, extracted_prefix).replace(".mp3", "_volc.mp3")
    else:
        filename = f"{date_str}_volc.mp3"
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

    final.export(OUTPUT_PATH, format="mp3", bitrate="192k", tags={'title': TITLE, 'artist': PRODUCER})
    print(f"Success! Saved → {OUTPUT_PATH}")
