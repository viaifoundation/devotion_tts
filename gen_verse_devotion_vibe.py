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
import argparse

# CLI Args
if "-?" in sys.argv:
    print(f"Usage: python {sys.argv[0]} [--prefix PREFIX] [--help]")
    print("Options:")
    print("  --prefix PREFIX      Filename prefix (overrides 'FilenamePrefix' in text)")
    print("  --help, -h           Show this help")
    print("\n  (Note: You can also add 'FilenamePrefix: <Prefix>' in the input TEXT)")
    sys.exit(0)

parser = argparse.ArgumentParser()
parser.add_argument("--prefix", type=str, default=None, help="Filename prefix")
args, unknown = parser.parse_known_args()
CLI_PREFIX = args.prefix


TEXT = """
学习凡事谦虚 (以弗所书 4:2) 12/17/2025

进了房子，看见小孩子和他母亲马利亚，就俯伏拜那小孩子，揭开宝盒，拿黄金、乳香、没药为礼物献给他。博士因为在梦中被主指示不要回去见希律，就从别的路回本地去了。
(马太福音 2:11-12)
他们听见王的话就去了。在东方所看见的那星忽然在他们前头行，直行到小孩子的地方，就在上头停住了。
(马太福音 2:9)

我为主被囚的劝你们：既然蒙召，行事为人就当与蒙召的恩相称。凡事谦虚、温柔、忍耐，用爱心互相宽容，用和平彼此联络，竭力保守圣灵所赐合而为一的心。
(以弗所书 4:1-3 和合本)
凡事谦虚、温柔、忍耐，用爱心彼此宽容；
(以弗所书 4:2 新译本)

学习凡事谦虚

你见过愤怒的基督徒吗？ 

你可能遇到过喜欢发牢骚、埋怨、甚至恶言相向的基督徒。也许你，有时在自己的生活中也是这样的人。

如果不谨慎，我们很容易会因本身的基督信仰而变得自以为义 。毕竟，我们知道其他人所不知道的真理。你可能还会忍不住看不起别人、贬低他们，或认为他们比我们更罪恶。

这种行为就完全错过了耶稣福音的要点。 

福音告诉我们，我们所有人都从同一个起点开始。只有通过恩典，我们才能获得救恩，并了解神对我们的爱的真相。

这并不使我们比其他基督徒更好！事实上，正如保罗在以弗所书 4:2 中所说，我们实际上应该谦虚、温柔地对待别人，而不是严厉和挑剔。他说我们要彼此忍耐，尽我们所能互相帮助，那样我们才能共同成长。

这些想法并非保罗原创。它们实际上来自耶稣的生活方式。作为跟随耶稣的人，我们也应该努力对生活中的每个人表现出温柔、谦虚和忍耐。无论他们的外表或想法是否不同，每个人都应当享有我们的敬重、忍耐和爱。

今天就花时间想一些实际的方法，让你学习对人忍耐、谦虚和有爱心。也许你可以放慢脚步，投入时间以让人们知道你关心他们；或是对某人说一些鼓励的话；或是向某人承认你犯了一个错误。 

今天就做出决定，以谦虚和满有恩慈的态度与他人相处。

禱告
神啊，你的话语激励我要凡事都谦虚、温柔和忍耐。但如果我心里没有你的爱，我根本就做不到。请你教导我，如何出于爱而恩慈对待我身边的人。奉耶稣的名，阿们。
"""

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



# 1. Date Extraction
TEXT = clean_text(TEXT)
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
    extracted_prefix = CLI_PREFIX if CLI_PREFIX else filename_parser.extract_filename_prefix(TEXT)
    filename = filename_parser.generate_filename(verse_ref, date_str, extracted_prefix).replace(".mp3", "_vibe.mp3")
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

# Metadata extraction
PRODUCER = "VI AI Foundation"
TITLE = TEXT.strip().split('\n')[0]

final_mix.export(OUTPUT_PATH, format="mp3", bitrate="192k", tags={'title': TITLE, 'artist': PRODUCER})
print(f"✅ Saved: {OUTPUT_PATH}")
