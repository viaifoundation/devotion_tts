import asyncio
import sys
import edge_tts
from pydub import AudioSegment
import os
from bible_parser import convert_bible_reference
from date_parser import convert_dates_in_text, extract_date_from_text, strip_all_dates, strip_date_from_title
from text_cleaner import clean_text_basic, clean_text_for_tts, clean_text
import filename_parser
import re
from datetime import datetime
import audio_mixer
from caption_generator import parse_caption_flag, parse_caption_scale, generate_srt_from_paragraphs, create_subtitles_from_edge_cues
from audio_to_mp4 import create_mp4, DEFAULT_BG, DEFAULT_SOH_BG

import argparse
import sys

VERSION = "1.1.0"
ENABLE_BGM = True
BGM_FILE = "AmazingGrace.MP3"
TTS_RATE = "+0%"  # Default Speed (normal)
BGM_VOLUME = -10   # Default dB relative to speech (audible & balanced)
BGM_INTRO_DELAY = 4000 # Default ms

# ——————————————————————————————————————————————————————————————————————————
# Argument Parsing (Moved to top to allow CLI args to affect filename)
# ——————————————————————————————————————————————————————————————————————————
if __name__ == "__main__": 
    pass

# Custom handling for -? 
if "-?" in sys.argv or "-h" in sys.argv or "--help" in sys.argv:
    print(f"Usage: python {sys.argv[0]} [OPTIONS]")
    print("\nOptions:")
    print("  --input FILE, -i     Text file to read input from")
    print("  --lang LANG, -l      Caption language: tw (zh_TW) or cn (zh_CN) (Default: tw)")
    print("  --tw                 Shortcut for --lang tw (Traditional Chinese captions, Default)")
    print("  --cn                 Shortcut for --lang cn (Simplified Chinese captions)")
    print("  --voice MODE         Voice mode: male, female, two, four, six (Default: two)")
    print("  --voices LIST        Custom voices (CSV, overrides --voice)")
    print("                       e.g. zh-CN-YunyangNeural,zh-CN-XiaoxiaoNeural")
    print("  --speed SPEED        Speech rate: +10%, --speed=-10% (Default: +0%)")
    print("  --bgm                Enable background music")
    print("  --bgm-track TRACK    BGM filename (Default: AmazingGrace.MP3)")
    print("  --bgm-volume VOL     BGM volume in dB relative to speech (Default: -10)")
    print("  --bgm-intro MS       BGM intro delay in ms (Default: 4000)")
    print("  --mp4                Generate MP4 video from audio")
    print(f"  --mp4-bg IMAGE       Background image for MP4 (Default: {DEFAULT_SOH_BG})")
    print("  --mp4-res RES        MP4 resolution (Default: 1920x1080)")
    print("  --caption [true/false]       Enable burned-in captions on video (Default: true)")
    print("  --no-caption                 Disable burned-in captions on video")
    print("  --caption-scale SCALE        Caption font scale multiplier: 1x, 2x, 3x, 4x, etc. (Default: 2x)")
    print("  --caption-large [true/false] Make burned-in caption font size 3x larger (Default: false)")
    print("  --caption-file FILE          Explicit SRT/VTT caption file")
    print("  -?, -h, --help       Show this help")
    print("\nVoice Modes:")
    print("  male    - Single male voice (YunyangNeural)")
    print("  female  - Single female voice (XiaoxiaoNeural)")
    print("  two     - Rotate 2 voices (1 male + 1 female) (Default)")
    print("  four    - Rotate 4 voices (2 male + 2 female)")
    print("  six     - Rotate all 6 voices")
    print("\nExamples:")
    print(f"  python {sys.argv[0]} -i input.txt --tw                                  # Traditional Chinese captions (default)")
    print(f"  python {sys.argv[0]} -i input.txt --cn                                  # Simplified Chinese captions")
    print(f"  python {sys.argv[0]} -i input.txt -l tw --voice two --bgm")
    print(f"  python {sys.argv[0]} -i input.txt --mp4                                  # Video with date on thumb & 2x captions")
    print(f"  python {sys.argv[0]} -i input.txt --mp4 --no-caption                     # Video without captions")
    print(f"  python {sys.argv[0]} -i input.txt --mp4 --caption-scale 3x              # 3x larger captions")
    sys.exit(0)

parser = argparse.ArgumentParser(description="Generate Prayer Audio with Edge TTS (SOH Version)", add_help=False)
parser.add_argument("--input", "-i", type=str, help="Input text file")
parser.add_argument("--lang", "-l", type=str, default="zh_TW",
                    help="Language: tw (zh_TW) or cn (zh_CN) (Default: zh_TW)")
parser.add_argument("--tw", "-tw", action="store_true", help="Shortcut for --lang tw (Traditional Chinese, Default)")
parser.add_argument("--cn", "-cn", action="store_true", help="Shortcut for --lang cn (Simplified Chinese)")
parser.add_argument("--voice", type=str, default="two", choices=["male", "female", "two", "four", "six"],
                    help="Voice mode: male, female, two, four, six")
parser.add_argument("--voices", type=str, default=None,
                    help="Custom voices (CSV format, overrides --voice)")
