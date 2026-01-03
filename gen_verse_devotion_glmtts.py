# gen_verse_devotion_glmtts.py
# GLM-TTS - Zero-shot voice cloning with RL-enhanced emotion
# Based on: https://github.com/zai-org/GLM-TTS

import torch
import numpy as np
import re
import sys
import os
import warnings
import argparse
from datetime import datetime

# Silence noisy libraries
warnings.filterwarnings("ignore", category=FutureWarning, module="diffusers")
warnings.filterwarnings("ignore", category=UserWarning, module="lightning")

from pydub import AudioSegment

# Setup path to find GLM-TTS
GLMTTS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../GLM-TTS"))

if os.path.exists(GLMTTS_PATH):
    sys.path.insert(0, GLMTTS_PATH)
else:
    print(f"⚠️ Warning: GLM-TTS path not found at {GLMTTS_PATH}")
    sys.exit(1)

try:
    # GLM-TTS imports
    from glmtts_pipeline import GLMTTSPipeline
except ImportError as e:
    print(f"❌ Failed to import GLM-TTS: {e}")
    print(f"Ensure you have cloned the repo to {GLMTTS_PATH} and installed its requirements.")
    sys.exit(1)

from bible_parser import convert_bible_reference
from date_parser import convert_dates_in_text
from text_cleaner import clean_text
import filename_parser
import audio_mixer

# --- Configuration ---
DEFAULT_REF_TEXT = "然而，靠着爱我们的主，在这一切的事上已经得胜有余了。"
CKPT_DIR = os.path.join(GLMTTS_PATH, "ckpt")

# Default voices (comma-separated, can be overridden via CLI)
DEFAULT_VOICES = "assets/ref_audio/ref_female.wav,assets/ref_audio/ref_male.wav"

def build_preset_voices(voices_str, ref_text):
    """Build PRESET_VOICES list from comma-separated voice files."""
    voices = []
    for voice_path in voices_str.split(","):
        voice_path = voice_path.strip()
        if voice_path:
            voices.append({
                "name": os.path.basename(voice_path),
                "audio": voice_path,
                "text": ref_text
            })
    return voices

# CLI Help
if "-?" in sys.argv or "-h" in sys.argv or "--help" in sys.argv:
    print(f"Usage: python {sys.argv[0]} [OPTIONS]")
    print("\nGLM-TTS - Zero-shot voice cloning with RL-enhanced emotion")
    print("\nOptions:")
    print("  --input, -i FILE     Input text file (or pipe via stdin)")
    print("  --prefix PREFIX      Output filename prefix")
    print("  --voices FILES       Comma-separated voice files for rotation")
    print("                       (Default: ref_female.wav,ref_male.wav)")
    print("  --ref-text TEXT      Reference text for all voices")
    print("  --no-rotate          Disable voice rotation (use first voice only)")
    print("  --bgm                Enable background music")
    print("  --bgm-track FILE     BGM filename (Default: AmazingGrace.MP3)")
    print("  --bgm-volume DB      BGM volume adjustment (Default: -20)")
    print("  --bgm-intro MS       BGM intro delay (Default: 4000)")
    print("  --debug, -d LEVEL    Debug level: 0=minimal, 1=progress, 2=full")
    print("\nExamples:")
    print("  # Default (rotate male/female):")
    print("  python gen_verse_devotion_glmtts.py --input sample.txt")
    print("  # Custom voices:")
    print("  python gen_verse_devotion_glmtts.py --voices voice1.wav,voice2.wav,voice3.wav")
    sys.exit(0)

