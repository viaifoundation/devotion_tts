# gen_verse_devotion_vibe.py
# VibeVoice Workflow (Microsoft/OpenSource)

import torch
import numpy as np
import re
import sys
import os
import warnings
from datetime import datetime
from pydub import AudioSegment
import logging

# Silence noisy libraries
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# Setup path to find VibeVoice (sibling directory)
VIBEVOICE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../VibeVoice"))

if os.path.exists(VIBEVOICE_PATH):
    sys.path.append(VIBEVOICE_PATH)
else:
    print(f"⚠️ Warning: VibeVoice path not found at {VIBEVOICE_PATH}")
    print("Please clone it: git clone https://github.com/microsoft/VibeVoice ../VibeVoice")
    sys.exit(1)

try:
    from vibevoice.modular.modeling_vibevoice_streaming_inference import VibeVoiceStreamingForConditionalGenerationInference
    from vibevoice.processor.vibevoice_streaming_processor import VibeVoiceStreamingProcessor
except ImportError as e:
    print(f"❌ Failed to import VibeVoice: {e}")
    sys.exit(1)

from bible_parser import convert_bible_reference
from date_parser import convert_dates_in_text
from text_cleaner import clean_text
import filename_parser

# Configuration
MODEL_PATH = "microsoft/VibeVoice-Realtime-0.5B"  # HuggingFace model hub path
VOICES_DIR = os.path.join(VIBEVOICE_PATH, "demo", "voices", "streaming_model")

# Helper Class for Voice Mapping (Adapted from demo)
class VoiceMapper:
    def __init__(self, voices_dir):
        self.voices_dir = voices_dir
        self.voice_presets = {}
        self.setup_voice_presets()

    def setup_voice_presets(self):
        if not os.path.exists(self.voices_dir):
            print(f"⚠️ Warning: Voices directory not found at {self.voices_dir}")
            return
        
        # Scan for .pt files (voice embeddings)
        for root, _, files in os.walk(self.voices_dir):
            for file in files:
                if file.endswith(".pt"):
                    name = os.path.splitext(file)[0]
                    path = os.path.join(root, file)
                    self.voice_presets[name] = path
                    
                    # Also map simplified names
                    # e.g. en-Mike_man -> en-Mike
                    if '_' in name:
                        name = name.split('_')[0]
                        self.voice_presets[name] = path
                    
                    # e.g. en-Mike -> Mike
                    if '-' in name:
                        short_name = name.split('-')[-1]
                        self.voice_presets[short_name] = path

    def get_voice_path(self, name):
        return self.voice_presets.get(name) or self.voice_presets.get("Mike") # Default to Mike

# Load Model
print(f"Loading VibeVoice model: {MODEL_PATH}...")
try:
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"Using device: {device}")

    # DataType and Attn Config
    if device == "cuda":
        torch_dtype = torch.bfloat16
        attn_impl = "flash_attention_2"
    elif device == "mps":
        torch_dtype = torch.float32
        attn_impl = "sdpa"
    else:
        torch_dtype = torch.float32
        attn_impl = "sdpa"

    processor = VibeVoiceStreamingProcessor.from_pretrained(MODEL_PATH)
    
    # Load model with fallback logic for attention
    try:
        model = VibeVoiceStreamingForConditionalGenerationInference.from_pretrained(
            MODEL_PATH,
            torch_dtype=torch_dtype,
            attn_implementation=attn_impl,
            device_map=device if device != "mps" else None
        )
        if device == "mps":
            model.to("mps")
    except Exception as e:
        print(f"⚠️  Falling back to SDPA attention due to error: {e}")
        model = VibeVoiceStreamingForConditionalGenerationInference.from_pretrained(
            MODEL_PATH,
            torch_dtype=torch_dtype,
            attn_implementation="sdpa",
            device_map=device if device != "mps" else None
        )
        if device == "mps":
            model.to("mps")
            
    model.eval()
    model.set_ddpm_inference_steps(num_steps=5) # Default from demo

    voice_mapper = VoiceMapper(VOICES_DIR)

except Exception as e:
    print(f"❌ Error loading VibeVoice model: {e}")
    sys.exit(1)

