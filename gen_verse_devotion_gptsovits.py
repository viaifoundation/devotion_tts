
# gen_verse_devotion_gptsovits.py
# GPT-SoVITS Generator for Spark (NVIDIA Container)

import os
import sys
import re
import argparse
import logging
from datetime import datetime
from pydub import AudioSegment
import numpy as np
import audio_mixer
import filename_parser
from text_cleaner import clean_text
from bible_parser import convert_bible_reference
from date_parser import convert_dates_in_text

# --- GPT-SoVITS Setup ---
# Assuming standard container path
GPT_SOVITS_ROOT = "/workspace/GPT-SoVITS"

def find_and_add_module(root_dir, module_name):
    """Dynamically find a module file and add its parent directory to sys.path."""
    # module_name should be like "ERes2NetV2" (without .py)
    target_file = f"{module_name}.py"
    for root, dirs, files in os.walk(root_dir):
        if target_file in files:
            if root not in sys.path:
                print(f"🔧 Found {target_file} in {root}, adding to sys.path")
                sys.path.append(root)
            return True
    return False

if os.path.exists(GPT_SOVITS_ROOT):
    sys.path.append(GPT_SOVITS_ROOT)
    sys.path.append(os.path.join(GPT_SOVITS_ROOT, "GPT_SoVITS"))
    
    # Dynamic fix for missing modules
    find_and_add_module(GPT_SOVITS_ROOT, "ERes2NetV2")
    find_and_add_module(GPT_SOVITS_ROOT, "vits_decoder") # Another common one usually
else:
    print(f"⚠️ Warning: GPT_SOVITS_ROOT not found at {GPT_SOVITS_ROOT}")

# Attempt Imports
try:
    from GPT_SoVITS.TTS_infer_pack.TTS import TTS, TTS_Config
    from tools.i18n.i18n import I18nAuto
    import torch
except ImportError as e:
    print(f"❌ Failed to import GPT-SoVITS modules: {e}")
    print("Ensure you are running in the correct container and paths are set.")
    # We continue to allow checking help/args, but main will fail
    TTS = None

# --- Configuration ---
# Default Reference Audio (User should provide this for best results)
DEFAULT_REF_AUDIO = "assets/ref_audio/ref.wav"
DEFAULT_REF_TEXT = "你好，我是可以在本地运行的语音生成模型。"
DEFAULT_REF_LANG = "zh"

def scan_models(root_dir):
    """Scan for SoVITS (.pth) and GPT (.ckpt) models."""
    sovits_path = ""
    gpt_path = ""
    
    # Search in pretrained_models
    search_dirs = [
        os.path.join(root_dir, "GPT_SoVITS", "pretrained_models"),
        os.path.join(root_dir, "pretrained_models")
    ]
    
    for d in search_dirs:
        if not os.path.exists(d): continue
        for root, _, files in os.walk(d):
            for f in files:
                if f.endswith(".pth"):
                    # Typically SoVITS weights (e.g. s2G488k.pth)
                    if "s2" in f or "SoVITS" in f:
                        sovits_path = os.path.join(root, f)
                elif f.endswith(".ckpt"):
                    # Typically GPT weights (e.g. s1bert...ckpt)
                    if "s1" in f or "GPT" in f or ".ckpt" in f:
                        gpt_path = os.path.join(root, f)
                        
    return sovits_path, gpt_path

