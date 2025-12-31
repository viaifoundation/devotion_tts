# gen_verse_devotion_cosy3.py
# Fun-CosyVoice 3.0 (0.5B) – Zero-shot voice cloning for verse devotion
# Higher quality than CosyVoice-300M with RLHF-trained prosody

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

# Setup path to find CosyVoice (sibling directory)
# and its third_party dependencies (Matcha-TTS)
COSYVOICE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../CosyVoice"))
MATCHA_PATH = os.path.join(COSYVOICE_PATH, "third_party", "Matcha-TTS")

if os.path.exists(COSYVOICE_PATH):
    sys.path.append(COSYVOICE_PATH)
    if os.path.exists(MATCHA_PATH):
        sys.path.append(MATCHA_PATH)
    else:
        print(f"⚠️ Warning: Matcha-TTS not found at {MATCHA_PATH}")
        print("Run: cd ../CosyVoice && git submodule update --init --recursive")
else:
    print(f"⚠️ Warning: CosyVoice path not found at {COSYVOICE_PATH}")
    print("Please clone it: git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git ../CosyVoice")

try:
    # Fun-CosyVoice 3.0 uses AutoModel instead of CosyVoice
    from cosyvoice.cli.cosyvoice import AutoModel
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

# --- Configuration ---
DEFAULT_REF_AUDIO = "assets/ref_audio/ref_female.wav"
DEFAULT_REF_TEXT = "然而，靠着爱我们的主，在这一切的事上已经得胜有余了。"
MODEL_DIR = "pretrained_models/Fun-CosyVoice3-0.5B"  # Fun-CosyVoice 3.0 model

# Preset voice rotation (for --rotate mode)
# Uses existing reference audio files in assets/ref_audio/
PRESET_VOICES = [
    {"name": "female (ref_female.wav)", "audio": "assets/ref_audio/ref_female.wav", "text": "然而，靠着爱我们的主，在这一切的事上已经得胜有余了。"},
    {"name": "male (ref_male.wav)", "audio": "assets/ref_audio/ref_male.wav", "text": "然而，靠着爱我们的主，在这一切的事上已经得胜有余了。"},
]

# CLI Help
if "-?" in sys.argv:
    print(f"Usage: python {sys.argv[0]} [OPTIONS]")
    print("\nFun-CosyVoice 3.0 - Zero-shot voice cloning TTS")
    print("\nOptions:")
    print("  --input, -i FILE     Input text file (or pipe via stdin)")
    print("  --prefix PREFIX      Output filename prefix")
    print("  --ref-audio FILE     Reference audio for voice cloning (Default: ref_female.m4a)")
    print("  --ref-text TEXT      Text spoken in reference audio")
    print("  --rotate             Rotate through preset voices (ref_female.m4a, ref_male.m4a)")
    print("  --bgm                Enable background music")
    print("  --bgm-track FILE     BGM filename (Default: AmazingGrace.MP3)")
    print("  --bgm-volume DB      BGM volume adjustment (Default: -20)")
    print("  --bgm-intro MS       BGM intro delay (Default: 4000)")
    print("  --debug, -d LEVEL    Debug level: 0=minimal, 1=progress, 2=full")
    print("\nVoice Cloning:")
    print("  Default voice: ref_female.m4a (female)")
    print("  With --rotate: alternates between ref_female.m4a and ref_male.m4a")
    print("  Custom voice: --ref-audio your_voice.m4a --ref-text '对应的文字'")
    sys.exit(0)

# CLI Args
parser = argparse.ArgumentParser(description="Generate Verse Audio with Fun-CosyVoice 3.0 (zero-shot voice cloning)")
parser.add_argument("--input", "-i", type=str, help="Input text file")
parser.add_argument("--prefix", type=str, default=None, help="Filename prefix")
parser.add_argument("--ref-audio", type=str, default=DEFAULT_REF_AUDIO, help="Reference audio for voice cloning (Default: ref_female.m4a)")
parser.add_argument("--ref-text", type=str, default=DEFAULT_REF_TEXT, help="Text spoken in reference audio")
parser.add_argument("--rotate", action="store_true", help="Rotate between ref_female.m4a and ref_male.m4a")
parser.add_argument("--speed", type=str, default="1.0", help="Speed instruction (placeholder)")
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

