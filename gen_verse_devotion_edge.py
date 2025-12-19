import asyncio
import sys
import edge_tts
from pydub import AudioSegment
import os
from bible_parser import convert_bible_reference
from date_parser import convert_dates_in_text
from text_cleaner import clean_text
import filename_parser
import re
from datetime import datetime

TTS_RATE = "+10%"  # Speed up by 10%

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

# Cleaned Chinese devotional text (replace with actual text)
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
# Handle both English () and Chinese （） parentheses, and both : and ： colons
verse_ref = filename_parser.extract_verse_from_text(TEXT)

if verse_ref:
    extracted_prefix = CLI_PREFIX if CLI_PREFIX else filename_parser.extract_filename_prefix(TEXT)
    filename = filename_parser.generate_filename(verse_ref, date_str, extracted_prefix).replace(".mp3", "_edge.mp3")
else:
    filename = f"{date_str}_edge.mp3"
OUTPUT_DIR = os.path.join(os.getcwd(), "output")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
OUTPUT_PATH = os.path.join(OUTPUT_DIR, filename)
print(f"Target Output: {OUTPUT_PATH}")

# Convert Bible references in the text (e.g., '罗马书 1:17' to '罗马书 1章17節')
TEXT = convert_bible_reference(TEXT)
TEXT = convert_dates_in_text(TEXT)
TEXT = clean_text(TEXT)
# Split the text into paragraphs
paragraphs = [p.strip() for p in re.split(r'\n{2,}', TEXT.strip()) if p.strip()]
first_paragraphs = [paragraphs[0]] # First paragraph (introduction)
second_paragraphs = [paragraphs[1]] # Second paragraph
third_paragraphs = [paragraphs[2]] # Third paragraph
fourth_paragraphs = ["\n\n".join(paragraphs[3:-1])] # Paragraphs between 3rd and last
fifth_paragraphs = [paragraphs[-1]] # Last paragraph
"""
Locale,ShortName,Gender,Voice Personalities,Content Categories
zh-CN,zh-CN-XiaoxiaoNeural,Female,Warm,"News, Novel"
zh-CN,zh-CN-XiaoyiNeural,Female,Lively,"Cartoon, Novel"
zh-CN,zh-CN-YunjianNeural,Male,Passion,"Sports, Novel"
zh-CN,zh-CN-YunxiNeural,Male,"Lively, Sunshine",Novel
zh-CN,zh-CN-YunxiaNeural,Male,Cute,"Cartoon, Novel"
zh-CN,zh-CN-YunyangNeural,Male,"Professional, Reliable",News
zh-CN-liaoning,zh-CN-liaoning-XiaobeiNeural,Female,Humorous,Dialect
zh-CN-shaanxi,zh-CN-shaanxi-XiaoniNeural,Female,Bright,Dialect
zh-HK,zh-HK-HiuGaaiNeural,Female,"Friendly, Positive",General
zh-HK,zh-HK-HiuMaanNeural,Female,"Friendly, Positive",General
zh-HK,zh-HK-WanLungNeural,Male,"Friendly, Positive",General
zh-TW,zh-TW-HsiaoChenNeural,Female,"Friendly, Positive",General
zh-TW,zh-TW-HsiaoYuNeural,Female,"Friendly, Positive",General
zh-TW,zh-TW-YunJheNeural,Male,"Friendly, Positive",General
"""
# Voice settings
FIRST_VOICE = "zh-CN-YunxiNeural" # First voice (introduction)
SECOND_VOICE = "zh-CN-XiaoyiNeural" # Second voice (second paragraph)
THIRD_VOICE = "zh-CN-YunyangNeural" # Third voice (third paragraph)
FOURTH_VOICE = "zh-CN-XiaoxiaoNeural" # Fourth voice (paragraphs between 3rd and last)
FIFTH_VOICE = "zh-CN-YunxiaNeural" # Fifth voice (last paragraph)
#THIRD_VOICE = "zh-CN-XiaoxiaoNeural" # Second voice (second paragraph)

TEMP_DIR = OUTPUT_DIR + os.sep # For temp files
TEMP_FIRST = os.path.join(OUTPUT_DIR, "temp_first_verse.mp3")
TEMP_SECOND = os.path.join(OUTPUT_DIR, "temp_second_verse.mp3")
TEMP_THIRD = os.path.join(OUTPUT_DIR, "temp_third_verse.mp3")

# Alias for backward compatibility with main()
OUTPUT = OUTPUT_PATH
async def generate_audio(text, voice, output_file):
    print(f"DEBUG: Text to read: {text[:100]}...")
    # print(f"DEBUG: Generating audio for text: '{text[:50]}...' (len={len(text)})")
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=TTS_RATE)
    await communicate.save(output_file)
async def main():
    # Group paragraphs
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

    # Voice mapping
    voices = [FIRST_VOICE, SECOND_VOICE, THIRD_VOICE, FOURTH_VOICE, FIFTH_VOICE]
    section_titles = ["Intro", "Scripture 1", "Scripture 2", "Main Body", "Prayer"]
    
    print(f"Processing {len(logical_sections)} logical sections...")
    final_segments = []
    global_p_index = 0

    for i, section_paras in enumerate(logical_sections):
        title = section_titles[i] if i < len(section_titles) else f"Section {i+1}"
        print(f"--- Section {i+1}: {title} ---")
        
        section_audio = AudioSegment.empty()
        silence_between_paras = AudioSegment.silent(duration=700) # Edge TTS often returns 24k or 44.1k, pydub handles mixing usually

        for j, para in enumerate(section_paras):
            voice = voices[global_p_index % len(voices)]
            print(f"  > Part {i+1}.{j+1} - {voice} ({len(para)} chars)")
            global_p_index += 1
            
            # Edge TTS requires temp file
            temp_file = f"{TEMP_DIR}temp_v{i}_p{j}.mp3"
            await generate_audio(para, voice, temp_file)
            
            try:
                segment = AudioSegment.from_mp3(temp_file)
                section_audio += segment
                if j < len(section_paras) - 1:
                    section_audio += silence_between_paras
            finally:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
        
        final_segments.append(section_audio)

    # Combine all sections
    final = AudioSegment.empty()
    silence_sections = AudioSegment.silent(duration=1000)

    for i, seg in enumerate(final_segments):
        final += seg
        if i < len(final_segments) - 1:
            final += silence_sections

    # Metadata extraction
    PRODUCER = "VI AI Foundation"
    TITLE = TEXT.strip().split('\n')[0]

    final.export(OUTPUT, format="mp3", tags={'title': TITLE, 'artist': PRODUCER})
    print(f"✅ Combined audio saved: {OUTPUT}")

if __name__ == "__main__":
    asyncio.run(main())
