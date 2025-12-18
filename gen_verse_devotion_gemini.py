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
学习凡事谦虚 (以弗所书 4:2) 12/17/2025

进了房子，看见小孩子和他母亲马利亚，就俯伏拜那小孩子，揭开宝盒，拿黄金、乳香、没药为礼物献给他。博士因为在梦中被主指示不要回去见希律，就从别的路回本地去了。
(马太福音 2:11-12)
他们听见王的话就去了。在东方所看见的那星忽然在他们前头行，直行到小孩子的地方，就在上头停住了。
(马太福音 2:9)

我为主被囚的劝你们：既然蒙召，行事为人就当与蒙召的恩相称。凡事谦虚、温柔、忍耐，用爱心互相宽容，用和平彼此联络，竭力保守圣灵所赐合而为一的心。
(以弗所书 4:1-3 和合本)
凡事谦虚、温柔、忍耐，用爱心彼此宽容；
(以弗所书 4:2 新译本)

学习凡事谦虚

你见过愤怒的基督徒吗？ 

你可能遇到过喜欢发牢骚、埋怨、甚至恶言相向的基督徒。也许你，有时在自己的生活中也是这样的人。

如果不谨慎，我们很容易会因本身的基督信仰而变得自以为义 。毕竟，我们知道其他人所不知道的真理。你可能还会忍不住看不起别人、贬低他们，或认为他们比我们更罪恶。

这种行为就完全错过了耶稣福音的要点。 

福音告诉我们，我们所有人都从同一个起点开始。只有通过恩典，我们才能获得救恩，并了解神对我们的爱的真相。

这并不使我们比其他基督徒更好！事实上，正如保罗在以弗所书 4:2 中所说，我们实际上应该谦虚、温柔地对待别人，而不是严厉和挑剔。他说我们要彼此忍耐，尽我们所能互相帮助，那样我们才能共同成长。

这些想法并非保罗原创。它们实际上来自耶稣的生活方式。作为跟随耶稣的人，我们也应该努力对生活中的每个人表现出温柔、谦虚和忍耐。无论他们的外表或想法是否不同，每个人都应当享有我们的敬重、忍耐和爱。

今天就花时间想一些实际的方法，让你学习对人忍耐、谦虚和有爱心。也许你可以放慢脚步，投入时间以让人们知道你关心他们；或是对某人说一些鼓励的话；或是向某人承认你犯了一个错误。 

今天就做出决定，以谦虚和满有恩慈的态度与他人相处。

