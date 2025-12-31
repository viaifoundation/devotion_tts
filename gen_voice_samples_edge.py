#!/usr/bin/env python3
# gen_voice_samples_edge.py
# Generate voice samples using Edge TTS for use as CosyVoice 3.0 reference audio
# Output: WAV files suitable for zero-shot voice cloning

import asyncio
import argparse
import os
import sys
import edge_tts
from pydub import AudioSegment

# Available Chinese voices from Edge TTS
AVAILABLE_VOICES = {
    # Simplified Chinese
    "zh_female_warm": ("zh-CN-XiaoxiaoNeural", "Female - Warm (Xiaoxiao)"),
    "zh_female_lively": ("zh-CN-XiaoyiNeural", "Female - Lively (Xiaoyi)"),
    "zh_male_passion": ("zh-CN-YunjianNeural", "Male - Passion (Yunjian)"),
    "zh_male_sunshine": ("zh-CN-YunxiNeural", "Male - Lively Sunshine (Yunxi)"),
    "zh_male_cute": ("zh-CN-YunxiaNeural", "Male - Cute (Yunxia)"),
    "zh_male_pro": ("zh-CN-YunyangNeural", "Male - Professional (Yunyang)"),
    # Traditional Chinese (Taiwan)
    "tw_female": ("zh-TW-HsiaoChenNeural", "Female - Taiwan (HsiaoChen)"),
    "tw_male": ("zh-TW-YunJheNeural", "Male - Taiwan (YunJhe)"),
    # Cantonese (Hong Kong)
    "hk_female": ("zh-HK-HiuGaaiNeural", "Female - Cantonese (HiuGaai)"),
    "hk_male": ("zh-HK-WanLungNeural", "Male - Cantonese (WanLung)"),
}

# Default reference text (suitable for voice cloning)
DEFAULT_REF_TEXT = "然而，靠着爱我们的主，在这一切的事上已经得胜有余了。"

def list_voices():
    """Print available voices."""
    print("\n📢 Available Edge TTS Voices for Chinese:\n")
    print(f"{'Key':<20} {'Voice ID':<30} {'Description'}")
    print("-" * 80)
    for key, (voice_id, desc) in AVAILABLE_VOICES.items():
        print(f"{key:<20} {voice_id:<30} {desc}")
    print()

async def generate_sample(text: str, voice_id: str, output_path: str, rate: str = "+0%"):
    """Generate audio sample using Edge TTS and save as WAV."""
    print(f"🔊 Generating: {voice_id}")
    print(f"   Text: {text[:50]}...")
    
    # Generate MP3 first (Edge TTS outputs MP3)
    temp_mp3 = output_path.replace(".wav", "_temp.mp3")
    communicate = edge_tts.Communicate(text=text, voice=voice_id, rate=rate)
    await communicate.save(temp_mp3)
    
    # Convert to WAV (16kHz mono for CosyVoice compatibility)
    audio = AudioSegment.from_mp3(temp_mp3)
    audio = audio.set_frame_rate(16000).set_channels(1)
    audio.export(output_path, format="wav")
    
    # Clean up temp file
    os.remove(temp_mp3)
    
    duration = len(audio) / 1000.0
    print(f"   ✅ Saved: {output_path} ({duration:.1f}s)")
    return output_path

async def main():
    parser = argparse.ArgumentParser(
        description="Generate Edge TTS voice samples for CosyVoice 3.0 reference audio"
    )
    parser.add_argument("--text", "-t", type=str, default=DEFAULT_REF_TEXT,
                        help="Text to speak (Default: Chinese reference sentence)")
    parser.add_argument("--voices", "-v", type=str, default="zh_female_warm,zh_male_sunshine",
                        help="Comma-separated voice keys to generate (Default: zh_female_warm,zh_male_sunshine)")
    parser.add_argument("--all", action="store_true",
                        help="Generate samples for ALL available voices")
    parser.add_argument("--output-dir", "-o", type=str, default="assets/ref_audio",
                        help="Output directory (Default: assets/ref_audio)")
    parser.add_argument("--list", "-l", action="store_true",
                        help="List available voices and exit")
    parser.add_argument("--rate", type=str, default="+0%",
                        help="Speech rate adjustment (e.g. +10%%, -5%%)")
    
    args = parser.parse_args()
    
    if args.list:
        list_voices()
        return
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Determine which voices to generate
    if args.all:
        voice_keys = list(AVAILABLE_VOICES.keys())
    else:
        voice_keys = [k.strip() for k in args.voices.split(",")]
    
    print(f"\n🎤 Generating {len(voice_keys)} voice samples...")
    print(f"   Text: \"{args.text}\"")
    print(f"   Output: {args.output_dir}/\n")
    
    generated = []
    for key in voice_keys:
        if key not in AVAILABLE_VOICES:
            print(f"⚠️  Unknown voice key: {key} (use --list to see available)")
            continue
        
        voice_id, desc = AVAILABLE_VOICES[key]
        # Filename: ref_edge_{key}.wav
        filename = f"ref_edge_{key}.wav"
        output_path = os.path.join(args.output_dir, filename)
        
        try:
            await generate_sample(args.text, voice_id, output_path, args.rate)
            generated.append(output_path)
        except Exception as e:
            print(f"❌ Error generating {key}: {e}")
    
    print(f"\n✅ Generated {len(generated)} voice samples!")
    print("\nTo use with CosyVoice 3.0:")
    print(f"  python gen_verse_devotion_cosy3.py --voices {','.join(generated)} --input sample.txt")

if __name__ == "__main__":
    asyncio.run(main())
