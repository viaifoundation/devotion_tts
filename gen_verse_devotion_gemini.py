# gen_verse_devotion_gemini.py
# Google Gemini TTS – Multi-voice, works with Google Cloud credentials

import io
import os
import re
from google.cloud import texttospeech
from pydub import AudioSegment

from bible_parser import convert_bible_reference
from date_parser import convert_dates_in_text
from text_cleaner import remove_space_before_god
import filename_parser
import re
from datetime import datetime

# Ensure Google Cloud credentials are set
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/path/to/key.json" 
# Verify credentials exist
if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    print("⚠️ WARNING: GOOGLE_APPLICATION_CREDENTIALS not set. Ensure you have authenticated via gcloud or set the env var.")



TEXT = """
忍耐生甘甜 (雅各书 5:8) 12/14/2025

　神说：“要有光”，就有了光。
(创世记 1:3 )
大山可以挪开，
小山可以迁移；
但我的慈爱必不离开你；
我平安的约也不迁移。
这是怜恤你的耶和华说的。
(以赛亚书 54:10)
主为我们舍命，我们从此就知道何为爱；我们也当为弟兄舍命。
(约翰一书 3:16)
“　神爱世人，甚至将他的独生子赐给他们，叫一切信他的，不至灭亡，反得永生。
(约翰福音 3:16)

弟兄们哪，你们要忍耐，直到主来。看哪，农夫忍耐等候地里宝贵的出产，直到得了秋雨春雨。你们也当忍耐，坚固你们的心，因为主来的日子近了。
(雅各书 5:7-8 和合本)
你们也应当忍耐，坚定自己的心；因为主再来的日子近了。
(雅各书 5:8 新译本)

忍耐生甘甜

你曾在水果未熟时就把它采摘下来吃吗？

也许你被它鲜艳的色彩和空气中弥漫的甜美气味所吸引。可惜你一口咬下去，却发现它没有你预期的熟度。这个水果表面看来可以吃了，然而还缺乏一个因素……

时间。

即使是一个摘果子的简单动作，也能教会我们时间和忍耐的重要性：

“弟兄们哪，你们要忍耐，直到主来。看哪，农夫忍耐等候地里宝贵的出产，直到得了秋雨春雨。你们也当忍耐，坚固你们的心，因为主来的日子近了。 ”（雅各书 5:7-8）

作者雅各在圣灵的默示下，给一群新归信基督且分散在各个地区的犹太人写了这一番话。这些早期的基督徒因他们的初生信仰而面临许多试炼，包括迫害和反对。雅各对他们要耐心等候和坚忍的呼吁，不仅仅是纸上的文字，更是逆境中的一线生机，为他们带来盼望和鼓励。

正如那些早期信徒面临试炼一样，我们在基督信仰的旅途中也会遇到挑战和苦难。因此，你可以效法那些早期的信徒一样选择忍耐；无论你正处于什么人生境况，让圣灵的果子在你里面成熟。当你这样做时，你的品格就会老练、你的信心就会加深、你与神的关系就会变得比你想象的更加甘甜。忍耐总会结出毅力和力量的果子。今天就开始来操练吧！

祷告—
神啊，你是忍耐与恩慈的完美典范。感谢你一直对我的忍耐！请你显明我生活中需要培养忍耐的层面。求你用盼望和智慧来充满我，以帮助我信靠你，尤其是在我遇上艰难挑战的时候。
奉耶稣的名，
阿们。
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

# 2. Extract Verse (First parenthesis content)
verse_match = re.search(r"\((.*?)\)", TEXT)
verse_ref = verse_match.group(1).strip() if verse_match else "Unknown-Verse"

filename = filename_parser.generate_filename(verse_ref, date_str).replace(".mp3", "_gemini.mp3")
OUTPUT_DIR = os.getcwd()
OUTPUT_PATH = os.path.join(OUTPUT_DIR, filename)
print(f"Target Output: {OUTPUT_PATH}")

TEXT = convert_bible_reference(TEXT)
TEXT = convert_dates_in_text(TEXT)
TEXT = remove_space_before_god(TEXT)

paragraphs = [p.strip() for p in TEXT.strip().split("\n\n") if p.strip()]

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
