import os
import dashscope
from dashscope.audio.tts import SpeechSynthesizer

dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

models_to_test = ["qwen-tts", "cosyvoice-v1", "sambert-zh-v1", "qwen3-tts-flash"]
voice = "Yunxi"
text = "你好"

for m in models_to_test:
    print(f"Testing model: {m}...")
    try:
        resp = SpeechSynthesizer.call(model=m, text=text, voice=voice)
        if resp.get_response().status_code == 200:
            print(f"✅ SUCCESS: {m}")
            break
        else:
            print(f"❌ FAILED: {m} - {resp.get_response().message}")
    except Exception as e:
        print(f"❌ EXCEPTION: {m} - {e}")
