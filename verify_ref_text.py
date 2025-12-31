import whisper
import os

def check(wav_path):
    if not os.path.exists(wav_path):
        print(f"File not found: {wav_path}")
        return
    
    print(f"\nTranscribing: {wav_path}...")
    try:
        model = whisper.load_model('base')
        result = model.transcribe(wav_path, language='zh')
        print(f"Recognized Text: {result['text']}")
    except Exception as e:
        print(f"Error ({e}) - trying without language hint...")
        try:
            result = model.transcribe(wav_path)
            print(f"Recognized Text: {result['text']}")
        except:
            print("Failed to transcribe.")

print("Loading Whisper model...")
check("assets/ref_audio/ref_female.wav")
check("assets/ref_audio/ref_male.wav")
