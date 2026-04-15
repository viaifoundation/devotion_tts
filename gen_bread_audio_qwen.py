import io
import os
import requests
import dashscope
from dashscope.audio.qwen_tts import SpeechSynthesizer
from pydub import AudioSegment
import re

from bible_parser import convert_bible_reference
from bible_parser import convert_bible_reference
from text_cleaner import clean_text_basic, clean_text_for_tts
from datetime import datetime
import argparse
import sys
import filename_parser
import audio_mixer

# CLI Args
if "-?" in sys.argv or "-h" in sys.argv or "--help" in sys.argv:
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


# Load API key from ~/.secrets (you already set this)
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
if not dashscope.api_key:
    raise ValueError("Please set DASHSCOPE_API_KEY in ~/.secrets")

OUTPUT_DIR = os.getcwd()
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

extracted_prefix = CLI_PREFIX if CLI_PREFIX else filename_parser.extract_filename_prefix(TEXT)

basename = f"Bread_{date_str}_qwen.mp3"
if extracted_prefix:
    filename = f"{extracted_prefix}_{basename}"
else:
    filename = basename

if ENABLE_BGM and BGM_FILE:
    bgm_base = os.path.splitext(os.path.basename(BGM_FILE))[0]
    filename = filename.replace(".mp3", f"_bgm_{bgm_base}.mp3")

OUTPUT_PATH = os.path.join(OUTPUT_DIR, filename)



# 2. Final cleaning for display/text output
TEXT = clean_text_basic(TEXT)

paragraphs = [p.strip() for p in re.split(r'\n{2,}', TEXT.strip()) if p.strip()]
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
    # Prepare text specifically for TTS (pronunciation fixes, etc.)
    tts_text = convert_bible_reference(text)
    tts_text = clean_text_for_tts(tts_text)
    
    print(f"DEBUG: Text to read: {tts_text[:100]}...")
    resp = SpeechSynthesizer.call(
        model="qwen-tts",
        text=tts_text,
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