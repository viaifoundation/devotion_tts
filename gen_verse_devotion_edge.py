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

TTS_RATE = "+0%"  # Default Speed (normal)

import argparse

import audio_mixer

# CLI Args
if "-?" in sys.argv or "-h" in sys.argv or "--help" in sys.argv:
    print(f"Usage: python {sys.argv[0]} [OPTIONS]")
    print("\nOptions:")
    print("  --input FILE, -i     Text file to read input from")
    print("  --prefix PREFIX      Filename prefix (e.g. MyPrefix)")
    print("  --voice MODE         Voice mode: male, female, two, four, six (Default: six)")
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
    print("  two     - Rotate 2 voices (1 male + 1 female)")
    print("  four    - Rotate 4 voices (2 male + 2 female)")
    print("  six     - Rotate all 6 zh-CN voices (Default)")
    print("\nExamples:")
    print(f"  python {sys.argv[0]} -i input.txt --voice male")
    print(f"  python {sys.argv[0]} -i input.txt --voice two --bgm")
    print(f"  python {sys.argv[0]} -i input.txt --voice six --speed +10%")
    sys.exit(0)

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("--input", "-i", type=str, help="Input text file")
parser.add_argument("--prefix", type=str, default=None, help="Filename prefix")
parser.add_argument("--voice", type=str, default="six", choices=["male", "female", "two", "four", "six"], 
                    help="Voice mode: male, female, two, four, six")
parser.add_argument("--voices", type=str, default=None, 
                    help="Custom voices (CSV format, overrides --voice)")
parser.add_argument("--speed", type=str, default=None, help="Speech rate adjustment (e.g. +10%%)")
parser.add_argument("--bgm", action="store_true", help="Enable background music")
parser.add_argument("--bgm-track", type=str, default="AmazingGrace.MP3", help="BGM filename")
parser.add_argument("--bgm-volume", type=int, default=-20, help="BGM volume in dB")
parser.add_argument("--bgm-intro", type=int, default=4000, help="BGM intro delay in ms")

args, unknown = parser.parse_known_args()
CLI_PREFIX = args.prefix

ENABLE_BGM = args.bgm
BGM_FILE = args.bgm_track
BGM_VOLUME = args.bgm_volume
BGM_INTRO_DELAY = args.bgm_intro

# Speed parsing
if args.speed:
    if not "%" in args.speed and (args.speed.startswith("+") or args.speed.startswith("-") or args.speed.isdigit()):
        TTS_RATE = f"{args.speed}%"
    else:
        TTS_RATE = args.speed

# Voice presets
VOICE_MALE_1 = "zh-CN-YunyangNeural"    # Professional, Reliable
VOICE_MALE_2 = "zh-CN-YunxiNeural"      # Lively, Sunshine
VOICE_MALE_3 = "zh-CN-YunjianNeural"    # Passion
VOICE_FEMALE_1 = "zh-CN-XiaoxiaoNeural"  # Warm
VOICE_FEMALE_2 = "zh-CN-XiaoyiNeural"    # Lively
VOICE_FEMALE_3 = "zh-CN-YunxiaNeural"    # Cute (Male but high pitch)

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
    print(f"🎤 Voice mode: two (rotating 2 voices)")
elif args.voice == "four":
    VOICES = [VOICE_MALE_1, VOICE_FEMALE_1, VOICE_MALE_2, VOICE_FEMALE_2]
    print(f"🎤 Voice mode: four (rotating 4 voices)")
else:  # six (default)
    VOICES = [VOICE_MALE_1, VOICE_FEMALE_1, VOICE_MALE_2, VOICE_FEMALE_2, VOICE_MALE_3, VOICE_FEMALE_3]
    print(f"🎤 Voice mode: six (rotating 6 voices)")

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


# Generate filename dynamically
# 1. Extract Date
TEXT = clean_text(TEXT)
first_line = TEXT.strip().split('\n')[0]
date_match = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", first_line)
if date_match:
    m, d, y = date_match.groups()
    date_str = f"{y}-{int(m):02d}-{int(d):02d}"
else:
    # Try YYYY-MM-DD
    date_match = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", first_line)
    if date_match:
        y, m, d = date_match.groups()
        date_str = f"{y}-{int(m):02d}-{int(d):02d}"
    else:
        date_str = datetime.today().strftime("%Y-%m-%d")

# 2. Extract Verse Reference (for metadata only)
verse_ref = filename_parser.extract_verse_from_text(TEXT)

# 3. Generate Filename (Standardized V2)
extracted_prefix = CLI_PREFIX if CLI_PREFIX else filename_parser.extract_filename_prefix(TEXT)
filename = filename_parser.generate_filename_v2(
    title=first_line, 
    date=date_str, 
    prefix=extracted_prefix,
    ext=".mp3"
).replace(".mp3", "_edge.mp3")

if ENABLE_BGM:
    filename = filename.replace(".mp3", "_bgm.mp3")