# CLI Args
parser = argparse.ArgumentParser(description="Generate Verse Audio with GLM-TTS (zero-shot voice cloning)")
parser.add_argument("--input", "-i", type=str, help="Input text file")
parser.add_argument("--prefix", type=str, default=None, help="Filename prefix")
parser.add_argument("--voices", type=str, default=DEFAULT_VOICES, help="Comma-separated voice files for rotation")
parser.add_argument("--ref-text", type=str, default=DEFAULT_REF_TEXT, help="Reference text for all voices")
parser.add_argument("--no-rotate", action="store_true", help="Disable voice rotation (use first voice only)")
parser.add_argument("--bgm", action="store_true", help="Enable background music")
parser.add_argument("--bgm-track", type=str, default="AmazingGrace.MP3", help="BGM filename")
parser.add_argument("--bgm-volume", type=int, default=-20, help="BGM volume in dB")
parser.add_argument("--bgm-intro", type=int, default=4000, help="BGM intro delay in ms")
parser.add_argument("--debug", "-d", type=int, default=0, choices=[0, 1, 2], help="Debug level")

args, unknown = parser.parse_known_args()
CLI_PREFIX = args.prefix
ENABLE_BGM = args.bgm
BGM_FILE = args.bgm_track
BGM_VOLUME = args.bgm_volume
BGM_INTRO_DELAY = args.bgm_intro
DEBUG_LEVEL = args.debug

# Get text input
if args.input:
    print(f"Reading text from file: {args.input}")
    with open(args.input, "r", encoding="utf-8") as f:
        TEXT = f.read()
elif not sys.stdin.isatty():
    print("Reading text from Stdin...")
    TEXT = sys.stdin.read()
else:
    TEXT = """
"　神爱世人，甚至将他的独生子赐给他们，叫一切信他的，不至灭亡，反得永生。
(约翰福音 3:16)
"""

# --- Model Loading ---
print("Loading GLM-TTS (1.5B) - RL-enhanced for natural emotion...")
try:
    use_cuda = torch.cuda.is_available()
    print(f"Loading GLM-TTS... [CUDA={use_cuda}]")
    
    # Initialize GLM-TTS pipeline
    pipeline = GLMTTSPipeline(ckpt_dir=CKPT_DIR, device="cuda" if use_cuda else "cpu")
    sample_rate = 24000  # GLM-TTS default
    
    print(f"✅ GLM-TTS loaded successfully (sample_rate={sample_rate})")
