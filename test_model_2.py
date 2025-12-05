import os
import dashscope
from dashscope.audio.tts import SpeechSynthesizer

dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

print("--- Testing default model (no model arg) ---")
try:
    resp = SpeechSynthesizer.call(text="你好", voice="Yunxi")
    if resp.get_response().status_code == 200:
        print("✅ SUCCESS: default model")
    else:
        print(f"❌ FAILED: default model - {resp.get_response().message}")
except Exception as e:
    print(f"❌ EXCEPTION: default model - {e}")

print("--- Testing cosyvoice-v1 with LongXiaochun ---")
try:
    resp = SpeechSynthesizer.call(model="cosyvoice-v1", text="你好", voice="LongXiaochun")
    if resp.get_response().status_code == 200:
        print("✅ SUCCESS: cosyvoice-v1")
    else:
        print(f"❌ FAILED: cosyvoice-v1 - {resp.get_response().message}")
except Exception as e:
    print(f"❌ EXCEPTION: cosyvoice-v1 - {e}")