parser.add_argument("--speed", type=str, default=None, help="Speech rate (e.g. +10%%)")
parser.add_argument("--bgm", action="store_true", default=True, help="Enable background music (Default: True)")
parser.add_argument("--no-bgm", action="store_true", help="Disable background music")
parser.add_argument("--bgm-track", type=str, default="AmazingGrace.MP3", help="BGM filename")
parser.add_argument("--bgm-volume", type=int, default=-10, help="BGM volume in dB relative to speech")
parser.add_argument("--bgm-intro", type=int, default=4000, help="BGM intro delay in ms")
parser.add_argument("--mp4", action="store_true", help="Generate MP4 video from audio")
parser.add_argument("--mp4-bg", type=str, default=DEFAULT_SOH_BG, help=f"Background image for MP4 (Default: {DEFAULT_SOH_BG})")
parser.add_argument("--mp4-res", type=str, default="1920x1080", help="MP4 resolution")
parser.add_argument("--caption", "--captions", nargs="?", const="true", default=None,
                    help="Enable burned-in captions on video (true/false, default: true)")
parser.add_argument("--no-caption", "--no-captions", action="store_true",
                    help="Disable burned-in captions on video")
parser.add_argument("--caption-scale", "--caption-size", type=str, default=None,
                    help="Caption font scale multiplier: 1x, 2x, 3x, 4x, etc. (Default: 2x)")
parser.add_argument("--caption-large", "--large-caption", "--caption-3x", nargs="?", const="true", default=None,
                    help="Make burned-in caption font size 3x larger (true/false, default: false)")
parser.add_argument("--caption-file", type=str, default=None, help="Explicit SRT/VTT caption file")

args, unknown = parser.parse_known_args()

# Update global config based on CLI
if args.no_bgm:
    ENABLE_BGM = False
else:
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

# Language Normalization
def normalize_lang(lang_arg: str, is_tw: bool = False, is_cn: bool = False) -> str:
    if is_cn:
        return "zh_CN"
    if is_tw:
        return "zh_TW"
    if not lang_arg:
        return "zh_TW"
    s = str(lang_arg).strip().lower().replace("-", "_")
    if s in ("cn", "zh_cn", "simplified", "s", "chs", "hans"):
        return "zh_CN"
    return "zh_TW"

TARGET_LANG = normalize_lang(args.lang, args.tw, args.cn)
lang_desc = "Traditional Chinese (zh_TW)" if TARGET_LANG == "zh_TW" else "Simplified Chinese (zh_CN)"
print(f"🌐 Caption Language: {lang_desc}")

# Voice presets (Consistent SOH standard voices)
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
elif args.voice == "two":
    VOICES = [VOICE_MALE_1, VOICE_FEMALE_1]
    print(f"🎤 Voice mode: two ({VOICE_MALE_1}, {VOICE_FEMALE_1})")
elif args.voice == "four":
    VOICES = [VOICE_MALE_1, VOICE_FEMALE_1, VOICE_MALE_2, VOICE_FEMALE_2]
    print(f"🎤 Voice mode: four (rotating 4 voices)")
else:  # six
    VOICES = [VOICE_MALE_1, VOICE_FEMALE_1, VOICE_MALE_2, VOICE_FEMALE_2, VOICE_MALE_3, VOICE_FEMALE_3]
    print(f"🎤 Voice mode: six (rotating 6 voices)")


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

# Extract raw org name from original text BEFORE it is cleaned (so it preserves Simplified/Traditional)
raw_title_line = TEXT.strip().splitlines()[0] if TEXT.strip() else ""
m_raw = re.search(r"(\d{4})[年\-](\d{1,2})[月\-](\d{1,2})[日]*\s*(.*)", raw_title_line)
raw_org_name = m_raw.group(4).strip() if m_raw and m_raw.group(4).strip() else None

# Generate filename dynamically
# 1. Extract Date
TEXT = clean_text_basic(TEXT)

# Extract date for filename BEFORE stripping date from spoken text
date_str_dash = extract_date_from_text(TEXT)

if not date_str_dash:
    try:
        import zoneinfo
        target_tz = zoneinfo.ZoneInfo("Asia/Shanghai")
        date_str_dash = datetime.now(target_tz).strftime("%Y-%m-%d")
    except Exception:
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
# Convert script according to TARGET_LANG (zh_TW -> Traditional, zh_CN -> Simplified)
try:
    import opencc
    if TARGET_LANG == "zh_TW":
        cc = opencc.OpenCC('s2tw')
        TEXT = cc.convert(TEXT)
    else:
        cc = opencc.OpenCC('t2s')
        TEXT = cc.convert(TEXT)
except Exception as e:
    print(f"⚠️ OpenCC conversion notice: {e}")

# Note: Date of title line is retained as requested (do not strip date from title)
# TEXT = strip_date_from_title(TEXT)

# Extract first line for MP3 title (retaining date as requested)
TEXT_DISPLAY = clean_text_basic(TEXT)
first_line = TEXT_DISPLAY.strip().split('\n')[0] if TEXT_DISPLAY.strip() else "SOH Prayer"

