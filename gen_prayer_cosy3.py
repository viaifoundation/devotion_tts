# gen_prayer_cosy3.py
# Fun-CosyVoice 3.0 (0.5B) – Zero-shot voice cloning for prayer
# Higher quality than CosyVoice-300M with RLHF-trained prosody

import torch
import numpy as np
import re
import sys
import os
import warnings
import argparse
from datetime import datetime
from pydub import AudioSegment

# Silence noisy libraries
warnings.filterwarnings("ignore", category=FutureWarning, module="diffusers")
warnings.filterwarnings("ignore", category=UserWarning, module="lightning")

# Setup path to find CosyVoice
COSYVOICE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../CosyVoice"))
MATCHA_PATH = os.path.join(COSYVOICE_PATH, "third_party", "Matcha-TTS")

if os.path.exists(COSYVOICE_PATH):
    sys.path.append(COSYVOICE_PATH)
    if os.path.exists(MATCHA_PATH):
        sys.path.append(MATCHA_PATH)
else:
    print(f"⚠️ Warning: CosyVoice path not found at {COSYVOICE_PATH}")
    sys.exit(1)

try:
    from cosyvoice.cli.cosyvoice import AutoModel
except ImportError as e:
    print(f"❌ Failed to import CosyVoice: {e}")
    sys.exit(1)

from bible_parser import convert_bible_reference
from date_parser import convert_dates_in_text, extract_date_from_text
from text_cleaner import clean_text
import filename_parser
import audio_mixer

# --- Configuration ---
DEFAULT_REF_AUDIO = "assets/ref_audio/ref_female.wav"
DEFAULT_REF_TEXT = "然而，靠着爱我们的主，在这一切的事上已经得胜有余了。"
MODEL_DIR = "pretrained_models/Fun-CosyVoice3-0.5B"

# Preset voice rotation (for --rotate mode)
# Uses existing reference audio files in assets/ref_audio/
PRESET_VOICES = [
    {"audio": "assets/ref_audio/ref_female.wav", "text": "然而，靠着爱我们的主，在这一切的事上已经得胜有余了。"},
    {"audio": "assets/ref_audio/ref_male.wav", "text": "然而，靠着爱我们的主，在这一切的事上已经得胜有余了。"},
]

# CLI Help
if "-?" in sys.argv:
    print(f"Usage: python {sys.argv[0]} [OPTIONS]")
    print("\nFun-CosyVoice 3.0 - Zero-shot voice cloning TTS for Prayer")
    print("\nOptions:")
    print("  --input, -i FILE     Input text file")
    print("  --prefix PREFIX      Output filename prefix")
    print("  --ref-audio FILE     Reference audio (Default: ref_female.m4a)")
    print("  --ref-text TEXT      Text spoken in reference audio")
    print("  --rotate             Rotate through ref_female.m4a and ref_male.m4a per paragraph")
    print("  --bgm                Enable background music")
    print("  --debug, -d LEVEL    Debug level: 0=minimal, 1=progress, 2=full")
    sys.exit(0)

# CLI Args
parser = argparse.ArgumentParser(description="Generate Prayer Audio with Fun-CosyVoice 3.0")
parser.add_argument("--input", "-i", type=str, help="Input text file")
parser.add_argument("--prefix", type=str, default=None, help="Filename prefix")
parser.add_argument("--ref-audio", type=str, default=DEFAULT_REF_AUDIO, help="Reference audio (Default: ref_female.m4a)")
parser.add_argument("--ref-text", type=str, default=DEFAULT_REF_TEXT, help="Text spoken in reference audio")
parser.add_argument("--rotate", action="store_true", help="Rotate through preset voices per paragraph")
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

# 1. Try --input argument
if args.input:
    print(f"Reading text from file: {args.input}")
    with open(args.input, "r", encoding="utf-8") as f:
        TEXT = f.read()
# 2. Try Stdin
elif not sys.stdin.isatty():
    print("Reading text from Stdin...")
    TEXT = sys.stdin.read()
# 3. Fallback
else:
    TEXT = """
"　神爱世人，甚至将他的独生子赐给他们，叫一切信他的，不至灭亡，反得永生。
(约翰福音 3:16)
"""

# --- Model Loading ---
print("Loading Fun-CosyVoice 3.0 (0.5B) - RLHF-trained for better prosody...")
try:
    use_cuda = torch.cuda.is_available()
    print(f"Loading Fun-CosyVoice3-0.5B... [CUDA={use_cuda}]")
    
    if os.path.exists(os.path.join(COSYVOICE_PATH, MODEL_DIR)):
        model_path = os.path.join(COSYVOICE_PATH, MODEL_DIR)
    elif os.path.exists(MODEL_DIR):
        model_path = MODEL_DIR
    else:
        model_path = 'FunAudioLLM/Fun-CosyVoice3-0.5B-2512'
        print(f"Model not found locally, attempting to download from: {model_path}")
    
    cosyvoice = AutoModel(model_dir=model_path)
    print(f"✅ Fun-CosyVoice 3.0 loaded (sample_rate={cosyvoice.sample_rate})")
except Exception as e:
    print(f"❌ Error loading Fun-CosyVoice 3.0: {e}")
    sys.exit(1)

# --- Reference Audio Setup ---
ref_audio_path = os.path.abspath(args.ref_audio) if args.ref_audio else None
if ref_audio_path and os.path.exists(ref_audio_path):
    print(f"Using reference audio for voice cloning: {ref_audio_path}")
