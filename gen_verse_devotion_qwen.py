
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
from text_cleaner import clean_text
import filename_parser
import re
from datetime import datetime

dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
if not dashscope.api_key:
    raise ValueError("Please set DASHSCOPE_API_KEY in ~/.secrets")

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
verse_ref = filename_parser.extract_verse_from_text(TEXT)

if verse_ref:
    filename = filename_parser.generate_filename(verse_ref, date_str).replace(".mp3", "_qwen.mp3")
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

final.export(OUTPUT_PATH, format="mp3", bitrate="192k")
print(f"Success! Saved → {OUTPUT_PATH}")
