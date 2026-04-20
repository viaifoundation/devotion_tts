"""
gen_votd_cosy3.py – Enhanced Verse of the Day Audio Generator (CosyVoice 3.0)

Based on gen_votd_edge.py, replaces Edge TTS with Fun-CosyVoice 3.0 (0.5B)
for highest accuracy Chinese TTS (CER 0.81%).

Features:
  1. CUV-only Bible verse TTS in the verse section
  2. Bible Audio section: 6 readings (5 translations, CUV bookends) per verse + full chapter (Everest)
  3. Auto-expands verse references from input.txt using local SQLite Bible DB
  4. Zero-shot voice cloning with reference audio

Input: input.txt (simple format with verse references like (詩篇 77:12 和合本))
Output: Exports two versions:
  - Short Version: `_short.mp3` + `_short.txt` (Contains Essay + Prayer + Credits)
  - Long Version: `.mp3` + `.txt` (Includes all of the above + multi-translation Bible audio + Chapter audio)

Usage:
  python gen_votd_cosy3.py -i input.txt
  python gen_votd_cosy3.py -i input.txt --voice rotate --bgm
  python gen_votd_cosy3.py -i input.txt --bible-bgm-volume -18 --speech-volume 6
"""

import torch
import numpy as np
import sys
import os
import re
import warnings
import argparse
from datetime import datetime
from typing import Optional, Tuple

# Silence noisy libraries
warnings.filterwarnings("ignore", category=FutureWarning, module="diffusers")
warnings.filterwarnings("ignore", category=UserWarning, module="lightning")

from pydub import AudioSegment

# Setup path to find CosyVoice (sibling directory)
COSYVOICE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../CosyVoice"))
MATCHA_PATH = os.path.join(COSYVOICE_PATH, "third_party", "Matcha-TTS")

if os.path.exists(COSYVOICE_PATH):
    sys.path.append(COSYVOICE_PATH)
    if os.path.exists(MATCHA_PATH):
        sys.path.append(MATCHA_PATH)
    else:
        print(f"⚠️ Warning: Matcha-TTS not found at {MATCHA_PATH}")
        print("Run: cd ../CosyVoice && git submodule update --init --recursive")
else:
    print(f"⚠️ Warning: CosyVoice path not found at {COSYVOICE_PATH}")
    print("Please clone it: git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git ../CosyVoice")

try:
    from cosyvoice.cli.cosyvoice import AutoModel
    from cosyvoice.utils.file_utils import load_wav
except ImportError as e:
    print(f"❌ Failed to import CosyVoice: {e}")
    print(f"Ensure you have cloned the repo to {COSYVOICE_PATH} and installed its requirements.")
    sys.exit(1)

from bible_parser import convert_bible_reference
from date_parser import convert_dates_in_text
from text_cleaner import clean_text_basic, clean_text_for_tts
import filename_parser
import audio_mixer
from mp3_to_mp4 import create_mp4, DEFAULT_BG
from bible_db import BibleDB, parse_verse_reference, book_number_to_chinese
from chapter_narration_gain import CHAPTER_VOICE_CHOICES, boost_db_for_chapter_voice
from votd_narration_chapter import load_narration_chapter_mp3

# --- Configuration ---
DEFAULT_REF_TEXT = "然而，靠着爱我们的主，在这一切的事上已经得胜有余了。"
MODEL_DIR = "pretrained_models/Fun-CosyVoice3-0.5B"

# Voice presets (Edge TTS-generated reference audio for CosyVoice zero-shot cloning)
VOICE_MALE_PRO = "assets/ref_audio/ref_edge_zh_male_pro.wav"        # YunyangNeural - Professional
VOICE_MALE_SUNSHINE = "assets/ref_audio/ref_edge_zh_male_sunshine.wav"  # YunxiNeural - Lively
VOICE_MALE_PASSION = "assets/ref_audio/ref_edge_zh_male_passion.wav"  # YunjianNeural - Passion
VOICE_FEMALE_WARM = "assets/ref_audio/ref_edge_zh_female_warm.wav"    # XiaoxiaoNeural - Warm
VOICE_FEMALE_LIVELY = "assets/ref_audio/ref_edge_zh_female_lively.wav"  # XiaoyiNeural - Lively
VOICE_MALE_CUTE = "assets/ref_audio/ref_edge_zh_male_cute.wav"        # YunxiaNeural - Cute

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CHAPTERS_DIR_EVEREST = os.path.join(SCRIPT_DIR, "assets", "bible", "audio", "chapters")
CHAPTERS_DIR_DAVIDYEN = os.path.join(SCRIPT_DIR, "assets", "bible", "audio", "chapters_davidyen")
BIBLE_BGM_DIR = os.path.join(SCRIPT_DIR, "assets", "bible", "bgm")

