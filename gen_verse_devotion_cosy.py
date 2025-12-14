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

# -----------------------------------------------------------------------------
# Runtime Patch: Enable MPS (Metal) Support for macOS
# -----------------------------------------------------------------------------
try:
    from cosyvoice.cli.model import CosyVoiceModel
    original_init = CosyVoiceModel.__init__

    def patched_init(self, llm, flow, hift, fp16=False):
        # Call original init (sets gpu or cpu)
        original_init(self, llm, flow, hift, fp16)
        # Check for MPS and override if available
        if torch.backends.mps.is_available():
            print("🚀 MPS (Metal Performance Shaders) detected! Enabling Mac GPU acceleration...")
            self.device = torch.device('mps')
            # Move submodules to MPS
            self.llm = self.llm.to(self.device)
            self.flow = self.flow.to(self.device)
            self.hift = self.hift.to(self.device)
    
    # Apply patch
    CosyVoiceModel.__init__ = patched_init
except ImportError:
    pass # CosyVoice not found or structure changed

from bible_parser import convert_bible_reference
from date_parser import convert_dates_in_text
from text_cleaner import remove_space_before_god
import filename_parser

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

TEXT = """
忍耐生甘甜 (雅各书 5:8) 12/14/2025

　神说：“要有光”，就有了光。
(创世记 1:3 )
大山可以挪开，
小山可以迁移；
但我的慈爱必不离开你；
我平安的约也不迁移。
这是怜恤你的耶和华说的。
(以赛亚书 54:10)
主为我们舍命，我们从此就知道何为爱；我们也当为弟兄舍命。
(约翰一书 3:16)
“　神爱世人，甚至将他的独生子赐给他们，叫一切信他的，不至灭亡，反得永生。
(约翰福音 3:16)

弟兄们哪，你们要忍耐，直到主来。看哪，农夫忍耐等候地里宝贵的出产，直到得了秋雨春雨。你们也当忍耐，坚固你们的心，因为主来的日子近了。
(雅各书 5:7-8 和合本)
你们也应当忍耐，坚定自己的心；因为主再来的日子近了。
(雅各书 5:8 新译本)

忍耐生甘甜

你曾在水果未熟时就把它采摘下来吃吗？

也许你被它鲜艳的色彩和空气中弥漫的甜美气味所吸引。可惜你一口咬下去，却发现它没有你预期的熟度。这个水果表面看来可以吃了，然而还缺乏一个因素……

时间。

即使是一个摘果子的简单动作，也能教会我们时间和忍耐的重要性：

“弟兄们哪，你们要忍耐，直到主来。看哪，农夫忍耐等候地里宝贵的出产，直到得了秋雨春雨。你们也当忍耐，坚固你们的心，因为主来的日子近了。 ”（雅各书 5:7-8）

作者雅各在圣灵的默示下，给一群新归信基督且分散在各个地区的犹太人写了这一番话。这些早期的基督徒因他们的初生信仰而面临许多试炼，包括迫害和反对。雅各对他们要耐心等候和坚忍的呼吁，不仅仅是纸上的文字，更是逆境中的一线生机，为他们带来盼望和鼓励。

正如那些早期信徒面临试炼一样，我们在基督信仰的旅途中也会遇到挑战和苦难。因此，你可以效法那些早期的信徒一样选择忍耐；无论你正处于什么人生境况，让圣灵的果子在你里面成熟。当你这样做时，你的品格就会老练、你的信心就会加深、你与神的关系就会变得比你想象的更加甘甜。忍耐总会结出毅力和力量的果子。今天就开始来操练吧！

祷告—
神啊，你是忍耐与恩慈的完美典范。感谢你一直对我的忍耐！请你显明我生活中需要培养忍耐的层面。求你用盼望和智慧来充满我，以帮助我信靠你，尤其是在我遇上艰难挑战的时候。
奉耶稣的名，
阿们。
"""

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

# 2. Extract Verse (First parenthesis content)
verse_match = re.search(r"\((.*?)\)", TEXT)
verse_ref = verse_match.group(1).strip() if verse_match else "Unknown-Verse"

filename = filename_parser.generate_filename(verse_ref, date_str).replace(".mp3", "_cosy.mp3")
OUTPUT_DIR = os.getcwd()
OUTPUT_PATH = os.path.join(OUTPUT_DIR, filename)
print(f"Target Output: {OUTPUT_PATH}")

TEXT = convert_bible_reference(TEXT)
TEXT = convert_dates_in_text(TEXT)
TEXT = remove_space_before_god(TEXT)

paragraphs = [p.strip() for p in TEXT.strip().split("\n\n") if p.strip()]

# Built-in CosyVoice voices
# NOTE: CosyVoice SFT inference uses specific speaker names.
# Common ones: "中文女", "中文男", "日语男", "粤语女", "英文女", "英文男", "韩语女"
voices = ["中文女", "中文男", "英文女", "中文女", "中文男"]

def speak(text: str, voice: str) -> AudioSegment:
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
final.export(OUTPUT_PATH, format="mp3", bitrate="192k")
print(f"Success! Saved → {OUTPUT_PATH}")
