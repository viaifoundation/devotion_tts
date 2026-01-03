
# gen_soh_prayer_gptsovits.py
# GPT-SoVITS Generator for SOH Prayer (Spark/Docker)

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
from date_parser import convert_dates_in_text, extract_date_from_text

# --- GPT-SoVITS Setup ---
# Assuming standard container path
GPT_SOVITS_ROOT = "/workspace/GPT-SoVITS"

def find_and_add_module(root_dir, module_name):
    """Dynamically find a module file and add its parent directory to sys.path."""
    target_file = f"{module_name}.py"
    for root, dirs, files in os.walk(root_dir):
        if target_file in files:
            if root not in sys.path:
                print(f"🔧 Found {target_file} in {root}, adding to sys.path")
                sys.path.append(root)
            return True
    return False

if os.path.exists(GPT_SOVITS_ROOT):
    # absolute paths to ensure robustness even if cwd changes
    sys.path.append(os.path.abspath(GPT_SOVITS_ROOT))
    sys.path.append(os.path.abspath(os.path.join(GPT_SOVITS_ROOT, "GPT_SoVITS")))
    
    find_and_add_module(GPT_SOVITS_ROOT, "ERes2NetV2")
    find_and_add_module(GPT_SOVITS_ROOT, "vits_decoder")
else:
    print(f"⚠️ Warning: GPT_SOVITS_ROOT not found at {GPT_SOVITS_ROOT}")

# Attempt Imports
try:
    # Important: switch to GPT-SoVITS root for imports to work if they rely on relative paths
    # But we restore cwd later
    old_cwd = os.getcwd()
    if os.path.exists(GPT_SOVITS_ROOT):
        os.chdir(GPT_SOVITS_ROOT)
        
    from GPT_SoVITS.TTS_infer_pack.TTS import TTS, TTS_Config
    from tools.i18n.i18n import I18nAuto
    import torch
    import torch.distributed as dist
    
    # Initialize torch.distributed for single-process inference
    # Required by some GPT-SoVITS internal operations
    if not dist.is_initialized():
        os.environ.setdefault("MASTER_ADDR", "localhost")
        os.environ.setdefault("MASTER_PORT", "29500")
        os.environ.setdefault("RANK", "0")
        os.environ.setdefault("WORLD_SIZE", "1")
        dist.init_process_group(backend="gloo", rank=0, world_size=1)
    
    os.chdir(old_cwd)
    
    # Note: The gsv-v2final-pretrained checkpoints already contain complete configs,
    # so no patching is needed. If you're using older or incomplete checkpoints,
    # you may need to add compatibility patches here.
    print("✅ GPT-SoVITS modules loaded successfully")
    
except ImportError as e:
    print(f"❌ Failed to import GPT-SoVITS modules: {e}")
    print("Ensure you are running in the correct container and paths are set.")
    TTS = None

# --- Configuration ---
DEFAULT_REF_AUDIO = "assets/ref_audio/ref.wav"
DEFAULT_REF_TEXT = "你好，我是可以在本地运行的语音生成模型。"
DEFAULT_REF_LANG = "zh"

def scan_models(root_dir):
    """Scan for SoVITS (.pth) and GPT (.ckpt) models."""
    sovits_path = ""
    gpt_path = ""
    
    search_dirs = [
        os.path.join(root_dir, "GPT_SoVITS", "pretrained_models"),
        os.path.join(root_dir, "pretrained_models")
    ]
    
    for d in search_dirs:
        if not os.path.exists(d): continue
        for root, _, files in os.walk(d):
            for f in files:
                if f.endswith(".pth"):
                    if "s2" in f or "SoVITS" in f:
                        sovits_path = os.path.join(root, f)
                elif f.endswith(".ckpt"):
                    if "s1" in f or "GPT" in f or ".ckpt" in f:
                        gpt_path = os.path.join(root, f)
                        
    return sovits_path, gpt_path