else:
    print(f"⚠️ Reference audio not found: {ref_audio_path}")
    ref_audio_path = None

# --- Filename Generation ---
TEXT = clean_text(TEXT)
first_line = TEXT.strip().split('\n')[0]
date_str = extract_date_from_text(TEXT)

if not date_str:
    date_str = datetime.today().strftime("%Y-%m-%d")

verse_ref = filename_parser.extract_verse_from_text(TEXT)
extracted_prefix = CLI_PREFIX if CLI_PREFIX else filename_parser.extract_filename_prefix(TEXT)

if verse_ref:
    filename = filename_parser.generate_filename(verse_ref, date_str, extracted_prefix, base_name="Prayer").replace(".mp3", "_cosy3.mp3")
else:
    if extracted_prefix:
        filename = f"{extracted_prefix}_Prayer_{date_str}_cosy3.mp3"
    else:
        filename = f"Prayer_{date_str}_cosy3.mp3"

if ENABLE_BGM and BGM_FILE:
    bgm_base = os.path.splitext(os.path.basename(BGM_FILE))[0]
    filename = filename.replace(".mp3", f"_bgm_{bgm_base}.mp3")

OUTPUT_DIR = os.path.join(os.getcwd(), "output")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
OUTPUT_PATH = os.path.join(OUTPUT_DIR, filename)
print(f"Target Output: {OUTPUT_PATH}")

TEXT = convert_bible_reference(TEXT)
TEXT = convert_dates_in_text(TEXT)
TEXT = clean_text(TEXT)

paragraphs = [p.strip() for p in re.split(r'\n{2,}', TEXT.strip()) if p.strip()]


def speak(text: str, ref_audio: str = None, ref_text: str = None) -> AudioSegment:
    """Convert text to audio using Fun-CosyVoice 3.0 zero-shot voice cloning."""
    if DEBUG_LEVEL >= 2:
        print(f"DEBUG: Text to read: {text[:100]}...")
    if DEBUG_LEVEL >= 1:
        print(f"   Synthesizing ({len(text)} chars)...")
    
    if ref_audio and os.path.exists(ref_audio):
        prompt_text = f"You are a helpful assistant.<|endofprompt|>{ref_text or ''}"
        output_gen = cosyvoice.inference_zero_shot(text, prompt_text, ref_audio, stream=False)
    else:
        output_gen = cosyvoice.inference_cross_lingual(text, './asset/zero_shot_prompt.wav', stream=False)
    
    final_audio = AudioSegment.empty()
    for item in output_gen:
        if 'tts_speech' in item:
            audio_np = item['tts_speech'].numpy()
            audio_np = np.nan_to_num(audio_np, nan=0.0, posinf=1.0, neginf=-1.0)
            audio_int16 = (audio_np * 32767).astype(np.int16)
            segment = AudioSegment(
                audio_int16.tobytes(),
                frame_rate=cosyvoice.sample_rate,
                sample_width=2,
                channels=1
            )
            final_audio += segment
    return final_audio


# --- Process paragraphs ---
final_mix = AudioSegment.empty()
silence = AudioSegment.silent(duration=800, frame_rate=cosyvoice.sample_rate)

# Check for voice rotation mode
USE_ROTATION = args.rotate
available_voices = []
if USE_ROTATION:
    for voice in PRESET_VOICES:
        voice_path = os.path.abspath(voice["audio"])
        if os.path.exists(voice_path):
            available_voices.append({"audio": voice_path, "text": voice["text"]})
    if not available_voices:
        print("⚠️ No preset voices found for rotation. Using single voice mode.")
        USE_ROTATION = False
    else:
        print(f"🔄 Voice rotation enabled with {len(available_voices)} voices")

print(f"Processing {len(paragraphs)} paragraphs with Fun-CosyVoice 3.0...")

for i, para in enumerate(paragraphs):
    # Select voice based on rotation or single mode
    if USE_ROTATION and available_voices:
        voice = available_voices[i % len(available_voices)]
        current_ref_audio = voice["audio"]
        current_ref_text = voice["text"]
        if DEBUG_LEVEL >= 1:
            voice_name = os.path.basename(voice["audio"])
            print(f"  > Para {i+1}/{len(paragraphs)} - {voice_name} ({len(para)} chars)")
    else:
        current_ref_audio = ref_audio_path
        current_ref_text = args.ref_text
        if DEBUG_LEVEL >= 1:
            print(f"  > Para {i+1}/{len(paragraphs)} ({len(para)} chars)")
    
    try:
        segment = speak(para, current_ref_audio, current_ref_text)
        final_mix += segment
        if i < len(paragraphs) - 1:
            final_mix += silence
    except Exception as e:
        print(f"❌ Error generating para {i}: {e}")

# Upsample to 24k for consistency
final_mix = final_mix.set_frame_rate(24000)

# Add Background Music
if ENABLE_BGM:
    print(f"🎵 Mixing Background Music...")
    final_mix = audio_mixer.mix_bgm(final_mix, specific_filename=BGM_FILE, volume_db=BGM_VOLUME, intro_delay_ms=BGM_INTRO_DELAY)

# Metadata
PRODUCER = "VI AI Foundation"
TITLE = first_line.strip()

final_mix.export(OUTPUT_PATH, format="mp3", bitrate="192k", tags={'title': TITLE, 'artist': PRODUCER})
print(f"✅ Success! Saved → {OUTPUT_PATH}")
