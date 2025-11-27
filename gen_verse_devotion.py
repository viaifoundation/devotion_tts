import asyncio
import sys
import edge_tts
from pydub import AudioSegment
import os
from bible_parser import convert_bible_reference
from date_parser import convert_dates_in_text
# Cleaned Chinese devotional text (replace with actual text)
TEXT = """
记念神的作为的属灵习惯
2025年11月27日

道成了肉身，住在我们中间，充充满满地有恩典有真理。我们也见过他的荣光，正是父独生子的荣光。
(约翰福音 1:14)
所以，有了机会就当向众人行善，向信徒一家的人更当这样。
(加拉太书 6:10)

我要一心称谢耶和华；
我要传扬你一切奇妙的作为。
我要因你欢喜快乐；
至高者啊，我要歌颂你的名！
(诗篇 9:1-2)
耶和华啊，我要全心赞美你，
传扬你一切奇妙的作为。
我要因你欢喜快乐，
至高者啊，我要歌颂你的名。
(诗篇 9:1-2 当代译本)

记念神的作为的属灵习惯

纵观旧约圣经，神将以色列人从许多不同的情况中拯救出来。他施行神迹，将他们带出外邦，甚至在荒野中为他们提供水和食物。

然而，以色列民逐渐变得悖逆和远离神及神的律法。他们最终背弃了神，部分原因是他们忘记了神。

他们忘记了神为他们大施拯救、忘记了神在他们当中行各样神迹，也忘记了神是良善的、临在的、爱他们的神。

还好圣经中也有些人物展示了记念神过去作为的属灵习惯。当艰难来临，或者环境暗淡的时候，他们会花时间记念神以前是如何对待他们的。

诗篇第9章的作者就是其中之一。诗人以两件事作为开端。首先，他称谢神，表达对神的感激之情。

其次，作者讲述了神奇妙的作为。回顾过去的这些事可以帮助以色列人记住神对他们的信实和良善，即使处于艰辛时期。

我们也应当如此。

圣经多次吩咐我们要记住神所做的一切，因为这会激发我们对他将来要做的事情的盼望。

因此，今天请花一些时间来记念神为你所做的一切。想想你生命中的某个时期，当时是如何体验了神的良善和慈爱。告诉他你多么感恩他在你生命中赐下的良善和爱。开始让那些关于神的爱的记忆塑造你对未来的盼望。


祷告
神啊，有时我的处境很具挑战性，但我也知道自己已享有太多应当感恩的事。感谢你赐给我生命，并给我机会跟你建立关系。感谢你总是眷顾我，即使是在人生最艰难的时刻。主啊，我爱你。奉耶稣的名，阿们。
"""
# Convert Bible references in the text (e.g., '罗马书 1:17' to '罗马书 1章17節')
TEXT = convert_bible_reference(TEXT)
TEXT = convert_dates_in_text(TEXT)
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
OUTPUT = "/Users/mhuo/Downloads/verse_1127.mp3"
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

    # Generate and collect fourth voice audio segments (for remaining paragraphs)
    fourth_segments = []
    for i, para in enumerate(fourth_paragraphs):
        temp_file = f"{TEMP_DIR}temp_fourth_verse_{i}.mp3"
        await generate_audio(para, FOURTH_VOICE, temp_file)
        print(f"✅ Generated fourth voice chunk {i}: {temp_file}")
        segment = AudioSegment.from_mp3(temp_file)
        fourth_segments.append(segment)
        os.remove(temp_file) # Clean up immediately

    # Concatenate fourth segments with short silence between
    fourth_audio = AudioSegment.empty()
    for i, segment in enumerate(fourth_segments):
        fourth_audio += segment
        if i < len(fourth_segments) - 1: # Add silence between segments, not after last
            fourth_audio += silence

    # Generate and collect fifth voice audio segments (for last paragraph)
    fifth_segments = []
    for i, para in enumerate(fifth_paragraphs):
        temp_file = f"{TEMP_DIR}temp_fifth_verse_{i}.mp3"
        await generate_audio(para, FIFTH_VOICE, temp_file)
        print(f"✅ Generated fifth voice chunk {i}: {temp_file}")
        segment = AudioSegment.from_mp3(temp_file)
        fifth_segments.append(segment)
        os.remove(temp_file) # Clean up immediately

    # Concatenate fifth segments with short silence between
    fifth_audio = AudioSegment.empty()
    for i, segment in enumerate(fifth_segments):
        fifth_audio += segment
        if i < len(fifth_segments) - 1: # Add silence between segments, not after last
            fifth_audio += silence
    # Combine all five with a pause between sections
    combined_audio = first_audio + silence + second_audio + silence + third_audio + silence + fourth_audio + silence + fifth_audio
    combined_audio.export(OUTPUT, format="mp3")
    print(f"✅ Combined audio saved: {OUTPUT}")
if __name__ == "__main__":
    asyncio.run(main())