# CLI Help
if "-?" in sys.argv or "-h" in sys.argv or "--help" in sys.argv:
    print(f"Usage: python {sys.argv[0]} [OPTIONS]")
    print("\nOptions:")
    print("  --input, -i FILE     Input text file")
    print("  --prefix PREFIX      Filename prefix (e.g. MyPrefix)")
    print("  --ref-audio PATH     Reference audio file (3-10 seconds, required for voice cloning)")
    print("  --ref-text TEXT      Exact text content of the reference audio")
    print("  --ref-lang LANG      Reference audio language: zh, en, ja (Default: zh)")
    print("  --speed SPEED        Speed factor: 1.0, 1.2, +20%, -10% (Default: 1.0)")
    print("  --bgm                Enable background music (Default: False)")
    print("  --bgm-track TRACK    Specific BGM filename (Default: AmazingGrace.mp3)")
    print("  --bgm-volume VOL     BGM volume adjustment in dB (Default: -20)")
    print("  --bgm-intro MS       BGM intro delay in ms (Default: 4000)")
    print("  --help, -h           Show this help")
    print("\nExample:")
    print("  python gen_soh_prayer_gptsovits.py -i input.txt --ref-audio ref.wav --ref-text \"Content\"")
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description="Generate SOH Prayer Audio with GPT-SoVITS")
    parser.add_argument("--input", "-i", type=str, help="Input text file")
    parser.add_argument("--prefix", type=str, default=None, help="Filename prefix")
    
    # GPT-SoVITS specific args
    parser.add_argument("--ref-audio", type=str, default=DEFAULT_REF_AUDIO, help="Reference audio path")
    parser.add_argument("--ref-text", type=str, default=DEFAULT_REF_TEXT, help="Reference audio text")
    parser.add_argument("--ref-lang", type=str, default=DEFAULT_REF_LANG, help="Reference audio language")
    
    parser.add_argument("--speed", type=str, default="1.0", help="Speed factor/rate")
    
    # BGM args
    parser.add_argument("--bgm", action="store_true", help="Enable background music")
    parser.add_argument("--bgm-track", type=str, default="AmazingGrace.mp3", help="BGM track filename")
    parser.add_argument("--bgm-volume", type=int, default=-20, help="BGM volume adjustment in dB")
    parser.add_argument("--bgm-intro", type=int, default=4000, help="BGM intro delay in ms")

    args = parser.parse_args()
    
    # Parse Speed
    speed_factor = 1.0
    if args.speed:
        try:
            s = args.speed
            if "%" in s:
                val = float(s.replace("%", ""))
                speed_factor = 1.0 + (val / 100.0)
            else:
                speed_factor = float(s)
        except ValueError:
            print(f"⚠️ Invalid speed format '{args.speed}', using 1.0")

    # Limit speed to safe range for SoVITS
    speed_factor = max(0.5, min(2.0, speed_factor))

    # Input Text Processing
    if args.input:
        print(f"Reading text from file: {args.input}")
        with open(args.input, "r", encoding="utf-8") as f:
            TEXT = f.read()
    elif not sys.stdin.isatty():
        print("Reading text from Stdin...")
        TEXT = sys.stdin.read()
    else:
        TEXT = """
“　神爱世人，甚至将他的独生子赐给他们，叫一切信他的，不至灭亡，反得永生。
(约翰福音 3:16)
"""

    # --- SOH Filename Logic ---
    TEXT = clean_text(TEXT)
    first_line = TEXT.strip().split('\n')[0]
    
    # Extract date
    date_str_dash = extract_date_from_text(TEXT)
    if not date_str_dash:
        date_str_dash = datetime.today().strftime("%Y-%m-%d")
    
    # YYYY-MM-DD -> YYYYMMDD
    date_obj = datetime.strptime(date_str_dash, "%Y-%m-%d")
    date_str_compact = date_obj.strftime("%Y%m%d")
    
    # SOH Convention: 乡音情_{yyyymmdd}.mp3, unless prefix override
    if args.prefix:
        filename = f"{args.prefix}_{date_str_compact}.mp3"
    else:
        filename = f"乡音情_{date_str_compact}.mp3"

    OUTPUT_DIR = os.path.join(os.getcwd(), "output")
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    # Note: Using absolute path for export to avoid cwd confusion
    output_path_abs = os.path.abspath(os.path.join(OUTPUT_DIR, filename))
    print(f"Target Output: {output_path_abs}")

    # Process Text content
    TEXT = convert_bible_reference(TEXT)
    TEXT = convert_dates_in_text(TEXT)
    TEXT = clean_text(TEXT)
    
    # Split for TTS processing (simple paragraph split)
    paragraphs = [p.strip() for p in re.split(r'\n{2,}', TEXT.strip()) if p.strip()]

    # --- Initialize GPT-SoVITS ---
    if not TTS:
        print("❌ TTS module not loaded. Exiting.")
        sys.exit(1)

    print("🚀 Initializing GPT-SoVITS...")
    
    # Use absolute path for config to avoid CWD issues
    config_path = os.path.join(GPT_SOVITS_ROOT, "GPT_SoVITS", "configs", "tts_infer.yaml")
    
    if not os.path.exists(config_path):
        # Fallback: maybe it's in the root configs?
        config_path = os.path.join(GPT_SOVITS_ROOT, "configs", "tts_infer.yaml")
        if not os.path.exists(config_path):
             print(f"⚠️ Warning: Could not find tts_infer.yaml at {config_path}")
    
    try:
        config = TTS_Config(config_path)
    except Exception as e:
        print(f"⚠️ Failed to init TTS_Config with {config_path}: {e}")
        print("Attempting default init...")
        config = TTS_Config("tts_infer.yaml")
    
    sovits_path, gpt_path = scan_models(GPT_SOVITS_ROOT)
    if not sovits_path or not gpt_path:
        print("❌ Could not find SoVITS or GPT models in pretrained_models directories.")
        sys.exit(1)
        
    print(f"  • SoVITS: {os.path.basename(sovits_path)}")
    print(f"  • GPT:    {os.path.basename(gpt_path)}")
    
    # Set the correct config attributes for TTS
    # NOTE: TTS uses t2s_weights_path and sovits_weights_path, NOT default_gpt_path
    config.t2s_weights_path = gpt_path      # GPT/t2s = .ckpt file
    config.sovits_weights_path = sovits_path  # SoVITS = .pth file
    
    # CRITICAL: TTS uses relative paths internally. Change to GPT-SoVITS root.
    # But FIRST, convert our paths to absolute so they still work after chdir.
    original_cwd = os.getcwd()
    output_path_abs = os.path.abspath(output_path_abs)
    ref_audio_abs = os.path.abspath(args.ref_audio) if args.ref_audio else None
    output_dir_abs = os.path.abspath(OUTPUT_DIR)
    
    os.chdir(GPT_SOVITS_ROOT)
    print(f"Changed working directory to: {GPT_SOVITS_ROOT}")
    
    tts_pipeline = TTS(config)

    # --- Ref Audio Preparation ---
    ref_audio_path = ref_audio_abs  # Use the pre-computed absolute path
    if not os.path.exists(ref_audio_path):
        print(f"❌ Reference audio not found: {ref_audio_path}")
        sys.exit(1)

    # Convert ref audio if needed (logic from verse script)
    ext = os.path.splitext(ref_audio_path)[1].lower()
    if ext != ".wav":
        print(f"🔄 Converting reference audio {ext} -> .wav ...")
        try:
            audio = AudioSegment.from_file(ref_audio_path)
            # Ensure 3-10s duration check here?
            if len(audio) < 3000 or len(audio) > 10000:
                 print(f"⚠️ Warning: Reference audio length {len(audio)}ms is outside recommended 3-10s range.")
            
            new_ref_path = ref_audio_path.replace(ext, ".wav")
            audio.export(new_ref_path, format="wav")
            ref_audio_path = new_ref_path
            print(f"  • Converted to: {ref_audio_path}")
        except Exception as e:
            print(f"❌ Failed to convert reference audio: {e}")
            sys.exit(1)

    # Change CWD back done later
    # os.chdir(original_cwd) 


    # --- Generation Loop ---
    final_audio = AudioSegment.empty()
    silence = AudioSegment.silent(duration=800) # Gap between paragraphs

    print(f"Processing {len(paragraphs)} paragraphs (Voice Clone)...")
    
    try:
        for i, para in enumerate(paragraphs):
            print(f"  > Para {i+1}/{len(paragraphs)} ({len(para)} chars)...")
            
            # Run Inference
            # Returns generator
            sources = tts_pipeline.run({
                "text": para,
                "text_lang": "zh",
                "ref_audio_path": ref_audio_path,
                "prompt_text": args.ref_text,
                "prompt_lang": args.ref_lang,
                "top_k": 5,
                "top_p": 1,
                "temperature": 1,
                "text_split_method": "cut5",
                "batch_size": 1,
                "speed_factor": speed_factor,
                "split_bucket": False,  # Disable bucket splitting for speed adjustment
                "parallel_infer": False,  # Disable parallel inference (requires torch.distributed)
                "return_fragment": False
            })
            
            # Collect audio fragments
            full_sr, full_audio_data = next(sources)
            
            # Convert numpy array to int16 for AudioSegment
            # GPT-SoVITS output usually (32000, np.array)
            if full_audio_data.dtype == np.float32 or full_audio_data.dtype == np.float64:
                # Normalize float (-1 to 1) to int16
                full_audio_data = (full_audio_data * 32767).clip(-32768, 32767).astype(np.int16)
            elif full_audio_data.dtype != np.int16:
                full_audio_data = full_audio_data.astype(np.int16)

            # Create segment
            # Note: pydub requires bytes
            segment = AudioSegment(
                full_audio_data.tobytes(), 
                frame_rate=full_sr,
                sample_width=2, 
                channels=1
            )
            
            final_audio += segment
            if i < len(paragraphs) - 1:
                final_audio += silence

    except Exception as e:
        print(f"❌ Error during generation: {e}")
        # Try to restore CWD even if crash
        os.chdir(original_cwd)
        sys.exit(1)
        
    # Restore CWD
    os.chdir(original_cwd)

    # --- Post-Processing (BGM) ---
    bgm_info_str = "None"
    if args.bgm:
        print(f"🎵 Mixing Background Music (Vol={args.bgm_volume}dB)...")
        final_audio = audio_mixer.mix_bgm(
            final_audio,
            specific_filename=args.bgm_track,
            volume_db=args.bgm_volume,
            intro_delay_ms=args.bgm_intro
        )
        bgm_info_str = os.path.basename(args.bgm_track)

    # --- Export ---
    PRODUCER = "VI AI Foundation"
    ALBUM = "SOH Prayer (GPT-SoVITS)"
    COMMENTS = f"Ref: {os.path.basename(args.ref_audio)}; BGM: {bgm_info_str}"

    print(f"💾 Exporting to {output_path_abs}...")
    final_audio.export(output_path_abs, format="mp3", tags={
        'title': first_line[:50],
        'artist': PRODUCER,
        'album': ALBUM,
        'comments': COMMENTS
    })
    print("✅ Done!")

if __name__ == "__main__":
    main()
