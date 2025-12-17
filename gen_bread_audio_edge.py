
import asyncio
import sys
import edge_tts
from pydub import AudioSegment
import os
import re
from bible_parser import convert_bible_reference
from text_cleaner import clean_text

from text_cleaner import clean_text

import argparse
import audio_mixer

VERSION = "1.0.0"
ENABLE_BGM = False
BGM_FILE = "AmazingGrace.MP3"
TTS_RATE = "+10%"  # Default Speed
BGM_VOLUME = -12   # Default dB
BGM_INTRO_DELAY = 4000 # Default ms


# Cleaned Chinese devotional text (replace with actual text)
TEXT = """
靈晨靈糧12月16日Jerry长老：<“恩典25”第50总结篇：在恩典中定向奔跑 –25周年庆典的回望与前行>

亲爱的弟兄姊妹：在12月14日的长执会当中，大家都非常感恩地回顾2025年教会25周年的庆典。我把与之相关的几个细节记录一下，用在11月22日庆典上《在恩典中定向奔跑》的思路重新组织一下，表达对这次恩典25周年的特别纪念。
这也算是最后一个见证被收录成册，当这滴五十篇故事汇入恩典的长河，我们站在25周年的里程碑前，回望这条恩典之路。这不仅是纪念，更是定向——对准那呼召我们的神，整合于那救赎我们的基督，动员自那充满我们的圣灵。

4月5日上山祷告见到的经文！
对准神的心意：Alignment
“你们要先求祂的国和祂的义…”（太6:33）
这一年，我们从二月十六日的G25委员会成立开始，就学习对准神的心意。每月一次的长执会Review，不是计划的检查，而是集体的俯伏——我们在神面前放下自己的聪明，求问祂为25周年定下的心意。
山上祷告成为我们的定向仪式。从四月五日开始，Sally传道带领会众在神面前安静。那些“时光锦囊”里封存的，不仅是个人计划，更是对准神的渴望。葛立新执事看见其中的精妙：『每个人都有属于自己的 plan，而「时光锦囊」的精妙之处，正是在于它兼具隐私性与集体参与感：计划只有自己在合适的时间打开、与自己对话；但大家又是在同一个行动中一起参与、彼此陪伴和督促，反思。』

“时光锦囊”
四十天禁食祷告（10/13-11/21）更是神给我们的一课。当每日更新中传来紧急代祷的需要，我们真实体会“若一个肢体受苦，所有的肢体就一同受苦”（林前12:26）。祷告不再只是例行公事，而是对准神心意的校准——学习为别人的重担代求，学习在别人的喜乐中欢呼。
神的心意总是超越我们所求所想。当我们对准祂时，祂就打开更宽广的视野：海外校园、圣言、远东、普世佳音…一封封贺信从天南地北飞来，让我们看见自己不过是神普世教会中的一个小小肢体。苏文峰牧师、赖若瀚牧师、杨胜世牧师、李彼得牧师、张德立牧师等的祝福，“慷慨之道事工”蔡豪仁弟兄的字画，基督五家的贺匾，爱邻社的祝贺——这一切都在说：我们不是孤岛，我们是基督身体的一部分。

基督五家教会送给HOC6的贺画

爱邻社LTN祝贺基督六家

来自「慷慨之道事工」的字画：
与基督整合：Integration
“现在活着的不再是我，乃是基督在我里面活着…”（加2:20）
25周年最宝贵的礼物，是那五十篇见证。从九月二十九日开始，每个工作日一篇“上帝的恩典，我们的故事”，这不仅是回顾，更是与基督生命的整合。

谢谢Sally传道收集编辑并出版25周年庆典的见证集《上帝的恩典 我们的故事》
这些故事里，有初信时的懵懂，有创会中的呼求，有破碎后的重建，有喜乐中的感恩……一切都是关乎神的恩典。每一篇都在述说同一个真理：不是我们抓住了基督，而是基督抓住了我们。祂在我们的成功中得荣耀，在我们的失败中显恩典，在我们的平凡中作奇事。
原本计划的四十篇见证，却溢出到五十篇——这不正是神的数学吗？二十五周年，五十篇见证——双倍的恩典，双倍的见证。当我们把这些故事印刷成册，我们捧在手里的不是一本纪念集，而是基督六家见证神引领的恩典满满。
庆典中，我的信息正是这整合的呼召：与基督整合，支取祂的喜乐。不是努力模仿基督，而是让基督的生命自然流露；不是勉强行善，而是支取祂里面那涌流的喜乐。二十五年的路，若有什么秘诀，就是学习越来越不靠自己，越来越住在基督里 — In Christ alone。
被圣灵动员：Mobilization
“但圣灵降临在你们身上，你们就必得着能力…作我的见证。”（徒1:8）
恩典从来不是为了停留在庆典中。那些贺信、贺匾、字画，都在提醒我们：恩典是动员令，不是退休证。

谢谢Robbin传道关于恩典25年的诸多宣传设计
从G25委员会的成立，到山上祷告的发起，从见证的征集，到禁食祷告的坚持——每一步都是圣灵动员的痕迹。祂动员Rebecca、Lixin、Crystal、Robbin、Dean长老组成委员会；祂动员Sally传道带领山上祷告和带领见证集的编辑出版；祂动员四十多位弟兄姊妹写下见证；祂动员全教会参与四十天禁食祷告。
Mobilization——被圣灵动员，活出群体的见证。这正是神给基督六家下一个二十五年的方向。我们不是要建立更宏伟的建筑，而是要成为更鲜活的身体；不是要策划更精彩的活动，而是要活出更真实的见证。
庆典当天的信息《在恩典中定向奔跑》，如今成为我们继续前行的指南针：
A：对准神——继续在每次聚会、每次祷告、每次服事中寻求祂的心意；
I：与基督整合——继续让祂的生命透过我们这群不完美的人流露出来；
M：被圣灵动员——继续敏感于圣灵的感动，去祂要我们去的地方，做祂要我们做的事。

4月5日上山祷告时的信息
结语：向着标杆直跑
五十篇见证的最后一页，不是句号，而是破折号——连接过去与未来，恩典与奔跑。
二十五年前，神把一小群人聚集在这里；二十五年间，祂用恩手托住我们经过高山低谷；今天，祂说：跑吧，继续跑吧！
不是漫无目的地奔跑，而是在恩典中定向奔跑——对准那永不改变的神，整合于那永活的主，被那永在的圣灵动员。
内聚于基督，外散到世界！让我们带着这五十个故事，带着二十五年的恩典记忆，带着从各地而来的祝福与托付，继续奔跑！
跑向那更需要见证的职场，跑向那不再隐藏的网络，跑向那更需要关怀的社区，跑向那更需要真光的世界，跑向神为我们预备那更荣耀的下一个二十五年！
“我们既有这许多的见证人，如同云彩围着我们，就当放下各样的重担，脱去容易缠累我们的罪，存心忍耐，奔那摆在我们前头的路程。”（来12:1）
在恩典中，
定向奔跑！
"""



