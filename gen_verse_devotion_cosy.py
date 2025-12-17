# gen_verse_devotion_cosy.py
# Local offline CosyVoice-300M – 5 voices for verse devotion

import torch
import numpy as np
import re
import sys
import os
import warnings
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
    # Also add Matcha-TTS to path as CosyVoice imports 'matcha' directly
    if os.path.exists(MATCHA_PATH):
        sys.path.append(MATCHA_PATH)
    else:
        print(f"⚠️ Warning: Matcha-TTS not found at {MATCHA_PATH}")
        print("Run: cd ../CosyVoice && git submodule update --init --recursive")
else:
    print(f"⚠️ Warning: CosyVoice path not found at {COSYVOICE_PATH}")
    print("Please clone it: git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git ../CosyVoice")

try:
    from cosyvoice.cli.cosyvoice import CosyVoice
    from cosyvoice.utils.file_utils import load_wav
except ImportError as e:
    print(f"❌ Failed to import CosyVoice: {e}")
    print(f"Ensure you have cloned the repo to {COSYVOICE_PATH} and installed its requirements.")
    sys.exit(1)

from bible_parser import convert_bible_reference
from date_parser import convert_dates_in_text
from text_cleaner import clean_text
import filename_parser

TEXT = """
学习凡事谦虚 (以弗所书 4:2) 12/17/2025

进了房子，看见小孩子和他母亲马利亚，就俯伏拜那小孩子，揭开宝盒，拿黄金、乳香、没药为礼物献给他。博士因为在梦中被主指示不要回去见希律，就从别的路回本地去了。
(马太福音 2:11-12)
他们听见王的话就去了。在东方所看见的那星忽然在他们前头行，直行到小孩子的地方，就在上头停住了。
(马太福音 2:9)

我为主被囚的劝你们：既然蒙召，行事为人就当与蒙召的恩相称。凡事谦虚、温柔、忍耐，用爱心互相宽容，用和平彼此联络，竭力保守圣灵所赐合而为一的心。
(以弗所书 4:1-3 和合本)
凡事谦虚、温柔、忍耐，用爱心彼此宽容；
(以弗所书 4:2 新译本)

学习凡事谦虚

你见过愤怒的基督徒吗？ 

你可能遇到过喜欢发牢骚、埋怨、甚至恶言相向的基督徒。也许你，有时在自己的生活中也是这样的人。

如果不谨慎，我们很容易会因本身的基督信仰而变得自以为义 。毕竟，我们知道其他人所不知道的真理。你可能还会忍不住看不起别人、贬低他们，或认为他们比我们更罪恶。

这种行为就完全错过了耶稣福音的要点。 

福音告诉我们，我们所有人都从同一个起点开始。只有通过恩典，我们才能获得救恩，并了解神对我们的爱的真相。

这并不使我们比其他基督徒更好！事实上，正如保罗在以弗所书 4:2 中所说，我们实际上应该谦虚、温柔地对待别人，而不是严厉和挑剔。他说我们要彼此忍耐，尽我们所能互相帮助，那样我们才能共同成长。

这些想法并非保罗原创。它们实际上来自耶稣的生活方式。作为跟随耶稣的人，我们也应该努力对生活中的每个人表现出温柔、谦虚和忍耐。无论他们的外表或想法是否不同，每个人都应当享有我们的敬重、忍耐和爱。

今天就花时间想一些实际的方法，让你学习对人忍耐、谦虚和有爱心。也许你可以放慢脚步，投入时间以让人们知道你关心他们；或是对某人说一些鼓励的话；或是向某人承认你犯了一个错误。 

今天就做出决定，以谦虚和满有恩慈的态度与他人相处。

禱告
神啊，你的话语激励我要凡事都谦虚、温柔和忍耐。但如果我心里没有你的爱，我根本就做不到。请你教导我，如何出于爱而恩慈对待我身边的人。奉耶稣的名，阿们。
"""


print("Loading CosyVoice-300M-Instruct (local offline)...")
# CosyVoice automatically handles model download via modelscope if not present
try:
    # Auto-enable FP16 if CUDA is available for speed
    use_fp16 = torch.cuda.is_available()
    print(f"Loading CosyVoice-300M-Instruct (local offline)... [CUDA={use_fp16}, FP16={use_fp16}]")
    cosyvoice = CosyVoice('iic/CosyVoice-300M-Instruct', fp16=use_fp16)
except Exception as e:
    print(f"❌ Error loading model: {e}")
    print("Ensure you have 'modelscope' installed and dependencies met.")
    sys.exit(1)



