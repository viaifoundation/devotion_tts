
# gen_verse_devotion_qwen.py
# Real Qwen3-TTS – 5 voices, works perfectly

import io
import os
import sys
import requests
import dashscope
from dashscope.audio.qwen_tts import SpeechSynthesizer
from pydub import AudioSegment

from bible_parser import convert_bible_reference
from date_parser import convert_dates_in_text
from text_cleaner import clean_text
import filename_parser
import re
from datetime import datetime

import argparse

# CLI Args
if "-?" in sys.argv:
    print(f"Usage: python {sys.argv[0]} [--prefix PREFIX] [--help]")
    print("Options:")
    print("  --prefix PREFIX      Filename prefix (overrides 'FilenamePrefix' in text)")
    print("  --help, -h           Show this help")
    print("\n  (Note: You can also add 'FilenamePrefix: <Prefix>' in the input TEXT)")
    sys.exit(0)

parser = argparse.ArgumentParser()
parser.add_argument("--prefix", type=str, default=None, help="Filename prefix")
args, unknown = parser.parse_known_args()
CLI_PREFIX = args.prefix

TEXT = """
谦卑的开始 (路加福音 1:35) 12/19/2025

现在我们既靠着他的血称义，就更要藉着他免去　神的忿怒。因为我们作仇敌的时候，且藉着　神儿子的死，得与　神和好；既已和好，就更要因他的生得救了。不但如此，我们既藉着我主耶稣基督得与　神和好，也就藉着他以　神为乐。
亚当和基督
(罗马书 5:9-11 和合本)
不但这样，我们现在已经藉着我们的主耶稣基督与　神复和，也藉着他以　神为荣。
(罗马书 5:11 新译本)
到那日，你们什么也就不问我了。我实实在在地告诉你们，你们若向父求什么，他必因我的名赐给你们。向来你们没有奉我的名求什么，如今你们求，就必得着，叫你们的喜乐可以满足。”
(约翰福音 16:23-24 和合本)
到了那天，你们什么也不会问我了。我实实在在告诉你们，你们奉我的名无论向父求什么，他必定赐给你们。你们向来没有奉我的名求什么；现在你们祈求，就必定得着，让你们的喜乐满溢。
(约翰福音 16:23-24 新译本)

天使回答说：“圣灵要临到你身上，至高者的能力要荫庇你，因此所要生的圣者必称为　神的儿子（或译：所要生的，必称为圣，称为　神的儿子）。
(路加福音 1:35 和合本)
天使回答：“圣灵要临到你，至高者的能力要覆庇你，因此那将要出生的圣者，必称为　神的儿子。
(路加福音 1:35 新译本)
天使回答她，说：
“圣灵将要临到你，
至高者的大能要荫庇你，
因此，那要诞生的圣者
将被称为神的儿子。
(路加福音 1:35 标准译本)
天使回答说：“圣灵要临到你身上，至高者的能力要荫庇你，所以你要生的那圣婴必称为上帝的儿子。
(路加福音 1:35 当代译本)

谦卑的开始

“天使回答说：‘圣灵要临到你身上，至高者的能力要荫庇你，因此所要生的圣者必称为神的儿子。’”（路加福音 1:35）

世代以来期盼的弥撒亚。先知已预言，人们也殷切地等候。就在一个纯朴的小镇里，预言实现了。像我们一样从呱呱落地那一刻起展开一生，神的儿子也拥有了人类的脆弱和局限。圣洁与大能同时在人类身上得以体现。对马利亚来说，她的儿子出世了。

在耶稣降临的所有预言之后，你认为有人会想象到，他会以婴儿的形体来开始他在地上的生命吗？他会从婴儿成长为儿童，再成长为青少年，最后成长为成年人，就像亚当和夏娃的后代一样？即使在他传道期间，人们也喜欢将耶稣视为征服者——一个将推翻罗马政权并成为他们的王的强大人物。他们要耶稣通过赋予他们力量来展现他的权能。

然而耶稣却谦卑至极。

他心甘情愿地在世上开始他完全无能为力的人生，由他的母亲马利亚所生，过着简单的生活。

耶稣从与天父合一、强大而至高无上，到心甘情愿地从人类的生命开始，生为一个必须依赖他人的婴儿。这种谦卑是他生命和使命的标志。他不是来推翻政权的，而是通过他充满爱的牺牲，通过道成肉身，然后自愿放弃生命来推翻罪恶。

神的儿子。马利亚的儿子。神完美的计划终于显现出来。

谦卑。从一开始就是耶稣的印记。

祷告
主耶稣，你拥有世界上和宇宙中所有的权能，但你却放弃了这些权柄，并降生于世上。你是何等谦卑。如果不是你谦卑地降世为人，我就不可能从罪恶和死亡中被拯救出来。谢谢你。谢谢你。谢谢你。阿们。
"""


dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
if not dashscope.api_key:
    raise ValueError("Please set DASHSCOPE_API_KEY in ~/.secrets")



# Generate filename dynamically
# 1. Extract Date
TEXT = clean_text(TEXT)
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
verse_ref = filename_parser.extract_verse_from_text(TEXT)

if verse_ref:
    extracted_prefix = CLI_PREFIX if CLI_PREFIX else filename_parser.extract_filename_prefix(TEXT)
    filename = filename_parser.generate_filename(verse_ref, date_str, extracted_prefix).replace(".mp3", "_qwen.mp3")
else:
    filename = f"{date_str}_qwen.mp3"
OUTPUT_DIR = os.path.join(os.getcwd(), "output")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
OUTPUT_PATH = os.path.join(OUTPUT_DIR, filename)
print(f"Target Output: {OUTPUT_PATH}")

TEXT = convert_bible_reference(TEXT)
TEXT = convert_dates_in_text(TEXT)
TEXT = clean_text(TEXT)

paragraphs = [p.strip() for p in re.split(r'\n{2,}', TEXT.strip()) if p.strip()]
# Supported Qwen-TTS voices
voices = ["Cherry", "Serena", "Ethan", "Chelsie", "Cherry"]

def chunk_text(text: str, max_len: int = 400) -> list[str]:
    if len(text) <= max_len:
        return [text]
    import re
    chunks = []
    current_chunk = ""
    parts = re.split(r'([。！？；!.?\n]+)', text)
    for part in parts:
        if len(current_chunk) + len(part) < max_len:
            current_chunk += part
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = part
    if current_chunk:
        chunks.append(current_chunk)
    return chunks

def speak(text: str, voice: str) -> AudioSegment:
    print(f"DEBUG: Text to read: {text[:100]}...")
    resp = SpeechSynthesizer.call(
        model="qwen-tts",
        text=text,
        voice=voice,
        format="wav",
        sample_rate=24000
    )
    if resp.status_code != 200:
        raise Exception(f"API Error: {resp.message}")
    
    # Qwen-TTS returns a URL, we need to download it
    audio_url = resp.output.audio["url"]
    audio_data = requests.get(audio_url).content
    return AudioSegment.from_wav(io.BytesIO(audio_data))

# Group paragraphs into 5 logical sections
# 1. Intro (Title/Date)
# 2. Scripture 1
# 3. Scripture 2
# 4. Main Body (Middle paragraphs)
# 5. Prayer (Last paragraph)

if len(paragraphs) < 5:
    # Fallback if text is too short, just treat as list
    logical_sections = [[p] for p in paragraphs]
else:
    logical_sections = [
        [paragraphs[0]],              # Intro
        [paragraphs[1]],              # Scripture 1
        [paragraphs[2]],              # Scripture 2
        paragraphs[3:-1],             # Main Body (List of paragraphs)
        [paragraphs[-1]]              # Prayer
    ]

# Ensure we don't exceed available voices
num_sections = len(logical_sections)
section_titles = ["Intro", "Scripture 1", "Scripture 2", "Main Body", "Prayer"]
print(f"Processing {num_sections} logical sections...")

final_segments = []
global_p_index = 0

for i, section_paras in enumerate(logical_sections):
    title = section_titles[i] if i < len(section_titles) else f"Section {i+1}"
    print(f"--- Section {i+1}: {title} ---")
    
    section_audio = AudioSegment.empty()
    silence_between_paras = AudioSegment.silent(duration=700, frame_rate=24000)

    for j, para in enumerate(section_paras):
        # Cycle voices based on global paragraph count to match original behavior
        voice = voices[global_p_index % len(voices)]
        print(f"  > Part {i+1}.{j+1} - {voice} ({len(para)} chars)")
        global_p_index += 1
        
        # Check length and chunk if needed
        if len(para) > 450:
            chunks = chunk_text(para, 400)
            print(f"    Split into {len(chunks)} chunks due to length.")
            para_audio = AudioSegment.empty()
            for chunk in chunks:
                if chunk.strip():
                    para_audio += speak(chunk, voice)
            current_segment = para_audio
        else:
            current_segment = speak(para, voice)
            
        section_audio += current_segment
        
        # Add silence between paragraphs in the same section
        if j < len(section_paras) - 1:
            section_audio += silence_between_paras
            
    final_segments.append(section_audio)

final = AudioSegment.empty()
silence_between_sections = AudioSegment.silent(duration=1000, frame_rate=24000)

for i, seg in enumerate(final_segments):
    final += seg
    if i < len(final_segments) - 1:
        final += silence_between_sections

# Metadata extraction
PRODUCER = "VI AI Foundation"
TITLE = TEXT.strip().split('\n')[0]

final.export(OUTPUT_PATH, format="mp3", bitrate="192k", tags={'title': TITLE, 'artist': PRODUCER})
print(f"Success! Saved → {OUTPUT_PATH}")
