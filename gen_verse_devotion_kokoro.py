# gen_verse_devotion_kokoro.py
# Kokoro TTS - Ultra-lightweight 82M TTS (CPU-friendly)
# Based on: https://github.com/hexgrad/kokoro
# License: Apache 2.0

import numpy as np
import re
import sys
import os
import warnings
import argparse
from datetime import datetime

# Silence noisy libraries
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

from pydub import AudioSegment

try:
    from kokoro import KPipeline
except ImportError as e:
    print(f"❌ Failed to import kokoro: {e}")
    print("Install with: pip install kokoro misaki[zh]")
    sys.exit(1)

from bible_parser import convert_bible_reference
from date_parser import convert_dates_in_text
from text_cleaner import clean_text
import filename_parser
import audio_mixer

# --- Configuration ---
# Kokoro Chinese voices (from voicepacks)
# Use lang_code='z' for Chinese (Mandarin)
DEFAULT_VOICE = "zf_001"  # Chinese female voice 001

# Voice rotation presets for Kokoro Chinese
KOKORO_VOICES = [
    "zf_001",  # Chinese female 1
    "zm_001",  # Chinese male 1
    "zf_002",  # Chinese female 2
    "zm_002",  # Chinese male 2
]

# CLI Args
parser = argparse.ArgumentParser(description="Generate Verse Audio with Kokoro TTS (ultra-lightweight 82M)")
parser.add_argument("--input", "-i", type=str, help="Input text file")
parser.add_argument("--prefix", type=str, default=None, help="Filename prefix")
parser.add_argument("--voice", type=str, default=DEFAULT_VOICE, help=f"Voice ID (default: {DEFAULT_VOICE})")
parser.add_argument("--voices", type=str, default=None,
                    help="Comma-separated voice IDs for rotation (default: zf_001,zm_001)")
parser.add_argument("--no-rotate", action="store_true", help="Disable voice rotation (use single voice)")
parser.add_argument("--speed", type=float, default=1.0, help="Speech speed (0.5-2.0, default 1.0)")
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

# Build voice rotation list
if args.voices:
    voice_list = [v.strip() for v in args.voices.split(",") if v.strip()]
else:
    voice_list = [args.voice] if args.no_rotate else KOKORO_VOICES[:2]

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
print("Loading Kokoro TTS (82M) - Ultra-lightweight Chinese TTS...")
try:
    # Initialize Kokoro pipeline for Chinese
    pipeline = KPipeline(lang_code='z')  # 'z' for Chinese (Mandarin)
    sample_rate = 24000  # Kokoro default

    print(f"✅ Kokoro TTS loaded successfully (sample_rate={sample_rate})")
    print(f"   Voices: {', '.join(voice_list)}")
except Exception as e:
    print(f"❌ Error loading Kokoro: {e}")
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
    filename = filename_parser.generate_filename(verse_ref, date_str, extracted_prefix).replace(".mp3", "_kokoro.mp3")
else:
    if extracted_prefix:
        filename = f"{extracted_prefix}_Devotion_{date_str}_kokoro.mp3"
    else:
        filename = f"Devotion_{date_str}_kokoro.mp3"

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


def speak(text: str, voice_id: str) -> AudioSegment:
    """Convert text to audio using Kokoro TTS."""
    if DEBUG_LEVEL >= 2:
        print(f"DEBUG: Text to read: {text[:100]}...")
    if DEBUG_LEVEL >= 1:
        print(f"   Synthesizing ({len(text)} chars, voice={voice_id})...")

    try:
        # Kokoro generates audio in chunks via generator
        audio_chunks = []
        for _, _, audio in pipeline(text, voice=voice_id, speed=args.speed):
            audio_chunks.append(audio)

        if not audio_chunks:
            print(f"⚠️ No audio generated for text")
            return AudioSegment.silent(duration=500)

        # Concatenate all chunks
        wav = np.concatenate(audio_chunks)
        wav = np.nan_to_num(wav, nan=0.0, posinf=1.0, neginf=-1.0)

        max_val = np.abs(wav).max()
        if max_val > 1.0:
            wav = wav / max_val

        wav_int16 = (wav * 32767).astype(np.int16)
        segment = AudioSegment(
            wav_int16.tobytes(),
            frame_rate=sample_rate,
            sample_width=2,
            channels=1
        )
        return segment
    except Exception as e:
        print(f"❌ Error in synthesis: {e}")
        if DEBUG_LEVEL >= 2:
            import traceback
            traceback.print_exc()
        return AudioSegment.silent(duration=500)


# --- Process paragraphs ---
if DEBUG_LEVEL >= 1:
    print(f"Processing {len(paragraphs)} paragraphs with Kokoro TTS...")

USE_ROTATION = not args.no_rotate and len(voice_list) > 1
if USE_ROTATION:
    print(f"🔄 Voice rotation enabled with {len(voice_list)} voices: {', '.join(voice_list)}")

final = AudioSegment.empty()
silence_between = AudioSegment.silent(duration=700, frame_rate=sample_rate)

for i, para in enumerate(paragraphs):
    current_voice = voice_list[i % len(voice_list)] if USE_ROTATION else voice_list[0]

    if DEBUG_LEVEL >= 1:
        print(f"  > Paragraph {i+1}/{len(paragraphs)} - {current_voice} ({len(para)} chars)")

    try:
        segment = speak(para, current_voice)
        final += segment
        if i < len(paragraphs) - 1:
            final += silence_between
    except Exception as e:
        print(f"❌ Error generating para {i}: {e}")

# Normalize
final = final.set_frame_rate(sample_rate)

# Add Background Music
if ENABLE_BGM:
    print(f"🎵 Mixing Background Music...")
    final = audio_mixer.mix_bgm(final, specific_filename=BGM_FILE, volume_db=BGM_VOLUME, intro_delay_ms=BGM_INTRO_DELAY)

# Metadata
PRODUCER = "VI AI Foundation"
TITLE = first_line.strip()

final.export(OUTPUT_PATH, format="mp3", bitrate="192k", tags={'title': TITLE, 'artist': PRODUCER})
print(f"✅ Success! Saved → {OUTPUT_PATH}")
