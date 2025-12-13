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
我们的好牧人 (约翰福音 10:10) 12/12/2025

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

# 2. Extract Verse (First parenthesis content)
verse_match = re.search(r"\((.*?)\)", TEXT)
verse_ref = verse_match.group(1).strip() if verse_match else "Unknown-Verse"

filename = filename_parser.generate_filename(verse_ref, date_str).replace(".mp3", "_edge.mp3")
OUTPUT = f"/Users/mhuo/Downloads/{filename}"
print(f"Target Output: {OUTPUT}")

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

TEMP_DIR = "/Users/mhuo/Downloads/" # For temp files
TEMP_FIRST = "/Users/mhuo/Downloads/temp_first_verse.mp3"
TEMP_SECOND = "/Users/mhuo/Downloads/temp_second_verse.mp3"
TEMP_THIRD = "/Users/mhuo/Downloads/temp_third_verse.mp3"
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
