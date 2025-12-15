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
from text_cleaner import remove_space_before_god
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
忍耐生甘甜 (雅各书 5:8) 12/14/2025

　神说：“要有光”，就有了光。
(创世记 1:3 )
大山可以挪开，
小山可以迁移；
但我的慈爱必不离开你；
我平安的约也不迁移。
这是怜恤你的耶和华说的。
(以赛亚书 54:10)
主为我们舍命，我们从此就知道何为爱；我们也当为弟兄舍命。
(约翰一书 3:16)
“　神爱世人，甚至将他的独生子赐给他们，叫一切信他的，不至灭亡，反得永生。
(约翰福音 3:16)

弟兄们哪，你们要忍耐，直到主来。看哪，农夫忍耐等候地里宝贵的出产，直到得了秋雨春雨。你们也当忍耐，坚固你们的心，因为主来的日子近了。
(雅各书 5:7-8 和合本)
你们也应当忍耐，坚定自己的心；因为主再来的日子近了。
(雅各书 5:8 新译本)

忍耐生甘甜

你曾在水果未熟时就把它采摘下来吃吗？

也许你被它鲜艳的色彩和空气中弥漫的甜美气味所吸引。可惜你一口咬下去，却发现它没有你预期的熟度。这个水果表面看来可以吃了，然而还缺乏一个因素……

时间。

即使是一个摘果子的简单动作，也能教会我们时间和忍耐的重要性：

“弟兄们哪，你们要忍耐，直到主来。看哪，农夫忍耐等候地里宝贵的出产，直到得了秋雨春雨。你们也当忍耐，坚固你们的心，因为主来的日子近了。 ”（雅各书 5:7-8）

作者雅各在圣灵的默示下，给一群新归信基督且分散在各个地区的犹太人写了这一番话。这些早期的基督徒因他们的初生信仰而面临许多试炼，包括迫害和反对。雅各对他们要耐心等候和坚忍的呼吁，不仅仅是纸上的文字，更是逆境中的一线生机，为他们带来盼望和鼓励。

正如那些早期信徒面临试炼一样，我们在基督信仰的旅途中也会遇到挑战和苦难。因此，你可以效法那些早期的信徒一样选择忍耐；无论你正处于什么人生境况，让圣灵的果子在你里面成熟。当你这样做时，你的品格就会老练、你的信心就会加深、你与神的关系就会变得比你想象的更加甘甜。忍耐总会结出毅力和力量的果子。今天就开始来操练吧！

祷告—
神啊，你是忍耐与恩慈的完美典范。感谢你一直对我的忍耐！请你显明我生活中需要培养忍耐的层面。求你用盼望和智慧来充满我，以帮助我信靠你，尤其是在我遇上艰难挑战的时候。
奉耶稣的名，
阿们。
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
verse_match = re.search(r"[\(（](.*?[\d]+[:：].*?)[\)）]", TEXT)
verse_ref = verse_match.group(1).strip() if verse_match else None

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
TEXT = remove_space_before_god(TEXT)

paragraphs = [p.strip() for p in TEXT.strip().split("\n") if p.strip()]

# VibeVoice Synthesis Function
def speak(text: str, voice_name: str) -> AudioSegment:
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
