import asyncio
import sys
import edge_tts
from pydub import AudioSegment
import os
from bible_parser import convert_bible_reference

# Cleaned Chinese devotional text
TEXT = """
因信称义

福音的一个核心信息就是神的公义——意思就是神对人类的作为都是公义的。

使徒保罗首先在罗马书 1:17 中提出这个主题，并在书信的其余篇幅中加以阐述。对保罗来说，这节经文是他在其后的章节中所提立论的前提。

保罗在罗马书 3:23 中说，我们所有人都背弃了神，罪使我们与他分离。

因为只有神是公义圣洁的，我们却不是，所以我们不能凭自己去亲近神，而是需要一个弥合神人之间差距的解决办法。神差耶稣到我们当中，就是让他成为那座桥梁。这样，通过耶稣我们又能重新与神建立关系，同时神的公义依然没有妥协。

这就是为什么保罗说神的公义是在福音上彰显出来的。而且他澄清说，公义来自于信心。保罗说，“义人必因信得生”（罗马书 1:17）。正义的生活，或按神的方式生活，是从信心开始的，即相信耶稣为我们所做的一切。

我们不论做多少善事，也无法赢得与神的关系。神衡量公义，并非看我们所行的善事、父母是基督徒与否，或其他的标准，而是看我们的内心。他要衡量我们是否信耶稣。

要来到神面前的每一个人，都必须凭着信心。

如果我们相信耶稣并凭信心行事，就能与神建立关系。这样做，我们就成为在基督里新造的人。我们的旧方式和旧习惯已成为过去，而且我们从此可以在新生命里与耶稣同行。

今天花一些时间想想，耶稣在十字架上为你舍命对你有什么切身的意义。你生活中的哪些方面可以靠着信心来过，而不是靠努力来赢得神的恩惠？在神的同在中得安息吧，因为你已凭着对耶稣的信心被他接纳，并成为新造的人。
"""

# Convert Bible references in the text (e.g., '罗马书 1:17' to '罗马书 1章17節')
TEXT = convert_bible_reference(TEXT)

# Split the text into paragraphs
paragraphs = [p.strip() for p in TEXT.strip().split("\n\n") if p.strip()]
first_paragraphs = [paragraphs[0]]  # First paragraph (introduction)
second_paragraphs = ["\n\n".join(paragraphs[1:])]  # All remaining paragraphs (main content)

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
FIRST_VOICE = "zh-CN-YunyangNeural"  # First voice (introduction)
SECOND_VOICE = "zh-CN-XiaoyiNeural"  # Second voice (main content)
OUTPUT = "/Users/mhuo/Downloads/devotion_1014.mp3"
TEMP_DIR = "/Users/mhuo/Downloads/"  # For temp files
TEMP_FIRST = "/Users/mhuo/Downloads/temp_first_devotion.mp3"
TEMP_SECOND = "/Users/mhuo/Downloads/temp_second_devotion.mp3"

async def generate_audio(text, voice, output_file):
    communicate = edge_tts.Communicate(text=text, voice=voice)
    await communicate.save(output_file)

async def main():
    # Generate and collect first voice audio segments (for first paragraph)
    first_segments = []
    for i, para in enumerate(first_paragraphs):
        temp_file = f"{TEMP_DIR}temp_first_devotion_{i}.mp3"
        await generate_audio(para, FIRST_VOICE, temp_file)
        print(f"✅ Generated first voice chunk {i}: {temp_file}")
        segment = AudioSegment.from_mp3(temp_file)
        first_segments.append(segment)
        os.remove(temp_file)  # Clean up immediately

    # Concatenate first segments with short silence between
    silence = AudioSegment.silent(duration=500)  # 0.5s pause; adjust as needed
    first_audio = AudioSegment.empty()
    for i, segment in enumerate(first_segments):
        first_audio += segment
        if i < len(first_segments) - 1:  # Add silence between segments, not after last
            first_audio += silence

    # Generate and collect second voice audio segments (for remaining paragraphs)
    second_segments = []
    for i, para in enumerate(second_paragraphs):
        temp_file = f"{TEMP_DIR}temp_second_devotion_{i}.mp3"
        await generate_audio(para, SECOND_VOICE, temp_file)
        print(f"✅ Generated second voice chunk {i}: {temp_file}")
        segment = AudioSegment.from_mp3(temp_file)
        second_segments.append(segment)
        os.remove(temp_file)  # Clean up immediately

    # Concatenate second segments with short silence between
    second_audio = AudioSegment.empty()
    for i, segment in enumerate(second_segments):
        second_audio += segment
        if i < len(second_segments) - 1:  # Add silence between segments, not after last
            second_audio += silence

    # Combine first and second with a pause between sections
    combined_audio = first_audio + silence + second_audio
    combined_audio.export(OUTPUT, format="mp3")
    print(f"✅ Combined audio saved: {OUTPUT}")

if __name__ == "__main__":
    asyncio.run(main())