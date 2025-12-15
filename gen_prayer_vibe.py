# gen_prayer_vibe.py
# VibeVoice Workflow for Prayer (Microsoft/OpenSource)

import torch
import numpy as np
import re
import sys
import os
import warnings
from datetime import datetime
from pydub import AudioSegment

# Silence noisy libraries
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# Setup path to find VibeVoice (sibling directory)
VIBEVOICE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../VibeVoice"))

if os.path.exists(VIBEVOICE_PATH):
    sys.path.append(VIBEVOICE_PATH)
else:
    print(f"⚠️ Warning: VibeVoice path not found at {VIBEVOICE_PATH}")
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
亲爱的天父：
我们感谢你，因你的恩典每一天都是新的！
在这个安静的时刻，我们将心全然向你敞开。求你保守我们的心思意念，让我们在忙碌的生活中，依然能听见你微小的声音。
主啊，求你赐给我们属天的智慧，让我们在面对挑战时，不依靠自己的聪明，而是单单仰望你。
愿你的平安充满我们的家庭，愿你的爱流淌在我们彼此之间。
也求你记念那些在病痛和软弱中的肢体，愿你的医治临到他们，使他们重新得力。
感谢赞美主，听我们不配的祷告，奉主耶稣基督得胜的名求！阿门！
(腓立比书 4:6-7) 12/14/2025
"""

# Generate filename dynamically
first_line = TEXT.strip().split('\n')[0]
date_match = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", TEXT)
if date_match:
    m, d, y = date_match.groups()
    date_str = f"{y}-{int(m):02d}-{int(d):02d}"
else:
    date_match = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", TEXT)
    if date_match:
        y, m, d = date_match.groups()
        date_str = f"{y}-{int(m):02d}-{int(d):02d}"
    else:
        date_str = datetime.today().strftime("%Y-%m-%d")

# 2. Extract Verse
verse_match = re.search(r"[\(（](.*?[\d]+[:：].*?)[\)）]", TEXT)
verse_ref = verse_match.group(1).strip() if verse_match else None

if verse_ref:
    raw_filename = filename_parser.generate_filename(verse_ref, date_str)
    if raw_filename.startswith("VOTD_"):
        raw_filename = raw_filename[5:]
    filename = f"prayer_{raw_filename.replace('.mp3', '')}_vibe.mp3"
else:
    filename = f"prayer_{date_str}_vibe.mp3"

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
            all_prefilled_outputs=all_prefilled
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

# Multi-Voice Rotation
voices = ["Mike", "Emma", "Frank", "Grace", "Carter"]
print(f"Available Voices being used: {voices}")

for i, para in enumerate(paragraphs):
    current_voice = voices[i % len(voices)]
    print(f"  > Para {i+1} - {current_voice}")
    
    try:
        segment = speak(para, current_voice)
        final_mix += segment
        if i < len(paragraphs) - 1:
            final_mix += silence
    except Exception as e:
        print(f"❌ Error generating para {i}: {e}")

final_mix = final_mix.set_frame_rate(24000)
final_mix.export(OUTPUT_PATH, format="mp3", bitrate="192k")
print(f"✅ Saved: {OUTPUT_PATH}")
