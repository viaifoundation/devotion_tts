import os
import random
from pydub import AudioSegment

def mix_bgm(speech_audio: AudioSegment, bgm_dir: str = "assets/bgm", volume_db: int = -12, intro_delay_ms: int = 4000, specific_filename: str = None, tail_delay_ms: int = 3000) -> AudioSegment:
    """
    Mixes speech audio with a background music track.
    
    Args:
        speech_audio: The spoken audio segment.
        bgm_dir: Directory containing mp3/wav background music files.
        volume_db: Volume adjustment for the background music (default -12dB).
        intro_delay_ms: How long the music plays before speech starts (ms).
        specific_filename: Optional filename to force use of a specific track.
        tail_delay_ms: How long the music plays after speech ends (ms).
        
    Returns:
        AudioSegment: The mixed audio.
    """
    if not os.path.exists(bgm_dir):
        print(f"⚠️ BGM Directory not found: {bgm_dir}. Skipping BGM.")
        return speech_audio

    # Select track
    bgm_path = None
    if specific_filename:
        if os.path.exists(specific_filename):
            bgm_path = specific_filename
        elif os.path.exists(os.path.join(bgm_dir, specific_filename)):
            bgm_path = os.path.join(bgm_dir, specific_filename)
        elif os.path.exists(os.path.join(bgm_dir, os.path.basename(specific_filename))):
            bgm_path = os.path.join(bgm_dir, os.path.basename(specific_filename))
        else:
            print(f"⚠️ Specific BGM file {specific_filename} not found. Falling back to random track.")

    if not bgm_path:
        files = [f for f in os.listdir(bgm_dir) if f.lower().endswith(('.mp3', '.wav', '.m4a'))]
        if not files:
            print(f"⚠️ No music files found in {bgm_dir}. Skipping BGM.")
            return speech_audio
        bgm_path = os.path.join(bgm_dir, random.choice(files))
        
    bgm_file = os.path.basename(bgm_path)
    print(f"🎵 Adding background music: {bgm_file}")

    try:
        bgm = AudioSegment.from_file(bgm_path)
    except Exception as e:
        print(f"❌ Error loading BGM {bgm_file}: {e}")
        return speech_audio

    # Adjust volume relative to speech audio (e.g. volume_db = -10 dB below speech)
    if len(speech_audio) > 0 and speech_audio.dBFS > -60:
        target_bgm_dBFS = speech_audio.dBFS + volume_db
        gain_needed = target_bgm_dBFS - bgm.dBFS
        bgm = bgm.apply_gain(gain_needed)
    else:
        bgm = bgm + volume_db

    # Calculate total duration required
    speech_len = len(speech_audio)
    # Total length = intro + speech + tail
    total_len = intro_delay_ms + speech_len + tail_delay_ms

    # Process BGM Loop
    # If BGM is shorter than needed, loop it
    if len(bgm) < total_len:
        loops = (total_len // len(bgm)) + 1
        bgm = bgm * loops
    
    # Trim to exact length
    bgm = bgm[:total_len]

    # Fade in/out BGM
    bgm = bgm.fade_in(2000).fade_out(tail_delay_ms)

    # Overlay speech onto BGM with delay
    final_mix = bgm.overlay(speech_audio, position=intro_delay_ms)

    return final_mix