_chapter_voice_rotation_idx = 0  # Global counter for rotation


def build_preset_voices(voices_str, ref_text):
    """Build PRESET_VOICES list from comma-separated voice files."""
    voices = []
    for voice_path in voices_str.split(","):
        voice_path = voice_path.strip()
        if voice_path:
            voices.append({
                "name": os.path.basename(voice_path),
                "audio": voice_path,
                "text": ref_text
            })
    return voices


# ─── CLI Args ───
if "-?" in sys.argv or "-h" in sys.argv or "--help" in sys.argv:
    print(f"Usage: python {sys.argv[0]} [OPTIONS]")
    print("\nFun-CosyVoice 3.0 VOTD - Highest accuracy Chinese TTS (CER 0.81%)")
    print("\nOptions:")
    print("  --input FILE, -i     Text file to read input from")
    print("  --prefix PREFIX      Filename prefix (e.g. MyPrefix)")
    print("  --voice MODE         Voice mode: male, female, two, four, six (Default: six)")
    print("  --voices LIST        Custom voices (CSV, overrides --voice)")
    print("  --ref-text TEXT      Reference text for voice cloning")
    print("  --bgm                Enable background music for non-bible sections")
    print("  --bgm-track TRACK    BGM filename (Default: AmazingGrace.MP3)")
    print("  --bgm-volume VOL     BGM volume in dB (Default: -20)")
    print("  --bgm-intro MS       BGM intro delay in ms (Default: 4000)")
    print("  --bible-bgm-volume   Bible chapter BGM volume in dB (Default: -20)")
    print("  --bible-bgm-intro    Bible chapter BGM intro delay in ms (Default: 4000)")
    print("  --speech-volume VOL  Boost for chapter speech in dB (Default: 4)")
    print("  --chapter-speed SPD  Speed multiplier for Everest chapter audio (Default: 1.5)")
    print("  --bible-db PATH      Path to bible.sqlite (Default: assets/bible/bible.sqlite)")
    print("  --mp4                Generate MP4 video from audio")
    print("  --mp4-bg IMAGE       Background image for MP4")
    print("  --mp4-res RES        MP4 resolution (Default: 1920x1080)")
    print("  --chapter-voice V    everest | davidyen | rotate | rotate_male_first | rotate_female_first")
    print("  --debug, -d LEVEL    Debug level: 0=minimal, 1=progress, 2=full")
    print("  -?, -h, --help       Show this help")
    print("\nVoice Modes:")
    print("  male    - Single male voice (Professional)")
    print("  female  - Single female voice (Warm)")
    print("  two     - Rotate 2 voices (1 male + 1 female)")
    print("  four    - Rotate 4 voices (2 male + 2 female)")
    print("  six     - Rotate all 6 voices (Default)")
    print("\nExamples:")
    print(f"  python {sys.argv[0]} -i input.txt")
    print(f"  python {sys.argv[0]} -i input.txt --voice rotate --bgm")
    print(f"  python {sys.argv[0]} -i input.txt --bible-bgm-volume -18")
    sys.exit(0)

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("--input", "-i", type=str, help="Input text file")
parser.add_argument("--prefix", type=str, default=None, help="Filename prefix")
parser.add_argument("--voice", type=str, default="six", choices=["male", "female", "two", "four", "six"],
                    help="Voice mode: male, female, two, four, six")
parser.add_argument("--voices", type=str, default=None,
                    help="Custom voices (CSV format, overrides --voice)")
parser.add_argument("--ref-text", type=str, default=DEFAULT_REF_TEXT, help="Reference text for voice cloning")
parser.add_argument("--bgm", action="store_true", help="Enable background music for non-bible sections")
parser.add_argument("--bgm-track", type=str, default="AmazingGrace.MP3", help="BGM filename")
parser.add_argument("--bgm-volume", type=int, default=-20, help="BGM volume in dB")
parser.add_argument("--bgm-intro", type=int, default=4000, help="BGM intro delay in ms")
parser.add_argument("--bible-bgm-volume", type=int, default=-20, help="Bible chapter BGM volume in dB")
parser.add_argument("--bible-bgm-intro", type=int, default=4000, help="Bible chapter BGM intro delay in ms")
parser.add_argument(
    "--speech-volume",
    type=int,
    default=4,
    help="Extra chapter speech gain in dB (after per-source leveling; default 4)",
)
parser.add_argument("--chapter-speed", type=float, default=1.5, help="Speed multiplier for Everest chapter audio (Default: 1.5)")
parser.add_argument("--bible-db", type=str, default=None, help="Path to bible.sqlite")
parser.add_argument("--mp4", action="store_true", help="Generate MP4 video from audio")
parser.add_argument("--mp4-bg", type=str, default=DEFAULT_BG, help="Background image for MP4")
parser.add_argument("--mp4-res", type=str, default="1920x1080", help="MP4 resolution")
parser.add_argument(
    "--chapter-voice",
    type=str,
    default="rotate",
    choices=CHAPTER_VOICE_CHOICES,
    help="Recorded chapter: everest/davidyen fixed; rotate*=alternate male-first or female-first",
)
parser.add_argument("--debug", "-d", type=int, default=0, choices=[0, 1, 2], help="Debug level")