# 2. Try Stdin (Piped)
elif not sys.stdin.isatty():
    print("Reading text from Stdin...")
    TEXT = sys.stdin.read()

# 3. Fallback
else:
    TEXT = """
"　神爱世人，甚至将他的独生子赐给他们，叫一切信他的，不至灭亡，反得永生。因为　神差他的儿子降世，不是要定世人的罪，乃是要叫世人因他得救。信他的人，不被定罪；不信的人，罪已经定了，因为他不信　神独生子的名。
(约翰福音 3:16-18)
"""

# --- Model Loading ---
print("Loading Fun-CosyVoice 3.0 (0.5B) - RLHF-trained for better prosody...")
try:
    use_cuda = torch.cuda.is_available()
    print(f"Loading Fun-CosyVoice3-0.5B... [CUDA={use_cuda}]")
    
    # Check if model exists locally, otherwise use HuggingFace path
    if os.path.exists(os.path.join(COSYVOICE_PATH, MODEL_DIR)):
        model_path = os.path.join(COSYVOICE_PATH, MODEL_DIR)
    elif os.path.exists(MODEL_DIR):
        model_path = MODEL_DIR
    else:
        # Try HuggingFace/Modelscope download
        model_path = 'FunAudioLLM/Fun-CosyVoice3-0.5B-2512'
        print(f"Model not found locally, attempting to download from: {model_path}")
    
    cosyvoice = AutoModel(model_dir=model_path)
    print(f"✅ Fun-CosyVoice 3.0 loaded successfully (sample_rate={cosyvoice.sample_rate})")

except Exception as e:
    print(f"❌ Error loading Fun-CosyVoice 3.0: {e}")
    print("Ensure you have downloaded the model:")
    print("  huggingface-cli download FunAudioLLM/Fun-CosyVoice3-0.5B-2512 --local-dir pretrained_models/Fun-CosyVoice3-0.5B")
    sys.exit(1)

# --- Reference Audio Setup ---
ref_audio_path = os.path.abspath(args.ref_audio) if args.ref_audio else None
if ref_audio_path and os.path.exists(ref_audio_path):
    print(f"Using reference audio for voice cloning: {ref_audio_path}")
    USE_VOICE_CLONING = True
else:
    print(f"⚠️ Reference audio not found: {ref_audio_path}")
    print("Will use zero-shot without voice cloning")
    USE_VOICE_CLONING = False
    ref_audio_path = None

# --- Generate filename dynamically ---
TEXT = clean_text(TEXT)
first_line = TEXT.strip().split('\n')[0]
date_match = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", first_line)
if date_match:
    m, d, y = date_match.groups()
    date_str = f"{y}-{int(m):02d}-{int(d):02d}"
else:
    date_match = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", first_line)
    if date_match:
        y, m, d = date_match.groups()
        date_str = f"{y}-{int(m):02d}-{int(d):02d}"
    else:
        date_str = datetime.today().strftime("%Y-%m-%d")

verse_ref = filename_parser.extract_verse_from_text(TEXT)
extracted_prefix = CLI_PREFIX if CLI_PREFIX else filename_parser.extract_filename_prefix(TEXT)

filename = filename_parser.generate_filename_v2(
    title=first_line, 
    date=date_str, 
    prefix=extracted_prefix,
    ext=".mp3"
).replace(".mp3", "_cosy3.mp3")

if ENABLE_BGM:
    filename = filename.replace(".mp3", "_bgm.mp3")

OUTPUT_DIR = os.path.join(os.getcwd(), "output")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
OUTPUT_PATH = os.path.join(OUTPUT_DIR, filename)
print(f"Target Output: {OUTPUT_PATH}")

