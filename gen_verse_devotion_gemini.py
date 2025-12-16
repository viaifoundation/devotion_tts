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

# Ensure Google Cloud credentials are set
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/path/to/key.json" 
# Verify credentials exist
if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    print("⚠️ WARNING: GOOGLE_APPLICATION_CREDENTIALS not set. Ensure you have authenticated via gcloud or set the env var.")



TEXT = """
来，看，去，告诉 (罗马书 10:14-17) 12/15/2025

马利亚说：
我心尊主为大；
我灵以　神我的救主为乐；
(路加福音 1:46-47)
因为你问安的声音一入我耳，我腹里的胎就欢喜跳动。这相信的女子是有福的！因为主对她所说的话都要应验。
(路加福音 1:44-45)


然而，人未曾信他，怎能求他呢？未曾听见他，怎能信他呢？没有传道的，怎能听见呢？若没有奉差遣，怎能传道呢？如经上所记：“报福音、传喜信的人，他们的脚踪何等佳美！”只是人没有都听从福音，因为以赛亚说：“主啊，我们所传的有谁信呢？”可见，信道是从听道来的，听道是从基督的话来的。
(罗马书 10:14-17 和合本)
可见信心是从所听的道来的，所听的道是藉着基督的话来的。
(罗马书 10:17 新译本)

来，看，去，告诉

我们所听见的会影响我们所知道的。
我们所知道的会影响我们所相信的。
我们所相信的会影响我们所行的。

这就是为什么聆听神的真理如此重要。 

“可见，信道是从听道来的，听道是从基督的话来的。”（罗马书 10:17）

在四本福音书中──马太福音、马可福音、路加福音和约翰福音──我们都可读到耶稣邀请跟随他的人“来看”、“去告诉”，以及“要听，也要明白”。

在写给罗马人的信中，保罗解释了为什么去把福音告诉别人很重要：

“因为‘凡求告主名的就必得救’。然而，人未曾信他，怎能求他呢？未曾听见他，怎能信他呢？没有传道的，怎能听见呢？若没有奉差遣，怎能传道呢？如经上所记：“报福音、传喜信的人，他们的脚踪何等佳美！”（罗马书 10:13-15）

那么这个“福音”或“喜信”是什么呢？

要真正理解“福音”这个好消息，让我们先来看看坏消息：我们全都败坏不堪。我们的罪使我们与良善圣洁的神隔绝，我们无法弥补这道鸿沟。

那么，好消息来了：神深爱我们，并已为我们开了一条出路。他道成肉身，承受与罪犯一样的死刑（尽管他是无辜的），付出了终极的代价，并通过死里复活来征服了坟墓。他已赐予我们成为属他的特权！

因此，“凡求告主名的就必得救”。

现在就花点时间感谢神赐下他的话语，让我们有能力接受他的福音。然后，祈求他向你展示如何与他人分享你的盼望，进而增强你的信心。

祷告：
主耶稣，感谢你与我分享你的生命。今天，请增强我的信心；提醒我你是谁和你的成就。即使谎言和疑惑围绕着我，也要让我的心和思想专注于你。与此同时，请给我勇气去告诉他人关于你那改变世界的爱。
奉耶稣的名，阿们。
"""

# Generate filename dynamically
# 1. Extract Date
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
    filename = filename_parser.generate_filename(verse_ref, date_str).replace(".mp3", "_gemini.mp3")
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

final.export(OUTPUT_PATH, format="mp3", bitrate="192k")
print(f"Success! Saved → {OUTPUT_PATH}")
