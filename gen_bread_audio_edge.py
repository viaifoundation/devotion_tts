
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
TTS_RATE = "+10%"  # Default Speed
BGM_VOLUME = -20   # Default dB
BGM_INTRO_DELAY = 4000 # Default ms

# Custom handling for -? 
if "-?" in sys.argv:
    print(f"Usage: python {sys.argv[0]} [--input FILE] [--bgm] [--rate RATE] [--speed SPEED] [--bgm-volume VOL] [--bgm-intro MS] [--bgm-track TRACK] [--help] [--version]")
    print("\nOptions:")
    print("  -h, --help           Show this help message and exit")
    print("  --input FILE, -i     Text file to read input from")
    print("  -?,                  Show this help message and exit")
    print("  --bgm                Enable background music (Default: False)")
    print("  --bgm-track TRACK    Specific BGM filename in assets/bgm (Default: AmazingGrace.MP3)")
    print("  --rate RATE          TTS Speech rate (Default: +10%)")
    print("  --speed SPEED        Alias for --rate (e.g. +10%, -5%)")
    print("  --bgm-volume VOL     BGM volume adjustment in dB (Default: -20)")
    print("  --bgm-intro MS       BGM intro delay in ms (Default: 4000)")
    print("  --version, -v        Show program version")
    sys.exit(0)

parser = argparse.ArgumentParser(description="Generate Bread Audio with Edge TTS")
parser.add_argument("--input", "-i", type=str, help="Input text file")
parser.add_argument("--bgm", action="store_true", help="Enable background music (Default: False)")
parser.add_argument("--rate", type=str, default="+10%", help="TTS Speech rate (Default: +10%%)")
parser.add_argument("--speed", type=str, default=None, help="Alias for --rate (e.g. +10%%)")
parser.add_argument("--bgm-volume", type=int, default=-20, help="BGM volume adjustment in dB (Default: -20)")
parser.add_argument("--bgm-intro", type=int, default=4000, help="BGM intro delay in ms (Default: 4000)")
parser.add_argument("--bgm-track", type=str, default="AmazingGrace.MP3", help="Specific BGM filename (Default: AmazingGrace.MP3)")
parser.add_argument("--prefix", type=str, default=None, help="Filename prefix (e.g. MyPrefix)")
parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {VERSION}")

args, unknown = parser.parse_known_args()

CLI_PREFIX = args.prefix

# Update global config based on CLI
if args.bgm:
    ENABLE_BGM = True

# Allow --speed to override --rate if provided
if args.speed:
    if not "%" in args.speed and (args.speed.startswith("+") or args.speed.startswith("-") or args.speed.isdigit()):
        TTS_RATE = f"{args.speed}%"
    else:
        TTS_RATE = args.speed
else:
    TTS_RATE = args.rate

BGM_VOLUME = args.bgm_volume
BGM_INTRO_DELAY = args.bgm_intro
BGM_FILE = args.bgm_track


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

