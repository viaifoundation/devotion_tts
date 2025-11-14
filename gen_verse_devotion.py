import asyncio
import sys
import edge_tts
from pydub import AudioSegment
import os
from bible_parser import convert_bible_reference
# Cleaned Chinese devotional text (replace with actual text)
TEXT = """
敬拜我们美善的神

“耶和华啊，你是我的　神； 我要尊崇你，我要称赞你的名。 因为你以忠信诚实行过奇妙的事， 成就你古时所定的。”
以赛亚书 25:1

敬拜我们美善的神

敬拜神是基督徒生活中最核心且最基本的属灵操练。神的子民积极地敬拜他的记载贯穿整本圣经。圣经里充满了专为敬拜神而写的曲子和诗歌。

我们常常认为敬拜就是唱赞美诗，但敬拜远不止于此。事实上，当我们把对神的敬拜仅限于唱歌时，我们就错过了基督徒生活中一个很关键的层面。

圣经中的敬拜不仅仅是唱歌。正确地思念和赞美神的属性以及他所行的事，就是敬拜。当我们承认神就是神时──当我们敬畏他的性情和他的供应时，敬拜就油然而生了。

这意味着我们可以在一天中的任何时刻敬拜神。当我们感谢神的仁慈时，那就是敬拜；当我们敬畏他的荣美时，那就是敬拜。

在以赛亚书 25 :1 中，先知以赛亚正是以这种方式赞美神。以赛亚因为神的属性以及作为他个人的神称颂他。他也因为神的信实而敬拜他。最后，以赛亚赞美神所做的一切奇妙的事。

以赛亚当时可能根本没有唱歌，但他的言语和行为告诉我们，他在敬拜神的属性和神的作为。以赛亚对神的伟大和奇妙有无比的敬畏。

今天花点时间想一想神。思考他的性情；他是美善、信实和慈爱的。想一想他赐给你的福分。静坐几分钟敬仰神的属性，心无旁骛地敬拜他。
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
OUTPUT = "/Users/mhuo/Downloads/verse_1114.mp3"
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
