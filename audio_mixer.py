import os
import random
from pydub import AudioSegment

def mix_bgm(speech_audio: AudioSegment, bgm_dir: str = "assets/bgm", volume_db: int = -12, intro_delay_ms: int = 4000, specific_filename: str = None) -> AudioSegment:
    """
    Mixes speech audio with a background music track.
    
    Args:
        speech_audio: The spoken audio segment.
        bgm_dir: Directory containing mp3/wav background music files.
        volume_db: Volume adjustment for the background music (default -12dB).
        intro_delay_ms: How long the music plays before speech starts (ms).
        specific_filename: Optional filename to force use of a specific track.
        
    Returns:
        AudioSegment: The mixed audio.
    """
    if not os.path.exists(bgm_dir):
        print(f"⚠️ BGM Directory not found: {bgm_dir}. Skipping BGM.")
        return speech_audio

    # Select track
    bgm_file = None
    if specific_filename:
        # Check if specific file exists
        if os.path.exists(os.path.join(bgm_dir, specific_filename)):
             bgm_file = specific_filename
        else:
             print(f"⚠️ Specific BGM file {specific_filename} not found in {bgm_dir}. Falling back to random.")

    if not bgm_file:
        files = [f for f in os.listdir(bgm_dir) if f.lower().endswith(('.mp3', '.wav', '.m4a'))]
        if not files:
            print(f"⚠️ No music files found in {bgm_dir}. Skipping BGM.")
            return speech_audio
        bgm_file = random.choice(files)
        
    bgm_path = os.path.join(bgm_dir, bgm_file)
    print(f"🎵 Adding background music: {bgm_file}")

    try:
        bgm = AudioSegment.from_file(bgm_path)
    except Exception as e:
        print(f"❌ Error loading BGM {bgm_file}: {e}")
        return speech_audio

    # Adjust volume
    bgm = bgm + volume_db

    # Calculate total duration required
    speech_len = len(speech_audio)
    # Total length = intro + speech + 3s tail
    total_len = intro_delay_ms + speech_len + 3000

    # Process BGM Loop
    # If BGM is shorter than needed, loop it
    if len(bgm) < total_len:
        loops = (total_len // len(bgm)) + 1
        bgm = bgm * loops
    
    # Trim to exact length
    bgm = bgm[:total_len]

    # Fade in/out BGM
    bgm = bgm.fade_in(2000).fade_out(3000)

    # Overlay speech onto BGM with delay
    final_mix = bgm.overlay(speech_audio, position=intro_delay_ms)

    return final_mix
