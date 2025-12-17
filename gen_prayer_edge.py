import asyncio
import sys
import edge_tts
from pydub import AudioSegment
import os
from bible_parser import convert_bible_reference
from date_parser import convert_dates_in_text
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
BGM_VOLUME = -12   # Default dB
BGM_INTRO_DELAY = 4000 # Default ms


TEXT = """
“犹大地的伯利恒啊， 你在犹大诸城中并不是最小的； 因为将来有一位君王要从你那里出来， 牧养我以色列民。」”
‭‭马太福音‬ ‭2‬:‭6‬ ‭CUNPSS-神‬‬

神亲爱的主耶稣基督，我们在纪念你诞生的日子向你感恩，因你的诞生给我们带来了永活的泉源，更为我们带来了永生的盼望，主啊，我们为把你旨意传遍世界，乡音更好的为主的福音做了美好榜样，主啊，你的道路高过任何人的道路，乡音就是奉主的名走主你引领的道路，带领更多的人信主，为主做了美好的见证，主，求你为今年的乡音预备各样的资源，并𧶽不同地区同工们合一答配的心，把主的福音传到地极，我们这样的祷告，是奉主基督的名。阿们！
"""

# Generate filename dynamically
# 1. Extract Date (Try to find a date in the text, otherwise use today)
first_line = TEXT.strip().split('\n')[0]
date_match = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", TEXT) # Search in whole text for 34:8 case might assume date is elsewhere or use today
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
    # Remove VOTD prefix if filename_parser adds it (it often does "VOTD_...")
    raw_filename = filename_parser.generate_filename(verse_ref, date_str)
    # Strip "VOTD_" if present
    if raw_filename.startswith("VOTD_"):
        raw_filename = raw_filename[5:]
    filename = f"prayer_{raw_filename.replace('.mp3', '')}_edge.mp3"
else:
    filename = f"prayer_{date_str}_edge.mp3"

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

    final_audio.export(OUTPUT_PATH, format="mp3")
    print(f"✅ Saved: {OUTPUT_PATH}")

if __name__ == "__main__":
    # Custom handling for -? (which argparse doesn't support natively as a flag often)
    if "-?" in sys.argv:
        print(f"Usage: python {sys.argv[0]} [--bgm] [--rate RATE] [--bgm-volume VOL] [--bgm-intro MS] [--help] [--version]")
        print("\nOptions:")
        print("  -h, --help           Show this help message and exit")
        print("  -?,                  Show this help message and exit")
        print("  --bgm                Enable background music")
        print("  --rate RATE          TTS Speech rate (default: +10%)")
        print("  --bgm-volume VOL     BGM volume adjustment in dB (default: -12)")
        print("  --bgm-intro MS       BGM intro delay in ms (default: 4000)")
        print("  --version, -v        Show program version")
        sys.exit(0)

    parser = argparse.ArgumentParser(description="Generate Prayer Audio with Edge TTS")
    parser.add_argument("--bgm", action="store_true", help="Enable background music")
    parser.add_argument("--rate", type=str, default="+10%", help="TTS Speech rate (e.g. +10%%)")
    parser.add_argument("--bgm-volume", type=int, default=-12, help="BGM volume adjustment in dB")
    parser.add_argument("--bgm-intro", type=int, default=4000, help="BGM intro delay in ms")
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {VERSION}")
    
    args = parser.parse_args()
    
    # Update global config based on CLI
    if args.bgm:
        ENABLE_BGM = True
    
    TTS_RATE = args.rate
    BGM_VOLUME = args.bgm_volume
    BGM_INTRO_DELAY = args.bgm_intro
        
    asyncio.run(main())
