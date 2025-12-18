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

# ——————————————————————————————————————————————————————————————————————————
# Argument Parsing (Moved to top to allow CLI args to affect filename)
# ——————————————————————————————————————————————————————————————————————————
if __name__ == "__main__": 
    # Only parse if run as script, but we need the variables to be set for the script to validly execute top-level code
    # Simple hack: just parse it.
    pass

# Custom handling for -? 
if "-?" in sys.argv:
    print(f"Usage: python {sys.argv[0]} [--bgm] [--rate RATE] [--bgm-volume VOL] [--bgm-intro MS] [--prefix PREFIX] [--help] [--version]")
    print("\nOptions:")
    print("  -h, --help           Show this help message and exit")
    print("  -?,                  Show this help message and exit")
    print("  --bgm                Enable background music")
    print("  --rate RATE          TTS Speech rate (default: +10%)")
    print("  --bgm-volume VOL     BGM volume adjustment in dB (default: -12)")
    print("  --bgm-intro MS       BGM intro delay in ms (default: 4000)")
    print("  --prefix PREFIX      Filename prefix (overrides 'FilenamePrefix' in text)")
    print("  --version, -v        Show program version")
    print("\n  (Note: You can also add 'FilenamePrefix: <Prefix>' in the input TEXT)")
    sys.exit(0)

parser = argparse.ArgumentParser(description="Generate Prayer Audio with Edge TTS")
parser.add_argument("--bgm", action="store_true", help="Enable background music")
parser.add_argument("--rate", type=str, default="+10%", help="TTS Speech rate (e.g. +10%%)")
parser.add_argument("--bgm-volume", type=int, default=-12, help="BGM volume adjustment in dB")
parser.add_argument("--bgm-intro", type=int, default=4000, help="BGM intro delay in ms")
parser.add_argument("--prefix", type=str, default=None, help="Filename prefix")
parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {VERSION}")

args, unknown = parser.parse_known_args()

# Update global config based on CLI
if args.bgm:
    ENABLE_BGM = True

TTS_RATE = args.rate
BGM_VOLUME = args.bgm_volume
BGM_INTRO_DELAY = args.bgm_intro
CLI_PREFIX = args.prefix



TEXT = """
从日出之地到日落之处， 耶和华的名是应当赞美的！
诗篇113:3

“感谢上帝，他使我们藉着我们的主耶稣基督得胜。”
‭‭哥林多前书‬ ‭15‬:‭57‬ ‭


亲爱的阿爸天父：
      我们＂乡音”团队十多年来的成长经历，全靠祢的亲自帶领，一步一步这样走过来的；一切的成就全应归功于祢！ 没有祢手携手的带领,不可能有今天的成就！ 一切荣耀归于祢！。                               最近我们非常感恩的是灣區「鄉音」場地 Redemption Church 已正式完成了簽約！在此，恳求天父繼續為聖地牙哥 UCSDUCSD – The Epstein Family Amphitheater 的租借與簽約過程親自開路、保守一切細節順利完成。另外我们把南北加州四場「鄉音」的宣傳推廣、贊助與籌款需要、節目籌備與執行製作流程及所有参与的同工及其家人的身體健康统统交在祢手中，求主賜下合一、智慧與平安！确保每场演出顺利成功！ 通过演唱的形式把祢的话语传到每个人的心中，让那些原不完全认识祢的人早日归入主名！
感謝祢垂聽我們的禱告，谢谢祢亲自继续引领我们往前行！－切荣耀归于祢！奉主耶穌基督的名求，阿們。[玫瑰][玫瑰][玫瑰][爱心][爱心][爱心][合十][合十][合十]
"""

# Generate filename dynamically
# 1. Extract Date (Try to find a date in the text, otherwise use today)
TEXT = clean_text(TEXT)
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
    extracted_prefix = CLI_PREFIX if CLI_PREFIX else filename_parser.extract_filename_prefix(TEXT)
    filename = filename_parser.generate_filename(verse_ref, date_str, extracted_prefix, base_name="Prayer").replace(".mp3", "_edge.mp3")
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
