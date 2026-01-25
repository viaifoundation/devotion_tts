# gen_verse_devotion_qwentts.py
# Qwen-TTS Local Inference on DGX Spark
# Supports multiple voices with rotation similar to Edge TTS

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

# Qwen3-TTS Voice Presets (from official documentation)
# Male voices (Chinese/English native)
VOICE_MALE_1 = "Dylan"      # Youthful Beijing male, clear natural timbre (Chinese)
VOICE_MALE_2 = "Aiden"      # Sunny American male, clear midrange (English)
VOICE_MALE_3 = "Ryan"       # Dynamic male with strong rhythmic drive (English)

# Female voices (Chinese native)
VOICE_FEMALE_1 = "Serena"   # Warm, gentle young female (Chinese)
VOICE_FEMALE_2 = "Vivian"   # Bright, slightly edgy young female (Chinese)
VOICE_FEMALE_3 = "Chelsie"  # Lively female voice (English)

# CLI Args
if "-?" in sys.argv or "-h" in sys.argv or "--help" in sys.argv:
    print(f"Usage: python {sys.argv[0]} [OPTIONS]")
    print("\nOptions:")
    print("  --input FILE, -i     Text file to read input from")
    print("  --prefix PREFIX      Filename prefix (e.g. MyPrefix)")
    print("  --voice MODE         Voice mode: male, female, two, four, six (Default: six)")
    print("  --voices LIST        Custom voices (comma-separated, overrides --voice)")
    print("  --bgm                Enable background music")
    print("  --bgm-track TRACK    BGM filename (Default: AmazingGrace.MP3)")
    print("  --bgm-volume VOL     BGM volume in dB (Default: -20)")
    print("  --bgm-intro MS       BGM intro delay in ms (Default: 4000)")
    print("  -?, -h, --help       Show this help")
    print("\nVoice Modes:")
    print("  male    - Single male voice (Dylan)")
    print("  female  - Single female voice (Serena)")
    print("  two     - Rotate 2 voices (1M + 1F): Dylan, Serena")
    print("  four    - Rotate 4 voices (2M + 2F): Dylan, Serena, Aiden, Vivian")
    print("  six     - Rotate 6 voices (3M + 3F): Dylan, Serena, Aiden, Vivian, Ryan, Chelsie")
    print("\nExamples:")
    print(f"  python {sys.argv[0]} -i input.txt --voice male")
    print(f"  python {sys.argv[0]} -i input.txt --voice two --bgm")
    print(f"  python {sys.argv[0]} -i input.txt --voice six")
    sys.exit(0)

# CLI Args
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("--input", "-i", type=str, help="Input text file")
parser.add_argument("--prefix", type=str, default=None, help="Filename prefix (e.g. MyPrefix)")
parser.add_argument("--voice", type=str, default="six", choices=["male", "female", "two", "four", "six"],
                    help="Voice mode: male, female, two, four, six (Default: six)")
parser.add_argument("--voices", type=str, default=None,
                    help="Custom voices (comma-separated, overrides --voice)")
# Cloning Args
parser.add_argument("--ref-audio", type=str, default=None, help="Reference audio path(s) for cloning (Triggers Cloned Mode). Sep with ',' for rotation.")
parser.add_argument("--ref-text", type=str, default="然而，靠着爱我们的主，在这一切的事上已经得胜有余了。", help="Reference audio transcript (Use '|' to separate multiple transcripts)")

parser.add_argument("--bgm", action="store_true", help="Enable background music (Default: False)")
parser.add_argument("--bgm-track", type=str, default="AmazingGrace.MP3", help="BGM filename")
parser.add_argument("--bgm-volume", type=int, default=-20, help="BGM volume adjustment in dB")
parser.add_argument("--bgm-intro", type=int, default=4000, help="BGM intro delay in ms")
args, unknown = parser.parse_known_args()

# Voice mode configuration
# --voices overrides --voice if provided
if args.voices:
    VOICES = [v.strip() for v in args.voices.split(",") if v.strip()]
    print(f"🎤 Custom voices: {', '.join(VOICES)}")
elif args.voice == "male":
    VOICES = [VOICE_MALE_1]
    print(f"🎤 Voice mode: male ({VOICE_MALE_1})")
elif args.voice == "female":
    VOICES = [VOICE_FEMALE_1]
    print(f"🎤 Voice mode: female ({VOICE_FEMALE_1})")
elif args.voice == "two":
    VOICES = [VOICE_MALE_1, VOICE_FEMALE_1]
    print(f"🎤 Voice mode: two (Dylan, Serena)")
elif args.voice == "four":
    VOICES = [VOICE_MALE_1, VOICE_FEMALE_1, VOICE_MALE_2, VOICE_FEMALE_2]
    print(f"🎤 Voice mode: four (Dylan, Serena, Aiden, Vivian)")
else:  # six
    VOICES = [VOICE_MALE_1, VOICE_FEMALE_1, VOICE_MALE_2, VOICE_FEMALE_2, VOICE_MALE_3, VOICE_FEMALE_3]
    print(f"🎤 Voice mode: six (Dylan, Serena, Aiden, Vivian, Ryan, Chelsie)")

