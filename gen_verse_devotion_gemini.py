# gen_verse_devotion_gemini.py
# Google Gemini TTS – Multi-voice, works with Google Cloud credentials

import io
import os
import re
from google.cloud import texttospeech
from pydub import AudioSegment

from bible_parser import convert_bible_reference
from date_parser import convert_dates_in_text
from text_cleaner import clean_text
import filename_parser
import re
from datetime import datetime
import argparse
import sys
import time
import io
import os
import re
from google.cloud import texttospeech
from google.api_core import exceptions
from pydub import AudioSegment
import audio_mixer
from bible_parser import convert_bible_reference
from date_parser import convert_dates_in_text
from text_cleaner import clean_text
import filename_parser
from datetime import datetime

# CLI Args
parser = argparse.ArgumentParser()
parser.add_argument("--input", "-i", type=str, help="Input text file")
parser.add_argument("--prefix", type=str, default=None, help="Filename prefix")
parser.add_argument("--bgm", action="store_true", help="Enable background music (Default: False)")
parser.add_argument("--bgm-track", type=str, default="AmazingGrace.MP3", help="Specific BGM filename (Default: AmazingGrace.MP3)")
parser.add_argument("--bgm-volume", type=int, default=-20, help="BGM volume adjustment in dB (Default: -20)")
parser.add_argument("--bgm-intro", type=int, default=4000, help="BGM intro delay in ms (Default: 4000)")
parser.add_argument("--rate", type=str, default="+0%", help="TTS Speech rate (e.g. +10%%)")
parser.add_argument("--speed", type=str, dest="rate", help="Alias for --rate")

args, unknown = parser.parse_known_args()
CLI_PREFIX = args.prefix
ENABLE_BGM = args.bgm
BGM_FILE = args.bgm_track
BGM_VOLUME = args.bgm_volume
BGM_INTRO_DELAY = args.bgm_intro

# Parse rate (e.g., "+10%" -> 1.1)
def parse_speed(speed_str):
    if not speed_str:
        return 1.0
    try:
        # Handle percentage "+10%" or "-10%"
        if "%" in speed_str:
            val = float(speed_str.replace("%", ""))
            return 1.0 + (val / 100.0)
        # Handle direct float "1.1"
        return float(speed_str)
    except Exception as e:
        print(f"⚠️ Invalid speed format '{speed_str}', using default 1.0. Error: {e}")
        return 1.0

SPEAKING_RATE = parse_speed(args.rate)
print(f"TTS Rate: {args.rate} -> {SPEAKING_RATE}x")

# ... [Text input logic] ... (Existing code)
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

# ... [Auth check] ... (Existing code)
# Verify credentials exist
if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    print("⚠️ WARNING: GOOGLE_APPLICATION_CREDENTIALS not set. Ensure you have authenticated via gcloud or set the env var.")

# ... [Filename logic] ... (Existing code)
TEXT = clean_text(TEXT)
first_line = TEXT.strip().split('\n')[0]
date_match = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", first_line)
if date_match:
    m, d, y = date_match.groups()
    date_str = f"{y}-{int(m):02d}-{int(d):02d}"
else:
    date_match = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", first_line)
    if date_match:
        y, m, d = date_match.groups()
        date_str = f"{y}-{int(m):02d}-{int(d):02d}"
    else:
        date_str = datetime.today().strftime("%Y-%m-%d")

verse_ref = filename_parser.extract_verse_from_text(TEXT)
extracted_prefix = CLI_PREFIX if CLI_PREFIX else filename_parser.extract_filename_prefix(TEXT)

filename = filename_parser.generate_filename_v2(
    title=first_line,
    date=date_str, 
    prefix=extracted_prefix,
    ext=".mp3"
).replace(".mp3", "_gemini.mp3")

# Handle BGM filename modification
if ENABLE_BGM:
    filename = filename.replace(".mp3", "_bgm.mp3")

OUTPUT_DIR = os.path.join(os.getcwd(), "output")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
OUTPUT_PATH = os.path.join(OUTPUT_DIR, filename)
print(f"Target Output: {OUTPUT_PATH}")

TEXT = convert_bible_reference(TEXT)
TEXT = convert_dates_in_text(TEXT)
TEXT = clean_text(TEXT)

paragraphs = [p.strip() for p in re.split(r'\n{2,}', TEXT.strip()) if p.strip()]