except Exception as e:
    print(f"❌ Error loading GLM-TTS: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# --- Text Processing ---
TEXT = clean_text(TEXT)
first_line = TEXT.strip().split('\n')[0]

# Extract date for filename
date_match = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", first_line)
if date_match:
    m, d, y = date_match.groups()
    date_str = f"{y}-{int(m):02d}-{int(d):02d}"
else:
    date_match = re.search(r"(\d{4})[-年](\d{1,2})[-月](\d{1,2})", first_line)
    if date_match:
        y, m, d = date_match.groups()
        date_str = f"{y}-{int(m):02d}-{int(d):02d}"
    else:
        date_str = datetime.today().strftime("%Y-%m-%d")

# Generate filename
verse_ref = filename_parser.extract_verse_from_text(TEXT)
extracted_prefix = CLI_PREFIX if CLI_PREFIX else filename_parser.extract_filename_prefix(TEXT)

if verse_ref:
    filename = filename_parser.generate_filename(verse_ref, date_str, extracted_prefix).replace(".mp3", "_glmtts.mp3")
else:
    if extracted_prefix:
        filename = f"{extracted_prefix}_Devotion_{date_str}_glmtts.mp3"
    else:
        filename = f"Devotion_{date_str}_glmtts.mp3"

if ENABLE_BGM and BGM_FILE:
    bgm_base = os.path.splitext(os.path.basename(BGM_FILE))[0]
    filename = filename.replace(".mp3", f"_bgm_{bgm_base}.mp3")

OUTPUT_DIR = os.path.join(os.getcwd(), "output")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
OUTPUT_PATH = os.path.join(OUTPUT_DIR, filename)
print(f"Target Output: {OUTPUT_PATH}")

# Process text
TEXT = convert_bible_reference(TEXT)
TEXT = convert_dates_in_text(TEXT)
TEXT = clean_text(TEXT)
paragraphs = [p.strip() for p in re.split(r'\n{2,}', TEXT.strip()) if p.strip()]


def speak(text: str, ref_audio: str = None, ref_text: str = None) -> AudioSegment:
    """Convert text to audio using GLM-TTS zero-shot voice cloning."""
    if DEBUG_LEVEL >= 2:
        print(f"DEBUG: Text to read: {text[:100]}...")
    if DEBUG_LEVEL >= 1:
        print(f"   Synthesizing ({len(text)} chars)...")
    
    try:
        # GLM-TTS inference
        if ref_audio and os.path.exists(ref_audio):
            audio_np = pipeline.inference(text, ref_audio=ref_audio)
        else:
            audio_np = pipeline.inference(text)
        
        # Convert to AudioSegment
        audio_np = np.nan_to_num(audio_np, nan=0.0, posinf=1.0, neginf=-1.0)
        audio_int16 = (audio_np * 32767).astype(np.int16)
        segment = AudioSegment(
            audio_int16.tobytes(),
            frame_rate=sample_rate,
            sample_width=2,
            channels=1
        )
        return segment
    except Exception as e:
        print(f"❌ Error in synthesis: {e}")
        return AudioSegment.silent(duration=500)


# --- Process paragraphs ---
if DEBUG_LEVEL >= 1:
    print(f"Processing {len(paragraphs)} paragraphs with GLM-TTS...")

# Build preset voices from CLI args
PRESET_VOICES = build_preset_voices(args.voices, args.ref_text)

# Check for voice rotation mode (default: enabled unless --no-rotate)
USE_ROTATION = not args.no_rotate and len(PRESET_VOICES) > 1
if USE_ROTATION:
    available_voices = []
    for voice in PRESET_VOICES:
        voice_path = os.path.abspath(voice["audio"])
        if os.path.exists(voice_path):
            available_voices.append({"audio": voice_path, "text": voice["text"], "name": voice.get("name", "Unknown")})
    
    if not available_voices:
        print("⚠️ No preset voices found for rotation. Using single voice mode.")
        USE_ROTATION = False
    else:
        print(f"🔄 Voice rotation enabled with {len(available_voices)} voices")
else:
    USE_ROTATION = False
    available_voices = None

final = AudioSegment.empty()
silence_between = AudioSegment.silent(duration=700, frame_rate=sample_rate)

for i, para in enumerate(paragraphs):
    if USE_ROTATION and available_voices:
        voice = available_voices[i % len(available_voices)]
        current_ref_audio = voice["audio"]
        current_ref_text = voice["text"]
        if DEBUG_LEVEL >= 1:
            voice_name = voice.get("name", "Unknown")
            print(f"  > Paragraph {i+1}/{len(paragraphs)} - {voice_name} ({len(para)} chars)")
    else:
        current_ref_audio = PRESET_VOICES[0]["audio"] if PRESET_VOICES else None
        current_ref_text = args.ref_text
        if DEBUG_LEVEL >= 1:
            print(f"  > Paragraph {i+1}/{len(paragraphs)} ({len(para)} chars)")
    
    try:
        segment = speak(para, current_ref_audio, current_ref_text)
        final += segment
        if i < len(paragraphs) - 1:
            final += silence_between
    except Exception as e:
        print(f"❌ Error generating para {i}: {e}")

# Normalize to 24kHz
final = final.set_frame_rate(24000)

# Add Background Music
if ENABLE_BGM:
    print(f"🎵 Mixing Background Music...")
    final = audio_mixer.mix_bgm(final, specific_filename=BGM_FILE, volume_db=BGM_VOLUME, intro_delay_ms=BGM_INTRO_DELAY)

# Metadata
PRODUCER = "VI AI Foundation"
TITLE = first_line.strip()

final.export(OUTPUT_PATH, format="mp3", bitrate="192k", tags={'title': TITLE, 'artist': PRODUCER})
print(f"✅ Success! Saved → {OUTPUT_PATH}")
