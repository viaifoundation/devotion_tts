import os
import dashscope
from dashscope.audio.tts import SpeechSynthesizer

dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

for model_name in ["cosyvoice-v1", "qwen-tts", "sambert-zhichu-v1"]:
    try:
        resp = SpeechSynthesizer.call(model=model_name, text="hello", format="wav", sample_rate=24000)
        if resp.get_audio_data() is not None:
            print(f"✅ {model_name} worked! Got audio data.")
        elif resp.get_response().message:
            print(f"❌ {model_name} failed: {resp.get_response().message}")
        else:
            print(f"❌ {model_name} failed: {resp}")
    except Exception as e:
        print(f"❌ {model_name} threw an exception:", e)
