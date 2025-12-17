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
天路音樂 「鄉音情」12月17日禱告

親愛的天父上帝，
我們滿懷感恩與敬畏來到祢面前，
感謝祢一路的帶領與看顧。

主啊，我們首先要向祢獻上感恩——
感謝祢的恩典與信實，
灣區「鄉音」場地 Redemption Church 已正式完成簽約！
這不是人的能力，乃是祢親自為我們開路。
一切榮耀、頌讚都歸給坐在寶座上的主。

主啊，我們也為接下來的道路向祢呼求：
懇切為 聖地牙哥 UCSD – The Epstein Family Amphitheater 的租借與簽約過程禱告。
求祢親自介入，
在每一個溝通、每一個流程、每一個決定中掌權，
除去一切攔阻與不確定，
使一切細節都按祢的旨意、平安順利地完成。
願福音的門，按祢的時間，在校園中被敞開。

主啊，我們將南北加州四場「鄉音」事工一同交託在祢手中——
求祢祝福宣傳推廣的展開，
使該聽見的人能聽見，該來到的人能被吸引；
也求祢親自供應贊助與籌款的一切需要，
因為祢是豐盛的主，從不誤事。

我們也為節目的籌備與執行製作流程禱告，
求祢賜下從天而來的智慧、秩序與專業，
使每一個環節彼此配搭、同心合一，
不為表演，乃為榮耀祢的名。

主啊，也懇切為所有同工及他們的家人禱告，
求祢保守身體健康、心力剛強，
在忙碌與壓力中仍得著從祢而來的平安與喜樂。
讓我們在愛中同工，在合一中前行。

天父，我們深信：
若不是耶和華建造房屋，建造的人就枉然勞力。
願我們在主裡同心合意，
一同見證祢奇妙、榮耀的作為。

以上禱告，
是奉靠我主耶穌基督得勝的名求，
阿們。

以馬內利 🤍

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
    filename = f"SOH_Sound_of_Home_Prayer_{raw_filename.replace('.mp3', '')}_edge.mp3"
else:
    filename = f"SOH_Sound_of_Home_Prayer_{date_str}_edge.mp3"

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

    final_audio.export(OUTPUT_PATH, format="mp3", tags={'title': TITLE, 'artist': PRODUCER})
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
    
    # Metadata extraction
    PRODUCER = "VI AI Foundation"
    TITLE = TEXT.strip().split('\n')[0]

    asyncio.run(main())
