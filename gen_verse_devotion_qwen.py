
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
import audio_mixer
import re
from datetime import datetime

import argparse

# CLI Args
if "-?" in sys.argv:
    print(f"Usage: python {sys.argv[0]} [--input FILE] [--prefix PREFIX] [--bgm] [--bgm-track TRACK] [--bgm-volume VOL] [--bgm-intro MS] [--help]")
    print ("\nOptions:")
    print("  --input FILE, -i     Text file to read input from")
    print("  --prefix PREFIX      Filename prefix (e.g. MyPrefix)")
    print("  --bgm                Enable background music (Default: False)")
    print("  --bgm-track TRACK    Specific BGM filename (Default: AmazingGrace.MP3)")
    print("  --bgm-volume VOL     BGM volume adjustment in dB (Default: -20)")
    print("  --bgm-intro MS       BGM intro delay in ms (Default: 4000)")
    print("  --help, -h           Show this help")
    print("\n  (Note: You can also add 'FilenamePrefix: <Prefix>' in the input TEXT)")
    sys.exit(0)

parser = argparse.ArgumentParser()
parser.add_argument("--input", "-i", type=str, help="Input text file")
parser.add_argument("--prefix", type=str, default=None, help="Filename prefix (e.g. MyPrefix)")
parser.add_argument("--bgm", action="store_true", help="Enable background music (Default: False)")
parser.add_argument("--bgm-track", type=str, default="AmazingGrace.MP3", help="Specific BGM filename (Default: AmazingGrace.MP3)")
parser.add_argument("--bgm-volume", type=int, default=-20, help="BGM volume adjustment in dB (Default: -20)")
parser.add_argument("--bgm-intro", type=int, default=4000, help="BGM intro delay in ms (Default: 4000)")

args, unknown = parser.parse_known_args()
CLI_PREFIX = args.prefix
ENABLE_BGM = args.bgm
BGM_FILE = args.bgm_track
BGM_VOLUME = args.bgm_volume
BGM_INTRO_DELAY = args.bgm_intro

# 1. Try --input argument
if args.input:
    print(f"Reading text from file: {args.input}")
    with open(args.input, "r", encoding="utf-8") as f:
        TEXT = f.read()

# 2. Try Stdin (Piped)
elif not sys.stdin.isatty():
    print("Reading text from Stdin...")
    TEXT = sys.stdin.read()

# 3. Fallback
else:
    TEXT = """
“　神爱世人，甚至将他的独生子赐给他们，叫一切信他的，不至灭亡，反得永生。因为　神差他的儿子降世，不是要定世人的罪，乃是要叫世人因他得救。信他的人，不被定罪；不信的人，罪已经定了，因为他不信　神独生子的名。
(约翰福音 3:16-18)
"""
信靠神的计划 (路加福音 2:7) 12/22/2025


忽然，有一大队天兵同那天使赞美　神说：
在至高之处荣耀归与　神！
在地上平安归与他所喜悦的人（有古卷：喜悦在至高之处荣耀归与　神！
在地上平安归与他所喜悦的人（有古卷：喜悦归与人）！
(路加福音 2:13-14 和合本)
“在至高之处，荣耀归与　神！
在地上，平安归与他所喜悦的人！”
(路加福音 2:14 新译本)
“在至高之处荣耀归于上帝！
在地上平安临到祂所喜悦的人！”
(路加福音 2:14 当代译本)
我将这些事告诉你们，是要叫你们在我里面有平安。在世上，你们有苦难；但你们可以放心，我已经胜了世界。”
(约翰福音 16:33 和合本)
我把这些事告诉你们，是要使你们在我里面有平安。在世上你们有患难，但你们放心，我已经胜了这世界。”
(约翰福音 16:33 新译本)