# Add speed suffix to filename if non-default speed is used
if args.speed:
    speed_val = args.speed.replace("%", "")
    if speed_val.startswith("+"):
        speed_suffix = f"plus{speed_val[1:]}"
    elif speed_val.startswith("-"):
        speed_suffix = f"minus{speed_val[1:]}"
    else:
        speed_suffix = speed_val
    # Only add suffix if not default speed
    if speed_suffix and speed_suffix not in ["0", "plus0", "1.0"]:
        filename = filename.replace(".mp3", f"_speed-{speed_suffix}.mp3")

OUTPUT_DIR = os.path.join(os.getcwd(), "output")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
OUTPUT_PATH = os.path.join(OUTPUT_DIR, filename)
print(f"Target Output: {OUTPUT_PATH}")

# Convert Bible references in the text (e.g., '罗马书 1:17' to '罗马书 1章17節')
TEXT = convert_bible_reference(TEXT)
TEXT = convert_dates_in_text(TEXT)
TEXT = clean_text(TEXT)
# Split the text into paragraphs
paragraphs = [p.strip() for p in re.split(r'\n{2,}', TEXT.strip()) if p.strip()]
first_paragraphs = [paragraphs[0]] # First paragraph (introduction)
second_paragraphs = [paragraphs[1]] # Second paragraph
third_paragraphs = [paragraphs[2]] # Third paragraph
fourth_paragraphs = ["\n\n".join(paragraphs[3:-1])] # Paragraphs between 3rd and last
fifth_paragraphs = [paragraphs[-1]] # Last paragraph\n
TEMP_DIR = OUTPUT_DIR + os.sep # For temp files
TEMP_FIRST = os.path.join(OUTPUT_DIR, "temp_first_verse.mp3")
TEMP_SECOND = os.path.join(OUTPUT_DIR, "temp_second_verse.mp3")
TEMP_THIRD = os.path.join(OUTPUT_DIR, "temp_third_verse.mp3")

# Alias for backward compatibility with main()
OUTPUT = OUTPUT_PATH
async def generate_audio(text, voice, output_file):
    print(f"DEBUG: Text to read: {text[:100]}...")
    # print(f"DEBUG: Generating audio for text: '{text[:50]}...' (len={len(text)})")
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=TTS_RATE)
    await communicate.save(output_file)
async def main():
    # Group paragraphs
    if len(paragraphs) < 5:
        logical_sections = [[p] for p in paragraphs]
    else:
        logical_sections = [
            [paragraphs[0]],              # Intro
            [paragraphs[1]],              # Scripture 1
            [paragraphs[2]],              # Scripture 2
            paragraphs[3:-1],             # Main Body
            [paragraphs[-1]]              # Prayer
        ]

    # Voice mapping - use VOICES array from --voice option
    voices = VOICES
    section_titles = ["Intro", "Scripture 1", "Scripture 2", "Main Body", "Prayer"]
    
    print(f"Processing {len(logical_sections)} logical sections...")
    final_segments = []
    global_p_index = 0

    for i, section_paras in enumerate(logical_sections):
        title = section_titles[i] if i < len(section_titles) else f"Section {i+1}"
        print(f"--- Section {i+1}: {title} ---")
        
        section_audio = AudioSegment.empty()
        silence_between_paras = AudioSegment.silent(duration=700) # Edge TTS often returns 24k or 44.1k, pydub handles mixing usually

        for j, para in enumerate(section_paras):
            voice = voices[global_p_index % len(voices)]
            print(f"  > Part {i+1}.{j+1} - {voice} ({len(para)} chars)")
            global_p_index += 1
            
            # Edge TTS requires temp file
            temp_file = f"{TEMP_DIR}temp_v{i}_p{j}.mp3"
            await generate_audio(para, voice, temp_file)
            
            try:
                segment = AudioSegment.from_mp3(temp_file)
                section_audio += segment
                if j < len(section_paras) - 1:
                    section_audio += silence_between_paras
            finally:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
        
        final_segments.append(section_audio)

    # Combine all sections
    final = AudioSegment.empty()
    silence_sections = AudioSegment.silent(duration=1000)

    for i, seg in enumerate(final_segments):
        final += seg
        if i < len(final_segments) - 1:
            final += silence_sections

    # Add Background Music (Optional)
    if ENABLE_BGM:
        print(f"🎵 Mixing Background Music (Vol={BGM_VOLUME}dB, Intro={BGM_INTRO_DELAY}ms)...")
        final = audio_mixer.mix_bgm(
            final, 
            specific_filename=BGM_FILE,
            volume_db=BGM_VOLUME,
            intro_delay_ms=BGM_INTRO_DELAY
        )

    # Metadata extraction
    PRODUCER = "VI AI Foundation"
    TITLE = TEXT.strip().split('\n')[0]
    ALBUM = "Devotion"
    bgm_info = os.path.basename(BGM_FILE) if ENABLE_BGM else "None"
    COMMENTS = f"Verse: {verse_ref}; BGM: {bgm_info}"

    final.export(OUTPUT, format="mp3", tags={
        'title': TITLE, 
        'artist': PRODUCER,
        'album': ALBUM,
        'comments': COMMENTS
    })
    print(f"✅ Combined audio saved: {OUTPUT}")

if __name__ == "__main__":
    asyncio.run(main())
