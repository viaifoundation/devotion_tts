import os
import dashscope
from dashscope.audio.qwen_tts import SpeechSynthesizer

dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

resp = SpeechSynthesizer.call(model='qwen-tts', text='Hello', voice='Cherry')
if resp.status_code == 200:
    print(f"Output type: {type(resp.output)}")
    print(f"Output keys: {resp.output.keys() if hasattr(resp.output, 'keys') else 'No keys'}")
    print(f"Output content: {resp.output}")
else:
    print(f"Failed: {resp.message}")
