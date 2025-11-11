import asyncio
import sys
import edge_tts
from pydub import AudioSegment
import os
from bible_parser import convert_bible_reference

# Cleaned Chinese devotional text
TEXT = """
弟兄姊妹，欢迎来到晨曦读经，今天由万里为我们领读列王记上第12章。
今日亮光：列王记上12章13-15节
王用严厉的话回答百姓，不用老年人给他所出的主意，照着少年人所出的主意对民说，我父亲使你们负重轭，我必使你们负更重的轭。我父亲用鞭子责打你们，我要用蝎子鞭责打你们。王不肯依从百姓，这事乃出于耶和华，为要应验他藉示罗人亚希雅对尼八的儿子耶罗波安所说的话。
罗波安继承所罗门的王位时面临重大抉择，百姓请求减轻负担，老年人建议他用好话回答百姓，少年人却怂恿他用严厉的话。罗波安选择听从少年人，结果导致国家分裂。这个历史事件给我们许多教训。首先是关于寻求智慧的counsel，老年人的建议出于经验和智慧，他们明白得人心者得天下的道理，但罗波安却选择听从与他一同长大的少年人。今天我们在做决定时，是寻求有经验有智慧的人的意见，还是只听那些迎合我们的声音。在职场上新上任的主管，是虚心听取前辈的建议，还是急于显示自己的权威。其次是关于权柄的使用，罗波安以为严厉就是力量，高压就是权威，却不知道真正的领导力来自服事和爱。耶稣说你们中间谁愿为大，就必作你们的用人。作父母的，作主管的，作领袖的，都要思考我们是用权柄来服事人，还是用权柄来压制人。虽然圣经说这事出于耶和华，但这不是说罗波安没有责任，而是说神能够使用人的错误来成就祂的计划。弟兄姊妹，让我们学习谦卑寻求智慧，善用神给我们的权柄来服事人，而不是辖制人。

与Robbin传道同心祷告
主，感谢你藉着历史给我们教训。求你赐给我们谦卑的心，愿意听取智慧的劝告。帮助我们善用你赐的权柄来服事人，而不是压制人。保守我们不因骄傲而做出错误的决定。感谢祷告奉耶稣得胜的名祈求，阿们！
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
FIRST_VOICE = "zh-CN-XiaoxiaoNeural"  # First voice (introduction)
FIRST_VOICE = "zh-CN-YunxiNeural"  # First voice (introduction)
SECOND_VOICE = "zh-CN-YunyangNeural"  # Second voice (main content)
OUTPUT = "/Users/mhuo/Downloads/devotion_1030.mp3"
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
