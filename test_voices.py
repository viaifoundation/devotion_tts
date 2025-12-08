import os
import requests
import dashscope
from dashscope.audio.qwen_tts import SpeechSynthesizer

dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

# Voices mentioned in search results but not in error message
candidates = ["Dylan", "Jada", "Sunny", "Yunxi", "LongXiaochun"]

print("Testing additional voices for model='qwen-tts'...")
for voice in candidates:
    try:
        resp = SpeechSynthesizer.call(model='qwen-tts', text='Hello', voice=voice)
        if resp.status_code == 200:
            print(f"✅ Supported: {voice}")
        else:
            print(f"❌ Failed: {voice} - {resp.message}")
    except Exception as e:
        print(f"❌ Error: {voice} - {e}")
