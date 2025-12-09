
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
import daily_devotional_filenames_v2
import re
from datetime import datetime

dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
if not dashscope.api_key:
    raise ValueError("Please set DASHSCOPE_API_KEY in ~/.secrets")





TEXT = """
神会持守他的应许。 12/9/2025

　神差他独生子到世间来，使我们藉着他得生，　神爱我们的心在此就显明了。不是我们爱　神，乃是　神爱我们，差他的儿子为我们的罪作了挽回祭，这就是爱了。
(约翰一书 4:9-10)
因我们还软弱的时候，基督就按所定的日期为罪人死。为义人死，是少有的；为仁人死，或者有敢做的。惟有基督在我们还作罪人的时候为我们死，　神的爱就在此向我们显明了。
(罗马书 5:6-8)

耶和华说：“日子将到，我应许以色列家和犹大家的恩言必然成就。当那日子，那时候，我必使大卫公义的苗裔长起来；他必在地上施行公平和公义。在那日子犹大必得救，耶路撒冷必安然居住，他的名必称为‘耶和华－我们的义’。
(耶利米书 33:14-16 和合本)
“看哪！日子快到（这是耶和华的宣告），我必实践我向以色列家和犹大家应许赐福的诺言。
(耶利米书 33:14 新译本)
耶和华说：“看啊，时候将到，我要实现我给以色列人和犹大人的美好应许。
(耶利米书 33:14 当代译本)

神会持守他的应许。

“耶和华说：‘日子将到，我应许以色列家和犹大家的恩言必然成就。’”（耶利米书 33:14）

当耶利米说这些话时，很多人都嘲笑他。为什么？因为当时的局势似乎显示神已经遗弃了以色列和犹大两家。

在圣经中所记载的这个时代，以色列家已经不复存在——被入侵的敌军消灭了。而犹大家已是孤独无助，另一支庞大的敌军也来侵并准备摧毁他们。情况再也糟糕不过了。

你经历过这样的时刻吗？也许是一次改变人生的丧失，或者是难以置信的噩耗。在那些痛苦的时刻，要信靠神的应许令人觉得不可能做到。听耶利米说话的人可能也有同样的感受。但这并不是他们生命的结局，因为处境不能动摇神的应许。

是的，敌人入侵，将神的子民囚虏了几十年。但神没有离弃他的子民，也没有违背他的应许。最终，他把以色列百姓从囚虏中解救出来，并带他们回家。

同样，神也没有在你痛苦的时候离弃你。你可能觉得根本无法摆脱困境，或者认为你的选择已导致你失去了神的爱。但神必然信守他的应许。

从流放归来后，神的子民历代都在挣扎。他们继续面对心碎、挫折、入侵和囚虏。但在他们最意想不到的时候，神实现了他的应许。他派他的儿子耶稣带领所有人，包括以色列人和犹大人，走向一个全新且更美好的未来。

神对更美好未来的应许也适用于你。当我们献上全身心来追求神时，我们就会找到平安、力量和满足。我们能够满怀信心地生活，因为知道终有一天，我们将与耶稣共度永生。我们拥有新生命，并相信神已经实现了他的应许。

祷告 :
神啊，
帮助我对你的美好应许充满信心。你是信实的，而且必不离弃我。所以求你让我远离消极或绝望，并帮助我用我的一生来追随你。
奉耶稣的名，
阿们 。
"""

# Generate filename dynamically
# 1. Extract Date
date_match = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", TEXT.split('\n')[0])
if date_match:
    m, d, y = date_match.groups()
    date_str = f"{y}-{int(m):02d}-{int(d):02d}"
else:
    date_str = datetime.today().strftime("%Y-%m-%d")

# 2. Extract Verse (First parenthesis content)
verse_match = re.search(r"\((.*?)\)", TEXT)
verse_ref = verse_match.group(1).strip() if verse_match else "Unknown-Verse"

filename = daily_devotional_filenames_v2.generate_filename(verse_ref, date_str)
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
