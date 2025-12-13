
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
我们的好牧人 (约翰福音 10:10) 2025-12-12

所以，你要知道耶和华－你的　神，他是　神，是信实的　神；向爱他、守他诫命的人守约，施慈爱，直到千代；
(申命记 7:9)
古时（或译：从远方）耶和华向以色列（原文是我）显现，说：
我以永远的爱爱你，
因此我以慈爱吸引你。
(耶利米书 31:3 和合本)
耶和华在古时（“在古时”或译：“从远处”）曾向以色列（按照《马索拉文本》，“以色列”应作“我”；现参照《七十士译本》翻译）显现，说：
“我以永远的爱爱你，
因此，我对你的慈爱延续不息（“我对你的慈爱延续不息”或译：“我要以慈爱吸引你”）。
(耶利米书 31:3 新译本)
从前，耶和华向以色列显现，说：
“我以永远的爱爱你，
我以不变的慈爱吸引你。
(耶利米书 31:3 当代译本)
你不要害怕，因为我与你同在；
不要惊惶，因为我是你的　神。
我必坚固你，我必帮助你；
我必用我公义的右手扶持你。
(以赛亚书 41:10)

所以，耶稣又对他们说：“我实实在在地告诉你们，我就是羊的门。凡在我以先来的都是贼，是强盗；羊却不听他们。我就是门；凡从我进来的，必然得救，并且出入得草吃。盗贼来，无非要偷窃，杀害，毁坏；我来了，是要叫羊（或译：人）得生命，并且得的更丰盛。我是好牧人；好牧人为羊舍命。
(约翰福音 10:7-11 和合本)
盗贼来，无非要偷窃，杀害，毁坏；我来了，是要叫羊（或译：人）得生命，并且得的更丰盛。
(约翰福音 10:10 和合本)
贼来了，不过是要偷窃、杀害、毁坏；我来了，是要使羊得生命，并且得的更丰盛。
(约翰福音 10:10 新译本)

我们的好牧人

耶稣多次使用的“我是”是一个很有力的声明，让我们一瞥耶稣的本性和他在世上的使命。首先，它展现了耶稣在世上执行使命的目的与姿态。其次，它将耶稣与父神联系起来；耶稣的“我是”表明了他的神性，与出埃及记 3:14 中神向摩西启示自己为“我是”的宣言息息相关。

在约翰福音第10章中，耶稣告诉人们他是好牧人。好牧人的标志是他必须愿意为他的羊舍命。耶稣说他愿意那样做。

耶稣的话与他那个时代的宗教领袖形成鲜明的对比。那些宗教领袖常常刁难神的追随者。他们添加律法和条规，导致人们更远离神。归根结底，他们是自私的领袖，认为自己比他们所领导的人更重要。

耶稣指出，做好牧人的最重要条件是为羊舍命。耶稣就是那位至高的牧羊人，因为他真正关心神的子民。他就像诗篇23篇中的牧羊人，把羊群领到可安歇的水边，使他们的灵魂苏醒。

你有没有想过耶稣是你个人灵魂的牧人？耶稣切望在生活中与你同行、照顾你的需求，并保守你的心。他一心要爱你并引导你做对你有益的事情。 

他不是一个想让你的生活变得沉重或困难的引领者。相反，他希望你活在自由和恩典中。花点时间来思想耶稣是你的好牧人的含义，并感谢他的爱和恩典。

祷告：
神啊，感谢你做我的好牧人。即使在我怀疑你的良善的时候，你仍无私地寻求我。你一次又一次地使我焦虑的心平静下来。感谢你背负我的重担。我知道你眷顾我，并且总是为我的益处着想。奉耶稣的名，阿们。
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
OUTPUT_PATH = f"/Users/mhuo/Downloads/{filename}"
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