args, unknown = parser.parse_known_args()
CLI_PREFIX = args.prefix
ENABLE_BGM = args.bgm
BGM_FILE = args.bgm_track
BGM_VOLUME = args.bgm_volume
BGM_INTRO_DELAY = args.bgm_intro
DEBUG_LEVEL = args.debug

# Voice mode configuration
if args.voices:
    VOICES_STR = args.voices
    print(f"🎤 Custom voices: {args.voices}")
elif args.voice == "male":
    VOICES_STR = VOICE_MALE_PRO
    print(f"🎤 Voice mode: male (Professional)")
elif args.voice == "female":
    VOICES_STR = VOICE_FEMALE_WARM
    print(f"🎤 Voice mode: female (Warm)")
elif args.voice == "two":
    VOICES_STR = f"{VOICE_MALE_PRO},{VOICE_FEMALE_WARM}"
    print(f"🎤 Voice mode: two (rotating 2 voices)")
elif args.voice == "four":
    VOICES_STR = f"{VOICE_MALE_PRO},{VOICE_FEMALE_WARM},{VOICE_MALE_SUNSHINE},{VOICE_FEMALE_LIVELY}"
    print(f"🎤 Voice mode: four (rotating 4 voices)")
else:  # six (default)
    VOICES_STR = f"{VOICE_MALE_PRO},{VOICE_FEMALE_WARM},{VOICE_MALE_SUNSHINE},{VOICE_FEMALE_LIVELY},{VOICE_MALE_PASSION},{VOICE_MALE_CUTE}"
    print(f"🎤 Voice mode: six (rotating 6 voices)")


# ─── Input text loading ───
if args.input:
    print(f"Reading text from file: {args.input}")
    with open(args.input, "r", encoding="utf-8") as f:
        TEXT = f.read()
elif not sys.stdin.isatty():
    print("Reading text from Stdin...")
    TEXT = sys.stdin.read()
else:
    print("❌ No input provided. Use --input or pipe text via stdin.")
    sys.exit(1)


# ─── Model Loading ───
print("Loading Fun-CosyVoice 3.0 (0.5B) - CER 0.81% (SOTA)...")
try:
    use_cuda = torch.cuda.is_available()
    print(f"Loading Fun-CosyVoice3-0.5B... [CUDA={use_cuda}]")

    # Check if model exists locally, otherwise use HuggingFace path
    if os.path.exists(os.path.join(COSYVOICE_PATH, MODEL_DIR)):
        model_path = os.path.join(COSYVOICE_PATH, MODEL_DIR)
    elif os.path.exists(MODEL_DIR):
        model_path = MODEL_DIR
    else:
        model_path = 'FunAudioLLM/Fun-CosyVoice3-0.5B-2512'
        print(f"Model not found locally, attempting to download from: {model_path}")

    cosyvoice = AutoModel(model_dir=model_path)
    if hasattr(cosyvoice, 'fp16'):
        print("🔧 Forcing FP32 (disabling FP16) to prevent audio noise...")
        cosyvoice.fp16 = False

    SAMPLE_RATE = cosyvoice.sample_rate
    print(f"✅ Fun-CosyVoice 3.0 loaded successfully (sample_rate={SAMPLE_RATE})")