# Convert Bible references in the text (e.g., '罗马书 1:17' to '罗马书 1章17節')
TEXT = convert_bible_reference(TEXT)
TEXT = clean_text(TEXT)

# Split the text into paragraphs
paragraphs = [p.strip() for p in re.split(r'\n{2,}', TEXT.strip()) if p.strip()]
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
FIRST_VOICE = "zh-CN-XiaoxiaoNeural"  # Second voice (main content)
SECOND_VOICE = "zh-CN-YunyangNeural"  # First voice (introduction)
#FIRST_VOICE = "zh-CN-YunyangNeural"  # First voice (introduction)
#SECOND_VOICE = "zh-CN-XiaoxiaoNeural"  # Second voice (main content)
#SECOND_VOICE = "zh-HK-WanLungNeural"  # First voice (introduction)
#FIRST_VOICE = "zh-HK-HiuGaaiNeural"  # Second voice (main content)
first_line = "Bread_Audio"

from datetime import datetime
import re

# Generate filename dynamically
# Try to find date in text like "12月15日" or "12/15"
date_match = re.search(r"(\d{1,2})月(\d{1,2})日", TEXT)
if date_match:
    m, d = date_match.groups()
    current_year = datetime.now().year
    # Handle year boundary if needed (e.g. text is for next year), but simple current year is safe for now
    date_str = f"{current_year}{int(m):02d}{int(d):02d}"
else:
    # Fallback to today
    date_str = datetime.today().strftime("%Y%m%d")

OUTPUT_DIR = os.path.join(os.getcwd(), "output")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
OUTPUT_PATH = os.path.join(OUTPUT_DIR, f"bread_{date_str}_edge.mp3")
TEMP_DIR = OUTPUT_DIR + os.sep  # For temp files
TEMP_FIRST = os.path.join(OUTPUT_DIR, "temp_first_bread.mp3")
TEMP_SECOND = os.path.join(OUTPUT_DIR, "temp_second_bread.mp3")

async def generate_audio(text, voice, output_file):
    print(f"DEBUG: Text to read: {text[:100]}...")
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=TTS_RATE)
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

    # Add Background Music (Optional)
    if ENABLE_BGM:
        print(f"🎵 Mixing Background Music (Vol={BGM_VOLUME}dB, Intro={BGM_INTRO_DELAY}ms)...")
        combined_audio = audio_mixer.mix_bgm(
            combined_audio, 
            specific_filename=BGM_FILE,
            volume_db=BGM_VOLUME,
            intro_delay_ms=BGM_INTRO_DELAY
        )

    combined_audio.export(OUTPUT_PATH, format="mp3")
    print(f"✅ Combined audio saved: {OUTPUT_PATH}")

if __name__ == "__main__":
    # Custom handling for -? (which argparse doesn't support natively as a flag often)
    if "-?" in sys.argv:
        print(f"Usage: python {sys.argv[0]} [--bgm] [--rate RATE] [--bgm-volume VOL] [--bgm-intro MS] [--help] [--version]")
        print("\nOptions:")
        print("  -h, --help           Show this help message and exit")
        print("  -?,                  Show this help message and exit")
        print("  --bgm                Enable background music")
        print("  --rate RATE          TTS Speech rate (default: +10%)")
        print("  --bgm-volume VOL     BGM volume adjustment in dB (default: -12)")
        print("  --bgm-intro MS       BGM intro delay in ms (default: 4000)")
        print("  --version, -v        Show program version")
        sys.exit(0)

    parser = argparse.ArgumentParser(description="Generate Bread Audio with Edge TTS")
    parser.add_argument("--bgm", action="store_true", help="Enable background music")
    parser.add_argument("--rate", type=str, default="+10%", help="TTS Speech rate (e.g. +10%%)")
    parser.add_argument("--bgm-volume", type=int, default=-12, help="BGM volume adjustment in dB")
    parser.add_argument("--bgm-intro", type=int, default=4000, help="BGM intro delay in ms")
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {VERSION}")
    
    args = parser.parse_args()
    
    # Update global config based on CLI
    if args.bgm:
        ENABLE_BGM = True
    
    TTS_RATE = args.rate
    BGM_VOLUME = args.bgm_volume
    BGM_INTRO_DELAY = args.bgm_intro

    asyncio.run(main())
