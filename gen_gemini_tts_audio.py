import sys
import argparse
import time
import io
import os
import re
from google.cloud import texttospeech
from google.api_core import exceptions
from pydub import AudioSegment
import audio_mixer
from bible_parser import convert_bible_reference
from text_cleaner import clean_text, clean_text_for_tts
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
    if not speed_str: return 1.0
    try:
        if "%" in speed_str:
            val = float(speed_str.replace("%", ""))
            return 1.0 + (val / 100.0)
        return float(speed_str)
    except Exception as e:
        print(f"⚠️ Invalid speed format '{speed_str}', using default 1.0. Error: {e}")
        return 1.0

SPEAKING_RATE = parse_speed(args.rate)
print(f"TTS Rate: {args.rate} -> {SPEAKING_RATE}x")

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

# Verify credentials exist
if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    print("⚠️ WARNING: GOOGLE_APPLICATION_CREDENTIALS not set. Ensure you have authenticated via gcloud or set the env var.")

TEXT = convert_bible_reference(TEXT)
TEXT = clean_text_for_tts(TEXT)

paragraphs = [p.strip() for p in TEXT.strip().split("\n\n") if p.strip()]
first_paragraphs = [paragraphs[0]] # First paragraph (introduction)
second_paragraphs = paragraphs[1:] # Remaining paragraphs

# Global client cache
_TTS_CLIENT = None
LANGUAGE_CODE = "cmn-CN"
MODEL_NAME = "gemini-2.5-pro-tts"

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

def speak(text: str, voice: str, style_prompt: str = None) -> AudioSegment:
    print(f"DEBUG: Text to read: {text[:100]}...")
    client = get_tts_client()
    
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
                print("❌ Max retries reached. Attempting fallback...")
                try:
                    fallback_voice = "cmn-CN-Wavenet-C" 
                    if voice in ["Kore", "Aoede"]: fallback_voice = "cmn-CN-Wavenet-A"
                    fallback_params = texttospeech.VoiceSelectionParams(language_code=LANGUAGE_CODE, name=fallback_voice)
                    request.voice = fallback_params
                    request.input = texttospeech.SynthesisInput(text=text) # No prompt
                    
                    print(f"      [DEBUG] Sending Fallback TTS request...")
                    response = client.synthesize_speech(request=request, timeout=30.0)
                    print(f"   ✅ Fallback success.")
                    return AudioSegment.from_mp3(io.BytesIO(response.audio_content))
                except Exception:
                    raise retry_err

        except Exception as e:
            if "sensitive or harmful content" in str(e) or "400" in str(e):
                print(f"⚠️ Safety filter triggered. Removing prompt...")
                try:
                     request.input = texttospeech.SynthesisInput(text=text)
                     print(f"      [DEBUG] Sending Safety-Retry TTS request...")
                     response = client.synthesize_speech(request=request, timeout=30.0)
                     return AudioSegment.from_mp3(io.BytesIO(response.audio_content))
                except Exception:
                    raise e
            raise e

# Settings
FIRST_VOICE = "Charon" 
SECOND_VOICE = "Kore" 
FIRST_PROMPT = "Speak in Tianjin dialect with a professional tone, fast pace, and lower tones: "
SECOND_PROMPT = "Speak in Tianjin dialect with a warm, lively tone: "

def main():
    # 1. Output Metadata
    TEXT_CLEAN = clean_text(TEXT)
    first_line = TEXT_CLEAN.strip().split('\n')[0]
    date_match = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", first_line)
    if date_match:
        m, d, y = date_match.groups()
        date_str = f"{y}-{int(m):02d}-{int(d):02d}"
    else:
        date_str = datetime.today().strftime("%Y-%m-%d")

    verse_ref = filename_parser.extract_verse_from_text(TEXT_CLEAN)
    if verse_ref:
        extracted_prefix = CLI_PREFIX if CLI_PREFIX else filename_parser.extract_filename_prefix(TEXT_CLEAN)
        filename = filename_parser.generate_filename(verse_ref, date_str, extracted_prefix).replace(".mp3", "_gemini_tts.mp3")
    else:
        filename = f"{date_str}_gemini_tts.mp3"

    if ENABLE_BGM and BGM_FILE:
        bgm_base = os.path.splitext(os.path.basename(BGM_FILE))[0]
        filename = filename.replace(".mp3", f"_bgm_{bgm_base}.mp3")

    OUTPUT_DIR = os.path.join(os.getcwd(), "output")
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
    OUTPUT_PATH = os.path.join(OUTPUT_DIR, filename)
    print(f"Target Output: {OUTPUT_PATH}")

    # 2. Generate Audio
    first_segments = []
    print("--- Section 1: Intro ---")
    for i, para in enumerate(first_paragraphs):
        segment = speak(para, FIRST_VOICE, FIRST_PROMPT)
        first_segments.append(segment)
    
    first_audio = AudioSegment.empty()
    silence = AudioSegment.silent(duration=500, frame_rate=24000)
    for seg in first_segments: first_audio += seg + silence

    second_segments = []
    print("--- Section 2: Main Content ---")
    for i, para in enumerate(second_paragraphs):
        segment = speak(para, SECOND_VOICE, SECOND_PROMPT)
        second_segments.append(segment)

    second_audio = AudioSegment.empty()
    for seg in second_segments: second_audio += seg + silence

    combined_audio = first_audio + silence + second_audio
    combined_audio = combined_audio.set_frame_rate(24000)

    if ENABLE_BGM:
        print(f"🎵 Mixing BGM: {BGM_FILE}")
        combined_audio = audio_mixer.mix_bgm(combined_audio, specific_filename=BGM_FILE, volume_db=BGM_VOLUME, intro_delay_ms=BGM_INTRO_DELAY)

    PRODUCER = "VI AI Foundation"
    TITLE = first_line
    combined_audio.export(OUTPUT_PATH, format="mp3", bitrate="192k", tags={'title': TITLE, 'artist': PRODUCER})
    print(f"✅ Saved: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()