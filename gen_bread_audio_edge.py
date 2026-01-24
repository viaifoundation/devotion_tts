
import asyncio
import sys
import edge_tts
from pydub import AudioSegment
import os
import re
from bible_parser import convert_bible_reference
from text_cleaner import clean_text

from text_cleaner import clean_text

import argparse
import audio_mixer

VERSION = "1.0.0"
ENABLE_BGM = False
BGM_FILE = "AmazingGrace.MP3" # Default to AmazingGrace
TTS_RATE = "+0%"  # Default Speed (normal)
BGM_VOLUME = -20   # Default dB
BGM_INTRO_DELAY = 4000 # Default ms

# Custom handling for -? 
if "-?" in sys.argv or "-h" in sys.argv or "--help" in sys.argv:
    print(f"Usage: python {sys.argv[0]} [OPTIONS]")
    print("\nOptions:")
    print("  --input FILE, -i     Text file to read input from")
    print("  --prefix PREFIX      Filename prefix")
    print("  --voice MODE         Voice mode: male, female, two, four, six (Default: two)")
    print("  --voices LIST        Custom voices (CSV, overrides --voice)")
    print("                       e.g. zh-CN-YunyangNeural,zh-CN-XiaoxiaoNeural")
    print("  --speed SPEED        Speech rate: +10%, --speed=-10% (Default: +0%)")
    print("  --bgm                Enable background music")
    print("  --bgm-track TRACK    BGM filename (Default: AmazingGrace.MP3)")
    print("  --bgm-volume VOL     BGM volume in dB (Default: -20)")
    print("  --bgm-intro MS       BGM intro delay in ms (Default: 4000)")
    print("  -?, -h, --help       Show this help")
    print("\nVoice Modes:")
    print("  male    - Single male voice (YunyangNeural)")
    print("  female  - Single female voice (XiaoxiaoNeural)")
    print("  two     - Two voices: intro=female, body=male (Default)")
    print("  four    - Rotate 4 voices (2 male + 2 female)")
    print("  six     - Rotate all 6 zh-CN voices")
    print("\nExamples:")
    print(f"  python {sys.argv[0]} -i input.txt --voice male")
    print(f"  python {sys.argv[0]} -i input.txt --voice two --bgm")
    sys.exit(0)

parser = argparse.ArgumentParser(description="Generate Bread Audio with Edge TTS", add_help=False)
parser.add_argument("--input", "-i", type=str, help="Input text file")
parser.add_argument("--prefix", type=str, default=None, help="Filename prefix")
parser.add_argument("--voice", type=str, default="two", choices=["male", "female", "two", "four", "six"],
                    help="Voice mode: male, female, two, four, six")
parser.add_argument("--voices", type=str, default=None,
                    help="Custom voices (CSV format, overrides --voice)")
parser.add_argument("--speed", type=str, default=None, help="Speech rate (e.g. +10%%)")
parser.add_argument("--bgm", action="store_true", help="Enable background music")
parser.add_argument("--bgm-track", type=str, default="AmazingGrace.MP3", help="BGM filename")
parser.add_argument("--bgm-volume", type=int, default=-20, help="BGM volume in dB")
parser.add_argument("--bgm-intro", type=int, default=4000, help="BGM intro delay in ms")

args, unknown = parser.parse_known_args()

CLI_PREFIX = args.prefix

# Update global config based on CLI
if args.bgm:
    ENABLE_BGM = True

# Speed parsing
if args.speed:
    if not "%" in args.speed and (args.speed.startswith("+") or args.speed.startswith("-") or args.speed.isdigit()):
        TTS_RATE = f"{args.speed}%"
    else:
        TTS_RATE = args.speed

BGM_VOLUME = args.bgm_volume
BGM_INTRO_DELAY = args.bgm_intro
BGM_FILE = args.bgm_track

# Voice presets
VOICE_MALE_1 = "zh-CN-YunyangNeural"    # Professional, Reliable
VOICE_MALE_2 = "zh-CN-YunxiNeural"      # Lively, Sunshine
VOICE_MALE_3 = "zh-CN-YunjianNeural"    # Passion
VOICE_FEMALE_1 = "zh-CN-XiaoxiaoNeural"  # Warm
VOICE_FEMALE_2 = "zh-CN-XiaoyiNeural"    # Lively
VOICE_FEMALE_3 = "zh-CN-YunxiaNeural"    # Cute

# Voice mode configuration
# --voices overrides --voice if provided
if args.voices:
    VOICES = [v.strip() for v in args.voices.split(",") if v.strip()]
    print(f"🎤 Custom voices: {', '.join(VOICES)}")
elif args.voice == "male":
    VOICES = [VOICE_MALE_1]
    print(f"🎤 Voice mode: male ({VOICE_MALE_1})")
elif args.voice == "female":
    VOICES = [VOICE_FEMALE_1]
    print(f"🎤 Voice mode: female ({VOICE_FEMALE_1})")
elif args.voice == "four":
    VOICES = [VOICE_MALE_1, VOICE_FEMALE_1, VOICE_MALE_2, VOICE_FEMALE_2]
    print(f"🎤 Voice mode: four (rotating 4 voices)")
elif args.voice == "six":
    VOICES = [VOICE_MALE_1, VOICE_FEMALE_1, VOICE_MALE_2, VOICE_FEMALE_2, VOICE_MALE_3, VOICE_FEMALE_3]
    print(f"🎤 Voice mode: six (rotating 6 voices)")
else:  # two (default for bread)
    VOICES = [VOICE_FEMALE_1, VOICE_MALE_1]  # Intro=female, Body=male
    print(f"🎤 Voice mode: two (intro={VOICE_FEMALE_1}, body={VOICE_MALE_1})")

