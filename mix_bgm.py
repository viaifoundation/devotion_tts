
import argparse
import os
import sys
from pydub import AudioSegment
import audio_mixer

# CLI Args
parser = argparse.ArgumentParser(
    description="Mix existing audio with background music.",
    formatter_class=argparse.RawTextHelpFormatter,
    epilog="""
Examples:
  # Use default settings (AmazingGrace.mp3, -15dB, 5s intro, 4s tail)
  python mix_bgm.py --input speech.mp3

  # Customize everything
  python mix_bgm.py --input speech.mp3 --bgm-track OHolyNight.mp3 --bgm-volume -10 --bgm-intro 3000 --bgm-tail 5000
"""
)
parser.add_argument("--input", "-i", type=str, required=True, help="Input speech audio file (mp3/wav)")
parser.add_argument("--output", "-o", type=str, help="Output mixed audio file (default: input_bgm.mp3)")
parser.add_argument("--bgm-track", type=str, default="AmazingGrace.mp3", help="Specific BGM filename (Default: AmazingGrace.mp3)")
parser.add_argument("--bgm-volume", type=int, default=-15, help="BGM volume adjustment in dB (Default: -15)")
parser.add_argument("--bgm-intro", type=int, default=5000, help="BGM intro delay in ms (Default: 5000)")
parser.add_argument("--bgm-tail", type=int, default=4000, help="BGM tail delay (after speech) in ms (Default: 4000)")
parser.add_argument("--bgm-dir", type=str, default="assets/bgm", help="Directory for BGM files")

args = parser.parse_args()

INPUT_FILE = args.input
if not os.path.exists(INPUT_FILE):
    print(f"❌ Input file not found: {INPUT_FILE}")
    sys.exit(1)

OUTPUT_FILE = args.output
if not OUTPUT_FILE:
    base, ext = os.path.splitext(INPUT_FILE)
    # Standardized: Just add _bgm, don't include track name
    if "_bgm" not in base:
        OUTPUT_FILE = f"{base}_bgm{ext}"
    else:
        # Avoid potential duplicate _bgm_bgm
        OUTPUT_FILE = f"{base}_mixed{ext}"

print(f"Input: {INPUT_FILE}")
print(f"BGM: {args.bgm_track} (Vol: {args.bgm_volume}dB, Intro: {args.bgm_intro}ms, Tail: {args.bgm_tail}ms)")

try:
    speech = AudioSegment.from_file(INPUT_FILE)
    
    mixed = audio_mixer.mix_bgm(
        speech_audio=speech,
        bgm_dir=args.bgm_dir,
        volume_db=args.bgm_volume,
        intro_delay_ms=args.bgm_intro,
        specific_filename=args.bgm_track,
        tail_delay_ms=args.bgm_tail
    )
    
    mixed.export(OUTPUT_FILE, format="mp3")
    print(f"✅ Success! Saved mixed audio to: {OUTPUT_FILE}")

except Exception as e:
    print(f"❌ Error during mixing: {e}")
    sys.exit(1)