约瑟也从加利利的拿撒勒城上犹太去，到了大卫的城，名叫伯利恒，因他本是大卫一族一家的人，要和他所聘之妻马利亚一同报名上册。那时马利亚的身孕已经重了。他们在那里的时候，马利亚的产期到了，就生了头胎的儿子，用布包起来，放在马槽里，因为客店里没有地方。
(路加福音 2:4-7 和合本)
生了头胎儿子，用布包着，放在马槽里，因为客店里没有地方。
(路加福音 2:7 新译本)

信靠神的计划

想象一下马利亚和约瑟准备当父母的情景。他们可能问了很多与今天的准父母相同的问题：孩子健康吗？我们准备好养育这个孩子了吗？我们拥有所需的一切吗？我们要在哪里生呢？我们准备好迎接孩子出生了吗？

在马利亚的妊娠晚期，凯撒·奥古斯都颁布法令，要罗马帝国的每个人都返回家乡进行人口普查（路加福音 2:1-4）。这意味着马利亚和约瑟必须离开他们在拿撒勒的家，踏上四天的旅程前往伯利恒——约瑟祖先大卫的城。

由于人口普查，伯利恒的客栈里挤满了回家的人。因此，当时候到了，马利亚只好在他们唯一可去的地方——马厩——生下了耶稣。在毫无设施的情况下，她把耶稣放在用来装饲料的马槽里。这肯定不是马利亚为她的第一个孩子计划的出生方式。

然而，这正是神所命定的。神通过他儿子诞生时的情景向我们展示了很多关于他的国的事情。

他向我们展示了耶稣是谦卑的。耶稣出生在马厩里，被放在马槽里。他是万物的创造者，却出身卑微。

他向我们展示了神的国是开放给所有人的。这位王并没有躲在城堡或豪宅里，或与他的百姓隔绝，或收集满满的奢侈品——低下的牧羊人和博学的智者都可以来见他。

他向我们展示了我们可以信靠他的计划。马利亚必须信靠神的计划。约瑟必须信靠神的计划。想象另一个情景，如果马利亚和约瑟在客栈里要求别人为他们腾出房间，大喊 “这是弥赛亚降临啊！快腾出房间给我们！”，故事会有什么不同的发展呢？但他们没有这样做。他们接受了眼前的情况并信靠神的计划，无论处境看起来有多奇异或令人不快。

正是在这种顺服的姿态和奇异的处境中，神赐下了他的儿子，正如他所计划的那样。

我们可以相信这个故事，因为神是作者。耶稣卑微的诞生并非偶然——那是一个信息，让我们看见神的国的真正样子。那也是一个邀请，让我们放弃我们的计划、放弃我们对故事应该如何发展的想法，并选择相信神在我们生命中值得信赖的手。我们可以信靠神的计划。

祷告
神啊，感谢你，因为你的道路非同我的道路。有时这的确很难接受，但却是一件好事！谢谢你派你的儿子前来，并通过他的诞生教导了我很多关于你的国的事情。你是如此谦卑，让我可以随时来到你面前。你配得我全然的信靠。今天，我要选择信靠你。
奉耶稣的名，阿们。
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

if ENABLE_BGM and BGM_FILE:
    bgm_base = os.path.splitext(os.path.basename(BGM_FILE))[0]
    filename = filename.replace(".mp3", f"_bgm_{bgm_base}.mp3")
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

# Add Background Music (Optional)
if ENABLE_BGM:
    print(f"🎵 Mixing Background Music (Vol={BGM_VOLUME}dB, Intro={BGM_INTRO_DELAY}ms)...")
    final = audio_mixer.mix_bgm(
        final, 
        specific_filename=BGM_FILE,
        volume_db=BGM_VOLUME,
        intro_delay_ms=BGM_INTRO_DELAY
    )

# Metadata extraction
PRODUCER = "VI AI Foundation"
TITLE = TEXT.strip().split('\n')[0]

final.export(OUTPUT_PATH, format="mp3", bitrate="192k", tags={'title': TITLE, 'artist': PRODUCER})
print(f"Success! Saved → {OUTPUT_PATH}")
