# gen_verse_devotion_voxcpm2.py
# VoxCPM2 - Tokenizer-Free TTS for Multilingual Speech (2B, 48kHz)
# Based on: https://github.com/OpenBMB/VoxCPM
# Model: openbmb/VoxCPM2 (Apache-2.0)

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

try:
    from voxcpm import VoxCPM
except ImportError as e:
    print(f"❌ Failed to import voxcpm: {e}")
    print("Install with: pip install voxcpm")
    sys.exit(1)

from bible_parser import convert_bible_reference
from date_parser import convert_dates_in_text
from text_cleaner import clean_text
import filename_parser
import audio_mixer

# --- Configuration ---
DEFAULT_REF_TEXT = "然而，靠着爱我们的主，在这一切的事上已经得胜有余了。"
HF_MODEL_ID = "openbmb/VoxCPM2"

# Default voices (comma-separated, can be overridden via CLI)
DEFAULT_VOICES = "assets/ref_audio/ref_female.wav,assets/ref_audio/ref_male.wav"

# Voice design presets (natural language descriptions for VoxCPM2's Voice Design)
VOICE_DESIGNS = {
    "gentle_female": "(A young woman, gentle and sweet voice, warm tone)",
    "mature_male": "(A middle-aged man, deep and steady voice, calm pace)",
    "bright_female": "(A young woman, bright and lively voice, slightly fast pace)",
    "warm_male": "(A young man, warm and clear voice, natural pace)",
    "elder_male": "(An elderly man, wise and gentle voice, slow pace)",
    "cheerful_female": "(A young woman, cheerful and energetic voice, upbeat tone)",
}

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
    print("\nVoxCPM2 - Tokenizer-Free TTS (2B, 30 languages, 48kHz)")
    print("\nModes:")
    print("  clone     - Voice cloning from reference audio (default)")
    print("  design    - Voice design from text description (no ref audio)")
    print("  ultimate  - Ultimate cloning (ref audio + transcript)")
    print("\nOptions:")
    print("  --input, -i FILE     Input text file (or pipe via stdin)")
    print("  --prefix PREFIX      Output filename prefix")
    print("  --mode MODE          TTS mode: clone, design, ultimate (Default: clone)")
    print("  --voices FILES       Comma-separated voice files for rotation (clone/ultimate)")
    print("                       (Default: ref_female.wav,ref_male.wav)")
    print("  --ref-text TEXT      Reference text for all voices (clone/ultimate)")
    print("  --design TEXT        Voice design description (design mode)")
    print("                       Or use preset: gentle_female, mature_male, bright_female,")
    print("                       warm_male, elder_male, cheerful_female")
    print("  --designs LIST       Comma-separated design descriptions for rotation (design mode)")
    print("  --no-rotate          Disable voice rotation (use first voice only)")
    print("  --cfg FLOAT          CFG guidance value (Default: 2.0)")
    print("  --steps INT          Diffusion inference timesteps (Default: 10)")
    print("  --bgm                Enable background music")
    print("  --bgm-track FILE     BGM filename (Default: AmazingGrace.MP3)")
    print("  --bgm-volume DB      BGM volume adjustment (Default: -20)")
    print("  --bgm-intro MS       BGM intro delay (Default: 4000)")
    print("  --debug, -d LEVEL    Debug level: 0=minimal, 1=progress, 2=full")
    print("\nExamples:")
    print("  # Voice cloning (default, rotate male/female):")
    print("  python gen_verse_devotion_voxcpm2.py --input sample.txt")
    print("  # Voice design (no reference audio needed):")
    print("  python gen_verse_devotion_voxcpm2.py --input sample.txt --mode design --design gentle_female")
    print("  # Design rotation (multiple voice designs):")
    print("  python gen_verse_devotion_voxcpm2.py --mode design --designs 'gentle_female,mature_male'")
    print("  # Ultimate cloning (highest fidelity):")
    print("  python gen_verse_devotion_voxcpm2.py --mode ultimate --voices ref.wav --ref-text '...'")
    sys.exit(0)

# CLI Args
parser = argparse.ArgumentParser(description="Generate Verse Audio with VoxCPM2 (tokenizer-free multilingual TTS)")
parser.add_argument("--input", "-i", type=str, help="Input text file")
parser.add_argument("--prefix", type=str, default=None, help="Filename prefix")
parser.add_argument("--mode", type=str, default="clone", choices=["clone", "design", "ultimate"],
                    help="TTS mode: clone, design, ultimate (Default: clone)")
parser.add_argument("--voices", type=str, default=DEFAULT_VOICES, help="Comma-separated voice files for rotation")
parser.add_argument("--ref-text", type=str, default=DEFAULT_REF_TEXT, help="Reference text for all voices")
parser.add_argument("--design", type=str, default=None, help="Voice design description or preset name")
parser.add_argument("--designs", type=str, default=None, help="Comma-separated design descriptions for rotation")
parser.add_argument("--no-rotate", action="store_true", help="Disable voice rotation (use first voice only)")
parser.add_argument("--cfg", type=float, default=2.0, help="CFG guidance value (Default: 2.0)")
parser.add_argument("--steps", type=int, default=10, help="Diffusion inference timesteps (Default: 10)")
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
TTS_MODE = args.mode

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
print(f"Loading VoxCPM2 (2B) - Tokenizer-Free Multilingual TTS...")
try:
    use_cuda = torch.cuda.is_available()
    print(f"Loading VoxCPM2... [CUDA={use_cuda}]")
    
    # Initialize VoxCPM2 pipeline
    model = VoxCPM.from_pretrained(
        HF_MODEL_ID,
        load_denoiser=False,
    )
    sample_rate = model.tts_model.sample_rate  # 48000 for VoxCPM2
    
    print(f"✅ VoxCPM2 loaded successfully (sample_rate={sample_rate})")
