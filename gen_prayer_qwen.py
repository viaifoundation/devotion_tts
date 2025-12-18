import io
import os
import requests
import dashscope
from dashscope.audio.qwen_tts import SpeechSynthesizer
from pydub import AudioSegment

from bible_parser import convert_bible_reference
from date_parser import convert_dates_in_text
from text_cleaner import clean_text
import filename_parser
import re
from datetime import datetime
import audio_mixer

import argparse

# CLI Args
if "-?" in sys.argv:
    print(f"Usage: python {sys.argv[0]} [--prefix PREFIX] [--help]")
    print("Options:")
    print("  --prefix PREFIX      Filename prefix (overrides 'FilenamePrefix' in text)")
    print("  --help, -h           Show this help")
    sys.exit(0)

parser = argparse.ArgumentParser()
parser.add_argument("--prefix", type=str, default=None, help="Filename prefix")
args, unknown = parser.parse_known_args()
CLI_PREFIX = args.prefix

ENABLE_BGM = False
BGM_FILE = "AmazingGrace.MP3"

TEXT = """
“犹大地的伯利恒啊， 你在犹大诸城中并不是最小的； 因为将来有一位君王要从你那里出来， 牧养我以色列民。」”
‭‭马太福音‬ ‭2‬:‭6‬ ‭CUNPSS-神‬‬

神亲爱的主耶稣基督，我们在纪念你诞生的日子向你感恩，因你的诞生给我们带来了永活的泉源，更为我们带来了永生的盼望，主啊，我们为把你旨意传遍世界，乡音更好的为主的福音做了美好榜样，主啊，你的道路高过任何人的道路，乡音就是奉主的名走主你引领的道路，带领更多的人信主，为主做了美好的见证，主，求你为今年的乡音预备各样的资源，并𧶽不同地区同工们合一答配的心，把主的福音传到地极，我们这样的祷告，是奉主基督的名。阿们！
"""

# Setup API Key
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
if not dashscope.api_key:
    # Try reading from secrets file locally if env var not set
    secrets_path = os.path.expanduser("~/.secrets")
    if os.path.exists(secrets_path):
        with open(secrets_path, "r") as f:
            for line in f:
                if line.startswith("DASHSCOPE_API_KEY"):
                    dashscope.api_key = line.split("=")[1].strip()
                    break
    
    if not dashscope.api_key:
         print("⚠️ Warning: DASHSCOPE_API_KEY not found in env or ~/.secrets. Script may fail.")



# Generate filename dynamically
# 1. Extract Date
TEXT = clean_text(TEXT)
date_match = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", TEXT)
if date_match:
    m, d, y = date_match.groups()
    date_str = f"{y}-{int(m):02d}-{int(d):02d}"
else:
    # Try YYYY-MM-DD
    date_match = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", TEXT)
    if date_match:
        y, m, d = date_match.groups()
        date_str = f"{y}-{int(m):02d}-{int(d):02d}"
    else:
        date_str = datetime.today().strftime("%Y-%m-%d")

# 2. Extract Verse
# Handle both English () and Chinese （） parentheses, and both : and ： colons
verse_ref = filename_parser.extract_verse_from_text(TEXT)

if verse_ref:
    extracted_prefix = CLI_PREFIX if CLI_PREFIX else filename_parser.extract_filename_prefix(TEXT)
    filename = filename_parser.generate_filename(verse_ref, date_str, extracted_prefix, base_name="Prayer").replace(".mp3", "_qwen.mp3")
else:
    filename = f"SOH_Sound_of_Home_Prayer_{date_str}_qwen.mp3"
OUTPUT_DIR = os.path.join(os.getcwd(), "output")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
OUTPUT_PATH = os.path.join(OUTPUT_DIR, filename)
print(f"Target Output: {OUTPUT_PATH}")

TEXT = convert_bible_reference(TEXT)
TEXT = convert_dates_in_text(TEXT)
TEXT = clean_text(TEXT)

paragraphs = [p.strip() for p in re.split(r'\n{2,}', TEXT.strip()) if p.strip()]

# Supported Qwen-TTS voices
voices = ["Cherry", "Serena", "Ethan", "Chelsie"]

def speak(text: str, voice: str) -> AudioSegment:
    print(f"DEBUG: Text to read: {text[:100]}...")
    # Qwen Limit check? It's usually good for short paragraphs.
    resp = SpeechSynthesizer.call(
        model="qwen-tts",
        text=text,
        voice=voice,
        format="wav",
        sample_rate=24000
    )
    if resp.status_code != 200:
        raise Exception(f"API Error: {resp.message}")
    
    audio_url = resp.output.audio["url"]
    audio_data = requests.get(audio_url).content
    return AudioSegment.from_wav(io.BytesIO(audio_data))

print(f"Processing {len(paragraphs)} paragraphs with voice rotation...")

final_audio = AudioSegment.empty()
silence = AudioSegment.silent(duration=800, frame_rate=24000)

for i, para in enumerate(paragraphs):
    voice = voices[i % len(voices)]
    print(f"  > Para {i+1} ({len(para)} chars) - {voice}")
    
    try:
        segment = speak(para, voice)
        final_audio += segment
        if i < len(paragraphs) - 1:
            final_audio += silence
    except Exception as e:
        print(f"❌ Error generating para {i}: {e}")


    # Add Background Music (Optional)
    if ENABLE_BGM:
        print("🎵 Mixing Background Music...")
        final_audio = audio_mixer.mix_bgm(final_audio, specific_filename=BGM_FILE)
    else:
        print("🎵 Background Music: Disabled (ENABLE_BGM=False)")

    # Metadata extraction
    PRODUCER = "VI AI Foundation"
    TITLE = TEXT.strip().split('\n')[0]

    final_audio.export(OUTPUT_PATH, format="mp3", bitrate="192k", tags={'title': TITLE, 'artist': PRODUCER})
    print(f"✅ Saved: {OUTPUT_PATH}")
