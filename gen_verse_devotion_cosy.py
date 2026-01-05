# gen_verse_devotion_cosy.py
# Local offline CosyVoice-300M – 5 voices for verse devotion

import torch
import numpy as np
import re
import sys
import os
import warnings
from datetime import datetime

# Silence noisy libraries
warnings.filterwarnings("ignore", category=FutureWarning, module="diffusers")
warnings.filterwarnings("ignore", category=UserWarning, module="lightning")

from pydub import AudioSegment

# Setup path to find CosyVoice (sibling directory)
# and its third_party dependencies (Matcha-TTS)
COSYVOICE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../CosyVoice"))
MATCHA_PATH = os.path.join(COSYVOICE_PATH, "third_party", "Matcha-TTS")

if os.path.exists(COSYVOICE_PATH):
    sys.path.append(COSYVOICE_PATH)
    # Also add Matcha-TTS to path as CosyVoice imports 'matcha' directly
    if os.path.exists(MATCHA_PATH):
        sys.path.append(MATCHA_PATH)
    else:
        print(f"⚠️ Warning: Matcha-TTS not found at {MATCHA_PATH}")
        print("Run: cd ../CosyVoice && git submodule update --init --recursive")
else:
    print(f"⚠️ Warning: CosyVoice path not found at {COSYVOICE_PATH}")
    print("Please clone it: git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git ../CosyVoice")

try:
    from cosyvoice.cli.cosyvoice import CosyVoice
    from cosyvoice.utils.file_utils import load_wav
except ImportError as e:
    print(f"❌ Failed to import CosyVoice: {e}")
    print(f"Ensure you have cloned the repo to {COSYVOICE_PATH} and installed its requirements.")
    sys.exit(1)

from bible_parser import convert_bible_reference
from date_parser import convert_dates_in_text
from text_cleaner import clean_text
import filename_parser
import audio_mixer
import argparse

# CLI Args
if "-?" in sys.argv or "-h" in sys.argv or "--help" in sys.argv:
    print(f"Usage: python {sys.argv[0]} [--input FILE] [--prefix PREFIX] [--bgm] [--bgm-track TRACK] [--bgm-volume VOL] [--bgm-intro MS] [--debug LEVEL] [--help]")
    print ("\nOptions:")
    print("  --input FILE, -i     Text file to read input from")
    print("  --prefix PREFIX      Filename prefix (e.g. MyPrefix)")
    print("  --bgm                Enable background music (Default: False)")
    print("  --bgm-track TRACK    Specific BGM filename (Default: AmazingGrace.MP3)")
    print("  --bgm-volume VOL     BGM volume adjustment in dB (Default: -20)")
    print("  --bgm-intro MS       BGM intro delay in ms (Default: 4000)")
    print("  --speed SPEED        Speed factor (Not supported for CosyVoice yet, placeholder)")
    print("  --debug LEVEL        Debug output level: 0=minimal, 1=progress, 2=full (Default: 0)")
    print("  --help, -h           Show this help")
    print("\n  (Note: You can also add 'FilenamePrefix: <Prefix>' in the input TEXT)")
    sys.exit(0)

parser = argparse.ArgumentParser()
parser.add_argument("--input", "-i", type=str, help="Input text file")
parser.add_argument("--prefix", type=str, default=None, help="Filename prefix (e.g. MyPrefix)")
parser.add_argument("--speed", type=str, default="1.0", help="Speed factor (Not supported yet)")
parser.add_argument("--bgm", action="store_true", help="Enable background music (Default: False)")
parser.add_argument("--bgm-track", type=str, default="AmazingGrace.MP3", help="Specific BGM filename (Default: AmazingGrace.MP3)")
parser.add_argument("--bgm-volume", type=int, default=-20, help="BGM volume adjustment in dB (Default: -20)")
parser.add_argument("--bgm-intro", type=int, default=4000, help="BGM intro delay in ms (Default: 4000)")
parser.add_argument("--debug", "-d", type=int, default=0, choices=[0, 1, 2], help="Debug level: 0=minimal, 1=progress, 2=full (Default: 0)")

args, unknown = parser.parse_known_args()
CLI_PREFIX = args.prefix
ENABLE_BGM = args.bgm
BGM_FILE = args.bgm_track
BGM_VOLUME = args.bgm_volume
BGM_INTRO_DELAY = args.bgm_intro
DEBUG_LEVEL = args.debug

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



print("Loading CosyVoice-300M-Instruct (local offline)...")
# CosyVoice automatically handles model download via modelscope if not present
try:
    # NOTE: FP16 causes NaN/silence on some GPUs (e.g., Blackwell/GB10). 
    # Use FP32 for stability. GPU acceleration still works without FP16.
    use_cuda = torch.cuda.is_available()
    use_fp16 = False  # Disabled due to NaN issues on Spark GPU
    print(f"Loading CosyVoice-300M-Instruct (local offline)... [CUDA={use_cuda}, FP16={use_fp16}]")
    cosyvoice = CosyVoice('iic/CosyVoice-300M-Instruct', fp16=use_fp16)
