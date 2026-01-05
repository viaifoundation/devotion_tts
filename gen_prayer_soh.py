import asyncio
import sys
import edge_tts
from pydub import AudioSegment
import os
from bible_parser import convert_bible_reference
from date_parser import convert_dates_in_text, extract_date_from_text
from text_cleaner import clean_text
import filename_parser
import re
from datetime import datetime
import audio_mixer

import argparse
import sys

VERSION = "1.0.0"
ENABLE_BGM = False
BGM_FILE = "AmazingGrace.MP3"
TTS_RATE = "+0%"  # Default Speed (normal)
BGM_VOLUME = -20   # Default dB
BGM_INTRO_DELAY = 4000 # Default ms

# ——————————————————————————————————————————————————————————————————————————
# Argument Parsing (Moved to top to allow CLI args to affect filename)
# ——————————————————————————————————————————————————————————————————————————
if __name__ == "__main__": 
    pass

# Custom handling for -? 
if "-?" in sys.argv or "-h" in sys.argv or "--help" in sys.argv:
    print(f"Usage: python {sys.argv[0]} [--input FILE] [--bgm] [--rate RATE] [--speed SPEED] [--bgm-volume VOL] [--bgm-intro MS] [--bgm-track TRACK] [--help] [--version]")
    print("\nOptions:")
    print("  -h, --help           Show this help message and exit")
    print("  --input FILE, -i     Text file to read input from (default: stdin if piped)")
    print("  -?,                  Show this help message and exit")
    print("  --bgm                Enable background music (Default: False)")
    print("  --bgm-track TRACK    Specific BGM filename in assets/bgm (Default: AmazingGrace.MP3)")
    print("  --rate RATE          TTS Speech rate (Default: +10%)")
    print("  --speed SPEED        Same as --rate (e.g. +10%, -5%)")
    print("  --bgm-volume VOL     BGM volume adjustment in dB (Default: -20)")
    print("  --bgm-intro MS       BGM intro delay in ms (Default: 4000)")
    print("  --version, -v        Show program version")
    print("\n  (Note: You can also add 'FilenamePrefix: <Prefix>' in the input TEXT)")
    sys.exit(0)

parser = argparse.ArgumentParser(description="Generate Prayer Audio with Edge TTS (SOH Version)")
parser.add_argument("--input", "-i", type=str, help="Input text file")
parser.add_argument("--bgm", action="store_true", help="Enable background music (Default: False)")
parser.add_argument("--rate", type=str, default="+10%", help="TTS Speech rate (Default: +10%%)")
parser.add_argument("--speed", type=str, default=None, help="Alias for --rate (e.g. +10%%)")
parser.add_argument("--bgm-volume", type=int, default=-20, help="BGM volume adjustment in dB (Default: -20)")
parser.add_argument("--bgm-intro", type=int, default=4000, help="BGM intro delay in ms (Default: 4000)")
parser.add_argument("--bgm-track", type=str, default="AmazingGrace.MP3", help="Specific BGM filename (Default: AmazingGrace.MP3)")
parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {VERSION}")

args, unknown = parser.parse_known_args()

# Update global config based on CLI
if args.bgm:
    ENABLE_BGM = True

# Allow --speed to override --rate if provided
if args.speed:
    # Check if user provided just a number like "+20" or "-10"
    if not "%" in args.speed and (args.speed.startswith("+") or args.speed.startswith("-") or args.speed.isdigit()):
        TTS_RATE = f"{args.speed}%"
    else:
        TTS_RATE = args.speed
else:
    TTS_RATE = args.rate

BGM_VOLUME = args.bgm_volume
BGM_INTRO_DELAY = args.bgm_intro
BGM_FILE = args.bgm_track # If None, mixer will pick random


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

# Generate filename dynamically
# 1. Extract Date
TEXT = clean_text(TEXT)
first_line = TEXT.strip().split('\n')[0]
date_str_dash = extract_date_from_text(TEXT)

if not date_str_dash:
    date_str_dash = datetime.today().strftime("%Y-%m-%d")

# Convert YYYY-MM-DD to YYYYMMDD
date_obj = datetime.strptime(date_str_dash, "%Y-%m-%d")
date_str_compact = date_obj.strftime("%Y%m%d")

# SOH Convention: 乡音情_{yyyymmdd}.mp3
# Remove all other dynamic info from filename (Verse, Title, Model, BGM)
filename = f"乡音情_{date_str_compact}.mp3"

OUTPUT_DIR = os.path.join(os.getcwd(), "output")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
OUTPUT_PATH = os.path.join(OUTPUT_DIR, filename)
print(f"Target Output: {OUTPUT_PATH}")

# Convert Bible references in the text
TEXT = convert_bible_reference(TEXT)
TEXT = convert_dates_in_text(TEXT)
TEXT = clean_text(TEXT)

# Split the text into paragraphs
paragraphs = [p.strip() for p in re.split(r'\n{2,}', TEXT.strip()) if p.strip()]

# Mandarin Voices for Rotation
voices = [
    "zh-CN-XiaoxiaoNeural", 
    "zh-CN-YunxiNeural", 
    "zh-CN-XiaoyiNeural", 
    "zh-CN-YunyangNeural", 
    "zh-CN-YunxiaNeural",
    "zh-CN-YunjianNeural"
]

TEMP_DIR = OUTPUT_DIR + os.sep 

async def generate_audio(text, voice, output_file):
    print(f"DEBUG: Text to read: {text[:100]}...")
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=TTS_RATE)
    await communicate.save(output_file)

async def main():
    final_audio = AudioSegment.empty()
    silence = AudioSegment.silent(duration=800) 

    print(f"Processing {len(paragraphs)} paragraphs with voice rotation...")
    
    for i, para in enumerate(paragraphs):
        voice = voices[i % len(voices)]
        print(f"  > Para {i+1} ({len(para)} chars) - {voice}")
        
        temp_file = f"{TEMP_DIR}temp_prayer_p{i}.mp3"
        await generate_audio(para, voice, temp_file)
        
        try:
            segment = AudioSegment.from_mp3(temp_file)
            final_audio += segment
            if i < len(paragraphs) - 1:
                final_audio += silence
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)


    # Add Background Music (Optional)
    bgm_info_str = "None"
    if ENABLE_BGM:
        print(f"🎵 Mixing Background Music (Vol={BGM_VOLUME}dB, Intro={BGM_INTRO_DELAY}ms)...")
        final_audio = audio_mixer.mix_bgm(
            final_audio, 
            specific_filename=BGM_FILE,
            volume_db=BGM_VOLUME,
            intro_delay_ms=BGM_INTRO_DELAY
        )
        bgm_info_str = os.path.basename(BGM_FILE)
    else:
        print("🎵 Background Music: Disabled (ENABLE_BGM=False)")

    # Metadata extraction
    PRODUCER = "VI AI Foundation"
    TITLE = first_line
    ALBUM = "SOH Prayer"
    
    # Extract Verse for metadata
    verse_ref = filename_parser.extract_verse_from_text(TEXT)
    COMMENTS = f"Verse: {verse_ref}; BGM: {bgm_info_str}"

    final_audio.export(OUTPUT_PATH, format="mp3", tags={
        'title': TITLE, 
        'artist': PRODUCER,
        'album': ALBUM,
        'comments': COMMENTS
    })
    print(f"✅ Saved: {OUTPUT_PATH}")

if __name__ == "__main__":
    asyncio.run(main())
