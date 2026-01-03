# gen_bread_audio_cosy3.py
# Fun-CosyVoice 3.0 (0.5B) – Zero-shot voice cloning for daily bread
# Higher quality than CosyVoice-300M with RLHF-trained prosody

import torch
import numpy as np
import sys
import os
import re
import warnings
import argparse
from datetime import datetime

# Silence noisy libraries
warnings.filterwarnings("ignore", category=FutureWarning, module="diffusers")
warnings.filterwarnings("ignore", category=UserWarning, module="lightning")

from pydub import AudioSegment

# Setup path to find CosyVoice
COSYVOICE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../CosyVoice"))
MATCHA_PATH = os.path.join(COSYVOICE_PATH, "third_party", "Matcha-TTS")

if os.path.exists(COSYVOICE_PATH):
    sys.path.append(COSYVOICE_PATH)
    if os.path.exists(MATCHA_PATH):
        sys.path.append(MATCHA_PATH)
    else:
        print(f"⚠️ Warning: Matcha-TTS not found at {MATCHA_PATH}")
else:
    print(f"⚠️ Warning: CosyVoice path not found at {COSYVOICE_PATH}")

try:
    from cosyvoice.cli.cosyvoice import AutoModel
    from cosyvoice.utils.file_utils import load_wav
except ImportError as e:
    print(f"❌ Failed to import CosyVoice: {e}")
    sys.exit(1)

from bible_parser import convert_bible_reference
from text_cleaner import clean_text
import filename_parser
import audio_mixer

# --- Configuration ---
DEFAULT_REF_AUDIO = "assets/ref_audio/ref_female.wav"
DEFAULT_REF_TEXT = "然而，靠着爱我们的主，在这一切的事上已经得胜有余了。"
MODEL_DIR = "pretrained_models/Fun-CosyVoice3-0.5B"

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
    print("\nFun-CosyVoice 3.0 - Zero-shot voice cloning TTS for Daily Bread")
    print("\nOptions:")
    print("  --input, -i FILE     Input text file")
    print("  --prefix PREFIX      Output filename prefix")
    print("  --voices FILES       Comma-separated voice files for rotation")
    print("                       (Default: ref_female.wav,ref_male.wav)")
    print("  --ref-text TEXT      Reference text for all voices")
    print("  --no-rotate          Disable voice rotation (use first voice only)")
    print("  --bgm                Enable background music")
    print("  --debug, -d LEVEL    Debug level: 0=minimal, 1=progress, 2=full")
    sys.exit(0)

# CLI Args
parser = argparse.ArgumentParser(description="Generate Bread Audio with Fun-CosyVoice 3.0")
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
    if hasattr(cosyvoice, 'fp16'):
        print("🔧 Forcing FP32 (disabling FP16) to prevent audio noise...")
        cosyvoice.fp16 = False
    print(f"✅ Fun-CosyVoice 3.0 loaded (sample_rate={cosyvoice.sample_rate})")
except Exception as e:
    print(f"❌ Error loading Fun-CosyVoice 3.0: {e}")
    sys.exit(1)

# --- Reference Audio Setup ---
# Use first voice from --voices as default reference
first_voice_path = args.voices.split(",")[0].strip() if args.voices else None
ref_audio_path = os.path.abspath(first_voice_path) if first_voice_path else None
if ref_audio_path and os.path.exists(ref_audio_path):
    print(f"Using reference audio: {ref_audio_path}")
else:
    print(f"⚠️ Reference audio not found: {ref_audio_path}")
    ref_audio_path = None

# --- Filename Generation ---
TEXT = clean_text(TEXT)
date_match = re.search(r"(\d{1,2})月(\d{1,2})日", TEXT)
if date_match:
    m, d = date_match.groups()
    date_str = f"{datetime.now().year}{int(m):02d}{int(d):02d}"
else:
    date_str = datetime.today().strftime("%Y%m%d")

extracted_prefix = CLI_PREFIX if CLI_PREFIX else filename_parser.extract_filename_prefix(TEXT)

basename = f"Bread_{date_str}_cosy3.mp3"
if extracted_prefix:
    filename = f"{extracted_prefix}_{basename}"
else:
    filename = basename

if ENABLE_BGM and BGM_FILE:
    bgm_base = os.path.splitext(os.path.basename(BGM_FILE))[0]
    filename = filename.replace(".mp3", f"_bgm_{bgm_base}.mp3")

OUTPUT_DIR = os.path.join(os.getcwd(), "output")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
OUTPUT_PATH = os.path.join(OUTPUT_DIR, filename)
print(f"Target Output: {OUTPUT_PATH}")

TEXT = convert_bible_reference(TEXT)
TEXT = clean_text(TEXT)

paragraphs = [p.strip() for p in re.split(r'\n{2,}', TEXT.strip()) if p.strip()]
intro = paragraphs[0] if paragraphs else ""
main = "\n".join(paragraphs[1:]) if len(paragraphs) > 1 else ""


def speak(text: str, ref_audio: str = None, ref_text: str = None) -> AudioSegment:
    """Convert text to audio using Fun-CosyVoice 3.0."""
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


# Build preset voices from CLI args
PRESET_VOICES = build_preset_voices(args.voices, args.ref_text)

# Check for voice rotation mode (default: enabled unless --no-rotate)
USE_ROTATION = not args.no_rotate and len(PRESET_VOICES) > 1
if USE_ROTATION:
    available_voices = []
    for voice in PRESET_VOICES:
        voice_path = os.path.abspath(voice["audio"])
        if os.path.exists(voice_path):
            available_voices.append({"audio": voice_path, "text": voice["text"]})
    if len(available_voices) >= 2:
        print(f"🔄 Voice rotation enabled with {len(available_voices)} voices")
        intro_voice = available_voices[0]
        main_voice = available_voices[1]
    else:
        print("⚠️ Not enough preset voices for rotation, using single voice")
        intro_voice = main_voice = {"audio": PRESET_VOICES[0]["audio"] if PRESET_VOICES else ref_audio_path, "text": args.ref_text}
else:
    intro_voice = main_voice = {"audio": PRESET_VOICES[0]["audio"] if PRESET_VOICES else ref_audio_path, "text": args.ref_text}

print("Generating introduction...")
seg_intro = speak(intro, intro_voice["audio"], intro_voice["text"])

print("Generating main content...")
seg_main = speak(main, main_voice["audio"], main_voice["text"])

final = seg_intro + AudioSegment.silent(duration=600) + seg_main
final = final.set_frame_rate(24000)

# Add Background Music
if ENABLE_BGM:
    print(f"🎵 Mixing Background Music...")
    final = audio_mixer.mix_bgm(final, specific_filename=BGM_FILE, volume_db=BGM_VOLUME, intro_delay_ms=BGM_INTRO_DELAY)

# Metadata
PRODUCER = "VI AI Foundation"
TITLE = TEXT.strip().split('\n')[0]

final.export(OUTPUT_PATH, format="mp3", bitrate="192k", tags={'title': TITLE, 'artist': PRODUCER})
print(f"✅ Success! Saved → {OUTPUT_PATH}")
