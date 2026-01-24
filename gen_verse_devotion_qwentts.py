# gen_verse_devotion_qwentts.py
# Qwen-TTS Local Inference on DGX Spark

import os
import sys
import argparse
import torch
import io
import soundfile as sf
from datetime import datetime
import re

# Repo modules
from bible_parser import convert_bible_reference
from date_parser import convert_dates_in_text
from text_cleaner import clean_text
import filename_parser
import audio_mixer
from pydub import AudioSegment

# HuggingFace / Transformers
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers.generation import GenerationConfig

# CLI Args
parser = argparse.ArgumentParser()
parser.add_argument("--input", "-i", type=str, help="Input text file")
parser.add_argument("--prefix", type=str, default=None, help="Filename prefix (e.g. MyPrefix)")
parser.add_argument("--voice-prompt", type=str, default="A clear, soothing male voice reading scripture.", help="Natural language voice prompt")
parser.add_argument("--bgm", action="store_true", help="Enable background music (Default: False)")
parser.add_argument("--bgm-track", type=str, default="AmazingGrace.MP3", help="BGM filename")
parser.add_argument("--bgm-volume", type=int, default=-20, help="BGM volume adjustment in dB")
parser.add_argument("--bgm-intro", type=int, default=4000, help="BGM intro delay in ms")
args, unknown = parser.parse_known_args()

class QwenTTSLocalEngine:
    def __init__(self, model_name="Qwen/Qwen2.5-TTS", device="cuda"):
        print(f"Loading Qwen-TTS Model: {model_name}...")
        self.device = device
        try:
            # Placeholder for actual Qwen3-TTS loading logic.
            # Assuming Qwen2-Audio/TTS structure or generic CausalLM with audio head
            # For 1.7B, we might use AutoModelForCausalLM or a specific pipeline
            self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name, 
                device_map=device, 
                trust_remote_code=True, 
                torch_dtype=torch.float16
            )
            self.model.eval()
            print("Model loaded successfully.")
        except Exception as e:
            print(f"Error loading model: {e}")
            print("Running in MOCK mode for structure verification.")
            self.model = None

    def synthesize(self, text, voice_prompt, lang="auto"):
        if not self.model:
            # Mock return for testing script logic without 10GB download
            print(f"MOCK SYNTHESIS: {text[:50]}...")
            sr = 24000
            # Generate 1 sec of silence as mock
            audio_data = torch.zeros(int(sr * 1.0)).numpy()
            return audio_data, sr

        # Real inference logic (adapted from Qwen TTS examples)
        # This is speculative as Qwen3-TTS API isn't fully public in standard transformers yet
        # But assuming the prompt-based structure:
        
        # Example: <|audio_start|> prompt <|audio_end|> text
        # logic would go here.
        # For now, we will assume a standard generate call
        
        print(f"Synthesizing: {text[:50]}... with prompt: '{voice_prompt}'")
        # Placeholder for actual generation code
        # audio = self.model.generate_audio(text=text, prompt=voice_prompt) 
        
        # MOCK for now until model ID is confirmed valid
        sr = 24000
        audio_data = torch.zeros(int(sr * 2.0)).numpy()
        return audio_data, sr

# --- Main Logic ---

# 1. Read Input
if args.input:
    with open(args.input, "r", encoding="utf-8") as f:
        TEXT = f.read()
elif not sys.stdin.isatty():
    TEXT = sys.stdin.read()
else:
    TEXT = "神爱世人，甚至将他的独生子赐给他们。"

# 2. Preprocess
TEXT = clean_text(TEXT)
TEXT = convert_bible_reference(TEXT)
TEXT = convert_dates_in_text(TEXT)

# 3. Filename
if args.prefix:
    prefix = args.prefix
else:
    prefix = filename_parser.extract_filename_prefix(TEXT)
    
date_str = datetime.today().strftime("%Y-%m-%d") # Simplified for now
title = TEXT.strip().split('\n')[0][:20]
filename = f"{prefix}_{title}_{date_str}_qwentts.mp3".replace(" ", "_")
OUTPUT_PATH = os.path.join("output", filename)

if not os.path.exists("output"):
    os.makedirs("output")

# 4. Synthesize
engine = QwenTTSLocalEngine() # Uses default Qwen2.5-TTS

# Split text into chunks (Qwen context limit)
paragraphs = [p for p in TEXT.split('\n') if p.strip()]
final_audio = AudioSegment.empty()
silence = AudioSegment.silent(duration=500)

for para in paragraphs:
    if not para.strip(): continue
    
    # Audio is numpy array, need to convert to AudioSegment
    wav_data, sr = engine.synthesize(para, args.voice_prompt)
    
    # Convert numpy to bytes for AudioSegment
    # Assuming float32 [-1, 1], convert to int16
    wav_int16 = (wav_data * 32767).astype('int16')
    byte_io = io.BytesIO()
    sf.write(byte_io, wav_int16, sr, format='WAV')
    byte_io.seek(0)
    
    segment = AudioSegment.from_wav(byte_io)
    final_audio += segment + silence

# 5. BGM Mixing
if args.bgm:
    print(f"Mixing BGM: {args.bgm_track}")
    final_audio = audio_mixer.mix_bgm(
        final_audio,
        specific_filename=args.bgm_track,
        volume_db=args.bgm_volume,
        intro_delay_ms=args.bgm_intro
    )

# 6. Export
final_audio.export(OUTPUT_PATH, format="mp3", bitrate="192k")
print(f"Saved to: {OUTPUT_PATH}")
