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
from text_cleaner import remove_space_before_god
import filename_parser

print("Loading CosyVoice-300M-Instruct (local offline)...")
# CosyVoice automatically handles model download via modelscope if not present
try:
    cosyvoice = CosyVoice('iic/CosyVoice-300M-Instruct')
except Exception as e:
    print(f"❌ Error loading model: {e}")
    print("Ensure you have 'modelscope' installed and dependencies met.")
    sys.exit(1)

TEXT = """
住在神的爱里面 (约翰一书 4:16) 12/13/2025

及至时候满足，　神就差遣他的儿子，为女子所生，且生在律法以下，要把律法以下的人赎出来，叫我们得着儿子的名分。你们既为儿子，　神就差他儿子的灵进入你们（原文是我们）的心，呼叫：“阿爸！父！”可见，从此以后，你不是奴仆，乃是儿子了；既是儿子，就靠着　神为后嗣。
(加拉太书 4:4-7 和合本)
但到了时机成熟，　神就差遣他的儿子，由女人所生，而且生在律法之下，要把律法之下的人救赎出来，好让我们得着嗣子的名分。
(加拉太书 4:4-5 新译本)
所以，你们要自卑，服在　神大能的手下，到了时候，他必叫你们升高。你们要将一切的忧虑卸给　神，因为他顾念你们。
(彼得前书 5:6-7)


　神爱我们的心，我们也知道也信。
　神就是爱；住在爱里面的，就是住在　神里面，　神也住在他里面。
(约翰一书 4:16 和合本)
　神对我们的爱，我们已经明白了，而且相信了。
　神就是爱；住在爱里面的，就住在　神里面，　神也住在他里面。
(约翰壹书 4:16 新译本)
这样，我们已经认识并相信了神对我们所怀的爱。神就是爱；那住在爱里面的，就住在神里面，神也住在他里面。
(约翰一书 4:16 标准译本)

住在神的爱里面

你曾遇到过特别善良和体贴的人吗？好朋友就是这样——平易近人、热心想知道你过得怎么样、心无旁骛地倾听你。好朋友会使我们记起我们是谁。他们怀着仁慈与爱来倾听你所说的一切，无论是喜还是忧。

神就是这样的朋友。他倾听；他感同身受。他非常关心你，并且仁慈地回应你。事实上，神所做的不仅仅是展示爱——他就是爱。他不可能不爱，因为爱就是他的本质。他的爱是纯洁的；不自私、不脱节、不苦涩、不怨恨，也不消极。我们可以信靠这种爱；我们可以信靠神。

在约翰一书 4:16 中，我们看到了一个美好的提醒，让我们知道与神同在的生活是什么样的：“神爱我们的心，我们也知道也信。神就是爱；住在爱里面的，就是住在神里面，神也住在他里面。”

和好朋友共度时光后，你感觉如何？也许你会觉得心情安逸、步履轻快，或者你发现自己有了勇气继续前行。你甚至可能发现自己因为感受到被爱而更加爱别人。这就是住在神的爱中产生的连锁反应。当你知道并体验到神多么爱你时，你就会情不自禁地爱别人。

这就是我们被邀请去过的生活。一种了解并依赖神对我们的爱，然后因此而爱他人的生活。今天，你将如何找到神对你的爱？在你认识并体验到神对你的爱之后，一切都会改变。

祷告：
神啊，你的爱对我来说太奇妙了。我需要更加理解你的爱。我想感受被爱和被重视；我想经历你对我何等的眷顾。请你今天就帮助我更深入认识你的爱。奉耶稣的名，阿们。
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
OUTPUT_PATH = f"/Users/mhuo/Downloads/{filename}"
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