except Exception as e:
    print(f"❌ Error loading Fun-CosyVoice 3.0: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


# ─── Filename generation ───
TEXT = clean_text_basic(TEXT)
first_line = TEXT.strip().split('\n')[0]

date_match = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", first_line)
if date_match:
    m, d, y = date_match.groups()
    date_str = f"{y}-{int(m):02d}-{int(d):02d}"
else:
    date_match = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", first_line)
    if date_match:
        y, m, d = date_match.groups()
        date_str = f"{y}-{int(m):02d}-{int(d):02d}"
    else:
        date_str = datetime.today().strftime("%Y-%m-%d")

verse_ref = filename_parser.extract_verse_from_text(TEXT)

extracted_prefix = CLI_PREFIX if CLI_PREFIX else filename_parser.extract_filename_prefix(TEXT)
filename = filename_parser.generate_filename_v2(
    title=first_line,
    date=date_str,
    prefix=extracted_prefix,
    ext=".mp3"
).replace(".mp3", "_votd_cosy3.mp3")

if ENABLE_BGM:
    filename = filename.replace(".mp3", "_bgm.mp3")

OUTPUT_DIR = os.path.join(os.getcwd(), "output")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
OUTPUT_PATH = os.path.join(OUTPUT_DIR, filename)
print(f"Target Output: {OUTPUT_PATH}")


# ─── Helpers ───

def _speedup_ffmpeg(seg: AudioSegment, speed: float) -> AudioSegment:
    """Speed up using ffmpeg atempo (preserves pitch). Chains atempo for speed > 2."""
    import tempfile
    import subprocess
    from pathlib import Path
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        tmp_in = f.name
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        tmp_out = f.name
    try:
        seg.export(tmp_in, format="wav")
        parts = []
        r = speed
        while r > 2.0:
            parts.append("atempo=2")
            r /= 2.0
        if r > 1.0:
            parts.append(f"atempo={r}")
        filter_str = ",".join(parts) if parts else "atempo=1"
        subprocess.run(
            ["ffmpeg", "-y", "-i", tmp_in, "-filter:a", filter_str, tmp_out],
            check=True, capture_output=True
        )
        return AudioSegment.from_wav(tmp_out)
    finally:
        Path(tmp_in).unlink(missing_ok=True)
        Path(tmp_out).unlink(missing_ok=True)


def _load_chapter_audio(
    book_num: int, chapter_num: int, speed: float = 1.0
) -> Tuple[Optional[AudioSegment], Optional[str]]:
    """Load pre-recorded chapter MP3 from Everest or David Yen directories."""
    global _chapter_voice_rotation_idx
    seg, v_name, _chapter_voice_rotation_idx = load_narration_chapter_mp3(
        args.chapter_voice,
        book_num,
        chapter_num,
        CHAPTERS_DIR_EVEREST,
        CHAPTERS_DIR_DAVIDYEN,
        _chapter_voice_rotation_idx,
        speed,
        _speedup_ffmpeg,
    )
    return seg, v_name


def parse_input_sections(text: str) -> dict:
    """
    Parse input.txt format (simple format) into sections:
    1. Title (first line)
    2. Verse paragraphs (each ending with (BookName X:Y 和合本))
    3. Essay titles (3 repeated short paragraphs)
    4. Essay body
    5. Prayer
    6. Credits
    """
    text = text.strip()
    paragraphs = [p.strip() for p in re.split(r'\n{2,}', text) if p.strip()]

    result = {
        'title': paragraphs[0] if paragraphs else '',
        'verse_refs': [],
        'verse_texts': [],
        'essay_titles': [],
        'essay_body': [],
        'prayer': '',
        'credits': []
    }

    if len(paragraphs) < 5:
        print(f"⚠️ Too few paragraphs ({len(paragraphs)}). Falling back to simple mode.")
        return result

    idx = 1

    # Collect verse paragraphs
    verse_end_idx = idx
    for i in range(idx, len(paragraphs)):
        para = paragraphs[i]
        has_ref = bool(re.search(r'\([^\)]*和合本\s*\)', para))
        if has_ref:
            verse_end_idx = i + 1
        else:
            break

    for i in range(idx, verse_end_idx):
        para = paragraphs[i]
        result['verse_texts'].append(para)
        ref_match = re.search(r'\(([^\)]+和合本)\)', para)
        if ref_match:
            ref = parse_verse_reference(ref_match.group(0))
            if ref:
                result['verse_refs'].append(ref)
            else:
                print(f"  ⚠️ Could not parse verse reference: {ref_match.group(0)}")

    idx = verse_end_idx

    # Essay titles
    essay_title_count = 0
    while idx < len(paragraphs) and essay_title_count < 3:
        para = paragraphs[idx]
        if len(para) < 50 and not re.search(r'https?://', para):
            result['essay_titles'].append(para)
            essay_title_count += 1
            idx += 1
        else:
            break

    # Essay body, prayer, credits
    credit_markers = ["內容來自", "聖經語音", "閱讀聆聽", "Verse of the Day", "Youversion", "Everest"]
    remaining = paragraphs[idx:]

    credits_start = len(remaining)
    for i in range(len(remaining) - 1, -1, -1):
        is_credit = any(marker in remaining[i] for marker in credit_markers)
        if is_credit:
            credits_start = i
        else:
            break

    body_and_prayer = remaining[:credits_start]
    result['credits'] = remaining[credits_start:]

    # Extract trailing verses
    trailing_verses = []
    trailing_refs = []
    while body_and_prayer:
        last = body_and_prayer[-1]
        ref_match = re.search(r'\(([^\)]+和合本)\)', last)
        if ref_match:
            trailing_verses.insert(0, last)
            body_and_prayer.pop()
            ref = parse_verse_reference(ref_match.group(0))
            if ref:
                trailing_refs.insert(0, ref)
            else:
                print(f"  ⚠️ Could not parse trailing verse reference: {ref_match.group(0)}")
        else:
            break

    result['verse_texts'].extend(trailing_verses)
    result['verse_refs'].extend(trailing_refs)

    # Prayer
    if body_and_prayer:
        prayer_start_idx = -1
        for i in range(len(body_and_prayer)):
            if body_and_prayer[i].strip() == "禱告":
                prayer_start_idx = i
                break

        if prayer_start_idx != -1:
            result['prayer'] = "\n\n".join(body_and_prayer[prayer_start_idx:])
            result['essay_body'] = body_and_prayer[:prayer_start_idx]
        else:
            last = body_and_prayer[-1]
            if "阿們" in last or "阿门" in last or "奉耶穌的名" in last or "奉耶稣的名" in last:
                result['prayer'] = last
                result['essay_body'] = body_and_prayer[:-1]
            else:
                result['essay_body'] = body_and_prayer

    return result


def tts_prep(text: str) -> str:
    """Prepare text for TTS: convert references, dates, clean with focus on pronunciation."""
    text = convert_bible_reference(text)
    text = convert_dates_in_text(text)
    text = clean_text_for_tts(text)
    return text


def generate_audio(text: str, ref_audio: str, ref_text: str) -> AudioSegment:
    """Generate TTS audio using Fun-CosyVoice 3.0 zero-shot voice cloning."""
    print(f"  🔊 TTS ({os.path.basename(ref_audio)}): {text[:60]}...")

    if DEBUG_LEVEL >= 2:
        print(f"  DEBUG: Full text: {text}")

    try:
        if ref_audio and os.path.exists(ref_audio):
            prompt_text = f"You are a helpful assistant.<|endofprompt|>{ref_text or ''}"
            output_gen = cosyvoice.inference_zero_shot(
                text,
                prompt_text,
                ref_audio,
                stream=False
            )
        else:
            output_gen = cosyvoice.inference_cross_lingual(
                text,
                './asset/zero_shot_prompt.wav',
                stream=False
            )

        final_audio = AudioSegment.empty()
        for item in output_gen:
            if 'tts_speech' in item:
                audio_np = item['tts_speech'].numpy()
                audio_np = np.nan_to_num(audio_np, nan=0.0, posinf=1.0, neginf=-1.0)
                audio_int16 = (audio_np * 32767).astype(np.int16)
                segment = AudioSegment(
                    audio_int16.tobytes(),
                    frame_rate=SAMPLE_RATE,
                    sample_width=2,
                    channels=1
                )
                final_audio += segment

        return final_audio

    except Exception as e:
        print(f"  ❌ Error in TTS: {e}")
        if DEBUG_LEVEL >= 2:
            import traceback
            traceback.print_exc()
        return AudioSegment.silent(duration=500)


# ─── Build voice list ───
PRESET_VOICES = build_preset_voices(VOICES_STR, args.ref_text)
available_voices = []
for voice in PRESET_VOICES:
    voice_path = os.path.abspath(voice["audio"])
    if os.path.exists(voice_path):
        available_voices.append({"audio": voice_path, "text": voice["text"], "name": voice.get("name", "Unknown")})

if not available_voices:
    print("❌ No voice files found. Please add reference audio to assets/ref_audio/")
    sys.exit(1)

print(f"🔄 {len(available_voices)} voice(s) available for rotation")


def main():
    global_voice_idx = 0

    def get_next_voice():
        nonlocal global_voice_idx
        voice = available_voices[global_voice_idx % len(available_voices)]
        global_voice_idx += 1
        return voice

    # Parse input sections
    sections = parse_input_sections(TEXT)

    print(f"\n📋 Parsed input.txt sections:")
    print(f"  Title: {sections['title'][:50]}...")
    print(f"  Verse refs: {len(sections['verse_refs'])}")
    for ref in sections['verse_refs']:
        book_name = book_number_to_chinese(ref[0])
        print(f"    {book_name} {ref[1]}:{ref[2]}-{ref[3]}")
    print(f"  Essay titles: {len(sections['essay_titles'])}")
    print(f"  Essay body: {len(sections['essay_body'])} paragraphs")
    print(f"  Prayer: {'Yes' if sections['prayer'] else 'No'}")
    print(f"  Credits: {len(sections['credits'])} lines")

    # Open Bible DB for verse expansion
    db = None
    try:
        db = BibleDB(args.bible_db)
        print(f"\n📖 Bible DB loaded: {db.db_path}")
    except FileNotFoundError as e:
        print(f"\n⚠️ {e}")
        print("   Verse expansion disabled. Only original verse text will be used.")

    # Expand verse blocks using the DB
    expanded_blocks = []
    if db and sections['verse_refs']:
        print(f"\n--- Expanding {len(sections['verse_refs'])} verse(s) ---")
        for ref in sections['verse_refs']:
            book_num, chapter, v_start, v_end = ref
            block = db.expand_verse_block(book_num, chapter, v_start, v_end)
            expanded_blocks.append(block)
            book_name = book_number_to_chinese(book_num)
            print(f"  📖 {book_name} {chapter}:{v_start}-{v_end}")
            print(f"      Chapter: {len(block['chapter_text'])} chars")
            print(f"      Translations: {len(block['translations'])}")

    final_segments = []
    txt_lines = []

    SILENCE_SHORT = AudioSegment.silent(duration=700)
    SILENCE_SECTION = AudioSegment.silent(duration=1000)

    # ─── Section 1: Title ───
    print(f"\n--- Section 1: Title ---")
    if sections['title']:
        voice = get_next_voice()
        seg = generate_audio(tts_prep(sections['title']), voice["audio"], voice["text"])
        final_segments.append(seg)
        txt_lines.append(clean_text_basic(sections['title']))
        txt_lines.append("")

    # ─── Section 2: Verse (CUV only) ───
    print(f"\n--- Section 2: Verse (CUV only) ---")
    chapter_txt_lines = []
    bible_audio_blocks = []

    if expanded_blocks:
        for block_idx, block in enumerate(expanded_blocks):
            print(f"\n  📖 Verse Block {block_idx + 1}")
            book_num = block['book_num']
            chapter_num = block['chapter_num']

            ch_seg, ch_voice_name = _load_chapter_audio(book_num, chapter_num, speed=args.chapter_speed)
            if ch_seg is not None:
                if not ch_voice_name:
                    print("  ⚠️ Internal error: chapter audio present but voice label is empty")
                base_boost = boost_db_for_chapter_voice(ch_voice_name)
                total_boost = base_boost + args.speech_volume
                
                if total_boost != 0:
                    ch_seg = ch_seg + total_boost

            if block['chapter_text']:
                chapter_txt_lines.append(block['chapter_text'])
                chapter_txt_lines.append(f"({block['chapter_ref']})")
                chapter_txt_lines.append("")
                if block['translations']:
                    chapter_txt_lines.append(block['translations'][0][2])
                    chapter_txt_lines.append(f"({block['translations'][0][3]})")
                    chapter_txt_lines.append("")
            else:
                if block_idx < len(sections['verse_texts']):
                    chapter_txt_lines.append(sections['verse_texts'][block_idx])
                    chapter_txt_lines.append("")

            bible_audio_blocks.append({
                'translations': block['translations'],
                'chapter_seg': ch_seg,
                'chapter_voice': ch_voice_name,
                'block_idx': block_idx,
            })

            # TTS the CUV (first) translation
            if block['translations']:
                final_segments.append(SILENCE_SECTION)
                code, label, text, ref_str = block['translations'][0]
                voice = get_next_voice()
                tts_text = f"{text}\n({ref_str})"
                seg = generate_audio(tts_prep(tts_text), voice["audio"], voice["text"])
                final_segments.append(seg)
                txt_lines.append(clean_text_basic(text))
                txt_lines.append(f"({ref_str})")
                txt_lines.append("")
    else:
        for v_idx, verse_text in enumerate(sections['verse_texts']):
            voice = get_next_voice()
            seg = generate_audio(tts_prep(verse_text), voice["audio"], voice["text"])
            final_segments.append(SILENCE_SECTION)
            final_segments.append(seg)
            txt_lines.append(verse_text)
            txt_lines.append("")

    # ─── Section 3: Essay Titles ───
    print(f"\n--- Section 3: Essay Titles ---")
    for et_idx, essay_title in enumerate(sections['essay_titles']):
        voice = get_next_voice()
        seg = generate_audio(tts_prep(essay_title), voice["audio"], voice["text"])
        final_segments.append(SILENCE_SECTION)
        final_segments.append(seg)
        txt_lines.append(clean_text_basic(essay_title))
        txt_lines.append("")

    # ─── Section 4: Essay Body ───
    print(f"\n--- Section 4: Essay Body ---")
    if sections['essay_body']:
        for eb_idx, essay_para in enumerate(sections['essay_body']):
            voice = get_next_voice()
            seg = generate_audio(tts_prep(essay_para), voice["audio"], voice["text"])
            final_segments.append(SILENCE_SECTION)
            final_segments.append(seg)
            txt_lines.append(clean_text_basic(essay_para))
            txt_lines.append("")

    # ─── Section 5: Prayer (voice rotation per paragraph) ───
    print(f"\n--- Section 5: Prayer ---")
    if sections['prayer']:
        prayer_paras = [p.strip() for p in sections['prayer'].split("\n\n") if p.strip()]
        print(f"  Prayer has {len(prayer_paras)} paragraph(s)")
        for pr_idx, prayer_para in enumerate(prayer_paras):
            voice = get_next_voice()
            seg = generate_audio(tts_prep(prayer_para), voice["audio"], voice["text"])
            final_segments.append(SILENCE_SECTION)
            final_segments.append(seg)
            txt_lines.append(clean_text_basic(prayer_para))
            txt_lines.append("")

    # ─── Section 6: Automatic Footer & Credits ───
    print(f"\n--- Section 6: Automatic Footer & Credits ---")
    
    # 1. Start with manual credits from input.txt (if any)
    footer_lines = [c for c in sections['credits'] if c.strip()]
    
    # 2. Add Source Credit
    footer_lines.append("內容取自 YouVersion「今日經文」(Verse of the Day)。")
    
    # 3. Add Dynamic Voice Attribution
    attributed_voices = list(set([b['chapter_voice'] for b in bible_audio_blocks if b.get('chapter_seg')]))
    if attributed_voices:
        if "David Yen" in attributed_voices and "Everest" in attributed_voices:
            footer_lines.append("聖經語音由 Everest (女聲) 與 閻大衛 (男聲) 老師提供。")
        elif "David Yen" in attributed_voices:
            footer_lines.append("聖經語音由 閻大衛 (男聲) 老師提供。")
        else:
            footer_lines.append("聖經語音由 Everest (女聲) 提供。" )
            
    # 4. Add Foundation Credit
    footer_lines.append("閱讀聆聽，盡在唯愛 AI 基金會。官網：v o t d 點 v i 點 f y i")

    # 5. End with the Title (thematic recap)
    if sections['title']:
        footer_lines.append(sections['title'])

    # Store footer_lines for reuse in Section 8
    sections['footer_lines'] = footer_lines

    credits_audio_segments = []
    for cr_idx, credit in enumerate(footer_lines):
        voice = get_next_voice()
        print(f"  🎙️ Footer Line {cr_idx+1}: {credit}")
        temp_file = os.path.join(OUTPUT_DIR, f"temp_votd_credit_{cr_idx}.wav")
        try:
            model.tts(text=tts_prep(credit), speaker_wav=voice["audio"], prompt_text=voice["text"], output_file=temp_file)
            seg = AudioSegment.from_wav(temp_file)
            final_segments.append(SILENCE_SECTION)
            final_segments.append(seg)
            credits_audio_segments.append(SILENCE_SECTION)
            credits_audio_segments.append(seg)
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
        # In the text file, use the real URL
        txt_credit = credit.replace("v o t d 點 v i 點 f y i", "https://votd.vi.fyi")
        txt_lines.append(txt_credit)
        txt_lines.append("")

    # ─── Combine and Export Short Version ───
    print(f"\n--- Combining Short Version ({len(final_segments)} segments) ---")
    short_final = AudioSegment.empty()
    for seg in final_segments:
        short_final += seg

    # Convert to 24kHz for consistency
    short_final = short_final.set_frame_rate(24000)

    if ENABLE_BGM:
        print(f"🎵 Mixing Overall BGM for Short Version...")
        short_final = audio_mixer.mix_bgm(
            short_final,
            specific_filename=BGM_FILE,
            volume_db=BGM_VOLUME,
            intro_delay_ms=BGM_INTRO_DELAY
        )

    PRODUCER = "唯愛 AI 基金會 (VI AI Foundation)"
    TITLE = sections['title']
    ALBUM = "今日經文 VOTD"
    bgm_info = os.path.basename(BGM_FILE) if ENABLE_BGM else "None"
    COMMENTS = f"Verse: {verse_ref}; Model: Fun-CosyVoice3; BGM: {bgm_info}"

    short_output_path = OUTPUT_PATH.replace(".mp3", "_short.mp3")
    short_final.export(short_output_path, format="mp3", bitrate="192k", tags={
        'title': f"{TITLE} (Short)",
        'artist': PRODUCER,
        'album': ALBUM,
        'comments': COMMENTS
    })
    print(f"\n✅ Short version saved: {short_output_path}")

    txt_output_short = OUTPUT_PATH.replace(".mp3", "_short.txt")
    with open(txt_output_short, "w", encoding="utf-8") as f:
        f.write("\n".join(txt_lines))
    print(f"📝 Short Text saved: {txt_output_short}")

    # ─── Section 7: Bible Audio (added to long version) ───
    if bible_audio_blocks:
        print(f"\n--- Section 7: Bible Audio ({len(bible_audio_blocks)} verse blocks) ---")
        for ba_block in bible_audio_blocks:
            translations = ba_block['translations']
            ch_seg = ba_block['chapter_seg']
            block_idx = ba_block['block_idx']

            # 7a. TTS all translations
            if translations:
                print(f"  🔁 Verse block {block_idx + 1}: {len(translations)} translation readings")
                final_segments.append(SILENCE_SECTION)
                for t_idx, (code, label, text, ref_str) in enumerate(translations):
                    voice = get_next_voice()
                    tts_text = f"{text}\n({ref_str})"
                    seg = generate_audio(tts_prep(tts_text), voice["audio"], voice["text"])
                    final_segments.append(seg)
                    if t_idx < len(translations) - 1:
                        final_segments.append(SILENCE_SHORT)
                    txt_lines.append(text)
                    txt_lines.append(f"({ref_str})")
                txt_lines.append("")

            # 7b. Full chapter audio (Everest pre-recorded)
            if ch_seg is not None:
                print(f"  📖 Appending chapter audio for block {block_idx + 1} ({len(ch_seg)/1000:.1f}s)")
                final_segments.append(SILENCE_SECTION)
                final_segments.append(ch_seg)

            # 7c. CUV again after chapter
            if translations:
                print(f"  🔁 Appending CUV verse again for block {block_idx + 1}")
                final_segments.append(SILENCE_SECTION)
                code, label, text, ref_str = translations[0]
                voice = get_next_voice()
                tts_text = f"{text}\n({ref_str})"
                seg = generate_audio(tts_prep(tts_text), voice["audio"], voice["text"])
                final_segments.append(seg)

        txt_lines.extend(chapter_txt_lines)

    # ─── Section 8: Final Credits (copy) ───
    print(f"\n--- Section 8: Final Credits (copy) ---")
    for seg in credits_audio_segments:
        final_segments.append(seg)
    # Also repeat in txt_lines for the long version
    for credit in sections.get('footer_lines', []):
        # Use real URL for text file
        txt_credit = credit.replace("v o t d 點 v i 點 f y i", "https://votd.vi.fyi")
        txt_lines.append(txt_credit)
        txt_lines.append("")

    # ─── Combine and Export Long Version ───
    print(f"\n--- Combining Long Version ({len(final_segments)} segments) ---")
    long_final = AudioSegment.empty()
    for seg in final_segments:
        long_final += seg

    # Convert to 24kHz for consistency
    long_final = long_final.set_frame_rate(24000)

    if ENABLE_BGM:
        print(f"🎵 Mixing Overall BGM for Long Version...")
        long_final = audio_mixer.mix_bgm(
            long_final,
            specific_filename=BGM_FILE,
            volume_db=BGM_VOLUME,
            intro_delay_ms=BGM_INTRO_DELAY
        )

    long_output_path = OUTPUT_PATH
    long_final.export(long_output_path, format="mp3", bitrate="192k", tags={
        'title': TITLE,
        'artist': PRODUCER,
        'album': ALBUM,
        'comments': COMMENTS
    })
    print(f"\n✅ Long version saved: {long_output_path}")

    txt_output_long = OUTPUT_PATH.replace(".mp3", ".txt")
    with open(txt_output_long, "w", encoding="utf-8") as f:
        f.write("\n".join(txt_lines))
    print(f"📝 Text saved: {txt_output_long}")

    # ─── Generate MP4 if requested ───
    if args.mp4:
        mp4_output = OUTPUT_PATH.replace(".mp3", ".mp4")
        bg_path = args.mp4_bg
        if not os.path.isabs(bg_path):
            bg_path = os.path.join(SCRIPT_DIR, bg_path)
        if os.path.exists(bg_path):
            success = create_mp4(
                input_mp3=OUTPUT_PATH,
                bg_image=bg_path,
                output_mp4=mp4_output,
                resolution=args.mp4_res
            )
            if not success:
                print("⚠️ MP4 generation failed")
        else:
            print(f"⚠️ Background image not found: {bg_path}")
            print(f"   Skipping MP4 generation.")

    # Cleanup
    if db:
        db.close()


if __name__ == "__main__":
    main()
