import sys
import os
import torch
import numpy as np

# Add CosyVoice to path
sys.path.append('/workspace/github/CosyVoice')
sys.path.append('/workspace/github/CosyVoice/third_party/Matcha-TTS')

try:
    from cosyvoice.utils.file_utils import load_wav
    print("✅ Imported load_wav successfully")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

def test_load(wav_path, target_sr=16000):
    print(f"\nTesting: {wav_path}")
    if not os.path.exists(wav_path):
        print("❌ File not found")
        return

    try:
        speech = load_wav(wav_path, target_sr)
        print(f"  Shape: {speech.shape}")
        print(f"  Dtype: {speech.dtype}")
        print(f"  Min: {speech.min():.4f}, Max: {speech.max():.4f}")
        print(f"  Mean: {speech.mean():.4f}")
        
        # Check for silence or noise
        if speech.abs().max() < 0.01:
            print("  ⚠️ WARNING: Audio seems silent/near-silent")
        
        # Save output to verify
        import soundfile as sf
        out_name = f"debug_{os.path.basename(wav_path)}"
        sf.write(out_name, speech.squeeze().numpy(), target_sr)
        print(f"  ✅ Saved debug output to {out_name}")
        
    except Exception as e:
        print(f"  ❌ Error loading: {e}")

# Test both files
test_load("assets/ref_audio/ref_female.wav")
test_load("assets/ref_audio/ref_male.wav")
