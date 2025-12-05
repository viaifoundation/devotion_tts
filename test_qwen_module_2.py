import os
import dashscope
from dashscope.audio.qwen_tts import SpeechSynthesizer

dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

try:
    print("Testing qwen-tts module with model='qwen-tts' voice='Cherry'...")
    resp = SpeechSynthesizer.call(model='qwen-tts', text='Hello', voice='Cherry')
    print(f"Response type: {type(resp)}")
    print(f"Dir resp: {dir(resp)}")
    print(f"Status code: {resp.status_code}")
except Exception as e:
    print(f"Error: {e}")
