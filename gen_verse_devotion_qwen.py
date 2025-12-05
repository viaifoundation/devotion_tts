
# gen_verse_devotion_qwen.py
# Real Qwen3-TTS – 5 voices, works perfectly

import io
import os
import requests
import dashscope
from dashscope.audio.qwen_tts import SpeechSynthesizer
from pydub import AudioSegment

from bible_parser import convert_bible_reference
from date_parser import convert_dates_in_text
from text_cleaner import remove_space_before_god

dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
if not dashscope.api_key:
    raise ValueError("Please set DASHSCOPE_API_KEY in ~/.secrets")

OUTPUT_PATH = "/Users/mhuo/Downloads/verse_qwen.mp3"



TEXT = """
彼此相爱 12/5/2025

天使回答说：“圣灵要临到你身上，至高者的能力要荫庇你，因此所要生的圣者必称为神的儿子（或译：所要生的，必称为圣，称为神的儿子）。
(路加福音 1:35 和合本)
天使回答：“圣灵要临到你，至高者的能力要覆庇你，因此那将要出生的圣者，必称为神的儿子。
(路加福音 1:35 新译本)
他要作雅各家的王，直到永远；他的国也没有穷尽。”
(路加福音 1:33 和合本)
他要作王统治雅各家，直到永远，他的国没有穷尽。”
(路加福音 1:33 新译本)
前行后随的众人喊着说：
和散那（原有求救的意思，在此是称颂的话）归于大卫的子孙！
奉主名来的是应当称颂的！
高高在上和散那！
(马太福音 21:9 和合本)
前呼后拥的群众喊叫着：
“‘和散那’归于大卫的子孙，
奉主名来的是应当称颂的，高天之上当唱‘和散那’。”
(马太福音 21:9 新译本)

神爱我们的心，我们也知道也信。
神就是爱；住在爱里面的，就是住在神里面，神也住在他里面。这样，爱在我们里面得以完全，我们就可以在审判的日子坦然无惧。因为他如何，我们在这世上也如何。爱里没有惧怕；爱既完全，就把惧怕除去。因为惧怕里含着刑罚，惧怕的人在爱里未得完全。我们爱，因为神先爱我们。
(约翰一书 4:16-19 和合本)
我们爱，因为神先爱我们。
(约翰壹书 4:19 新译本)
我们爱，是因为他先爱了我们。
(约翰一书 4:19 标准译本)

彼此相爱

关于我们彼此相爱，耶稣讲过两个要点。第一，我们若有彼此相爱的心，众人因此就认出我们是他的门徒（约翰福音13:35）；其次，我们在神里面合而为一，会使世人知道神差了他来到世上（约翰福音 17:23）。

耶稣说，通过追随他的人彼此相爱，世人将会知道他已经来了。我们应当如此相爱，好让不信耶稣的人感到惊讶和好奇，并想进一步了解他。 

耶稣洞悉这个世界将充满愤怒、纷争和冲突。正因如此，我们更应该像神爱我们一样去爱他人。爱他人能向世人展现，先爱我们的神是多么伟大和慈爱。

耶稣复活多年后，使徒约翰给耶稣的信徒写了三封短信。在第一封中，他谆谆告诫他们如何去爱，以及爱的重要性。约翰写道：“……爱是从神来的……神既是这样爱我们，我们也当彼此相爱……我们爱，因为神先爱我们。” （约翰一书4:7、4:11、4:19） 

他甚至进一步说：“人若说‘我爱神’，却恨他的弟兄，就是说谎话的；不爱他所看见的弟兄，就不能爱没有看见的神。” （约翰一书 4:20） 

在这关键上没有其他捷径可走。约翰对此说得相当明确，我们彼此相爱就是神的爱在我们里面的证据。所以，如果我们自称爱神，就应该致力于彼此相爱。

当你思考今天的经文时，问问自己：今天我需要向我生活中的哪些人表达爱？是否有人需要我去原谅？我可以用什么方式去爱主内的弟兄姐妹们？

祷告
神啊，感谢你向史上每一代的人都展现了同样无条件的爱。你一直邀请我们来与你亲近。这是多么美好的恩赐！今天，无论我面对什么，帮助我像你爱我一般去爱别人。让我的生命成为你的爱在世上运行的见证。奉耶稣名求，阿们。
"""

TEXT = convert_bible_reference(TEXT)
TEXT = convert_dates_in_text(TEXT)
TEXT = remove_space_before_god(TEXT)

paragraphs = [p.strip() for p in TEXT.strip().split("\n\n") if p.strip()]
# Supported Qwen-TTS voices
voices = ["Cherry", "Serena", "Ethan", "Chelsie", "Cherry"]

def chunk_text(text: str, max_len: int = 400) -> list[str]:
    if len(text) <= max_len:
        return [text]
    import re
    chunks = []
    current_chunk = ""
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

def speak(text: str, voice: str) -> AudioSegment:
    resp = SpeechSynthesizer.call(
        model="qwen-tts",
        text=text,
        voice=voice,
        format="wav",
        sample_rate=24000
    )
    if resp.status_code != 200:
        raise Exception(f"API Error: {resp.message}")
    
    # Qwen-TTS returns a URL, we need to download it
    audio_url = resp.output.audio["url"]
    audio_data = requests.get(audio_url).content
    return AudioSegment.from_wav(io.BytesIO(audio_data))

print("Generating 5 parts...")
segments = []
for i, para in enumerate(paragraphs):
    print(f"Part {i+1}/5 → {voices[i % len(voices)]}")
    
    # Check length
    if len(para) > 450:
        chunks = chunk_text(para, 400)
        print(f"  Split into {len(chunks)} chunks due to length.")
        para_segment = AudioSegment.empty()
        for chunk in chunks:
            if chunk.strip():
                para_segment += speak(chunk, voices[i % len(voices)])
        segments.append(para_segment)
    else:
        segments.append(speak(para, voices[i % len(voices)]))

final = AudioSegment.empty()
# ... (rest of concatenation)
silence = AudioSegment.silent(700)
for i, seg in enumerate(segments):
    final += seg
    if i < len(segments) - 1:
        final += silence
final.export(OUTPUT_PATH, format="mp3", bitrate="192k")
print(f"Success! Saved → {OUTPUT_PATH}")