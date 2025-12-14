import asyncio
import sys
import edge_tts
from pydub import AudioSegment
import os
from bible_parser import convert_bible_reference
from date_parser import convert_dates_in_text
from text_cleaner import remove_space_before_god
import filename_parser
import re
from datetime import datetime
# Cleaned Chinese devotional text (replace with actual text)
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

filename = filename_parser.generate_filename(verse_ref, date_str).replace(".mp3", "_edge.mp3")
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
OUTPUT_PATH = os.path.join(DOWNLOADS_DIR, filename)
print(f"Target Output: {OUTPUT_PATH}")

# Convert Bible references in the text (e.g., '罗马书 1:17' to '罗马书 1章17節')
TEXT = convert_bible_reference(TEXT)
TEXT = convert_dates_in_text(TEXT)
TEXT = remove_space_before_god(TEXT)
# Split the text into paragraphs
paragraphs = [p.strip() for p in TEXT.strip().split("\n\n") if p.strip()]
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

TEMP_DIR = DOWNLOADS_DIR + os.sep # For temp files
TEMP_FIRST = os.path.join(DOWNLOADS_DIR, "temp_first_verse.mp3")
TEMP_SECOND = os.path.join(DOWNLOADS_DIR, "temp_second_verse.mp3")
TEMP_THIRD = os.path.join(DOWNLOADS_DIR, "temp_third_verse.mp3")

# Alias for backward compatibility with main()
OUTPUT = OUTPUT_PATH
async def generate_audio(text, voice, output_file):
    print(f"DEBUG: Generating audio for text: '{text[:50]}...' (len={len(text)})")
    communicate = edge_tts.Communicate(text=text, voice=voice)
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

    final.export(OUTPUT, format="mp3")
    print(f"✅ Combined audio saved: {OUTPUT}")

if __name__ == "__main__":
    asyncio.run(main())
