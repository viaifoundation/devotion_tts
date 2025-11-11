import asyncio
import sys
import edge_tts
from pydub import AudioSegment
import os
from bible_parser import convert_bible_reference

# Cleaned Chinese devotional text (replace with actual text)
TEXT = """
靈晨靈糧11月11日翁榮根牧師：<“恩典25”第32篇：2025感恩見證分享>

【感恩 25】是甚麼概念？講出基督六家在蒙神的看顧保守中渡過了 25  個年頭。25 年前的開始（即 2006），與我無關，我對它一無所知，那時的我活在它的對岸（波士頓）。今天卻要感恩，這 25 年的內容，有無數的前輩、先賢和盡心盡力捨己的主內肢體，奠定了基督六家的模式，行出基督信仰的榜樣，守住了神託付的大誡命和大使命。這感恩分享，是奠基在他們像保羅所經歷一樣，為主為教會打過了美好仗，為信的道真守住了，為我們面前的路，他們盡忠跑完了，那我們就在主和眾聖徒的足印上，竭力傳承囑託，忠心侍主。

【感恩 25】對我又如何？前言開始我沒有份兒，只從前輩的過去，或肢體口中的流傳，25 年的上半部，讓人振奮，教會在人力資源的不足，憑藉對神的那份信望愛，每每在難過的時刻，經歷了神的同在、神的憐憫、神的拯救。開發出（英文/兒童）一個個動人的畫面，看到了上半部的 357，和下半部 NLT 的成果，今天的學員仍一個個站在臺上努力事主，他們的授教精神，到今天仍在教會每個層面、每個年齡層，作出他們的貢獻，是有目共睹的，為牧者與學員的委身事主要感謝神。25 年的下半部，基督六家終有我記錄的開始，2012 年底，堂主任黎廣傳牧師在基督工人神學院（CWTS）的週四分享會後，一經握手，被知道能通粵語，從此就在六家作實習傳道，到傳道，後被按立牧師，快長達 13 年的匆匆歲月，沒有異心的遵主命而行。

雖快 13 年，感恩六家對我的不離不棄，黎牧師和教牧同工，當然還有整個粵語部對我的包容忍耐，讓我在當中經歷了被愛。已故的陳慧婷姊妹對我這實習神學生照顧有加，甚至有講員帶來神學作品，覺得對我有益就買下來送給我，她的無私榜樣，成就了我今天外展事工的發展。感恩教會給了我事奉的機會，當由實習到正式傳道的過程中，感謝張平夷長老的諄諄告誡，讓我們有明確的事奉方向，也謝過粵語肢體們的接納，讓我們十多年的事奉仍喜樂渡日，更將他們對我們的好，言傳身教對我們的同工和弟兄姊妹。

感恩 3/15/25 終於由傳道再變身為牧師，這更新是經過千錘百鍊，神在疫情中為粵語部添加了同工：方麗鴻傳道。在我們（翁牧師、Sarah師母、方傳道）的時間配合下，推動了樂家、友家、約瑟芬、海庭、回歸線和422查經小組等外展事工，還有不同家庭探訪、臨終關懷、兒童主日學等服事，這些事工在神的恩典下，有些超過三年歲月的運作，並每個小組都能領人歸主、帶人受洗。所以，要為小組負責人感謝神，他們是神揀選的精英，是神差派他們出來服事。對事工：他們真的毫無保留、毫無退卻、毫無遺憾。對人：更是愛人如己，我們在主內向他們致敬，我們的事奉缺誰都不可，在主裡要合一，彼此相愛，作成主的工，榮耀主的名。

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
SECOND_VOICE = "zh-CN-XiaoxiaoNeural"  # Second voice (main content)
SECOND_VOICE = "zh-CN-XiaoyiNeural"  # Second voice (main content)
#FIRST_VOICE = "zh-HK-WanLungNeural"  # First voice (introduction)
#SECOND_VOICE = "zh-HK-HiuGaaiNeural"  # Second voice (main content)
#SECOND_VOICE = "zh-HK-HiuMaanNeural"  # Second voice (main content)
SECOND_VOICE = "zh-HK-WanLungNeural"  # First voice (introduction)
FIRST_VOICE = "zh-HK-HiuGaaiNeural"  # Second voice (main content)
FIRST_VOICE = "zh-TW-HsiaoChenNeural"  # First voice (introduction)
#SECOND_VOICE = "zh-TW-YunJheNeural"  # Second voice (main content)
FIRST_VOICE = "zh-CN-XiaoxiaoNeural"  # Second voice (main content)
SECOND_VOICE = "zh-CN-YunyangNeural"  # First voice (introduction)
#FIRST_VOICE = "zh-CN-YunyangNeural"  # First voice (introduction)
#SECOND_VOICE = "zh-CN-XiaoxiaoNeural"  # Second voice (main content)
SECOND_VOICE = "zh-HK-WanLungNeural"  # First voice (introduction)
FIRST_VOICE = "zh-HK-HiuGaaiNeural"  # Second voice (main content)
OUTPUT = "/Users/mhuo/Downloads/bread_1111_cantonese.mp3"
TEMP_DIR = "/Users/mhuo/Downloads/"  # For temp files
TEMP_FIRST = "/Users/mhuo/Downloads/temp_first_bread.mp3"
TEMP_SECOND = "/Users/mhuo/Downloads/temp_second_bread.mp3"

async def generate_audio(text, voice, output_file):
    communicate = edge_tts.Communicate(text=text, voice=voice)
    await communicate.save(output_file)

async def main():
    # Generate and collect first voice audio segments (for first paragraph)
    first_segments = []
    for i, para in enumerate(first_paragraphs):
        temp_file = f"{TEMP_DIR}temp_first_bread_{i}.mp3"
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
        temp_file = f"{TEMP_DIR}temp_second_bread_{i}.mp3"
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