FIRST_VOICE = VOICES[0]
SECOND_VOICE = VOICES[1] if len(VOICES) > 1 else VOICES[0]


# Cleaned Chinese devotional text (replace with actual text)
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




# Convert Bible references in the text (e.g., '罗马书 1:17' to '罗马书 1章17節')
TEXT = convert_bible_reference(TEXT)
TEXT = clean_text(TEXT)

# Split the text into paragraphs
paragraphs = [p.strip() for p in re.split(r'\n{2,}', TEXT.strip()) if p.strip()]
first_paragraphs = [paragraphs[0]]  # First paragraph (introduction)
second_paragraphs = ["\n\n".join(paragraphs[1:])]  # All remaining paragraphs (main content)
first_line = "Bread_Audio"

from datetime import datetime
import re

# Generate filename dynamically
# 1. Try to find date in text like "12月15日" or "12/15"
TEXT = clean_text(TEXT)
date_match = re.search(r"(\d{1,2})月(\d{1,2})日", TEXT)
if date_match:
    m, d = date_match.groups()
    current_year = datetime.now().year
    # Handle year boundary if needed (e.g. text is for next year), but simple current year is safe for now
    date_str = f"{current_year}{int(m):02d}{int(d):02d}"
else:
    # 2. Fallback to script modification time
    try:
        # Use the modification time of this script as the date
        mod_timestamp = os.path.getmtime(__file__)
        date_str = datetime.fromtimestamp(mod_timestamp).strftime("%Y%m%d")
        print(f"⚠️ Date not found in text. Using script modification date: {date_str}")
    except Exception as e:
        # 3. Fallback to today
        date_str = datetime.today().strftime("%Y%m%d")
        print(f"⚠️ Date not found in file stats. Using today's date: {date_str}")
        
import filename_parser
extracted_prefix = CLI_PREFIX if CLI_PREFIX else filename_parser.extract_filename_prefix(TEXT)

basename = f"Bread_{date_str}_edge.mp3"
if extracted_prefix:
    filename = f"{extracted_prefix}_{basename}"
else:
    filename = basename

if ENABLE_BGM and BGM_FILE:
    bgm_base = os.path.splitext(os.path.basename(BGM_FILE))[0]
    filename = filename.replace(".mp3", f"_bgm_{bgm_base}.mp3")

OUTPUT_DIR = os.path.join(os.getcwd(), "output")
OUTPUT_PATH = os.path.join(OUTPUT_DIR, filename)
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
OUTPUT_PATH = os.path.join(OUTPUT_DIR, f"bread_{date_str}_edge.mp3")
TEMP_DIR = OUTPUT_DIR + os.sep  # For temp files
TEMP_FIRST = os.path.join(OUTPUT_DIR, "temp_first_bread.mp3")
TEMP_SECOND = os.path.join(OUTPUT_DIR, "temp_second_bread.mp3")

async def generate_audio(text, voice, output_file):
    print(f"DEBUG: Text to read: {text[:100]}...")
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=TTS_RATE)
    await communicate.save(output_file)

async def main():
    # Generate and collect first voice audio segments (for first paragraph)
    first_segments = []
    for i, para in enumerate(first_paragraphs):
        temp_file = f"{TEMP_DIR}temp_first_bread_{i}.mp3"
        await generate_audio(para, FIRST_VOICE, temp_file)
        print(f"✅ Generated first voice chunk {i}: {temp_file}")
        segment = AudioSegment.from_mp3(temp_file)
        first_segments.append(segment)
        os.remove(temp_file)  # Clean up immediately

    # Concatenate first segments with short silence between
    silence = AudioSegment.silent(duration=500)  # 0.5s pause; adjust as needed
    first_audio = AudioSegment.empty()
    for i, segment in enumerate(first_segments):
        first_audio += segment
        if i < len(first_segments) - 1:  # Add silence between segments, not after last
            first_audio += silence

    # Generate and collect second voice audio segments (for remaining paragraphs)
    second_segments = []
    for i, para in enumerate(second_paragraphs):
        temp_file = f"{TEMP_DIR}temp_second_bread_{i}.mp3"
        await generate_audio(para, SECOND_VOICE, temp_file)
        print(f"✅ Generated second voice chunk {i}: {temp_file}")
        segment = AudioSegment.from_mp3(temp_file)
        second_segments.append(segment)
        os.remove(temp_file)  # Clean up immediately

    # Concatenate second segments with short silence between
    second_audio = AudioSegment.empty()
    for i, segment in enumerate(second_segments):
        second_audio += segment
        if i < len(second_segments) - 1:  # Add silence between segments, not after last
            second_audio += silence

    # Combine first and second with a pause between sections
    combined_audio = first_audio + silence + second_audio

    # Add Background Music (Optional)
    if ENABLE_BGM:
        print(f"🎵 Mixing Background Music (Vol={BGM_VOLUME}dB, Intro={BGM_INTRO_DELAY}ms)...")
        combined_audio = audio_mixer.mix_bgm(
            combined_audio, 
            specific_filename=BGM_FILE,
            volume_db=BGM_VOLUME,
            intro_delay_ms=BGM_INTRO_DELAY
        )

    # Metadata extraction
    PRODUCER = "VI AI Foundation"
    TITLE = TEXT.strip().split('\n')[0]

    combined_audio.export(OUTPUT_PATH, format="mp3", tags={'title': TITLE, 'artist': PRODUCER})
    print(f"✅ Combined audio saved: {OUTPUT_PATH}")




if __name__ == "__main__":


    asyncio.run(main())
