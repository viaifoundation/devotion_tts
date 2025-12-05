import os
import dashscope
from dashscope.audio.qwen_tts import SpeechSynthesizer

dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

try:
    print("Testing qwen-tts module with model='qwen-tts'...")
    resp = SpeechSynthesizer.call(model='qwen-tts', text='你好', voice='Yunxi')
    print(f"Response type: {type(resp)}")
    print(f"Response: {resp}")
except Exception as e:
    print(f"Error: {e}")

try:
    print("Testing qwen-tts module with model='cosyvoice-v1'...")
    resp = SpeechSynthesizer.call(model='cosyvoice-v1', text='你好', voice='LongXiaochun')
    print(f"Response: {resp}")
except Exception as e:
    print(f"Error: {e}")
