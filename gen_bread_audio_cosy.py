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
import filename_parser
import audio_mixer

# CLI Args
if "-?" in sys.argv:
    print(f"Usage: python {sys.argv[0]} [--input FILE] [--prefix PREFIX] [--bgm] [--bgm-track TRACK] [--bgm-volume VOL] [--bgm-intro MS] [--help]")
    print("\nOptions:")
    print("  --input FILE, -i     Text file to read input from")
    print("  --prefix PREFIX      Filename prefix (overrides 'FilenamePrefix' in text)")
    print("  --bgm                Enable background music (Default: False)")
    print("  --bgm-track TRACK    Specific BGM filename (Default: AmazingGrace.MP3)")
    print("  --bgm-volume VOL     BGM volume adjustment in dB (Default: -20)")
    print("  --bgm-intro MS       BGM intro delay in ms (Default: 4000)")
    print("  --help, -h           Show this help")
    print("\n  (Note: You can also add 'FilenamePrefix: <Prefix>' in the input TEXT)")
    sys.exit(0)

parser = argparse.ArgumentParser()
parser.add_argument("--input", "-i", type=str, help="Input text file")
parser.add_argument("--prefix", type=str, default=None, help="Filename prefix")
parser.add_argument("--bgm", action="store_true", help="Enable background music (Default: False)")
parser.add_argument("--bgm-track", type=str, default="AmazingGrace.MP3", help="Specific BGM filename (Default: AmazingGrace.MP3)")
parser.add_argument("--bgm-volume", type=int, default=-20, help="BGM volume adjustment in dB (Default: -20)")
parser.add_argument("--bgm-intro", type=int, default=4000, help="BGM intro delay in ms (Default: 4000)")

args, unknown = parser.parse_known_args()
CLI_PREFIX = args.prefix
ENABLE_BGM = args.bgm
BGM_FILE = args.bgm_track
BGM_VOLUME = args.bgm_volume
BGM_INTRO_DELAY = args.bgm_intro


# 1. Try --input argument
if args.input:
    print(f"Reading text from file: {args.input}")
    with open(args.input, "r", encoding="utf-8") as f:
        TEXT = f.read()

# 2. Try Stdin (Piped)
elif not sys.stdin.isatty():
    print("Reading text from Stdin...")
    TEXT = sys.stdin.read()

# 3. Fallback
else:
    TEXT = """
“　神爱世人，甚至将他的独生子赐给他们，叫一切信他的，不至灭亡，反得永生。因为　神差他的儿子降世，不是要定世人的罪，乃是要叫世人因他得救。信他的人，不被定罪；不信的人，罪已经定了，因为他不信　神独生子的名。
(约翰福音 3:16-18)
"""
靈晨靈糧12月15日吴静师母：<“恩典25”第49篇：40天禁食祷告中经历神的恩典>

借着教会这次40天禁食祷告活动，我也想分享一段我刚刚经历的40多天的回国旅程。这段经历让我深刻体会到两点：

第一，感谢神垂听祷告，让看似不可能的道路变得平坦；
第二，人生充满劳苦愁烦，唯有神是我们唯一的拯救。
自从父亲确诊胃癌后，我们全家就陷入了寝食难安的状态。那时我和姐姐每天越洋通话，商量对策，心里却充满了焦急与无助。网上查遍了资料，不仅没有得到安慰，反而徒增恐惧。在那段心力交瘁的日子里，我意识到：唯有神才是唯一的拯救
。也正是那时，教会的长辈和弟兄姊妹们开始为我父亲代祷，大家的支持让我的心逐渐有了平安。

在这40天的祷告旅程中，我亲眼见证了神的恩典带领我们度过每一个难关。

首先是父亲的肺部穿刺检查。因为父亲已做过胃部手术，后续面临化疗放疗，如果肺部发现问题，将严重影响治疗方案。等待结果的过程极其煎熬，但我记得全教会的弟兄姊妹都在为此迫切祷告。感谢主，结果出来确认为良性！这让我们心里的
石头落了地，只需定期复查，便可专心应对胃部治疗。

然而，术后的恢复并不顺利。父亲进食困难，伴随严重的咳嗽和呕吐。视频里看到他痛苦的样子，听到姐姐描述只能无奈地带父亲反复就医、打营养针，我心如刀绞。我开始动摇：家人如此需要我，我真的不回去吗？但理智又告诉我回国的风险
——我已经八年没有回国，之前的签证曾被行政审查（Check），如今形势不明，一旦被卡住两三个月，我的工作、这边的孩子该怎么办？

在两难之间，我选择将这一切带到祷告中。经过衡量与交托，我决定凭信心踏上归途。奇妙的是，从决定回国那一刻起，办理签证、拿到护照，再到过海关顺利返美，每一个环节都有大家的祷告托住，一切顺利得出乎意料。我知道，这若不是神
的保守，绝无可能。

在得知父亲生病之初，我脑海里曾闪过一句话：“关关难过，关关过。”抗癌是一场漫长的战役。有一天我和妈妈聊天，她感慨地说：“你们小时候，我盼着你们毕业我就轻松了；后来想着你们结婚了我就不操心了；再后来外婆生病，我两头跑，>以为送走了外婆事情就少了，结果我自己血糖又出了问题。本想养好身体过年去旅游，现在你爸又病了……”

妈妈的话让我深感心酸。是啊，世上的劳苦愁烦永无止境，我们身为凡人，总有操不完的心，也有无法逃避的软弱。这让我更加确信，唯有在神里面，才有真正的依靠和最终的拯救。

这次回国，最让我欣慰的是看到妈妈把圣经带回了房间，她说要重新开始读经。看着国内忙碌的生活——忙着生存，忙着挣钱，在那样快节奏的环境中坚持信仰确实不易。虽然几次想给姐姐们传福音未能深入，但我愿意恒切祷告，求神亲自开路，
愿他们在经历神的恩手后，能得着那份真正的安稳，享受神所赐的生命。
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

basename = f"Bread_{date_str}_cosy.mp3"
if extracted_prefix:
    filename = f"{extracted_prefix}_{basename}"
else:
    filename = basename

if ENABLE_BGM and BGM_FILE:
    bgm_base = os.path.splitext(os.path.basename(BGM_FILE))[0]
    filename = filename.replace(".mp3", f"_bgm_{bgm_base}.mp3")

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

# Add Background Music (Optional)
if ENABLE_BGM:
    print(f"🎵 Mixing Background Music (Vol={BGM_VOLUME}dB, Intro={BGM_INTRO_DELAY}ms)...")
    final = audio_mixer.mix_bgm(
        final, 
        specific_filename=BGM_FILE,
        volume_db=BGM_VOLUME,
        intro_delay_ms=BGM_INTRO_DELAY
    )

# Metadata extraction
PRODUCER = "VI AI Foundation"
TITLE = TEXT.strip().split('\n')[0]

final.export(OUTPUT_PATH, format="mp3", bitrate="192k", tags={'title': TITLE, 'artist': PRODUCER})
print(f"Success! Saved → {OUTPUT_PATH}")