def main():
    parser = argparse.ArgumentParser(description="Generate Verse Audio with GPT-SoVITS")
    parser.add_argument("--input", "-i", type=str, help="Input text file")
    parser.add_argument("--prefix", type=str, default=None, help="Filename prefix")
    parser.add_argument("--ref-audio", type=str, default=DEFAULT_REF_AUDIO, help="Reference audio path")
    parser.add_argument("--ref-text", type=str, default=DEFAULT_REF_TEXT, help="Reference audio text")
    parser.add_argument("--ref-lang", type=str, default=DEFAULT_REF_LANG, help="Reference audio language (zh, en, ja)")
    parser.add_argument("--bgm", action="store_true", help="Enable background music")
    parser.add_argument("--bgm-track", type=str, default="AmazingGrace.mp3", help="BGM track filename")
    parser.add_argument("--bgm-volume", type=int, default=-20, help="BGM volume (dB)")
    parser.add_argument("--bgm-intro", type=int, default=4000, help="BGM intro (ms)")
    
    args = parser.parse_args()
    
    if not TTS:
        print("❌ Core imports failed. Aborting.")
        sys.exit(1)

    # 1. Text Processing
    if args.input and os.path.exists(args.input):
        print(f"Reading text from file: {args.input}")
        with open(args.input, "r", encoding="utf-8") as f:
            TEXT = f.read()
    elif not sys.stdin.isatty():
        print("Reading text from Stdin...")
        TEXT = sys.stdin.read()
    else:
        # Fallback text
        TEXT = "神爱世人，甚至将他的独生子赐给他们。"

    # Clean and Process
    TEXT = clean_text(TEXT)
    first_line = TEXT.strip().split('\n')[0]
    
    # 2. Filename Generation
    # Extract Date
    date_match = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", first_line)
    if date_match:
         m, d, y = date_match.groups()
         date_str = f"{y}-{int(m):02d}-{int(d):02d}"
    else:
         date_str = datetime.today().strftime("%Y-%m-%d")         

    verse_ref = filename_parser.extract_verse_from_text(TEXT)
    extracted_prefix = args.prefix if args.prefix else filename_parser.extract_filename_prefix(TEXT)
    
    filename = filename_parser.generate_filename_v2(
        title=first_line, 
        date=date_str, 
        prefix=extracted_prefix,
        ext=".mp3"
    ).replace(".mp3", "_gptsovits.mp3")

    if args.bgm:
        filename = filename.replace(".mp3", "_bgm.mp3")

    OUTPUT_DIR = os.path.join(os.getcwd(), "output")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    OUTPUT_PATH = os.path.join(OUTPUT_DIR, filename)
    print(f"Target Output: {OUTPUT_PATH}")

    # 3. Model Loading
    sovits_path, gpt_path = scan_models(GPT_SOVITS_ROOT)
    if not sovits_path or not gpt_path:
        print(f"❌ Could not find models in {GPT_SOVITS_ROOT}")
        print("Please run 'source setup_gptsovits.sh' first.")
        sys.exit(1)
        
    print(f"Loading Models:\n  SoVITS: {sovits_path}\n  GPT: {gpt_path}")
    
    # Initialize TTS
    # Config structure might vary by version, assuming standard instantiation
    # Usually: TTS_Config(gpt_path, sovits_path) or similar
    # If TTS_Config expects a YAML, we might need to find it.
    # Looking at inference_cli.py usually helps.
    # We will try direct init if possible, or construct config
    
    # Assuming V2 api pattern:
    # Use absolute path for config to avoid CWD issues
    config_path = os.path.join(GPT_SOVITS_ROOT, "GPT_SoVITS", "configs", "tts_infer.yaml")
    
    if not os.path.exists(config_path):
        # Fallback: maybe it's in the root configs?
        config_path = os.path.join(GPT_SOVITS_ROOT, "configs", "tts_infer.yaml")
        if not os.path.exists(config_path):
             print(f"⚠️ Warning: Could not find tts_infer.yaml at {config_path}")
             # Some versions might default if None is passed
    
    try:
        config = TTS_Config(config_path)
    except Exception as e:
        print(f"⚠️ Failed to init TTS_Config with {config_path}: {e}")
        print("Attempting default init...")
        config = TTS_Config("tts_infer.yaml")

    config.default_gpt_path = gpt_path
    config.default_sovits_path = sovits_path
    
    # CRITICAL: TTS uses relative paths internally. Change to GPT-SoVITS root.
    original_cwd = os.getcwd()
    os.chdir(GPT_SOVITS_ROOT)
    print(f"Changed working directory to: {GPT_SOVITS_ROOT}")
    
    tts_pipeline = TTS(config)
    
    # 4. Inference
    # Check Ref Audio
    if not os.path.exists(args.ref_audio):
        print(f"⚠️ Reference audio not found at {args.ref_audio}")
        print("Using zero-shot (if supported) or failing.")
        processed_ref_audio = args.ref_audio # Pass through, will likely fail later
    else:
        # Preprocess Reference Audio: Convert to standard WAV (16-bit, 44100Hz) to avoid format issues
        # This handles .m4a, .mp3, etc. automatically via pydub + ffmpeg
        print(f"Processing reference audio: {args.ref_audio}")
        try:
            ref_seg = AudioSegment.from_file(args.ref_audio)
            # Normalize to 44.1kHz, 16-bit, Mono (optional but safer for SOME models, though typically stereo is fine)
            # GPT-SoVITS usually handles it, but clean wav is best.
            # We'll save to a temp filename in the same dir or output dir
            temp_ref_path = os.path.join(OUTPUT_DIR, "temp_ref_processed.wav")
            ref_seg = ref_seg.set_frame_rate(44100).set_sample_width(2).set_channels(1)
            ref_seg.export(temp_ref_path, format="wav")
            processed_ref_audio = temp_ref_path
            print(f"  Converted to safe WAV: {processed_ref_audio}")
        except Exception as e:
            print(f"⚠️ Failed to convert reference audio: {e}")
            print("Trying to use original file...")
            processed_ref_audio = args.ref_audio

    # Text Normalization
    TEXT = convert_bible_reference(TEXT)
    TEXT = convert_dates_in_text(TEXT)
    cleaned_input = clean_text(TEXT)
    
    print("Synthesizing...")
    # Generator output
    # tts_pipeline.run return generator of audio chunks
    # params: text, text_lang, ref_audio_path, ref_text, ref_text_lang, ...
    
    req = {
        "text": cleaned_input,
        "text_lang": "zh",
        "ref_audio_path": processed_ref_audio,
        "prompt_text": args.ref_text,
        "prompt_lang": args.ref_lang,
        "top_k": 5,
        "top_p": 1,
        "temperature": 1,
        "text_split_method": "cut5",
        "batch_size": 1,
        "speed_factor": 1.0,
        "fragment_interval": 0.3,
        "seed": -1,
        "return_fragment": False,
        "parallel_infer": True,
        "repetition_penalty": 1.35
    }
    
    audio_generator = tts_pipeline.run(req)
    
    final_audio = AudioSegment.empty()
    
    for item in audio_generator:
        sr, audio_data = item
        # audio_data is numpy float or int set?
        # Usually float32 (-1 to 1) or int16
        if audio_data.dtype == np.float32:
             audio_int16 = (audio_data * 32767).astype(np.int16)
        else:
             audio_int16 = audio_data
             
        segment = AudioSegment(
            audio_int16.tobytes(), 
            frame_rate=sr,
            sample_width=2, 
            channels=1
        )
        final_audio += segment
        
    # 5. BGM Mixing
    bgm_info_str = "None"
    if args.bgm:
        print(f"🎵 Mixing Background Music...")
        final_audio = audio_mixer.mix_bgm(
            final_audio,
            specific_filename=args.bgm_track,
            volume_db=args.bgm_volume,
            intro_delay_ms=args.bgm_intro
        )
        bgm_info_str = os.path.basename(args.bgm_track)

    # 6. Export with Metadata
    PRODUCER = "VI AI Foundation"
    TITLE = first_line
    ALBUM = "Devotion"
    COMMENTS = f"Verse: {verse_ref}; BGM: {bgm_info_str}"
    
    final_audio.export(OUTPUT_PATH, format="mp3", bitrate="192k", tags={
        'title': TITLE,
        'artist': PRODUCER,
        'album': ALBUM,
        'comments': COMMENTS
    })
    print(f"✅ Success! Saved → {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
