
# gen_verse_devotion_qwen.py
# Real Qwen3-TTS – 5 voices, works perfectly

import io
import os
import requests
import dashscope
from dashscope.audio.qwen_tts import SpeechSynthesizer
from pydub import AudioSegment

from bible_parser import convert_bible_reference
from date_parser import convert_dates_in_text
from text_cleaner import remove_space_before_god
import filename_parser
import re
from datetime import datetime

dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
if not dashscope.api_key:
    raise ValueError("Please set DASHSCOPE_API_KEY in ~/.secrets")

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

# 2. Extract Verse
# Try matching (Book) Chapter:Verse first (e.g. "(以赛亚书) 7:14")
verse_match = re.search(r"\((.*?)\)\s*(\d+[:：]\d+(?:[-\d+]*))", TEXT)
if verse_match:
    book = verse_match.group(1).strip()
    ref = verse_match.group(2).strip()
    verse_ref = f"{book} {ref}"
else:
    # Fallback to standard (Book Chapter:Verse)
    verse_match = re.search(r"\((.*?)\)", TEXT)
    verse_ref = verse_match.group(1).strip() if verse_match else "Unknown-Verse"

filename = filename_parser.generate_filename(verse_ref, date_str).replace(".mp3", "_qwen.mp3")
OUTPUT_DIR = os.getcwd()
OUTPUT_PATH = os.path.join(OUTPUT_DIR, filename)
print(f"Target Output: {OUTPUT_PATH}")

TEXT = convert_bible_reference(TEXT)
TEXT = convert_dates_in_text(TEXT)
TEXT = remove_space_before_god(TEXT)

paragraphs = [p.strip() for p in TEXT.strip().split("\n\n") if p.strip()]
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

final.export(OUTPUT_PATH, format="mp3", bitrate="192k")
print(f"Success! Saved → {OUTPUT_PATH}")