# Supported Gemini/Google Voices
voices = ["Charon", "Kore", "Fenrir", "Aoede", "Puck"]
LANGUAGE_CODE = "cmn-CN"
MODEL_NAME = "gemini-2.5-pro-tts"
_TTS_CLIENT = None

def get_tts_client():
    global _TTS_CLIENT
    if _TTS_CLIENT: return _TTS_CLIENT
    try:
        _TTS_CLIENT = texttospeech.TextToSpeechClient()
        return _TTS_CLIENT
    except Exception as e:
        print(f"⚠️ Default auth failed: {e}")
        print("🔄 Attempting to use gcloud access token...")
        try:
            import subprocess
            import google.oauth2.credentials
            from google.api_core.client_options import ClientOptions
            result = subprocess.run(["zsh", "-l", "-c", "gcloud auth print-access-token"], capture_output=True, text=True, check=True)
            token = result.stdout.strip()
            project_result = subprocess.run(["zsh", "-l", "-c", "gcloud config get-value project"], capture_output=True, text=True, check=True)
            project_id = project_result.stdout.strip()
            if not token: raise ValueError("Empty token received from gcloud")
            creds = google.oauth2.credentials.Credentials(token=token)
            client_options = ClientOptions(quota_project_id=project_id) if project_id else None
            _TTS_CLIENT = texttospeech.TextToSpeechClient(credentials=creds, client_options=client_options)
            print(f"✅ Successfully authenticated using gcloud access token (Project: {project_id}).")
            return _TTS_CLIENT
        except Exception as token_error:
            print(f"❌ Failed to get gcloud token/project: {token_error}")
            raise e

def chunk_text(text: str, max_len: int = 400) -> list[str]:
    if len(text) <= max_len: return [text]
    chunks = []
    current_chunk = ""
    parts = re.split(r'([。！？；!.?\n]+)', text)
    for part in parts:
        if len(current_chunk) + len(part) < max_len: current_chunk += part
        else:
            if current_chunk: chunks.append(current_chunk)
            current_chunk = part
    if current_chunk: chunks.append(current_chunk)
    return chunks

def speak(text: str, voice: str, style_prompt: str = None) -> AudioSegment:
    print(f"DEBUG: Text to read: {text[:100]}...")
    client = get_tts_client()
    
    # Retry logic for Cancelled/Timeout errors
    max_retries = 3
    for attempt in range(max_retries):
        try:
            synthesis_input = texttospeech.SynthesisInput(text=text)
            voice_params = texttospeech.VoiceSelectionParams(language_code=LANGUAGE_CODE, name=voice, model_name=MODEL_NAME)
            audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3, speaking_rate=SPEAKING_RATE)
            
            request = texttospeech.SynthesizeSpeechRequest(input=synthesis_input, voice=voice_params, audio_config=audio_config)
            
            if style_prompt:
                try:
                    synthesis_input = texttospeech.SynthesisInput(text=text, prompt=style_prompt)
                    request.input = synthesis_input
                except TypeError:
                    print(f"      [DEBUG] 'prompt' arg not supported in this client version.")

            print(f"      [DEBUG] Sending TTS request (Attempt {attempt+1})...")
            # Added timeout to prevent hanging indefinitely
            response = client.synthesize_speech(request=request, timeout=30.0)
            print(f"      [DEBUG] Received TTS response ({len(response.audio_content)} bytes).")
            return AudioSegment.from_mp3(io.BytesIO(response.audio_content))

        except (exceptions.Cancelled, exceptions.DeadlineExceeded, exceptions.ServiceUnavailable) as retry_err:
            print(f"⚠️ API Error ({type(retry_err).__name__}): {retry_err}. Retrying {attempt+1}/{max_retries}...")
            time.sleep(2)
            if attempt == max_retries - 1:
                print("❌ Max retries reached. Attempting fallback to standard voice...")
                try:
                    fallback_voice = "cmn-CN-Wavenet-C" 
                    if voice in ["Kore", "Aoede"]: fallback_voice = "cmn-CN-Wavenet-A"
                    
                    fallback_params = texttospeech.VoiceSelectionParams(language_code=LANGUAGE_CODE, name=fallback_voice)
                    request.voice = fallback_params
                    request.input = texttospeech.SynthesisInput(text=text) # No prompt
                    
                    print(f"      [DEBUG] Sending Fallback TTS request...")
                    response = client.synthesize_speech(request=request, timeout=30.0)
                    print(f"   ✅ Fallback success (Used {fallback_voice}).")
                    return AudioSegment.from_mp3(io.BytesIO(response.audio_content))
                except Exception as e3:
                    print(f"   ❌ Fallback failed: {e3}")
                    raise retry_err

        except Exception as e:
            if "sensitive or harmful content" in str(e) or "400" in str(e):
                print(f"⚠️ Safety filter triggered for voice {voice}. Auto-removing style prompt...")
                try:
                     request.input = texttospeech.SynthesisInput(text=text) # No prompt
                     print(f"      [DEBUG] Sending Safety-Retry TTS request...")
                     response = client.synthesize_speech(request=request, timeout=30.0)
                     return AudioSegment.from_mp3(io.BytesIO(response.audio_content))
                except Exception as e2:
                    print(f"❌ Retry failed: {e2}")
                    raise e
            raise e

