import sys
from pydub import AudioSegment
import os
from bible_parser import convert_bible_reference
from text_cleaner import clean_text, clean_text_for_tts
from google.cloud import texttospeech

import argparse

# CLI Args
parser = argparse.ArgumentParser()
parser.add_argument("--input", "-i", type=str, help="Input text file")
parser.add_argument("--prefix", type=str, default=None, help="Filename prefix")
args, unknown = parser.parse_known_args()
CLI_PREFIX = args.prefix

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
# Convert Bible references in the text (e.g., '罗马书 1:17' to '罗马书 1章17節')
TEXT = convert_bible_reference(TEXT)
TEXT = clean_text_for_tts(TEXT)
# Split the text into paragraphs
paragraphs = [p.strip() for p in TEXT.strip().split("\n\n") if p.strip()]
first_paragraphs = [paragraphs[0]] # First paragraph (introduction)
second_paragraphs  = ["\n\n".join(paragraphs[1:])] # All remaining paragraphs (main content)
"""
Locale,ShortName,Gender,Model Type,Content Categories
cmn-CN,cmn-CN-Standard-A,Female,Standard,General
cmn-CN,cmn-CN-Standard-B,Male,Standard,General
cmn-CN,cmn-CN-Standard-C,Female,Standard,General
cmn-CN,cmn-CN-Standard-D,Male,Standard,General
cmn-CN,cmn-CN-Wavenet-A,Female,WaveNet,General
cmn-CN,cmn-CN-Wavenet-B,Male,WaveNet,General
cmn-CN,cmn-CN-Wavenet-C,Female,WaveNet,General
cmn-CN,cmn-CN-Wavenet-D,Male,WaveNet,General
cmn-CN,cmn-CN-Neural2-A,Female,Neural2,General
cmn-CN,cmn-CN-Neural2-C,Male,Neural2,General
cmn-CN,cmn-CN-Neural2-D,Female,Neural2,General
zh-TW,zh-TW-Standard-A,Female,Standard,General
zh-TW,zh-TW-Standard-B,Male,Standard,General
zh-TW,zh-TW-Standard-C,Female,Standard,General
zh-TW,zh-TW-Wavenet-A,Female,WaveNet,General
zh-TW,zh-TW-Wavenet-B,Male,WaveNet,General
zh-TW,zh-TW-Wavenet-C,Female,WaveNet,General
zh-TW,zh-TW-Neural2-B,Male,Neural2,General
yue-HK,yue-HK-Standard-A,Female,Standard,General
yue-HK,yue-HK-Standard-B,Male,Standard,General
yue-HK,yue-HK-Standard-C,Female,Standard,General
yue-HK,yue-HK-Standard-D,Male,Standard,General
"""
# Voice settings (Note: Set up Google Cloud credentials, e.g., export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json")
FIRST_VOICE = "cmn-CN-Wavenet-A" # First voice (introduction, male, WaveNet)
SECOND_VOICE = "cmn-CN-Wavenet-B" # Second voice (main content, female, WaveNet)
#SECOND_VOICE = "cmn-CN-Neural2-A" # Second voice (main content, female, Neural2)
#FIRST_VOICE = "cmn-CN-Standard-B" # First voice (introduction, male, Standard)
#SECOND_VOICE = "cmn-CN-Standard-A" # Second voice (main content, female, Standard)
#SECOND_VOICE = "yue-HK-Standard-A" # Second voice (main content, female, Cantonese)
#FIRST_VOICE = "yue-HK-Standard-B" # First voice (introduction, male, Cantonese)
#SECOND_VOICE = "zh-TW-Wavenet-A" # Second voice (main content, female, Taiwan)
#FIRST_VOICE = "zh-TW-Wavenet-B" # First voice (introduction, male, Taiwan)
OUTPUT = "/Users/mhuo/Downloads/bread_1114_ji_tianjin.mp3"
TEMP_DIR = "/Users/mhuo/Downloads/" # For temp files
TEMP_FIRST = "/Users/mhuo/Downloads/temp_first_bread.mp3"
TEMP_SECOND = "/Users/mhuo/Downloads/temp_second_bread.mp3"
def generate_audio(text, voice, output_file):
    client = texttospeech.TextToSpeechClient()
    input_text = texttospeech.SynthesisInput(ssml=f"<speak><prosody rate=\"fast\" pitch=\"-2st\">{text}</prosody></speak>")
    language_code = "-".join(voice.split("-")[:2])
    voice_params = texttospeech.VoiceSelectionParams(
        language_code=language_code,
        name=voice,
    )
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
    response = client.synthesize_speech(
        input=input_text, voice=voice_params, audio_config=audio_config
    )
    with open(output_file, "wb") as out:
        out.write(response.audio_content)
def main():
    # Generate and collect first voice audio segments (for first paragraph)
    first_segments = []
    for i, para in enumerate(first_paragraphs):
        temp_file = f"{TEMP_DIR}temp_first_bread_{i}.mp3"
        generate_audio(para, FIRST_VOICE, temp_file)
        print(f"✅ Generated first voice chunk {i}: {temp_file}")
        segment = AudioSegment.from_mp3(temp_file)
        first_segments.append(segment)
        os.remove(temp_file) # Clean up immediately
    # Concatenate first segments with short silence between
    silence = AudioSegment.silent(duration=500) # 0.5s pause; adjust as needed
    first_audio = AudioSegment.empty()
    for i, segment in enumerate(first_segments):
        first_audio += segment
        if i < len(first_segments) - 1: # Add silence between segments, not after last
            first_audio += silence
    # Generate and collect second voice audio segments (for remaining paragraphs)
    second_segments = []
    for i, para in enumerate(second_paragraphs):
        temp_file = f"{TEMP_DIR}temp_second_bread_{i}.mp3"
        generate_audio(para, SECOND_VOICE, temp_file)
        print(f"✅ Generated second voice chunk {i}: {temp_file}")
        segment = AudioSegment.from_mp3(temp_file)
        second_segments.append(segment)
        os.remove(temp_file) # Clean up immediately
    # Concatenate second segments with short silence between
    second_audio = AudioSegment.empty()
    for i, segment in enumerate(second_segments):
        second_audio += segment
        if i < len(second_segments) - 1: # Add silence between segments, not after last
            second_audio += silence
    # Combine first and second with a pause between sections
    combined_audio = first_audio + silence + second_audio
    combined_audio.export(OUTPUT, format="mp3")
    print(f"✅ Combined audio saved: {OUTPUT}")
if __name__ == "__main__":
    main()
