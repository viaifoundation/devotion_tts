# gen_verse_devotion_vibe.py
# VibeVoice Workflow (Microsoft/OpenSource)

import torch
import numpy as np
import re
import sys
import os
import warnings
from datetime import datetime
from pydub import AudioSegment
import logging

# Silence noisy libraries
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# Setup path to find VibeVoice (sibling directory)
VIBEVOICE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../VibeVoice"))

if os.path.exists(VIBEVOICE_PATH):
    sys.path.append(VIBEVOICE_PATH)
else:
    print(f"⚠️ Warning: VibeVoice path not found at {VIBEVOICE_PATH}")
    print("Please clone it: git clone https://github.com/microsoft/VibeVoice ../VibeVoice")
    sys.exit(1)

try:
    from vibevoice.modular.modeling_vibevoice_streaming_inference import VibeVoiceStreamingForConditionalGenerationInference
    from vibevoice.processor.vibevoice_streaming_processor import VibeVoiceStreamingProcessor
except ImportError as e:
    print(f"❌ Failed to import VibeVoice: {e}")
    sys.exit(1)

from bible_parser import convert_bible_reference
from date_parser import convert_dates_in_text
from text_cleaner import clean_text
import filename_parser
import argparse

# CLI Args
if "-?" in sys.argv or "-h" in sys.argv or "--help" in sys.argv:
    print(f"Usage: python {sys.argv[0]} [--input FILE] [--prefix PREFIX] [--help] [--speed SPEED]")
    print ("\nOptions:")
    print("  --input FILE, -i     Input text file")
    print("  --prefix PREFIX      Filename prefix")
    print("  --speed SPEED        Speed factor (Not supported yet)")
    print("  --help, -h           Show this help")
    sys.exit(0)

parser = argparse.ArgumentParser()
parser.add_argument("--input", "-i", type=str, help="Input text file")
parser.add_argument("--prefix", type=str, default=None, help="Filename prefix")
parser.add_argument("--speed", type=str, default="1.0", help="Speed factor (Not supported yet)")

args, unknown = parser.parse_known_args()
CLI_PREFIX = args.prefix

if args.speed and args.speed != "1.0":
    print("⚠️  Warning: --speed is not currently supported for VibeVoice. Ignoring.")

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

# Configuration

MODEL_PATH = "microsoft/VibeVoice-Realtime-0.5B"  # HuggingFace model hub path
VOICES_DIR = os.path.join(VIBEVOICE_PATH, "demo", "voices", "streaming_model")

# Helper Class for Voice Mapping (Adapted from demo)
class VoiceMapper:
    def __init__(self, voices_dir):
        self.voices_dir = voices_dir
        self.voice_presets = {}
        self.setup_voice_presets()

    def setup_voice_presets(self):
        if not os.path.exists(self.voices_dir):
            print(f"⚠️ Warning: Voices directory not found at {self.voices_dir}")
            return
        
        # Scan for .pt files (voice embeddings)
        for root, _, files in os.walk(self.voices_dir):
            for file in files:
                if file.endswith(".pt"):
                    name = os.path.splitext(file)[0]
                    path = os.path.join(root, file)
                    self.voice_presets[name] = path
                    
                    # Also map simplified names
                    # e.g. en-Mike_man -> en-Mike
                    if '_' in name:
                        name = name.split('_')[0]
                        self.voice_presets[name] = path
                    
                    # e.g. en-Mike -> Mike
                    if '-' in name:
                        short_name = name.split('-')[-1]
                        self.voice_presets[short_name] = path

    def get_voice_path(self, name):
        return self.voice_presets.get(name) or self.voice_presets.get("Mike") # Default to Mike

# Load Model
print(f"Loading VibeVoice model: {MODEL_PATH}...")
try:
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"Using device: {device}")

    # DataType and Attn Config
    if device == "cuda":
        torch_dtype = torch.bfloat16
        attn_impl = "flash_attention_2"
    elif device == "mps":
        torch_dtype = torch.float32
        attn_impl = "sdpa"
    else:
        torch_dtype = torch.float32
        attn_impl = "sdpa"

    processor = VibeVoiceStreamingProcessor.from_pretrained(MODEL_PATH)
    
    # Load model with fallback logic for attention
    try:
        model = VibeVoiceStreamingForConditionalGenerationInference.from_pretrained(
            MODEL_PATH,
            torch_dtype=torch_dtype,
            attn_implementation=attn_impl,
            device_map=device if device != "mps" else None
        )
        if device == "mps":
            model.to("mps")
    except Exception as e:
        print(f"⚠️  Falling back to SDPA attention due to error: {e}")
        model = VibeVoiceStreamingForConditionalGenerationInference.from_pretrained(
            MODEL_PATH,
            torch_dtype=torch_dtype,
            attn_implementation="sdpa",
            device_map=device if device != "mps" else None
        )
        if device == "mps":
            model.to("mps")
            
    model.eval()
    model.set_ddpm_inference_steps(num_steps=5) # Default from demo

    voice_mapper = VoiceMapper(VOICES_DIR)

