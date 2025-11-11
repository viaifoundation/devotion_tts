import asyncio
import sys
import edge_tts
from pydub import AudioSegment
import os
from bible_parser import convert_bible_reference
# Cleaned Chinese devotional text (replace with actual text)
TEXT = """
“爱是恒久忍耐，又有恩慈；爱是不嫉妒；爱是不自夸，不张狂， 不做害羞的事，不求自己的益处，不轻易发怒，不计算人的恶， 不喜欢不义，只喜欢真理； 凡事包容，凡事相信，凡事盼望，凡事忍耐。 爱是永不止息”
哥林多前书 13:4-8a
“爱是恒久忍耐，又是仁慈； 爱是不嫉妒； 爱是不自夸、不自大； 不做不合宜的事，不求自己的益处， 不轻易动怒，不计算人的恶， 不为不义欢喜，而与真理同乐； 凡事包容，凡事相信， 凡事盼望，凡事忍耐。 爱是永不止息； 而做先知传道的恩赐将被废除， 殊言也将会停止， 知识也将被废除，”
哥林多前书 13:4-8a 中文标准译本

爱是什么样子的？

如果你随意问十个人，爱的定义是什么，很可能会得到十种不同答案。人们往往把最看重的或最愉悦的视作爱。但爱的定义何其多，且常常互为矛盾；作为基督徒，我们应当渴望去找到爱的真谛。

爱的真正定义并非来自文化、价值观或内心──它只能来自于神，因为“神就是爱”（约翰一书4:8）。因此，任何对爱的正确理解必来自于神。哥林多前书13章的整个章节都用来定义什么是爱。

哥林多前书13:6还说，爱“不喜欢不义”，任何敌对神和反对神道的即为不义。当我们不遵守神的律法、选择做错事或伤害他人时──那就是不义。

本质上讲，不爱神、不爱人就是不义。

比方说，若有难以相处的人不懂耶稣的爱，我们就不该取笑他们，而是凭着爱去与他们分享耶稣的真理；若有曾经伤害过你的人正经受痛苦，我们就不该幸灾乐祸，而是像神赦免我们那样去原谅他们。当我们宣讲、操练、和分享神的真理时，爱就是喜乐。

今天花点时间想想，你对爱的定义与神的有何不同；你有什么误解吗？此外，你在思想和行动上如何改变才能使自己更具爱心？最重要的是，你可以与谁分享神爱的真理？找两三个你可以为之祷告和与其交谈的人，去和他们分享神的爱。

"""
# Convert Bible references in the text (e.g., '罗马书 1:17' to '罗马书 1章17節')
TEXT = convert_bible_reference(TEXT)
# Split the text into paragraphs
paragraphs = [p.strip() for p in TEXT.strip().split("\n\n") if p.strip()]
first_paragraphs = [paragraphs[0]] # First paragraph (introduction)
second_paragraphs = [paragraphs[1]] # Second paragraph
third_paragraphs = ["\n\n".join(paragraphs[2:])] # All remaining paragraphs
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
FIRST_VOICE = "zh-CN-YunyangNeural" # First voice (introduction)
THIRD_VOICE = "zh-CN-XiaoxiaoNeural" # Second voice (second paragraph)
SECOND_VOICE = "zh-CN-YunxiNeural" # Third voice (remaining paragraphs)
OUTPUT = "/Users/mhuo/Downloads/verse_1111.mp3"
TEMP_DIR = "/Users/mhuo/Downloads/" # For temp files
TEMP_FIRST = "/Users/mhuo/Downloads/temp_first_verse.mp3"
TEMP_SECOND = "/Users/mhuo/Downloads/temp_second_verse.mp3"
TEMP_THIRD = "/Users/mhuo/Downloads/temp_third_verse.mp3"
async def generate_audio(text, voice, output_file):
    communicate = edge_tts.Communicate(text=text, voice=voice)
    await communicate.save(output_file)
async def main():
    # Generate and collect first voice audio segments (for first paragraph)
    first_segments = []
    for i, para in enumerate(first_paragraphs):
        temp_file = f"{TEMP_DIR}temp_first_verse_{i}.mp3"
        await generate_audio(para, FIRST_VOICE, temp_file)
        print(f"✅ Generated first voice chunk {i}: {temp_file}")
        segment = AudioSegment.from_mp3(temp_file)
        first_segments.append(segment)
        os.remove(temp_file) # Clean up immediately
    # Concatenate first segments with short silence between
    silence = AudioSegment.silent(duration=500) # 0.5s pause; adjust as needed
    first_audio = AudioSegment.empty()
    for i, segment in enumerate(first_segments):
        first_audio += segment
        if i < len(first_segments) - 1: # Add silence between segments, not after last
            first_audio += silence
    # Generate and collect second voice audio segments (for second paragraph)
    second_segments = []
    for i, para in enumerate(second_paragraphs):
        temp_file = f"{TEMP_DIR}temp_second_verse_{i}.mp3"
        await generate_audio(para, SECOND_VOICE, temp_file)
        print(f"✅ Generated second voice chunk {i}: {temp_file}")
        segment = AudioSegment.from_mp3(temp_file)
        second_segments.append(segment)
        os.remove(temp_file) # Clean up immediately
    # Concatenate second segments with short silence between
    second_audio = AudioSegment.empty()
    for i, segment in enumerate(second_segments):
        second_audio += segment
        if i < len(second_segments) - 1: # Add silence between segments, not after last
            second_audio += silence
    # Generate and collect third voice audio segments (for remaining paragraphs)
    third_segments = []
    for i, para in enumerate(third_paragraphs):
        temp_file = f"{TEMP_DIR}temp_third_verse_{i}.mp3"
        await generate_audio(para, THIRD_VOICE, temp_file)
        print(f"✅ Generated third voice chunk {i}: {temp_file}")
        segment = AudioSegment.from_mp3(temp_file)
        third_segments.append(segment)
        os.remove(temp_file) # Clean up immediately
    # Concatenate third segments with short silence between
    third_audio = AudioSegment.empty()
    for i, segment in enumerate(third_segments):
        third_audio += segment
        if i < len(third_segments) - 1: # Add silence between segments, not after last
            third_audio += silence
    # Combine first, second, and third with a pause between sections
    combined_audio = first_audio + silence + second_audio + silence + third_audio
    combined_audio.export(OUTPUT, format="mp3")
    print(f"✅ Combined audio saved: {OUTPUT}")
if __name__ == "__main__":
    asyncio.run(main())