except Exception as e:
    print(f"❌ Error loading model: {e}")
    print("Ensure you have 'modelscope' installed and dependencies met.")
    sys.exit(1)



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

# Logic: If no extracted prefix and no CLI prefix, it stays None (filename has no prefix)
filename = filename_parser.generate_filename_v2(
    title=first_line, 
    date=date_str, 
    prefix=extracted_prefix,
    ext=".mp3"
).replace(".mp3", "_cosy.mp3")

if ENABLE_BGM:
    filename = filename.replace(".mp3", "_bgm.mp3")

# Add speed suffix to filename if non-default speed is used
if args.speed and args.speed not in ["1.0", "1"]:
    speed_val = args.speed.replace("%", "")
    if speed_val.startswith("+"):
        speed_suffix = f"plus{speed_val[1:]}"
    elif speed_val.startswith("-"):
        speed_suffix = f"minus{speed_val[1:]}"
    else:
        speed_suffix = speed_val
        filename = filename.replace(".mp3", f"_speed-{speed_suffix}.mp3")

OUTPUT_DIR = os.path.join(os.getcwd(), "output")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
OUTPUT_PATH = os.path.join(OUTPUT_DIR, filename)
print(f"Target Output: {OUTPUT_PATH}")

TEXT = convert_bible_reference(TEXT)
TEXT = convert_dates_in_text(TEXT)
TEXT = clean_text(TEXT)

# Debug Level 2: Show the final text that will be processed
if DEBUG_LEVEL >= 2:
    print("\n=== TEXT AFTER CONVERSION (DEBUG) ===")
    print(TEXT)
    print("=== END DEBUG ===")

paragraphs = [p.strip() for p in re.split(r'\n{2,}', TEXT.strip()) if p.strip()]

# Built-in CosyVoice voices
# CosyVoice-300M-Instruct supports: 中文女, 中文男, 日语男, 粤语女, 英文女, 英文男, 韩语女
VOICES = ["中文女", "中文男", "英文女", "中文女", "中文男"]

def speak(text: str, voice: str) -> AudioSegment:
    """Convert text to audio using CosyVoice."""
    if DEBUG_LEVEL >= 2:
        print(f"DEBUG: Text to read: {text[:100]}...")
    if DEBUG_LEVEL >= 1:
        print(f"   Synthesizing ({len(text)} chars) with {voice}...")
    
    output_gen = cosyvoice.inference_sft(text, voice)
    final_audio = AudioSegment.empty()
    
    for item in output_gen:
        if 'tts_speech' in item:
            audio_np = item['tts_speech'].numpy()
            # Fix NaN/Inf values that cause silence
            audio_np = np.nan_to_num(audio_np, nan=0.0, posinf=1.0, neginf=-1.0)
            audio_int16 = (audio_np * 32767).astype(np.int16)
            segment = AudioSegment(
                audio_int16.tobytes(),
                frame_rate=22050, 
                sample_width=2,
                channels=1
            )
            final_audio += segment
            
    return final_audio

# Process paragraphs directly (no complex section grouping)
if DEBUG_LEVEL >= 1:
    print(f"Processing {len(paragraphs)} paragraphs...")

final = AudioSegment.empty()
silence_between = AudioSegment.silent(duration=700, frame_rate=22050)

for i, para in enumerate(paragraphs):
    voice = VOICES[i % len(VOICES)]
    if DEBUG_LEVEL >= 1:
        print(f"  > Paragraph {i+1}/{len(paragraphs)} - {voice} ({len(para)} chars)")
    
    segment = speak(para, voice)
    final += segment
    
    if i < len(paragraphs) - 1:
        final += silence_between

# Convert to 24k for consistency
final = final.set_frame_rate(24000)

# Add Background Music (Optional)
bgm_info_str = "None"
if ENABLE_BGM:
    print(f"🎵 Mixing Background Music (Vol={BGM_VOLUME}dB, Intro={BGM_INTRO_DELAY}ms)...")
    final = audio_mixer.mix_bgm(
        final, 
        specific_filename=BGM_FILE,
        volume_db=BGM_VOLUME,
        intro_delay_ms=BGM_INTRO_DELAY
    )
    bgm_info_str = os.path.basename(BGM_FILE)

# Metadata
PRODUCER = "VI AI Foundation"
TITLE = first_line.strip()
ALBUM = "Devotion"
COMMENTS = f"Verse: {verse_ref}; BGM: {bgm_info_str}"

final.export(OUTPUT_PATH, format="mp3", bitrate="192k", tags={
    'title': TITLE,
    'artist': PRODUCER,
    'album': ALBUM,
    'comments': COMMENTS
})
print(f"✅ Success! Saved → {OUTPUT_PATH}")

