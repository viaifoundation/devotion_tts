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
住在神的爱里面 (约翰一书 4:16) 12/13/2025

及至时候满足，　神就差遣他的儿子，为女子所生，且生在律法以下，要把律法以下的人赎出来，叫我们得着儿子的名分。你们既为儿子，　神就差他儿子的灵进入你们（原文是我们）的心，呼叫：“阿爸！父！”可见，从此以后，你不是奴仆，乃是儿子了；既是儿子，就靠着　神为后嗣。
(加拉太书 4:4-7 和合本)
但到了时机成熟，　神就差遣他的儿子，由女人所生，而且生在律法之下，要把律法之下的人救赎出来，好让我们得着嗣子的名分。
(加拉太书 4:4-5 新译本)
所以，你们要自卑，服在　神大能的手下，到了时候，他必叫你们升高。你们要将一切的忧虑卸给　神，因为他顾念你们。
(彼得前书 5:6-7)


　神爱我们的心，我们也知道也信。
　神就是爱；住在爱里面的，就是住在　神里面，　神也住在他里面。
(约翰一书 4:16 和合本)
　神对我们的爱，我们已经明白了，而且相信了。
　神就是爱；住在爱里面的，就住在　神里面，　神也住在他里面。
(约翰壹书 4:16 新译本)
这样，我们已经认识并相信了神对我们所怀的爱。神就是爱；那住在爱里面的，就住在神里面，神也住在他里面。
(约翰一书 4:16 标准译本)

住在神的爱里面

你曾遇到过特别善良和体贴的人吗？好朋友就是这样——平易近人、热心想知道你过得怎么样、心无旁骛地倾听你。好朋友会使我们记起我们是谁。他们怀着仁慈与爱来倾听你所说的一切，无论是喜还是忧。

神就是这样的朋友。他倾听；他感同身受。他非常关心你，并且仁慈地回应你。事实上，神所做的不仅仅是展示爱——他就是爱。他不可能不爱，因为爱就是他的本质。他的爱是纯洁的；不自私、不脱节、不苦涩、不怨恨，也不消极。我们可以信靠这种爱；我们可以信靠神。

在约翰一书 4:16 中，我们看到了一个美好的提醒，让我们知道与神同在的生活是什么样的：“神爱我们的心，我们也知道也信。神就是爱；住在爱里面的，就是住在神里面，神也住在他里面。”

和好朋友共度时光后，你感觉如何？也许你会觉得心情安逸、步履轻快，或者你发现自己有了勇气继续前行。你甚至可能发现自己因为感受到被爱而更加爱别人。这就是住在神的爱中产生的连锁反应。当你知道并体验到神多么爱你时，你就会情不自禁地爱别人。

这就是我们被邀请去过的生活。一种了解并依赖神对我们的爱，然后因此而爱他人的生活。今天，你将如何找到神对你的爱？在你认识并体验到神对你的爱之后，一切都会改变。

祷告：
神啊，你的爱对我来说太奇妙了。我需要更加理解你的爱。我想感受被爱和被重视；我想经历你对我何等的眷顾。请你今天就帮助我更深入认识你的爱。奉耶稣的名，阿们。
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

filename = filename_parser.generate_filename(verse_ref, date_str)
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