禱告
神啊，你的话语激励我要凡事都谦虚、温柔和忍耐。但如果我心里没有你的爱，我根本就做不到。请你教导我，如何出于爱而恩慈对待我身边的人。奉耶稣的名，阿们。
"""


# Ensure Google Cloud credentials are set
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/path/to/key.json" 
# Verify credentials exist
if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    print("⚠️ WARNING: GOOGLE_APPLICATION_CREDENTIALS not set. Ensure you have authenticated via gcloud or set the env var.")





# Generate filename dynamically
# 1. Extract Date
TEXT = clean_text(TEXT)
first_line = TEXT.strip().split('\n')[0]
date_match = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", first_line)
if date_match:
    m, d, y = date_match.groups()
    date_str = f"{y}-{int(m):02d}-{int(d):02d}"
else:
    # Try YYYY-MM-DD
    date_match = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", first_line)
    if date_match:
        y, m, d = date_match.groups()
        date_str = f"{y}-{int(m):02d}-{int(d):02d}"
    else:
        date_str = datetime.today().strftime("%Y-%m-%d")

# 2. Extract Verse
# Handle both English () and Chinese （） parentheses, and both : and ： colons
verse_ref = filename_parser.extract_verse_from_text(TEXT)

if verse_ref:
    extracted_prefix = CLI_PREFIX if CLI_PREFIX else filename_parser.extract_filename_prefix(TEXT)
    filename = filename_parser.generate_filename(verse_ref, date_str, extracted_prefix).replace(".mp3", "_gemini.mp3")
else:
    filename = f"{date_str}_gemini.mp3"
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
# Using a mix of male/female voices for variety
voices = ["Charon", "Kore", "Fenrir", "Aoede", "Puck"]

# Voice configuration
LANGUAGE_CODE = "cmn-CN"
MODEL_NAME = "gemini-2.5-pro-tts" # Or appropriate model

# Global client cache
_TTS_CLIENT = None

def get_tts_client():
    global _TTS_CLIENT
    if _TTS_CLIENT:
        return _TTS_CLIENT

    try:
        # Try default credentials first
        _TTS_CLIENT = texttospeech.TextToSpeechClient()
        return _TTS_CLIENT
    except Exception as e:
        print(f"⚠️ Default auth failed: {e}")
        print("🔄 Attempting to use gcloud access token...")
        
        try:
            import subprocess
            import google.oauth2.credentials
            from google.api_core.client_options import ClientOptions
            
            # Get token via gcloud
            result = subprocess.run(
                ["zsh", "-l", "-c", "gcloud auth print-access-token"],
                capture_output=True,
                text=True,
                check=True
            )
            token = result.stdout.strip()
            
            # Get project ID via gcloud for quota
            project_result = subprocess.run(
                ["zsh", "-l", "-c", "gcloud config get-value project"],
                capture_output=True,
                text=True,
                check=True
            )
            project_id = project_result.stdout.strip()
            
            if not token:
                raise ValueError("Empty token received from gcloud")
                
            creds = google.oauth2.credentials.Credentials(token=token)
            
            # Set quota project to fix 403 error
            client_options = ClientOptions(quota_project_id=project_id) if project_id else None
            
            _TTS_CLIENT = texttospeech.TextToSpeechClient(credentials=creds, client_options=client_options)
            print(f"✅ Successfully authenticated using gcloud access token (Project: {project_id}).")
            return _TTS_CLIENT
            
        except Exception as token_error:
            print(f"❌ Failed to get gcloud token/project: {token_error}")
            raise e


def chunk_text(text: str, max_len: int = 400) -> list[str]:
    """Split text if too long (though Google limit is high, good practice)."""
    if len(text) <= max_len:
        return [text]
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

def speak(text: str, voice: str, style_prompt: str = None) -> AudioSegment:
    print(f"DEBUG: Text to read: {text[:100]}...")
    client = get_tts_client()
    synthesis_input = texttospeech.SynthesisInput(text=text)
    
    # Selecting voice
    voice_params = texttospeech.VoiceSelectionParams(
        language_code=LANGUAGE_CODE,
        name=voice,
        # Enable model name for Gemini voices
        model_name=MODEL_NAME 
    )
    
    # Audio config
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    
    # Request
    request = texttospeech.SynthesizeSpeechRequest(
        input=synthesis_input,
        voice=voice_params,
        audio_config=audio_config
    )
    
    # If style prompt is provided... (same logic as before)
    if style_prompt:
         try:
             synthesis_input = texttospeech.SynthesisInput(text=text, prompt=style_prompt)
             # Re-assign input to request
             request.input = synthesis_input
         except TypeError:
             print(f"⚠️ Warning: 'prompt' not supported in SynthesisInput for this client version. Ignoring prompt: {style_prompt}")

    try:
        response = client.synthesize_speech(request=request)
        return AudioSegment.from_mp3(io.BytesIO(response.audio_content))
    except Exception as e:
        # Check for safety filter error (400 InvalidArgument)
        if "sensitive or harmful content" in str(e) or "400" in str(e):
            print(f"⚠️ Safety filter triggered for voice {voice}. Retrying strategies...")
            
            # Strategy 1: Remove style prompt if present
            if style_prompt:
                print("   ↳ Strategy 1: Removing style prompt...")
                try:
                    # Clear prompt from input
                    request.input = texttospeech.SynthesisInput(text=text)
                    response = client.synthesize_speech(request=request)
                    print("   ✅ Strategy 1 success.")
                    return AudioSegment.from_mp3(io.BytesIO(response.audio_content))
                except Exception as e2:
                    print(f"   ❌ Strategy 1 failed: {e2}")

            # Strategy 2: Fallback to standard Wavenet voice (High quality, widely available)
            print("   ↳ Strategy 2: Fallback to standard Wavenet voice...")
            try:
                # Use Wavenet voices for Chinese (Neural2 is not fully supported for cmn-CN yet)
                # cmn-CN-Wavenet-A (Female), cmn-CN-Wavenet-B (Male), cmn-CN-Wavenet-C (Male), cmn-CN-Wavenet-D (Female)
                
                # Simple mapping
                fallback_voice = "cmn-CN-Wavenet-C" # Male default (replaces Charon/Fenrir/Puck)
                if voice in ["Kore", "Aoede"]:
                    fallback_voice = "cmn-CN-Wavenet-A" # Female default (replaces Kore/Aoede)
                
                fallback_params = texttospeech.VoiceSelectionParams(
                    language_code=LANGUAGE_CODE,
                    name=fallback_voice
                    # No model_name needed for standard voices
                )
                
                # Reset request with new voice and simple input (no prompt)
                request.voice = fallback_params
                request.input = texttospeech.SynthesisInput(text=text)
                
                response = client.synthesize_speech(request=request)
                print(f"   ✅ Strategy 2 success (Used {fallback_voice}).")
                return AudioSegment.from_mp3(io.BytesIO(response.audio_content))
                
            except Exception as e3:
                print(f"   ❌ Strategy 2 failed: {e3}")
                raise e # Give up if even standard voice fails
        
        # Re-raise other errors
        raise e

# Group paragraphs into 5 logical sections
# 1. Intro (Title/Date)
# 2. Scripture 1
# 3. Scripture 2
# 4. Main Body (Middle paragraphs)
# 5. Prayer (Last paragraph)

if len(paragraphs) < 5:
    # Fallback
    logical_sections = [[p] for p in paragraphs]
else:
    logical_sections = [
        [paragraphs[0]],              # Intro
        [paragraphs[1]],              # Scripture 1
        [paragraphs[2]],              # Scripture 2
        paragraphs[3:-1],             # Main Body
        [paragraphs[-1]]              # Prayer
    ]

# Ensure we don't exceed available voices
num_sections = len(logical_sections)
section_titles = ["Intro", "Scripture 1", "Scripture 2", "Main Body", "Prayer"]

# Define Style Prompts for each section
# These prompts help guide the "Gemini" model to adopt the correct tone
section_styles = [
    "Speak with a clear, professional, announcer-like tone for a title introduction.", # Intro
    "Speak with a solemn, reverent, and slow pace, suitable for reading Holy Scripture.", # Scripture 1
    "Speak with a solemn, reverent, and slow pace, suitable for reading Holy Scripture.", # Scripture 2
    "Speak with a warm, engaging, and personal storytelling tone, like a friend sharing wisdom.", # Main Body
    "Speak with a humble, quiet, and earnest tone, suitable for prayer.", # Prayer
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
    # Assuming silence same as 'silence' defined later, but we need it here.
    # We'll use 24000 as default or detect from first segment if available.
    silence_between_paras = AudioSegment.silent(duration=700, frame_rate=24000)

    for j, para in enumerate(section_paras):
        voice = voices[global_p_index % len(voices)]
        print(f"  > Part {i+1}.{j+1} - {voice} ({len(para)} chars)")
        global_p_index += 1
        
        current_segment = AudioSegment.empty()
        # Check length
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

# Determine sample rate from first segment to ensure consistency
# Determine sample rate from first segment to ensure consistency
frame_rate = final_segments[0].frame_rate if final_segments else 24000
silence = AudioSegment.silent(duration=1000, frame_rate=frame_rate)

for i, seg in enumerate(final_segments):
    final += seg
    if i < len(final_segments) - 1:
        final += silence

# Metadata extraction
PRODUCER = "VI AI Foundation"
TITLE = TEXT.strip().split('\n')[0]

final.export(OUTPUT_PATH, format="mp3", bitrate="192k", tags={'title': TITLE, 'artist': PRODUCER})
print(f"Success! Saved → {OUTPUT_PATH}")
