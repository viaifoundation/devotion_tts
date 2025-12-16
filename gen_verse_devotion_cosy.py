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
神知道你的一切，你并不孤单 (约翰福音 1:12) 2025-12-16

在伯利恒之野地里有牧羊的人，夜间按着更次看守羊群。有主的使者站在他们旁边，主的荣光四面照着他们；牧羊的人就甚惧怕。
(路加福音 2:8-9)
那天使对他们说：“不要惧怕！我报给你们大喜的信息，是关乎万民的；因今天在大卫的城里，为你们生了救主，就是主基督。
(路加福音 2:10-11)
牧羊的人回去了，因所听见所看见的一切事，正如天使向他们所说的，就归荣耀与　神，赞美他。
(路加福音 2:20)

凡接待他的，就是信他名的人，他就赐他们权柄作　神的儿女。
(约翰福音 1:12 和合本)
凡接受他的，就是信他名的人，他就赐给他们权利，成为　神的儿女。
(约翰福音 1:12 新译本)
但所有接受祂的，就是那些信祂的人，祂就赐给他们权利成为上帝的儿女。
(约翰福音 1:12 当代译本)

神知道你的一切，你并不孤单

从决心跟随耶稣开始，我们在基督里就是新造的人，那这究竟是什么意思呢？

耶稣为了世上的每一个人——就是我们——降生和受死。当我们把生命交托给他并决心跟随他时，我们就因他而获得新生。同时，我们也被收养进入神永恒的家中，享有神儿女应有的一切权利。 

接受耶稣，就是说我们选择相信关于他的全部真理：我们赞同他有完美的一生、为我们而死，并从死里复活。相信这些，我们就进入神的国，被称为神的儿女。

作为神的儿女，则意味着我们能毫无拘束、时时刻刻地拥有神的同在、爱和权柄。大好消息是：没有人能使我们与神隔绝。

神儿女的身份不是从我们的生身父母，或靠我们行善得来的——是神白白赐给我们的。唯有神才有这个权柄，领我们进到永恒的神家中，还应许永远不撇下我们或丢弃我们。（参考申命记31:6)

成为神儿女的那一刻，旧我的身份就不再重要了。之前我们被冠以的一切不好绰号、每一个过犯、每一个所经历（或造成）的伤害——全部都被涂抹了。 我们的身份、安全感和未来，现在都植根在那位爱我们，并为我们舍命的神里面。

现在花点时间思考这个真理。如果你是属耶稣的，你就不孤独。你被那位宇宙的创造者所知，他称你为孩子、知道你的名字，并无条件地爱着你！

祷告：
神啊，感谢你如此爱我。你知道我的真面目，但你仍接纳我！今天，我把所有不实的标签和名称都交给你，你知道人们是怎样评价我的，也知道我怎样看待我自己。请用你的真理来取代任何谎言——我是你深爱的儿女。
奉耶稣的名祈求，
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
final.export(OUTPUT_PATH, format="mp3", bitrate="192k")
print(f"Success! Saved → {OUTPUT_PATH}")
