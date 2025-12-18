# gen_bread_audio_cosy.py
# Local offline CosyVoice-300M-Instruct (via CosyVoice repo)

import torch
import numpy as np
import sys
import os
import re
import warnings

# Silence noisy libraries
warnings.filterwarnings("ignore", category=FutureWarning, module="diffusers")
warnings.filterwarnings("ignore", category=UserWarning, module="lightning")

from pydub import AudioSegment

# Setup path to find CosyVoice (sibling directory)
# and its third_party dependencies (Matcha-TTS)
COSYVOICE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../CosyVoice"))
MATCHA_PATH = os.path.join(COSYVOICE_PATH, "third_party", "Matcha-TTS")

if os.path.exists(COSYVOICE_PATH):
    sys.path.append(COSYVOICE_PATH)
    # Also add Matcha-TTS to path as CosyVoice imports 'matcha' directly
    if os.path.exists(MATCHA_PATH):
        sys.path.append(MATCHA_PATH)
    else:
        print(f"⚠️ Warning: Matcha-TTS not found at {MATCHA_PATH}")
        print("Run: cd ../CosyVoice && git submodule update --init --recursive")
else:
    print(f"⚠️ Warning: CosyVoice path not found at {COSYVOICE_PATH}")
    print("Please clone it: git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git ../CosyVoice")

try:
    from cosyvoice.cli.cosyvoice import CosyVoice
    from cosyvoice.utils.file_utils import load_wav
except ImportError as e:
    print(f"❌ Failed to import CosyVoice: {e}")
    print(f"Ensure you have cloned the repo to {COSYVOICE_PATH} and installed its requirements.")
    sys.exit(1)

from bible_parser import convert_bible_reference
from bible_parser import convert_bible_reference
from text_cleaner import clean_text
from datetime import datetime
import argparse

# CLI Args
if "-?" in sys.argv:
    print(f"Usage: python {sys.argv[0]} [--prefix PREFIX] [--help]")
    print("Options:")
    print("  --prefix PREFIX      Filename prefix (overrides 'FilenamePrefix' in text)")
    print("  --help, -h           Show this help")
    print("\n  (Note: You can also add 'FilenamePrefix: <Prefix>' in the input TEXT)")
    sys.exit(0)

parser = argparse.ArgumentParser()
parser.add_argument("--prefix", type=str, default=None, help="Filename prefix")
args, unknown = parser.parse_known_args()
CLI_PREFIX = args.prefix

TEXT = """
灵晨灵粮12月3日罗丽芳姊妹：<“恩典25”第48篇：打通信主的“任督二脉”>
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

# Load model (uses cached files – no download)
print("Loading CosyVoice-300M-Instruct (local offline)...")
try:
    use_fp16 = torch.cuda.is_available()
    print(f"Loading CosyVoice-300M-Instruct... [CUDA={use_fp16}, FP16={use_fp16}]")
    cosyvoice = CosyVoice('iic/CosyVoice-300M-Instruct', fp16=use_fp16)
except Exception as e:
    print(f"❌ Error loading model: {e}")
    print("Ensure you have 'modelscope' installed and dependencies met.")
    sys.exit(1)

OUTPUT_DIR = os.path.join(os.getcwd(), "output")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
# Generate filename dynamically
# 1. Try to find date in text like "12月15日" or "12/15"
TEXT = clean_text(TEXT)
date_match = re.search(r"(\d{1,2})月(\d{1,2})日", TEXT)
if date_match:
    m, d = date_match.groups()
    current_year = datetime.now().year
    date_str = f"{current_year}{int(m):02d}{int(d):02d}"
else:
    # 2. Fallback to script modification time
    try:
        mod_timestamp = os.path.getmtime(__file__)
        date_str = datetime.fromtimestamp(mod_timestamp).strftime("%Y%m%d")
        print(f"⚠️ Date not found in text. Using script modification date: {date_str}")
    except:
        # 3. Fallback to today
        date_str = datetime.today().strftime("%Y%m%d")

import filename_parser
extracted_prefix = CLI_PREFIX if CLI_PREFIX else filename_parser.extract_filename_prefix(TEXT)

basename = f"Bread_{date_str}_spark.mp3"
if extracted_prefix:
    filename = f"{extracted_prefix}_{basename}"
else:
    filename = basename

OUTPUT_PATH = os.path.join(OUTPUT_DIR, filename)



TEXT = convert_bible_reference(TEXT)
TEXT = clean_text(TEXT)

paragraphs = [p.strip() for p in re.split(r'\n{2,}', TEXT.strip()) if p.strip()]
intro = paragraphs[0] if paragraphs else ""
main = "\n".join(paragraphs[1:]) if len(paragraphs) > 1 else ""

def speak(text: str, voice: str = "中文女") -> AudioSegment:
    print(f"DEBUG: Text to read: {text[:100]}...")
    print(f"   Synthesizing ({len(text)} chars) with {voice}...")
    output_gen = cosyvoice.inference_sft(text, voice)
    
    final_audio = AudioSegment.empty()
    # Iterate through the generator
    for item in output_gen:
        if 'tts_speech' in item:
            audio_np = item['tts_speech'].numpy()
            audio_int16 = (audio_np * 32767).astype(np.int16)
            segment = AudioSegment(
                audio_int16.tobytes(),
                frame_rate=22050, 
                sample_width=2,
                channels=1
            )
            final_audio += segment
    return final_audio

print("Generating introduction (中文女)…")
seg_intro = speak(intro, "中文女")

print("Generating main content (中文男)…")
seg_main = speak(main, "中文男")

final = seg_intro + AudioSegment.silent(duration=600) + seg_main
final = final.set_frame_rate(24000)

# Metadata extraction
PRODUCER = "VI AI Foundation"
TITLE = TEXT.strip().split('\n')[0]

final.export(OUTPUT_PATH, format="mp3", bitrate="192k", tags={'title': TITLE, 'artist': PRODUCER})
print(f"Success! Saved → {OUTPUT_PATH}")