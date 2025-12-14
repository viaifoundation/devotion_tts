
import asyncio
import sys
import edge_tts
from pydub import AudioSegment
import os
from bible_parser import convert_bible_reference
from text_cleaner import remove_space_before_god

# Cleaned Chinese devotional text (replace with actual text)
TEXT = """
靈晨靈糧12月3日罗丽芳姊妹：<“恩典25”第48篇：打通信主的“任督二脉”>

我是典型的从中国来的 “无神论“ 的理科生，国内读了本科硕士，从未接触过宗教，然后来美国读博士学位。

其实我从 2005 年左右就开始接触基督徒了，在东部大学城攻读博士学位的第二年，有一位从中部搬来的白人牧师，经常邀请留学生周末去他家吃饭。为什么他们可以那样无私的为我们付出呢？这是一个我完全理解不了的世界，也没大兴趣去了解，甚至对传教反感。

后来到南加工作，接触了台湾陈妈妈、陈爸爸，他们60岁左右，开快餐店，养育子女，非常辛苦，但是每周五晚上敞开他们的家，做美味的佳肴给大家吃。他们的喜乐和面对生活挑战时所拥有的平安让我好奇这不一样的世界，开启了我慕道的漫长之路。虽然在弟兄姊妹的帮助下，我和先生 2010 年受洗了，但是我的头脑依然没被说服神创造万物、基督是我们的救赎。我的心仍是坚硬的，所谓 “见其门，但不得入其门”。

这种慕道但不信的状态一直持续了 15 年左右。2012 年初，我搬到了湾区，加入了基督六家。2016 年，我的孩子参加了颜牧师和Sharon 师母带领的 AWANA，我也在 AWANA服侍。我愿意读经但不主动读经，愿意敬拜但不把敬拜当成最重要的事情之一。因为我不真的信，心里很虚，无法做孩子们真正属灵的老师，也无法在家里做孩子们属灵的母亲；去教会也变成很挣扎的事情，经不起各种试探如工作忙碌、家人不统一、孩子的其他活动等。经常不去教会，我内心滋生愧疚，愧疚滋生逃避，逃避滋生远离。当我遇到难题时，经常转向学理（比如心理学），只依靠小我，而不是信靠主。我很少祷告，我不信也觉得自己不配，同时心中缺少谦卑。我的不信和小我的骄傲几乎完全阻断了我和天父的关系。2025 上半年，我甚至开始考虑要不要完全放弃教会，放弃游离纠结的状态，走一条其他的路。

即使这样，神永远没有放弃我这只长期迷途的羔羊。在这期间，他派了许多兄弟姊妹来引领我，他们的见证像吸铁石一样，又让我远离时不由自主地靠近，比如，近期良友B组和橄榄树小组的查经，Jerry长老和师母长久以来的呼召和为我家的祷告，利萍师母敞开的怀抱。Jerry 长老倾听我的家庭琐碎的烦恼，还帮我们立家规，为我们祈祷，让我非常感动。

如果说有一个转折点，那就是于师母教导的基督生平的课程一，这个课程一般参加者为资深基督的，我这个迷路的人在利萍师母和Linwei的帮助下，最后一个混进去了。意想不到的是，我被打通了信的任督二脉。以前对我来说，耶稣基督像一个神话故事里的人物，上完第一期的课后，他变得又真又活，兼备人性和神性，是完美的神。

感谢赞美主，我终于不在心虚，开始真诚的信靠主。我开始主动一个人读圣经，意识到我之前不信，一个主要原因是我在知识上没有预备好，没有真正的读懂圣经。我更加享受教会的各种活动。写下上面文字的时候，我们全家正参加了FVC基督徒5天4夜的家庭度假，宴信中牧师让我有许多感动。God is good。

以前我学习了许多心理学方面的知识和技巧，虽然知道，但常常做不到。我的自傲让我常常愧疚。现在，我更能谦卑下来：主啊，我有我的软弱和罪过，你却爱着这样的我。

“哥林多后书 12:9“他对我说：「我的恩典够你用的，因为我的能力是在人的软弱上显得完全。」所以，我更喜欢夸自己的软弱，好叫基督的能力覆庇我。”

期待以后在六家的大家庭中有信有靠有望的日子。


"""