TEXT = convert_bible_reference(TEXT)
TEXT = convert_dates_in_text(TEXT)
TEXT = clean_text(TEXT)

if DEBUG_LEVEL >= 2:
    print("\n=== TEXT AFTER CONVERSION (DEBUG) ===")
    print(TEXT)
    print("=== END DEBUG ===")

paragraphs = [p.strip() for p in re.split(r'\n{2,}', TEXT.strip()) if p.strip()]


def speak(text: str, ref_audio: str = None, ref_text: str = None) -> AudioSegment:
    """Convert text to audio using Fun-CosyVoice 3.0 zero-shot voice cloning."""
    if DEBUG_LEVEL >= 2:
        print(f"DEBUG: Text to read: {text[:100]}...")
    if DEBUG_LEVEL >= 1:
        print(f"   Synthesizing ({len(text)} chars)...")
    
    # Fun-CosyVoice 3.0 inference
    # Uses zero-shot voice cloning with reference audio
    if ref_audio and os.path.exists(ref_audio):
        # Format: "You are a helpful assistant.<|endofprompt|>reference_text"
        prompt_text = f"You are a helpful assistant.<|endofprompt|>{ref_text or ''}"
        output_gen = cosyvoice.inference_zero_shot(
            text, 
            prompt_text,
            ref_audio,
            stream=False
        )
    else:
        # Fallback: cross-lingual without specific voice
        output_gen = cosyvoice.inference_cross_lingual(
            text,
            './asset/zero_shot_prompt.wav',  # Default prompt
            stream=False
        )
    
    final_audio = AudioSegment.empty()
    
    for item in output_gen:
        if 'tts_speech' in item:
            audio_np = item['tts_speech'].numpy()
            # Fix NaN/Inf values that cause silence
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
if DEBUG_LEVEL >= 1:
    print(f"Processing {len(paragraphs)} paragraphs with Fun-CosyVoice 3.0...")

# Check for voice rotation mode
USE_ROTATION = args.rotate
if USE_ROTATION:
    # Find available preset voices
    available_voices = []
    for voice in PRESET_VOICES:
        voice_path = os.path.abspath(voice["audio"])
        if os.path.exists(voice_path):
            available_voices.append({"audio": voice_path, "text": voice["text"], "name": voice.get("name", "Unknown")})
    
    if not available_voices:
        print("⚠️ No preset voices found for rotation. Using single voice mode.")
        print("   To enable rotation, add voice samples to assets/ref_audio/voices/")
        USE_ROTATION = False
    else:
        print(f"🔄 Voice rotation enabled with {len(available_voices)} voices")

final = AudioSegment.empty()
silence_between = AudioSegment.silent(duration=700, frame_rate=cosyvoice.sample_rate)

for i, para in enumerate(paragraphs):
    # Select voice based on rotation or single mode
    if USE_ROTATION and available_voices:
        voice = available_voices[i % len(available_voices)]
        current_ref_audio = voice["audio"]
        current_ref_text = voice["text"]
        if DEBUG_LEVEL >= 1:
            voice_name = voice["name"]
            print(f"  > Paragraph {i+1}/{len(paragraphs)} - Voice: {voice_name} ({len(para)} chars)")
    else:
        current_ref_audio = ref_audio_path
        current_ref_text = args.ref_text
        if DEBUG_LEVEL >= 1:
            print(f"  > Paragraph {i+1}/{len(paragraphs)} ({len(para)} chars)")
    
    segment = speak(para, current_ref_audio, current_ref_text)
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
COMMENTS = f"Verse: {verse_ref}; Model: Fun-CosyVoice3; BGM: {bgm_info_str}"

final.export(OUTPUT_PATH, format="mp3", bitrate="192k", tags={
    'title': TITLE,
    'artist': PRODUCER,
    'album': ALBUM,
    'comments': COMMENTS
})
print(f"✅ Success! Saved → {OUTPUT_PATH}")
