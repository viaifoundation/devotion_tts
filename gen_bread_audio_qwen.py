import io
import os
import requests
import dashscope
from dashscope.audio.qwen_tts import SpeechSynthesizer
from pydub import AudioSegment

from bible_parser import convert_bible_reference
from text_cleaner import remove_space_before_god

# Load API key from ~/.secrets (you already set this)
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
if not dashscope.api_key:
    raise ValueError("Please set DASHSCOPE_API_KEY in ~/.secrets")

OUTPUT_DIR = os.getcwd()
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "bread_qwen.mp3")

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

TEXT = convert_bible_reference(TEXT)
TEXT = remove_space_before_god(TEXT)

paragraphs = [p.strip() for p in TEXT.strip().split("\n") if p.strip()]
intro = paragraphs[0]
main = "\n".join(paragraphs[1:])

def chunk_text(text: str, max_len: int = 450) -> list[str]:
    """Split text into chunks smaller than max_len."""
    if len(text) <= max_len:
        return [text]
    
    chunks = []
    current_chunk = ""
    
    # Simple split by punctuations first
    # This is a basic implementation. For Chinese, we can split by '。', '！', '？', '；', '\n'
    import re
    # Split by common sentence delimiters
    parts = re.split(r'([。！？；!.?\n]+)', text)
    
    for part in parts:
        if len(current_chunk) + len(part) < max_len:
            current_chunk += part
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = part
            
    if current_chunk:
        chunks.append(current_chunk)
        
    return chunks

def speak(text: str, voice: str = "Cherry") -> AudioSegment:
    resp = SpeechSynthesizer.call(
        model="qwen-tts",
        text=text,
        voice=voice,
        format="wav",
        sample_rate=24000
    )
    if resp.status_code != 200:
        raise Exception(f"API Error {resp.status_code}: {resp.message}")
    
    # Qwen-TTS returns a URL, download it
    audio_url = resp.output.audio["url"]
    audio_data = requests.get(audio_url).content
    return AudioSegment.from_wav(io.BytesIO(audio_data))

print("Generating introduction (Cherry)…")
seg_intro = speak(intro, "Cherry")

print("Generating main content (Serena)…") # Hao is not supported, using Serena
# Chunk the main text to fit within 512 char limit
main_chunks = chunk_text(main, 400)
main_segments = []
for i, chunk in enumerate(main_chunks):
    if not chunk.strip():
        continue
    print(f"  Generating chunk {i+1}/{len(main_chunks)} ({len(chunk)} chars)...")
    main_segments.append(speak(chunk, "Serena"))

# Concatenate all main segments
if main_segments:
    seg_main = main_segments[0]
    for seg in main_segments[1:]:
        seg_main += seg
else:
    seg_main = AudioSegment.silent(0)

final = seg_intro + AudioSegment.silent(duration=600, frame_rate=24000) + seg_main
final.export(OUTPUT_PATH, format="mp3", bitrate="192k")
print(f"Success! Saved → {OUTPUT_PATH}")