class QwenTTSLocalEngine:
    def __init__(self, mode="custom", device="cuda"):
        # Select model based on mode
        if mode == "clone":
            self.model_name = "Qwen/Qwen3-TTS-12Hz-1.7B-Base"
            print(f"🔬 Loading Qwen-TTS CLONING Model: {self.model_name}...")
        else:
            self.model_name = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
            print(f"🗣️ Loading Qwen-TTS PRESET Model: {self.model_name}...")
            
        self.device = device
        self.mode = mode
        
        try:
            # Placeholder for actual Qwen3-TTS loading logic.
            # Assuming usage of Qwen3TTSModel from qwen_tts package as per docs
            try:
                from qwen_tts import Qwen3TTSModel
                self.model = Qwen3TTSModel.from_pretrained(
                    self.model_name, 
                    device_map=device, 
                    torch_dtype=torch.float16,
                    attn_implementation="flash_attention_2"
                )
            except ImportError:
                 print("⚠️ 'qwen_tts' package not found. Trying transformers fallback...")
                 self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name, 
                    device_map=device, 
                    trust_remote_code=True, 
                    torch_dtype=torch.float16
                )
            # self.model.eval() # Qwen3TTSModel might not need explicit eval, but safe to keep
            print("✅ Model loaded successfully.")
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            print("⚠️ Running in MOCK mode for structure verification.")
            self.model = None

    def synthesize(self, text, speaker_or_ref, ref_text=None, lang="auto"):
        """
        Synthesize audio.
        If mode='custom', speaker_or_ref is the speaker name (str).
        If mode='clone', speaker_or_ref is the ref_audio path (str) and ref_text must be provided.
        """
        if not self.model:
            # Mock return
            id_str = speaker_or_ref if isinstance(speaker_or_ref, str) else "REF_AUDIO"
            print(f"MOCK SYNTHESIS ({self.mode}): '{id_str}' - {text[:30]}...")
            sr = 24000
            audio_data = torch.zeros(int(sr * 1.5)).numpy()
            return audio_data, sr

        if self.mode == "clone":
            # Voice Cloning (Base Model)
            ref_audio = speaker_or_ref
            print(f"🧬 Cloning from {os.path.basename(ref_audio)}: {text[:40]}...")
            
            # Real Qwen3-TTS Clone call
            # wavs, sr = model.generate_voice_clone(text=..., ref_audio=..., ref_text=...)
            try:
                wavs, sr = self.model.generate_voice_clone(
                    text=text,
                    language="auto", # or explicitly "Chinese"
                    ref_audio=ref_audio,
                    ref_text=ref_text
                )
                return wavs[0], sr
            except AttributeError:
                 # Fallback if using generic transformer model wrapper
                 print("⚠️ generate_voice_clone not found on model object.")
                 return self._mock_gen()
                 
        else:
            # Preset Voice (CustomVoice Model)
            speaker = speaker_or_ref
            print(f"🗣️ Speaking ({speaker}): {text[:40]}...")
            
            # Real Qwen3-TTS CustomVoice call
            # wavs, sr = model.generate_custom_voice(text=..., speaker=...)
            try:
                wavs, sr = self.model.generate_custom_voice(
                    text=text,
                    speaker=speaker,
                    language="auto"
                )
                return wavs[0], sr
            except AttributeError:
                 # Fallback
                 print("⚠️ generate_custom_voice not found on model object.")
                 return self._mock_gen()

    def _mock_gen(self):
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

# 3. Filename
# Extract Date
first_line = TEXT.strip().split('\n')[0]
date_match = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", first_line)
if date_match:
    m, d, y = date_match.groups()
    date_str = f"{y}-{int(m):02d}-{int(d):02d}"
else:
    # Try YYYY-MM-DD
    date_match = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", first_line)
    if date_match:
        y, m, d = date_match.groups()
        date_str = f"{y}-{int(m):02d}-{int(d):02d}"
    else:
        date_str = datetime.today().strftime("%Y-%m-%d")

# Extract Verse Reference (for metadata)
verse_ref = filename_parser.extract_verse_from_text(TEXT)

extracted_prefix = args.prefix if args.prefix else filename_parser.extract_filename_prefix(TEXT)
filename = filename_parser.generate_filename_v2(
    title=first_line, 
    date=date_str, 
    prefix=extracted_prefix,
    ext=".mp3"
).replace(".mp3", "_qwentts.mp3")

if args.bgm:
    filename = filename.replace(".mp3", "_bgm.mp3")

OUTPUT_PATH = os.path.join("output", filename)

# 4. Final Text Processing for TTS
TEXT = convert_bible_reference(TEXT)
TEXT = convert_dates_in_text(TEXT)
TEXT = clean_text(TEXT) # Final cleanup

if not os.path.exists("output"):
    os.makedirs("output")

# 4. Synthesize
# Detect Mode
if args.ref_audio:
    MODE = "clone"
    print(f"🚀 Starting Qwen-TTS in CLONING mode using: {args.ref_audio}")
else:
    MODE = "custom"
    print(f"🚀 Starting Qwen-TTS in PRESET mode (Voices: {len(VOICES)})")

engine = QwenTTSLocalEngine(mode=MODE) 

# Split text into chunks (Qwen context limit)
paragraphs = [p for p in TEXT.split('\n') if p.strip()]
final_audio = AudioSegment.empty()
silence = AudioSegment.silent(duration=500)


for i, para in enumerate(paragraphs):
    if not para.strip(): continue
    
    # Audio is numpy array, need to convert to AudioSegment
    if MODE == "clone":
        # Cloning Mode: Rotate through reference audios
        ref_audios = [x.strip() for x in args.ref_audio.split(',')]
        ref_texts = [x.strip() for x in args.ref_text.split('|')]
        
        current_ref_audio = ref_audios[i % len(ref_audios)]
        current_ref_text = ref_texts[i % len(ref_texts)] # Cycle if fewer texts
        
        print(f"  > Para {i+1} [Clone] - Ref: {os.path.basename(current_ref_audio)}")
        wav_data, sr = engine.synthesize(para, current_ref_audio, ref_text=current_ref_text)
    else:
        # Preset Mode: Rotate voices
        voice = VOICES[i % len(VOICES)]
        print(f"  > Para {i+1} - {voice} ({len(para)} chars)")
        wav_data, sr = engine.synthesize(para, voice)
    
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