# Convert Bible references and dates with RAG/phonetic pronunciation fixes for TTS
TEXT_TTS = convert_bible_reference(TEXT_DISPLAY)
TEXT_TTS = convert_dates_in_text(TEXT_TTS)
TEXT_TTS = clean_text_for_tts(TEXT_TTS)

# Split the text into paragraphs for TTS
paragraphs = [p.strip() for p in re.split(r'\n{2,}', TEXT_TTS.strip()) if p.strip()]

# Save companion text output for TTS with RAG (matching VOTD convention)
# Note: prayer_output.txt is no longer generated as requested
TXT_OUTPUT_PATH = OUTPUT_PATH.replace(".mp3", ".txt")
with open(TXT_OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write(TEXT_TTS)
print(f"📄 Saved TTS RAG text output to: {TXT_OUTPUT_PATH}")

# Clean up legacy prayer_output.txt if present
for legacy_path in [os.path.join(OUTPUT_DIR, "prayer_output.txt"), os.path.join(os.getcwd(), "prayer_output.txt")]:
    if os.path.exists(legacy_path):
        try:
            os.remove(legacy_path)
        except Exception:
            pass

# Use VOICES array from --voice option
voices = VOICES

TEMP_DIR = OUTPUT_DIR + os.sep 

async def generate_audio(text, voice, output_file, max_retries=3):
    print(f"DEBUG: Text to read: {text[:100]}...")
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            communicate = edge_tts.Communicate(text=text, voice=voice, rate=TTS_RATE)
            submaker = edge_tts.SubMaker()
            has_audio = False
            with open(output_file, "wb") as f:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        f.write(chunk["data"])
                        has_audio = True
                    elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                        submaker.feed(chunk)
            if has_audio and os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                return submaker
            else:
                raise RuntimeError("Empty audio output received.")
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                wait_sec = attempt * 1.5
                print(f"⚠️ TTS error on attempt {attempt}/{max_retries} ({e}). Retrying in {wait_sec:.1f}s...")
                await asyncio.sleep(wait_sec)
    raise last_error

async def main():
    final_audio = AudioSegment.empty()
    silence = AudioSegment.silent(duration=800) 
    paragraph_durations = []
    paragraph_submakers = []

    print(f"Processing {len(paragraphs)} paragraphs with voice rotation...")
    
    for i, para in enumerate(paragraphs):
        voice = voices[i % len(voices)]
        print(f"  > Para {i+1} ({len(para)} chars) - {voice}")
        
        temp_file = f"{TEMP_DIR}temp_prayer_p{i}.mp3"
        submaker = await generate_audio(para, voice, temp_file)
        paragraph_submakers.append(submaker)
        
        try:
            segment = AudioSegment.from_mp3(temp_file)
            paragraph_durations.append(len(segment))
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
    verse_ref = filename_parser.extract_verse_from_text(TEXT_DISPLAY)
    COMMENTS = f"Verse: {verse_ref}; BGM: {bgm_info_str}"

    final_audio.export(OUTPUT_PATH, format="mp3", tags={
        'title': TITLE, 
        'artist': PRODUCER,
        'album': ALBUM,
        'comments': COMMENTS
    })
    print(f"✅ Saved: {OUTPUT_PATH}")

    # Generate subtitles (.srt) using frame-accurate Edge-TTS timestamps
    srt_output_path = OUTPUT_PATH.replace(".mp3", ".srt")
    intro_offset = BGM_INTRO_DELAY if ENABLE_BGM else 0
    create_subtitles_from_edge_cues(
        paragraph_submakers=paragraph_submakers,
        output_path=srt_output_path,
        intro_delay_ms=intro_offset,
        silence_ms=800,
        show_title_during_intro=True,
    )
    print(f"📄 Saved frame-accurate subtitles to: {srt_output_path}")

    # Generate MP4 Video (Optional)
    if args.mp4:
        try:
            if args.no_caption:
                enable_caption = False
            elif args.caption is not None:
                enable_caption = parse_caption_flag(args.caption, default=True)
            else:
                enable_caption = True  # Captions are ON by default when --mp4 is used!

            enable_caption_large = parse_caption_flag(args.caption_large, default=False) if args.caption_large is not None else False
            scale_val = parse_caption_scale(args.caption_scale, default=2.0)
            if enable_caption_large:
                scale_val = 3.0
            caption_scale_str = f"{scale_val:g}x"
        except ValueError as e:
            print(f"❌ {e}")
            sys.exit(1)

        mp4_output = OUTPUT_PATH.replace(".mp3", ".mp4")
        date_display = f"{date_obj.year} 年 {date_obj.month} 月 {date_obj.day} 日"
        
        create_mp4(
            input_mp3=OUTPUT_PATH,
            bg_image=args.mp4_bg,
            output_mp4=mp4_output,
            resolution=args.mp4_res,
            caption=enable_caption,
            caption_file=args.caption_file or srt_output_path,
            is_soh=True,
            caption_scale=caption_scale_str,
            caption_large=enable_caption_large,
            date_text=date_display,
            org_name_text=raw_org_name,
        )

if __name__ == "__main__":
    asyncio.run(main())