# Convert Bible references in the text (e.g., '罗马书 1:17' to '罗马书 1章17節')
TEXT = convert_bible_reference(TEXT)
TEXT = remove_space_before_god(TEXT)

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
"""
Locale,ShortName,Gender,Voice Personalities,Content Categories
zh-CN,zh-CN-XiaoxiaoNeural,Female,Warm,"News, Novel"
zh-CN,zh-CN-XiaoyiNeural,Female,Lively,"Cartoon, Novel"
zh-CN,zh-CN-YunjianNeural,Male,Passion,"Sports, Novel"
zh-CN,zh-CN-YunxiNeural,Male,"Lively, Sunshine",Novel
zh-CN,zh-CN-YunxiaNeural,Male,Cute,"Cartoon, Novel"
zh-CN,zh-CN-YunyangNeural,Male,"Professional, Reliable",News
zh-CN,zh-CN-XiaochenNeural,Female,Warm,General
zh-CN,zh-CN-XiaohanNeural,Female,Cheerful,"Novel, Cartoon"
zh-CN,zh-CN-XiaomoNeural,Female,Emotional,"Novel, Cartoon"
zh-CN,zh-CN-XiaoqiuNeural,Female,Lively,General
zh-CN,zh-CN-XiaoruiNeural,Female,Angry,"Novel, Cartoon"
zh-CN,zh-CN-XiaoshuangNeural,Female,Cute,"Cartoon, Novel"
zh-CN,zh-CN-XiaoxuanNeural,Female,"Chat, Assistant","Novel, CustomerService"
zh-CN,zh-CN-XiaoyanNeural,Female,Professional,"News, Novel"
zh-CN,zh-CN-XiaoyouNeural,Female,Cheerful,"Cartoon, Novel"
zh-CN,zh-CN-XiaozhenNeural,Female,Friendly,General
zh-CN,zh-CN-YunhaoNeural,Male,Professional,"News, Novel"
zh-CN,zh-CN-YunxiaoNeural,Male,Friendly,General
zh-CN,zh-CN-YunyeNeural,Male,Serious,"Novel, Narration"
zh-CN,zh-CN-YunzeNeural,Male,Calm,"Novel, Narration"
zh-CN-liaoning,zh-CN-liaoning-XiaobeiNeural,Female,Humorous,Dialect
zh-CN-shaanxi,zh-CN-shaanxi-XiaoniNeural,Female,Bright,Dialect
zh-CN-sichuan,zh-CN-sichuan-YunxiNeural,Male,Lively,Dialect
zh-CN-wuu,zh-CN-wuu-XiaotongNeural,Female,Friendly,Dialect
zh-CN-wuu,zh-CN-wuu-YunzheNeural,Male,Professional,Dialect
zh-CN-yue,zh-CN-yue-XiaoshanNeural,Female,Friendly,Dialect
zh-CN-yue,zh-CN-yue-YunSongNeural,Male,Professional,Dialect
zh-HK,zh-HK-HiuGaaiNeural,Female,"Friendly, Positive",General
zh-HK,zh-HK-HiuMaanNeural,Female,"Friendly, Positive",General
zh-HK,zh-HK-WanLungNeural,Male,"Friendly, Positive",General
zh-TW,zh-TW-HsiaoChenNeural,Female,"Friendly, Positive",General
zh-TW,zh-TW-HsiaoYuNeural,Female,"Friendly, Positive",General
zh-TW,zh-TW-YunJheNeural,Male,"Friendly, Positive",General
zh-TW,zh-TW-HanHanNeural,Female,Friendly,General
"""
# Voice settings
FIRST_VOICE = "zh-CN-XiaoxiaoNeural"  # First voice (introduction)
SECOND_VOICE = "zh-CN-YunyangNeural"  # Second voice (main content)
#FIRST_VOICE = "zh-HK-WanLungNeural"  # Second voice (main content)
#SECOND_VOICE = "zh-HK-HiuGaaiNeural"  # First voice (introduction)
#SECOND_VOICE = "zh-CN-XiaoyiNeural"  # Second voice (main content)
#FIRST_VOICE = "zh-HK-WanLungNeural"  # First voice (introduction)
#SECOND_VOICE = "zh-HK-HiuGaaiNeural"  # Second voice (main content)
#SECOND_VOICE = "zh-HK-HiuMaanNeural"  # Second voice (main content)
#SECOND_VOICE = "zh-HK-WanLungNeural"  # First voice (introduction)
#FIRST_VOICE = "zh-HK-HiuGaaiNeural"  # Second voice (main content)
#FIRST_VOICE = "zh-TW-HsiaoChenNeural"  # First voice (introduction)
#SECOND_VOICE = "zh-TW-YunJheNeural"  # Second voice (main content)
#FIRST_VOICE = "zh-CN-XiaoxiaoNeural"  # Second voice (main content)
#SECOND_VOICE = "zh-CN-YunyangNeural"  # First voice (introduction)
FIRST_VOICE = "zh-CN-YunyangNeural"  # First voice (introduction)
SECOND_VOICE = "zh-CN-XiaoxiaoNeural"  # Second voice (main content)
#SECOND_VOICE = "zh-HK-WanLungNeural"  # First voice (introduction)
#FIRST_VOICE = "zh-HK-HiuGaaiNeural"  # Second voice (main content)
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
OUTPUT = os.path.join(DOWNLOADS_DIR, "bread_edge.mp3")
TEMP_DIR = DOWNLOADS_DIR + os.sep  # For temp files
TEMP_FIRST = os.path.join(DOWNLOADS_DIR, "temp_first_bread.mp3")
TEMP_SECOND = os.path.join(DOWNLOADS_DIR, "temp_second_bread.mp3")

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
