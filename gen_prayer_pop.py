# gen_prayer_pop.py
# Local offline CosyVoice-300M for Prayer (Paragraph Rotation)
import torch
import numpy as np
import re
import sys
import os
import warnings
from datetime import datetime
from pydub import AudioSegment

# Silence noisy libraries
warnings.filterwarnings("ignore", category=FutureWarning, module="diffusers")
warnings.filterwarnings("ignore", category=UserWarning, module="lightning")

# Setup path to find CosyVoice (sibling directory)
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
    from cosyvoice.cli.cosyvoice import CosyVoice
except ImportError as e:
    print(f"❌ Failed to import CosyVoice: {e}")
    sys.exit(1)

from bible_parser import convert_bible_reference
from date_parser import convert_dates_in_text
from text_cleaner import clean_text
import filename_parser
import audio_mixer

import argparse

# CLI Args
if "-?" in sys.argv:
    print(f"Usage: python {sys.argv[0]} [--prefix PREFIX] [--help]")
    print("Options:")
    print("  --prefix PREFIX      Filename prefix (overrides 'FilenamePrefix' in text)")
    print("  --help, -h           Show this help")
    sys.exit(0)

parser = argparse.ArgumentParser()
parser.add_argument("--prefix", type=str, default=None, help="Filename prefix")
args, unknown = parser.parse_known_args()
CLI_PREFIX = args.prefix

ENABLE_BGM = False
BGM_FILE = "AmazingGrace.MP3"

TEXT = """
亲爱的天父：
我们感谢你，因你的恩典每一天都是新的！
在这个安静的时刻，我们将心全然向你敞开。求你保守我们的心思意念，让我们在忙碌的生活中，依然能听见你微小的声音。
主啊，求你赐给我们属天的智慧，让我们在面对挑战时，不依靠自己的聪明，而是单单仰望你。
愿你的平安充满我们的家庭，愿你的爱流淌在我们彼此之间。
也求你记念那些在病痛和软弱中的肢体，愿你的医治临到他们，使他们重新得力。
感谢赞美主，听我们不配的祷告，奉主耶稣基督得胜的名求！阿门！
(腓立比书 4:6-7) 12/14/2025
"""


print("Loading CosyVoice-300M-Instruct (local offline)...")
try:
    use_fp16 = torch.cuda.is_available()
    print(f"Loading CosyVoice-300M-Instruct... [CUDA={use_fp16}, FP16={use_fp16}]")
    cosyvoice = CosyVoice('iic/CosyVoice-300M-Instruct', fp16=use_fp16)
except Exception as e:
    print(f"❌ Error loading model: {e}")
    sys.exit(1)



# Generate filename dynamically
TEXT = clean_text(TEXT)
first_line = TEXT.strip().split('\n')[0]
date_match = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", TEXT)
if date_match:
    m, d, y = date_match.groups()
    date_str = f"{y}-{int(m):02d}-{int(d):02d}"
else:
    date_match = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", TEXT)
    if date_match:
        y, m, d = date_match.groups()
        date_str = f"{y}-{int(m):02d}-{int(d):02d}"
    else:
        date_str = datetime.today().strftime("%Y-%m-%d")

# 2. Extract Verse
verse_ref = filename_parser.extract_verse_from_text(TEXT)

if verse_ref:
    extracted_prefix = CLI_PREFIX if CLI_PREFIX else filename_parser.extract_filename_prefix(TEXT)
    filename = filename_parser.generate_filename(verse_ref, date_str, extracted_prefix, base_name="Prayer").replace(".mp3", "_pop.mp3")
else:
    filename = f"SOH_Sound_of_Home_Prayer_{date_str}_pop.mp3"

OUTPUT_DIR = os.path.join(os.getcwd(), "output")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
OUTPUT_PATH = os.path.join(OUTPUT_DIR, filename)
print(f"Target Output: {OUTPUT_PATH}")

TEXT = convert_bible_reference(TEXT)
TEXT = convert_dates_in_text(TEXT)
TEXT = clean_text(TEXT)

paragraphs = [p.strip() for p in re.split(r'\n{2,}', TEXT.strip()) if p.strip()]

# Voice Rotation
voices = ["中文女", "英文男", "中文男", "日语男", "粤语女"]

def speak(text: str, voice: str) -> AudioSegment:
    print(f"DEBUG: Text to read: {text[:100]}...")
    print(f"   Synthesizing ({len(text)} chars) with {voice}...")
    output_gen = cosyvoice.inference_sft(text, voice)
    
    final_audio = AudioSegment.empty()
    for item in output_gen:
        if 'tts_speech' in item:
            audio_np = item['tts_speech'].numpy()
            audio_int16 = (audio_np * 32767).astype(np.int16)
            segment = AudioSegment(
                audio_int16.tobytes(),
                frame_rate=22050, 
                sample_width=2,
                channels=1
            )
            final_audio += segment
    return final_audio

final_mix = AudioSegment.empty()
silence = AudioSegment.silent(duration=800, frame_rate=22050)

print(f"Processing {len(paragraphs)} paragraphs with voice rotation...")

for i, para in enumerate(paragraphs):
    voice = voices[i % len(voices)]
    print(f"  > Para {i+1} - {voice}")
    
    try:
        segment = speak(para, voice)
        final_mix += segment
        if i < len(paragraphs) - 1:
            final_mix += silence
    except Exception as e:
        print("\nOptions:")
        print("  (Note: You can add 'FilenamePrefix: <Prefix>' in the input TEXT to customize output filename)")
        print(f"❌ Error generating para {i}: {e}")

final_mix = final_mix.set_frame_rate(24000)

# Add Background Music (Optional)
if ENABLE_BGM:
    print("🎵 Mixing Background Music...")
    final_mix = audio_mixer.mix_bgm(final_mix, specific_filename=BGM_FILE)
else:
    print("🎵 Background Music: Disabled (ENABLE_BGM=False)")

# Metadata extraction
PRODUCER = "VI AI Foundation"
TITLE = TEXT.strip().split('\n')[0]

final_mix.export(OUTPUT_PATH, format="mp3", bitrate="192k", tags={'title': TITLE, 'artist': PRODUCER})
print(f"✅ Saved: {OUTPUT_PATH}")