except Exception as e:
    print(f"❌ Error loading VibeVoice model: {e}")
    sys.exit(1)



# 1. Date Extraction
TEXT = clean_text(TEXT)
first_line = TEXT.strip().split('\n')[0]
date_match = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", first_line)
if date_match:
    m, d, y = date_match.groups()
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
).replace(".mp3", "_vibe.mp3")

OUTPUT_DIR = os.path.join(os.getcwd(), "output")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
OUTPUT_PATH = os.path.join(OUTPUT_DIR, filename)
print(f"Target Output: {OUTPUT_PATH}")

TEXT = convert_bible_reference(TEXT)
TEXT = convert_dates_in_text(TEXT)
TEXT = clean_text(TEXT)

paragraphs = [p.strip() for p in re.split(r'\n{2,}', TEXT.strip()) if p.strip()]

# VibeVoice Synthesis Function
def speak(text: str, voice_name: str) -> AudioSegment:
    print(f"DEBUG: Text to read: {text[:100]}...")
    print(f"   Synthesizing ({len(text)} chars) with {voice_name}...")
    
    voice_path = voice_mapper.get_voice_path(voice_name)
    if not voice_path:
        print(f"   ❌ Voice '{voice_name}' not found, falling back to default.")
        voice_path = voice_mapper.get_voice_path("Mike") # Fallback

    # Load voice prompt
    all_prefilled = torch.load(voice_path, map_location=device, weights_only=False)

    # Process Inputs
    inputs = processor.process_input_with_cached_prompt(
        text=text,
        cached_prompt=all_prefilled,
        padding=True,
        return_tensors="pt",
        return_attention_mask=True,
    )
    
    # Move to device
    for k, v in inputs.items():
        if torch.is_tensor(v):
            inputs[k] = v.to(device)
            
    # Generate
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=None,
            cfg_scale=1.5,
            tokenizer=processor.tokenizer,
            generation_config={'do_sample': False},
            verbose=False,
            all_prefilled_outputs=all_prefilled # copy not needed if read-only
        )
        
    if outputs.speech_outputs and outputs.speech_outputs[0] is not None:
        audio_np = outputs.speech_outputs[0].cpu().numpy()
        # VibeVoice output is float -1..1, usually 24kHz (check demo, said 24000)
        audio_int16 = (audio_np * 32767).astype(np.int16)
        
        return AudioSegment(
            audio_int16.tobytes(),
            frame_rate=24000,
            sample_width=2,
            channels=1
        )
    else:
        print("   ❌ No audio generated.")
        return AudioSegment.silent(duration=500)

final_mix = AudioSegment.empty()
silence = AudioSegment.silent(duration=800, frame_rate=24000)

# "Wayne" is the default male English voice in VibeVoice demo
# "Xiaoxiao"? "Yunxi"? Need to check Chinese available voices.
# For now, default to "Wayne" (English) or whatever is in the demo instructions.
# The user wants Chinese. The demo video showed Chinese.
# I will check `demo/voices` later to see available Chinese names.
# Voice Rotation (Using English voices for cross-lingual synthesis)
voices = ["Mike", "Emma", "Frank", "Grace", "Carter"]
print(f"Available Voices being used: {voices}")

for i, para in enumerate(paragraphs):
    current_voice = voices[i % len(voices)]
    print(f"  > Para {i+1} - {current_voice}")
    segment = speak(para, current_voice)
    final_mix += segment
    if i < len(paragraphs) - 1:
        final_mix += silence

# Metadata extraction
PRODUCER = "VI AI Foundation"
TITLE = TEXT.strip().split('\n')[0]
ALBUM = "Devotion"
COMMENTS = f"Verse: {verse_ref}"

final_mix.export(OUTPUT_PATH, format="mp3", bitrate="192k", tags={
    'title': TITLE, 
    'artist': PRODUCER,
    'album': ALBUM,
    'comments': COMMENTS
})
print(f"✅ Saved: {OUTPUT_PATH}")