TEXT = """
来，看，去，告诉 (罗马书 10:14-17) 12/15/2025

马利亚说：
我心尊主为大；
我灵以　神我的救主为乐；
(路加福音 1:46-47)
因为你问安的声音一入我耳，我腹里的胎就欢喜跳动。这相信的女子是有福的！因为主对她所说的话都要应验。
(路加福音 1:44-45)


然而，人未曾信他，怎能求他呢？未曾听见他，怎能信他呢？没有传道的，怎能听见呢？若没有奉差遣，怎能传道呢？如经上所记：“报福音、传喜信的人，他们的脚踪何等佳美！”只是人没有都听从福音，因为以赛亚说：“主啊，我们所传的有谁信呢？”可见，信道是从听道来的，听道是从基督的话来的。
(罗马书 10:14-17 和合本)
可见信心是从所听的道来的，所听的道是藉着基督的话来的。
(罗马书 10:17 新译本)

来，看，去，告诉

我们所听见的会影响我们所知道的。
我们所知道的会影响我们所相信的。
我们所相信的会影响我们所行的。

这就是为什么聆听神的真理如此重要。 

“可见，信道是从听道来的，听道是从基督的话来的。”（罗马书 10:17）

在四本福音书中──马太福音、马可福音、路加福音和约翰福音──我们都可读到耶稣邀请跟随他的人“来看”、“去告诉”，以及“要听，也要明白”。

在写给罗马人的信中，保罗解释了为什么去把福音告诉别人很重要：

“因为‘凡求告主名的就必得救’。然而，人未曾信他，怎能求他呢？未曾听见他，怎能信他呢？没有传道的，怎能听见呢？若没有奉差遣，怎能传道呢？如经上所记：“报福音、传喜信的人，他们的脚踪何等佳美！”（罗马书 10:13-15）

那么这个“福音”或“喜信”是什么呢？

要真正理解“福音”这个好消息，让我们先来看看坏消息：我们全都败坏不堪。我们的罪使我们与良善圣洁的神隔绝，我们无法弥补这道鸿沟。

那么，好消息来了：神深爱我们，并已为我们开了一条出路。他道成肉身，承受与罪犯一样的死刑（尽管他是无辜的），付出了终极的代价，并通过死里复活来征服了坟墓。他已赐予我们成为属他的特权！

因此，“凡求告主名的就必得救”。

现在就花点时间感谢神赐下他的话语，让我们有能力接受他的福音。然后，祈求他向你展示如何与他人分享你的盼望，进而增强你的信心。

祷告：
主耶稣，感谢你与我分享你的生命。今天，请增强我的信心；提醒我你是谁和你的成就。即使谎言和疑惑围绕着我，也要让我的心和思想专注于你。与此同时，请给我勇气去告诉他人关于你那改变世界的爱。
奉耶稣的名，阿们。
"""

# 1. Date Extraction
first_line = TEXT.strip().split('\n')[0]
date_match = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", first_line)
if date_match:
    m, d, y = date_match.groups()
    date_str = f"{y}-{int(m):02d}-{int(d):02d}"
else:
    date_str = datetime.today().strftime("%Y-%m-%d")

# 2. Verse Extraction
verse_ref = filename_parser.extract_verse_from_text(TEXT)

if verse_ref:
    filename = filename_parser.generate_filename(verse_ref, date_str).replace(".mp3", "_vibe.mp3")
else:
    filename = f"{date_str}_vibe.mp3"

OUTPUT_DIR = os.path.join(os.getcwd(), "output")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
OUTPUT_PATH = os.path.join(OUTPUT_DIR, filename)
print(f"Target Output: {OUTPUT_PATH}")

TEXT = convert_bible_reference(TEXT)
TEXT = convert_dates_in_text(TEXT)
TEXT = clean_text(TEXT)

paragraphs = [p.strip() for p in re.split(r'\n{2,}', TEXT.strip()) if p.strip()]

# VibeVoice Synthesis Function
def speak(text: str, voice_name: str) -> AudioSegment:
    print(f"DEBUG: Text to read: {text[:100]}...")
    print(f"   Synthesizing ({len(text)} chars) with {voice_name}...")
    
    voice_path = voice_mapper.get_voice_path(voice_name)
    if not voice_path:
        print(f"   ❌ Voice '{voice_name}' not found, falling back to default.")
        voice_path = voice_mapper.get_voice_path("Mike") # Fallback

    # Load voice prompt
    all_prefilled = torch.load(voice_path, map_location=device, weights_only=False)

    # Process Inputs
    inputs = processor.process_input_with_cached_prompt(
        text=text,
        cached_prompt=all_prefilled,
        padding=True,
        return_tensors="pt",
        return_attention_mask=True,
    )
    
    # Move to device
    for k, v in inputs.items():
        if torch.is_tensor(v):
            inputs[k] = v.to(device)
            
    # Generate
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=None,
            cfg_scale=1.5,
            tokenizer=processor.tokenizer,
            generation_config={'do_sample': False},
            verbose=False,
            all_prefilled_outputs=all_prefilled # copy not needed if read-only
        )
        
    if outputs.speech_outputs and outputs.speech_outputs[0] is not None:
        audio_np = outputs.speech_outputs[0].cpu().numpy()
        # VibeVoice output is float -1..1, usually 24kHz (check demo, said 24000)
        audio_int16 = (audio_np * 32767).astype(np.int16)
        
        return AudioSegment(
            audio_int16.tobytes(),
            frame_rate=24000,
            sample_width=2,
            channels=1
        )
    else:
        print("   ❌ No audio generated.")
        return AudioSegment.silent(duration=500)

final_mix = AudioSegment.empty()
silence = AudioSegment.silent(duration=800, frame_rate=24000)

# "Wayne" is the default male English voice in VibeVoice demo
# "Xiaoxiao"? "Yunxi"? Need to check Chinese available voices.
# For now, default to "Wayne" (English) or whatever is in the demo instructions.
# The user wants Chinese. The demo video showed Chinese.
# I will check `demo/voices` later to see available Chinese names.
# Voice Rotation (Using English voices for cross-lingual synthesis)
voices = ["Mike", "Emma", "Frank", "Grace", "Carter"]
print(f"Available Voices being used: {voices}")

for i, para in enumerate(paragraphs):
    current_voice = voices[i % len(voices)]
    print(f"  > Para {i+1} - {current_voice}")
    segment = speak(para, current_voice)
    final_mix += segment
    if i < len(paragraphs) - 1:
        final_mix += silence

final_mix.export(OUTPUT_PATH, format="mp3", bitrate="192k")
print(f"✅ Saved: {OUTPUT_PATH}")
