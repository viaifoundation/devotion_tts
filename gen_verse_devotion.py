import asyncio
import sys
import edge_tts
from pydub import AudioSegment
import os
from bible_parser import convert_bible_reference
# Cleaned Chinese devotional text (replace with actual text)
TEXT = """
帮助近在咫尺

“因为上帝爱世人，甚至将祂独一的儿子赐给他们，叫一切信祂的人不致灭亡，反得永生。
(约翰福音 3:16)
我们既然有一位已经升入高天尊荣的大祭司，就是神的儿子耶稣，便当持定所承认的道。因我们的大祭司并非不能体恤我们的软弱。他也曾凡事受过试探，与我们一样，只是他没有犯罪。所以，我们只管坦然无惧地来到施恩的宝座前，为要得怜恤，蒙恩惠，作随时的帮助。
(希伯来书 4:14-16)

天天背负我们重担的主，
就是拯救我们的神，
是应当称颂的！
（细拉）
(诗篇 68:19 和合本)
要称颂主，
称颂我们的救主上帝，
祂天天背负我们的重担。
（细拉）
(诗篇 68:19 当代译本)


帮助近在咫尺

背负着重担过一生不是神创造我们的本意。

感恩的是，我们不必如此过日子。

“凡劳苦担重担的人可以到我这里来，我就使你们得安息。我心里柔和谦卑，你们当负我的轭，学我的样式；这样，你们心里就必得享安息。因为我的轭是容易的，我的担子是轻省的。”（马太福音 11:28-30）

当耶稣来到世上时，他把我们的重担担在了自己身上。尽管我们远离神，耶稣却为我们的罪孽承担了惩罚，承担了我们的苦难。正因为如此，我们就有了一位理解我们、怜悯我们的救主。

这位救主在我们的混乱中与我们相遇，并邀请我们在他里面找到安息。这位救主是与我们同在的神。

“天天背负我们重担的主， 就是拯救我们的神， 是应当称颂的！”（诗篇 68:19）

大卫王在耶稣到来的数百年之前写下了这首诗篇。在那个时候，神已向人们表明他的品格是不变的，而且他是值得信靠的。

神在地球被洪水淹没时守护挪亚（创世记 8:1）；神与亚伯拉罕立约，以祝福、保护和繁衍他的后裔（创世记 17:4-7）；神在以色列人流浪旷野时照顾他们（申命记2:7）；神在大卫逃避仇人的追杀时安慰他。

神从未停止作为真正的神。他是我们在需要时近在咫尺的帮助；他是我们源源不断的力量源泉；他是我们的安慰者和供应者。大卫在诗篇 68 章中所赞美的神就是我们的神。他是那一位不停地照顾我们的神；在我们的混乱中弯腰迎接我们并修补我们的破碎。

他天天背负我们的重担。

我们仍然会要忍受苦难吗？会的。但我们永远不必独自经历它们。世界的救主已经临近了。神与我们同在。

祷告
神啊，你配得我的一切称颂！我软弱时，你支撑我；我不堪重负时，你扶持我。你知道我所有的重担。感谢你从不让我独自承受苦难；感谢你让我把这一切交托给你。奉耶稣的名祷告，阿们。

"""
# Convert Bible references in the text (e.g., '罗马书 1:17' to '罗马书 1章17節')
TEXT = convert_bible_reference(TEXT)
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
FIFTH_VOICE = "zh-CN-YunjianNeural" # Fifth voice (last paragraph)
#THIRD_VOICE = "zh-CN-XiaoxiaoNeural" # Second voice (second paragraph)
OUTPUT = "/Users/mhuo/Downloads/verse_1126.mp3"
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