"""
Locale,ShortName,Gender,Voice Personalities,Content Categories
zh-CN,zh-CN-XiaoxiaoNeural,Female,Warm,"News, Novel"
zh-CN,zh-CN-XiaoyiNeural,Female,Lively,"Cartoon, Novel"
zh-CN,zh-CN-YunjianNeural,Male,Passion,"Sports, Novel"
zh-CN,zh-CN-YunxiNeural,Male,"Lively, Sunshine",Novel
zh-CN,zh-CN-YunxiaNeural,Male,Cute,"Cartoon, Novel"
zh-CN,zh-CN-YunyangNeural,Male,"Professional, Reliable",News
zh-CN-liaoning,zh-CN-liaoning-XiaobeiNeural,Female,Humorous,Dialect
zh-CN-shaanxi,zh-CN-shaanxi-XiaoniNeural,Female,Bright,Dialect
zh-HK,zh-HK-HiuGaaiNeural,Female,"Friendly, Positive",General
zh-HK,zh-HK-HiuMaanNeural,Female,"Friendly, Positive",General
zh-HK,zh-HK-WanLungNeural,Male,"Friendly, Positive",General
zh-TW,zh-TW-HsiaoChenNeural,Female,"Friendly, Positive",General
zh-TW,zh-TW-HsiaoYuNeural,Female,"Friendly, Positive",General
zh-TW,zh-TW-YunJheNeural,Male,"Friendly, Positive",General
"""
"""
Locale,ShortName,Gender,Voice Personalities,Content Categories
zh-CN,zh-CN-XiaoxiaoNeural,Female,Warm,"News, Novel"
zh-CN,zh-CN-XiaoyiNeural,Female,Lively,"Cartoon, Novel"
zh-CN,zh-CN-YunjianNeural,Male,Passion,"Sports, Novel"
zh-CN,zh-CN-YunxiNeural,Male,"Lively, Sunshine",Novel
zh-CN,zh-CN-YunxiaNeural,Male,Cute,"Cartoon, Novel"
zh-CN,zh-CN-YunyangNeural,Male,"Professional, Reliable",News
zh-CN,zh-CN-XiaochenNeural,Female,Warm,General
zh-CN,zh-CN-XiaohanNeural,Female,Cheerful,"Novel, Cartoon"
zh-CN,zh-CN-XiaomoNeural,Female,Emotional,"Novel, Cartoon"
zh-CN,zh-CN-XiaoqiuNeural,Female,Lively,General
zh-CN,zh-CN-XiaoruiNeural,Female,Angry,"Novel, Cartoon"
zh-CN,zh-CN-XiaoshuangNeural,Female,Cute,"Cartoon, Novel"
zh-CN,zh-CN-XiaoxuanNeural,Female,"Chat, Assistant","Novel, CustomerService"
zh-CN,zh-CN-XiaoyanNeural,Female,Professional,"News, Novel"
zh-CN,zh-CN-XiaoyouNeural,Female,Cheerful,"Cartoon, Novel"
zh-CN,zh-CN-XiaozhenNeural,Female,Friendly,General
zh-CN,zh-CN-YunhaoNeural,Male,Professional,"News, Novel"
zh-CN,zh-CN-YunxiaoNeural,Male,Friendly,General
zh-CN,zh-CN-YunyeNeural,Male,Serious,"Novel, Narration"
zh-CN,zh-CN-YunzeNeural,Male,Calm,"Novel, Narration"
zh-CN-liaoning,zh-CN-liaoning-XiaobeiNeural,Female,Humorous,Dialect
zh-CN-shaanxi,zh-CN-shaanxi-XiaoniNeural,Female,Bright,Dialect
zh-CN-sichuan,zh-CN-sichuan-YunxiNeural,Male,Lively,Dialect
zh-CN-wuu,zh-CN-wuu-XiaotongNeural,Female,Friendly,Dialect
zh-CN-wuu,zh-CN-wuu-YunzheNeural,Male,Professional,Dialect
zh-CN-yue,zh-CN-yue-XiaoshanNeural,Female,Friendly,Dialect
zh-CN-yue,zh-CN-yue-YunSongNeural,Male,Professional,Dialect
zh-HK,zh-HK-HiuGaaiNeural,Female,"Friendly, Positive",General
zh-HK,zh-HK-HiuMaanNeural,Female,"Friendly, Positive",General
zh-HK,zh-HK-WanLungNeural,Male,"Friendly, Positive",General
zh-TW,zh-TW-HsiaoChenNeural,Female,"Friendly, Positive",General
zh-TW,zh-TW-HsiaoYuNeural,Female,"Friendly, Positive",General
zh-TW,zh-TW-YunJheNeural,Male,"Friendly, Positive",General
zh-TW,zh-TW-HanHanNeural,Female,Friendly,General
"""
# Voice settings
FIRST_VOICE = "zh-CN-XiaoxiaoNeural"  # First voice (introduction)
SECOND_VOICE = "zh-CN-YunyangNeural"  # Second voice (main content)
#FIRST_VOICE = "zh-HK-WanLungNeural"  # Second voice (main content)
#SECOND_VOICE = "zh-HK-HiuGaaiNeural"  # First voice (introduction)
#SECOND_VOICE = "zh-CN-XiaoyiNeural"  # Second voice (main content)
#FIRST_VOICE = "zh-HK-WanLungNeural"  # First voice (introduction)
#SECOND_VOICE = "zh-HK-HiuGaaiNeural"  # Second voice (main content)
#SECOND_VOICE = "zh-HK-HiuMaanNeural"  # Second voice (main content)
#SECOND_VOICE = "zh-HK-WanLungNeural"  # First voice (introduction)
#FIRST_VOICE = "zh-HK-HiuGaaiNeural"  # Second voice (main content)
#FIRST_VOICE = "zh-TW-HsiaoChenNeural"  # First voice (introduction)
#SECOND_VOICE = "zh-TW-YunJheNeural"  # Second voice (main content)
FIRST_VOICE = "zh-CN-XiaoxiaoNeural"  # Second voice (main content)
SECOND_VOICE = "zh-CN-YunyangNeural"  # First voice (introduction)
#FIRST_VOICE = "zh-CN-YunyangNeural"  # First voice (introduction)
#SECOND_VOICE = "zh-CN-XiaoxiaoNeural"  # Second voice (main content)
#SECOND_VOICE = "zh-HK-WanLungNeural"  # First voice (introduction)
#FIRST_VOICE = "zh-HK-HiuGaaiNeural"  # Second voice (main content)
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
