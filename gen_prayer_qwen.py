import io
import os
import requests
import dashscope
from dashscope.audio.qwen_tts import SpeechSynthesizer
from pydub import AudioSegment

from bible_parser import convert_bible_reference
from date_parser import convert_dates_in_text, extract_date_from_text
from text_cleaner import clean_text
import filename_parser
import re
from datetime import datetime
import audio_mixer

import argparse

# CLI Args
# CLI Args
if "-?" in sys.argv:
    print(f"Usage: python {sys.argv[0]} [--input FILE] [--prefix PREFIX] [--bgm] [--bgm-track TRACK] [--bgm-volume VOL] [--bgm-intro MS] [--help]")
    print("\nOptions:")
    print("  --input FILE, -i     Text file to read input from")
    print("  --prefix PREFIX      Filename prefix (overrides 'FilenamePrefix' in text)")
    print("  --bgm                Enable background music (Default: False)")
    print("  --bgm-track TRACK    Specific BGM filename (Default: AmazingGrace.MP3)")
    print("  --bgm-volume VOL     BGM volume adjustment in dB (Default: -20)")
    print("  --bgm-intro MS       BGM intro delay in ms (Default: 4000)")
    print("  --help, -h           Show this help")
    sys.exit(0)

parser = argparse.ArgumentParser()
parser.add_argument("--input", "-i", type=str, help="Input text file")
parser.add_argument("--prefix", type=str, default=None, help="Filename prefix")
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
date_str = extract_date_from_text(TEXT)

if not date_str:
    date_str = datetime.today().strftime("%Y-%m-%d")

# 2. Extract Verse
# Handle both English () and Chinese （） parentheses, and both : and ： colons
verse_ref = filename_parser.extract_verse_from_text(TEXT)

if verse_ref:
    extracted_prefix = CLI_PREFIX if CLI_PREFIX else filename_parser.extract_filename_prefix(TEXT)
    filename = filename_parser.generate_filename(verse_ref, date_str, extracted_prefix, base_name="Prayer").replace(".mp3", "_qwen.mp3")

if ENABLE_BGM and BGM_FILE:
    bgm_base = os.path.splitext(os.path.basename(BGM_FILE))[0]
    filename = filename.replace(".mp3", f"_bgm_{bgm_base}.mp3")
else:
    extracted_prefix = CLI_PREFIX if CLI_PREFIX else filename_parser.extract_filename_prefix(TEXT)
    if extracted_prefix:
        filename = f"{extracted_prefix}_Prayer_{date_str}_qwen.mp3"
    else:
        filename = f"Prayer_{date_str}_qwen.mp3"

if ENABLE_BGM and BGM_FILE:
    bgm_base = os.path.splitext(os.path.basename(BGM_FILE))[0]
    filename = filename.replace(".mp3", f"_bgm_{bgm_base}.mp3")
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
        final_audio = audio_mixer.mix_bgm(final_audio, specific_filename=BGM_FILE, volume_db=BGM_VOLUME, intro_delay_ms=BGM_INTRO_DELAY)
    else:
        print("🎵 Background Music: Disabled (ENABLE_BGM=False)")

    # Metadata extraction
    PRODUCER = "VI AI Foundation"
    TITLE = TEXT.strip().split('\n')[0]

    final_audio.export(OUTPUT_PATH, format="mp3", bitrate="192k", tags={'title': TITLE, 'artist': PRODUCER})
    print(f"✅ Saved: {OUTPUT_PATH}")