# Generate filename dynamically
# 1. Extract Date
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

# 2. Extract Verse
# Handle both English () and Chinese （） parentheses, and both : and ： colons
verse_ref = filename_parser.extract_verse_from_text(TEXT)

if verse_ref:
    filename = filename_parser.generate_filename(verse_ref, date_str).replace(".mp3", "_cosy.mp3")
else:
    filename = f"{date_str}_cosy.mp3"
OUTPUT_DIR = os.path.join(os.getcwd(), "output")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
OUTPUT_PATH = os.path.join(OUTPUT_DIR, filename)
print(f"Target Output: {OUTPUT_PATH}")

TEXT = convert_bible_reference(TEXT)
TEXT = convert_dates_in_text(TEXT)
TEXT = clean_text(TEXT)

paragraphs = [p.strip() for p in re.split(r'\n{2,}', TEXT.strip()) if p.strip()]

# Built-in CosyVoice voices
# NOTE: CosyVoice SFT inference uses specific speaker names.
# Common ones: "中文女", "中文男", "日语男", "粤语女", "英文女", "英文男", "韩语女"
voices = ["中文女", "中文男", "英文女", "中文女", "中文男"]

def speak(text: str, voice: str) -> AudioSegment:
    print(f"DEBUG: Text to read: {text[:100]}...")
    # inference_sft returns a result iterable usually, or creates a generator
    # output format: {'tts_speech': tensor, 'samplerate': 22050}
    # It might return a generator, so we iterate
    
    print(f"   Synthesizing ({len(text)} chars) with {voice}...")
    output_gen = cosyvoice.inference_sft(text, voice)
    
    final_audio = AudioSegment.empty()
    
    # Iterate through the generator
    for item in output_gen:
        if 'tts_speech' in item:
            audio_np = item['tts_speech'].numpy()
            # Normalize float -1..1 to int16
            audio_int16 = (audio_np * 32767).astype(np.int16)
            segment = AudioSegment(
                audio_int16.tobytes(),
                frame_rate=22050, 
                sample_width=2,
                channels=1
            )
            final_audio += segment
            
    return final_audio

# Group paragraphs into 5 logical sections
if len(paragraphs) < 5:
    logical_sections = [[p] for p in paragraphs]
else:
    logical_sections = [
        [paragraphs[0]],              # Intro
        [paragraphs[1]],              # Scripture 1
        [paragraphs[2]],              # Scripture 2
        paragraphs[3:-1],             # Main Body
        [paragraphs[-1]]              # Prayer
    ]

print(f"Processing {len(logical_sections)} logical sections...")
# Voice mapping (Rotation)
# CosyVoice-300M-Instruct supports: 中文女, 中文男, 日语男, 粤语女, 英文女, 英文男, 韩语女
# We add English Male and Japanese Male because they can speak Chinese too (Cross-lingual)
voices = ["中文女", "英文男", "中文男", "日语男", "中文女"]
section_titles = ["Intro", "Scripture 1", "Scripture 2", "Main Body", "Prayer"]

final_segments = []
global_p_index = 0

for i, section_paras in enumerate(logical_sections):
    title = section_titles[i] if i < len(section_titles) else f"Section {i+1}"
    print(f"--- Section {i+1}: {title} ---")
    
    section_audio = AudioSegment.empty()
    silence_between_paras = AudioSegment.silent(duration=700, frame_rate=22050)

    for j, para in enumerate(section_paras):
        voice = voices[global_p_index % len(voices)]
        print(f"  > Part {i+1}.{j+1} - {voice}")
        global_p_index += 1
        current_segment = speak(para, voice)
        section_audio += current_segment
        
        if j < len(section_paras) - 1:
            section_audio += silence_between_paras
            
    final_segments.append(section_audio)

final = AudioSegment.empty()
silence_between_sections = AudioSegment.silent(duration=1000, frame_rate=22050)

for i, seg in enumerate(final_segments):
    final += seg
    if i < len(final_segments) - 1:
        final += silence_between_sections

# Convert to 24k for consistency with others if desired, or keep 22k
final = final.set_frame_rate(24000)
# Metadata extraction
PRODUCER = "VI AI Foundation"
TITLE = TEXT.strip().split('\n')[0]

final.export(OUTPUT_PATH, format="mp3", bitrate="192k", tags={'title': TITLE, 'artist': PRODUCER})
print(f"Success! Saved → {OUTPUT_PATH}")