except Exception as e:
    print(f"❌ Error loading VoxCPM2: {e}")
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
    filename = filename_parser.generate_filename(verse_ref, date_str, extracted_prefix).replace(".mp3", "_voxcpm2.mp3")
else:
    if extracted_prefix:
        filename = f"{extracted_prefix}_Devotion_{date_str}_voxcpm2.mp3"
    else:
        filename = f"Devotion_{date_str}_voxcpm2.mp3"

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


def speak(text: str, ref_audio: str = None, ref_text: str = None, voice_design: str = None) -> AudioSegment:
    """Convert text to audio using VoxCPM2.
    
    Modes:
    - clone: reference_wav_path = ref_audio
    - design: prepend (description) to text
    - ultimate: prompt_wav_path + prompt_text + reference_wav_path
    """
    if DEBUG_LEVEL >= 2:
        print(f"DEBUG: Text to read: {text[:100]}...")
    if DEBUG_LEVEL >= 1:
        print(f"   Synthesizing ({len(text)} chars)...")
    
    try:
        if TTS_MODE == "design":
            # Voice Design: prepend description to text
            design_prefix = voice_design if voice_design else ""
            full_text = f"{design_prefix}{text}"
            if DEBUG_LEVEL >= 1:
                print(f"   🎨 Voice Design: {design_prefix[:60]}...")
            wav = model.generate(
                text=full_text,
                cfg_value=args.cfg,
                inference_timesteps=args.steps,
            )
        elif TTS_MODE == "ultimate" and ref_audio and os.path.exists(ref_audio):
            # Ultimate Cloning: ref audio + transcript
            if DEBUG_LEVEL >= 1:
                print(f"   🎙️ Ultimate Clone: {os.path.basename(ref_audio)}")
            wav = model.generate(
                text=text,
                prompt_wav_path=ref_audio,
                prompt_text=ref_text or "",
                reference_wav_path=ref_audio,  # same ref for max similarity
            )
        elif ref_audio and os.path.exists(ref_audio):
            # Controllable Voice Cloning
            if DEBUG_LEVEL >= 1:
                print(f"   🎛️ Clone: {os.path.basename(ref_audio)}")
            wav = model.generate(
                text=text,
                reference_wav_path=ref_audio,
                cfg_value=args.cfg,
                inference_timesteps=args.steps,
            )
        else:
            # Plain TTS (no ref audio, no design)
            wav = model.generate(
                text=text,
                cfg_value=args.cfg,
                inference_timesteps=args.steps,
            )
        
        # VoxCPM2 returns numpy array at 48kHz
        wav = np.nan_to_num(wav, nan=0.0, posinf=1.0, neginf=-1.0)
        
        # Normalize to [-1, 1] range
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
    print(f"Processing {len(paragraphs)} paragraphs with VoxCPM2 (mode={TTS_MODE})...")

# Build voice rotation based on mode
if TTS_MODE == "design":
    # Voice Design mode: rotate through design descriptions
    if args.designs:
        design_list = [d.strip() for d in args.designs.split(",") if d.strip()]
    elif args.design:
        design_list = [args.design.strip()]
    else:
        # Default: rotate gentle_female + mature_male
        design_list = ["gentle_female", "mature_male"]
    
    # Resolve preset names to descriptions
    resolved_designs = []
    for d in design_list:
        if d in VOICE_DESIGNS:
            resolved_designs.append(VOICE_DESIGNS[d])
        elif d.startswith("("):
            resolved_designs.append(d)  # Raw description
        else:
            # Wrap as a description
            resolved_designs.append(f"({d})")
    
    USE_ROTATION = not args.no_rotate and len(resolved_designs) > 1
    if USE_ROTATION:
        print(f"🎨 Voice Design rotation with {len(resolved_designs)} designs")
    else:
        print(f"🎨 Voice Design: {resolved_designs[0][:60]}...")

else:
    # Clone / Ultimate mode: rotate through reference audios
    PRESET_VOICES = build_preset_voices(args.voices, args.ref_text)
    
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
    if TTS_MODE == "design":
        # Voice Design mode
        current_design = resolved_designs[i % len(resolved_designs)] if USE_ROTATION else resolved_designs[0]
        if DEBUG_LEVEL >= 1:
            print(f"  > Paragraph {i+1}/{len(paragraphs)} - Design ({len(para)} chars)")
        
        try:
            segment = speak(para, voice_design=current_design)
            final += segment
            if i < len(paragraphs) - 1:
                final += silence_between
        except Exception as e:
            print(f"❌ Error generating para {i}: {e}")
    else:
        # Clone / Ultimate mode
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

# Normalize to 48kHz (VoxCPM2 native)
final = final.set_frame_rate(48000)

# Add Background Music
if ENABLE_BGM:
    print(f"🎵 Mixing Background Music...")
    final = audio_mixer.mix_bgm(final, specific_filename=BGM_FILE, volume_db=BGM_VOLUME, intro_delay_ms=BGM_INTRO_DELAY)

# Metadata
PRODUCER = "VI AI Foundation"
TITLE = first_line.strip()

final.export(OUTPUT_PATH, format="mp3", bitrate="192k", tags={'title': TITLE, 'artist': PRODUCER})
print(f"✅ Success! Saved → {OUTPUT_PATH}")
