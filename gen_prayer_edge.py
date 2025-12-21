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
TTS_RATE = "+10%"  # Default Speed
BGM_VOLUME = -20   # Default dB
BGM_INTRO_DELAY = 4000 # Default ms

# ——————————————————————————————————————————————————————————————————————————
# Argument Parsing (Moved to top to allow CLI args to affect filename)
# ——————————————————————————————————————————————————————————————————————————
if __name__ == "__main__": 
    # Only parse if run as script, but we need the variables to be set for the script to validly execute top-level code
    # Simple hack: just parse it.
    pass

# Custom handling for -? 
if "-?" in sys.argv:
    print(f"Usage: python {sys.argv[0]} [--bgm] [--rate RATE] [--speed SPEED] [--bgm-volume VOL] [--bgm-intro MS] [--bgm-track TRACK] [--prefix PREFIX] [--help] [--version]")
    print("\nOptions:")
    print("  -h, --help           Show this help message and exit")
    print("  -?,                  Show this help message and exit")
    print("  --bgm                Enable background music (Default: False)")
    print("  --bgm-track TRACK    Specific BGM filename in assets/bgm (Default: AmazingGrace.MP3)")
    print("  --rate RATE          TTS Speech rate (Default: +10%)")
    print("  --speed SPEED        Same as --rate (e.g. +10%, -5%)")
    print("  --bgm-volume VOL     BGM volume adjustment in dB (Default: -20)")
    print("  --bgm-intro MS       BGM intro delay in ms (Default: 4000)")
    print("  --prefix PREFIX      Filename prefix (overrides 'FilenamePrefix' in text)")
    print("  --version, -v        Show program version")
    print("\n  (Note: You can also add 'FilenamePrefix: <Prefix>' in the input TEXT)")
    sys.exit(0)

parser = argparse.ArgumentParser(description="Generate Prayer Audio with Edge TTS")
parser.add_argument("--bgm", action="store_true", help="Enable background music (Default: False)")
parser.add_argument("--rate", type=str, default="+10%", help="TTS Speech rate (Default: +10%%)")
parser.add_argument("--speed", type=str, default=None, help="Alias for --rate (e.g. +10%%)")
parser.add_argument("--bgm-volume", type=int, default=-20, help="BGM volume adjustment in dB (Default: -20)")
parser.add_argument("--bgm-intro", type=int, default=4000, help="BGM intro delay in ms (Default: 4000)")
parser.add_argument("--bgm-track", type=str, default="AmazingGrace.MP3", help="Specific BGM filename (Default: AmazingGrace.MP3)")
parser.add_argument("--prefix", type=str, default=None, help="Filename prefix (e.g. MyPrefix)")
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
CLI_PREFIX = args.prefix



TEXT = """
天路音樂 「鄉音情」12月21日禱告

亲爱的天父上帝，
在这纪念救主耶稣基督降生的圣诞佳节，
我们满心感恩来到祢的施恩宝座前，
为「乡音」事工中所有忠心摆上的筹备同工，
以及他们宝贵的家人向祢献上感谢。

主啊，祢看见他们在繁忙、压力与牺牲中的忠心，
也看见他们为福音、为合一所付出的每一滴汗水。
求祢亲自纪念他们一切看得见与看不见的辛劳，
以祢的恩典与平安亲自报答他们。

我们奉主耶稣的名祷告，
求祢用宝血遮盖每一位同工和他们的家人，
保守身体健康、心灵平安、家庭和睦，
在疲惫中得力，在挑战中得智慧，
在软弱时被祢的爱再次托住。

主啊，求祢设立属灵的保护墙，
阻挡并捆绑一切来自魔鬼的攻击、搅扰、分裂与灰心，
不容仇敌在任何层面有可乘之机。
宣告「乡音」的一切筹备工作都在祢的权柄与带领之下，
凡所计划的尽都顺利，凡所行的都蒙祢喜悦。

愿圣灵继续引导每一个细节，
使团队同心合意、沟通顺畅、时间与资源充足，
让筹备工作在平安与喜乐中完成，
使更多生命因「乡音」得着安慰、盼望与更新。

最后，主啊，
愿基督降生的真光，照亮每一位同工和他们的家庭，
使平安、喜乐与盼望充满这个圣诞节。

圣诞快乐！愿主的爱常与大家同在。 

我们如此祷告、仰望、交托，
奉我主耶稣基督得胜的名祈求，

阿们。

"""

# Generate filename dynamically
# 1. Extract Date
TEXT = clean_text(TEXT)
first_line = TEXT.strip().split('\n')[0]
date_str = extract_date_from_text(TEXT)

if not date_str:
    date_str = datetime.today().strftime("%Y-%m-%d")

# 2. Extract Verse
# Handle both English () and Chinese （） parentheses, and both : and ： colons
verse_ref = filename_parser.extract_verse_from_text(TEXT)

if verse_ref:
    extracted_prefix = CLI_PREFIX if CLI_PREFIX else filename_parser.extract_filename_prefix(TEXT)
    filename = filename_parser.generate_filename(verse_ref, date_str, extracted_prefix, base_name="Prayer").replace(".mp3", "_edge.mp3")
else:
    extracted_prefix = CLI_PREFIX if CLI_PREFIX else filename_parser.extract_filename_prefix(TEXT)
    if extracted_prefix:
        filename = f"{extracted_prefix}_Prayer_{date_str}_edge.mp3"
    else:
        filename = f"Prayer_{date_str}_edge.mp3"

if ENABLE_BGM and BGM_FILE:
    bgm_base = os.path.splitext(os.path.basename(BGM_FILE))[0]
    filename = filename.replace(".mp3", f"_bgm_{bgm_base}.mp3")

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
    if ENABLE_BGM:
        print(f"🎵 Mixing Background Music (Vol={BGM_VOLUME}dB, Intro={BGM_INTRO_DELAY}ms)...")
        final_audio = audio_mixer.mix_bgm(
            final_audio, 
            specific_filename=BGM_FILE,
            volume_db=BGM_VOLUME,
            intro_delay_ms=BGM_INTRO_DELAY
        )
    else:
        print("🎵 Background Music: Disabled (ENABLE_BGM=False)")

    # Metadata extraction
    PRODUCER = "VI AI Foundation"
    TITLE = TEXT.strip().split('\n')[0]

    # Metadata extraction
    PRODUCER = "VI AI Foundation"
    TITLE = TEXT.strip().split('\n')[0]

    final_audio.export(OUTPUT_PATH, format="mp3", tags={'title': TITLE, 'artist': PRODUCER})
    print(f"✅ Saved: {OUTPUT_PATH}")

if __name__ == "__main__":
    asyncio.run(main())