# ... [Section logic] ... (Existing code)
# ... [Main loop] ... (Existing code)

if len(paragraphs) < 5:
    logical_sections = [[p] for p in paragraphs]
else:
    logical_sections = [
        [paragraphs[0]],              # Intro
        [paragraphs[1]],              # Scripture 1
        [paragraphs[2]],              # Scripture 2
        paragraphs[3:-1],             # Main Body
        [paragraphs[-1]]              # Prayer
    ]

num_sections = len(logical_sections)
section_titles = ["Intro", "Scripture 1", "Scripture 2", "Main Body", "Prayer"]
section_styles = [
    "Speak with a clear, professional, announcer-like tone for a title introduction.",
    "Speak with a solemn, reverent, and slow pace, suitable for reading Holy Scripture.",
    "Speak with a solemn, reverent, and slow pace, suitable for reading Holy Scripture.",
    "Speak with a warm, engaging, and personal storytelling tone, like a friend sharing wisdom.",
    "Speak with a humble, quiet, and earnest tone, suitable for prayer.",
]

print(f"Processing {num_sections} logical sections...")

final_segments = []
global_p_index = 0

for i, section_paras in enumerate(logical_sections):
    title = section_titles[i] if i < len(section_titles) else f"Section {i+1}"
    style_prompt = section_styles[i] if i < len(section_styles) else None
    
    print(f"--- Section {i+1}: {title} ---")
    if style_prompt:
        print(f"  [Style Prompt]: {style_prompt}")
    
    section_audio = AudioSegment.empty()
    silence_between_paras = AudioSegment.silent(duration=700, frame_rate=24000)

    for j, para in enumerate(section_paras):
        voice = voices[global_p_index % len(voices)]
        print(f"  > Part {i+1}.{j+1} - {voice} ({len(para)} chars)")
        global_p_index += 1
        
        current_segment = AudioSegment.empty()
        if len(para) > 1000:
            chunks = chunk_text(para, 1000)
            print(f"    Split into {len(chunks)} chunks due to length.")
            for chunk in chunks:
                if chunk.strip():
                    current_segment += speak(chunk, voice, style_prompt)
        else:
            current_segment = speak(para, voice, style_prompt)
            
        section_audio += current_segment
        if j < len(section_paras) - 1:
            section_audio += silence_between_paras
            
    final_segments.append(section_audio)

final = AudioSegment.empty()
frame_rate = final_segments[0].frame_rate if final_segments else 24000
silence = AudioSegment.silent(duration=1000, frame_rate=frame_rate)

for i, seg in enumerate(final_segments):
    final += seg
    if i < len(final_segments) - 1:
        final += silence

# Ensure consistent frame rate before mixing/exporting
final = final.set_frame_rate(24000)

# Add BGM
if ENABLE_BGM:
    print(f"🎵 Mixing Background Music: {BGM_FILE} (Volume: {BGM_VOLUME}dB, Intro: {BGM_INTRO_DELAY}ms)")
    final = audio_mixer.mix_bgm(final, specific_filename=BGM_FILE, volume_db=BGM_VOLUME, intro_delay_ms=BGM_INTRO_DELAY)

# Metadata extraction
PRODUCER = "VI AI Foundation"
TITLE = TEXT.strip().split('\n')[0]
ALBUM = "Devotion"
bgm_info = os.path.basename(BGM_FILE) if ENABLE_BGM else "None"
COMMENTS = f"Verse: {verse_ref}; BGM: {bgm_info}"

final.export(OUTPUT_PATH, format="mp3", bitrate="192k", tags={
    'title': TITLE, 
    'artist': PRODUCER,
    'album': ALBUM,
    'comments': COMMENTS
})
print(f"Success! Saved → {OUTPUT_PATH}")
