"""
gen_votd.py – Enhanced Verse of the Day Audio Generator

Based on gen_verse_devotion_edge.py, adds:
  1. Multi-translation Bible verse TTS (4 translations per verse, rotating voices)
  2. Full chapter audio (pre-recorded Everest) mixed with BGM from assets/bible/bgm/
  3. Auto-expands verse references from input.txt using local SQLite Bible DB

Input: input.txt (simple format with verse references like (詩篇 77:12 和合本))
Output: MP3 audio + output.txt (expanded text with all translations)

Usage:
  python gen_votd.py -i input.txt
  python gen_votd.py -i input.txt --voice six --bgm
  python gen_votd.py -i input.txt --bible-bgm-volume -18 --speech-volume 6
"""

import asyncio
import sys
import edge_tts
from pydub import AudioSegment
import os
import re
from datetime import datetime

from bible_parser import convert_bible_reference
from date_parser import convert_dates_in_text
from text_cleaner import clean_text
import filename_parser
import audio_mixer
from mp3_to_mp4 import create_mp4, DEFAULT_BG
from bible_db import BibleDB, parse_verse_reference, book_number_to_chinese

TTS_RATE = "+0%"  # Default Speed (normal)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CHAPTERS_DIR = os.path.join(SCRIPT_DIR, "assets", "bible", "audio", "chapters")
BIBLE_BGM_DIR = os.path.join(SCRIPT_DIR, "assets", "bible", "bgm")

# ─── CLI Args ───
if "-?" in sys.argv or "-h" in sys.argv or "--help" in sys.argv:
    print(f"Usage: python {sys.argv[0]} [OPTIONS]")
    print("\nOptions:")
    print("  --input FILE, -i     Text file to read input from")
    print("  --prefix PREFIX      Filename prefix (e.g. MyPrefix)")
    print("  --voice MODE         Voice mode: male, female, two, four, six (Default: six)")
    print("  --voices LIST        Custom voices (CSV, overrides --voice)")
    print("  --speed SPEED        Speech rate: +10%, --speed=-10% (Default: +0%)")
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
    print("  -?, -h, --help       Show this help")
    print("\nVoice Modes:")
    print("  male    - Single male voice (YunyangNeural)")
    print("  female  - Single female voice (XiaoxiaoNeural)")
    print("  two     - Rotate 2 voices (1 male + 1 female)")
    print("  four    - Rotate 4 voices (2 male + 2 female)")
    print("  six     - Rotate all 6 zh-CN voices (Default)")
    print("\nExamples:")
    print(f"  python {sys.argv[0]} -i input.txt")
    print(f"  python {sys.argv[0]} -i input.txt --voice six --bgm")
    print(f"  python {sys.argv[0]} -i input.txt --bible-bgm-volume -18")
    sys.exit(0)

import argparse

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("--input", "-i", type=str, help="Input text file")
parser.add_argument("--prefix", type=str, default=None, help="Filename prefix")
parser.add_argument("--voice", type=str, default="six", choices=["male", "female", "two", "four", "six"],
                    help="Voice mode: male, female, two, four, six")
parser.add_argument("--voices", type=str, default=None,
                    help="Custom voices (CSV format, overrides --voice)")
parser.add_argument("--speed", type=str, default=None, help="Speech rate adjustment (e.g. +10%%)")
parser.add_argument("--bgm", action="store_true", help="Enable background music for non-bible sections")
parser.add_argument("--bgm-track", type=str, default="AmazingGrace.MP3", help="BGM filename")
parser.add_argument("--bgm-volume", type=int, default=-20, help="BGM volume in dB")
parser.add_argument("--bgm-intro", type=int, default=4000, help="BGM intro delay in ms")
parser.add_argument("--bible-bgm-volume", type=int, default=-20, help="Bible chapter BGM volume in dB")
parser.add_argument("--bible-bgm-intro", type=int, default=4000, help="Bible chapter BGM intro delay in ms")
parser.add_argument("--speech-volume", type=int, default=4, help="Boost for chapter speech in dB (Everest is quiet)")
parser.add_argument("--chapter-speed", type=float, default=1.5, help="Speed multiplier for Everest chapter audio (Default: 1.5)")
parser.add_argument("--bible-db", type=str, default=None, help="Path to bible.sqlite")
parser.add_argument("--mp4", action="store_true", help="Generate MP4 video from audio")
parser.add_argument("--mp4-bg", type=str, default=DEFAULT_BG, help="Background image for MP4")
parser.add_argument("--mp4-res", type=str, default="1920x1080", help="MP4 resolution")

args, unknown = parser.parse_known_args()
CLI_PREFIX = args.prefix

ENABLE_BGM = args.bgm
BGM_FILE = args.bgm_track
BGM_VOLUME = args.bgm_volume
BGM_INTRO_DELAY = args.bgm_intro

# Speed parsing
if args.speed:
    if "%" not in args.speed and (args.speed.startswith("+") or args.speed.startswith("-") or args.speed.isdigit()):
        TTS_RATE = f"{args.speed}%"
    else:
        TTS_RATE = args.speed

# Voice presets
VOICE_MALE_1 = "zh-CN-YunyangNeural"    # Professional, Reliable
VOICE_MALE_2 = "zh-CN-YunxiNeural"      # Lively, Sunshine
VOICE_MALE_3 = "zh-CN-YunjianNeural"    # Passion
VOICE_FEMALE_1 = "zh-CN-XiaoxiaoNeural"  # Warm
VOICE_FEMALE_2 = "zh-CN-XiaoyiNeural"    # Lively
VOICE_FEMALE_3 = "zh-CN-YunxiaNeural"    # Cute (Male but high pitch)

# Voice mode configuration
if args.voices:
    VOICES = [v.strip() for v in args.voices.split(",") if v.strip()]
    print(f"🎤 Custom voices: {', '.join(VOICES)}")
elif args.voice == "male":
    VOICES = [VOICE_MALE_1]
    print(f"🎤 Voice mode: male ({VOICE_MALE_1})")
elif args.voice == "female":
    VOICES = [VOICE_FEMALE_1]
    print(f"🎤 Voice mode: female ({VOICE_FEMALE_1})")
elif args.voice == "two":
    VOICES = [VOICE_MALE_1, VOICE_FEMALE_1]
    print(f"🎤 Voice mode: two (rotating 2 voices)")
elif args.voice == "four":
    VOICES = [VOICE_MALE_1, VOICE_FEMALE_1, VOICE_MALE_2, VOICE_FEMALE_2]
    print(f"🎤 Voice mode: four (rotating 4 voices)")
else:  # six (default)
    VOICES = [VOICE_MALE_1, VOICE_FEMALE_1, VOICE_MALE_2, VOICE_FEMALE_2, VOICE_MALE_3, VOICE_FEMALE_3]
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


# ─── Filename generation ───
TEXT = clean_text(TEXT)
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
).replace(".mp3", "_votd.mp3")

if ENABLE_BGM:
    filename = filename.replace(".mp3", "_bgm.mp3")

if args.speed:
    speed_val = args.speed.replace("%", "")
    if speed_val.startswith("+"):
        speed_suffix = f"plus{speed_val[1:]}"
    elif speed_val.startswith("-"):
        speed_suffix = f"minus{speed_val[1:]}"
    else:
        speed_suffix = speed_val
    if speed_suffix and speed_suffix not in ["0", "plus0", "1.0"]:
        filename = filename.replace(".mp3", f"_speed-{speed_suffix}.mp3")

OUTPUT_DIR = os.path.join(os.getcwd(), "output")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
OUTPUT_PATH = os.path.join(OUTPUT_DIR, filename)
print(f"Target Output: {OUTPUT_PATH}")


# ─── Helpers ───

def _load_chapter_audio(book_num: int, chapter_num: int, speed: float = 1.0) -> AudioSegment:
    """Load pre-recorded chapter MP3 from assets/bible/audio/chapters/."""
    fname = f"{book_num:03d}_{chapter_num:03d}.mp3"
    path = os.path.join(CHAPTERS_DIR, fname)
    if not os.path.exists(path):
        print(f"  ⚠️ Chapter audio not found: {path}")
        return None
    try:
        seg = AudioSegment.from_mp3(path)
        orig_len = len(seg) / 1000
        # Apply speed change if needed
        if speed != 1.0 and speed > 0:
            # Change speed by altering frame rate then converting back
            new_frame_rate = int(seg.frame_rate * speed)
            seg = seg._spawn(seg.raw_data, overrides={'frame_rate': new_frame_rate})
            seg = seg.set_frame_rate(44100)  # Normalize back to standard rate
        print(f"  📖 Loaded chapter audio: {fname} ({orig_len:.1f}s → {len(seg)/1000:.1f}s @ {speed}x)")
        return seg
    except Exception as e:
        print(f"  ❌ Error loading {fname}: {e}")
        return None


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
        'verse_refs': [],      # list of (book, chapter, verse_start, verse_end)
        'verse_texts': [],     # original verse text from input
        'essay_titles': [],
        'essay_body': [],
        'prayer': '',
        'credits': []
    }

    if len(paragraphs) < 5:
        print(f"⚠️ Too few paragraphs ({len(paragraphs)}). Falling back to simple mode.")
        return result

    idx = 1  # Start after title

    # Collect verse paragraphs (ending with translation label in parens)
    verse_end_idx = idx
    for i in range(idx, len(paragraphs)):
        para = paragraphs[i]
        has_ref = bool(re.search(r'\([^\)]*和合本\s*\)', para))
        if has_ref:
            verse_end_idx = i + 1
        else:
            break

    # Parse each verse paragraph to extract the reference
    for i in range(idx, verse_end_idx):
        para = paragraphs[i]
        result['verse_texts'].append(para)

        # Extract the reference from the last line
        ref_match = re.search(r'\(([^\)]+和合本)\)', para)
        if ref_match:
            ref = parse_verse_reference(ref_match.group(0))
            if ref:
                result['verse_refs'].append(ref)
            else:
                print(f"  ⚠️ Could not parse verse reference: {ref_match.group(0)}")

    idx = verse_end_idx

    # Essay titles (3 repeated short paragraphs)
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

    # Credits (scan from end)
    credits_start = len(remaining)
    for i in range(len(remaining) - 1, -1, -1):
        is_credit = any(marker in remaining[i] for marker in credit_markers)
        if is_credit:
            credits_start = i
        else:
            break

    body_and_prayer = remaining[:credits_start]
    result['credits'] = remaining[credits_start:]

    # Last paragraph may be prayer
    if body_and_prayer:
        last = body_and_prayer[-1]
        if (last.startswith("禱告") or "阿們" in last or "阿门" in last
                or "奉耶穌的名" in last or "奉耶稣的名" in last):
            result['prayer'] = last
            result['essay_body'] = body_and_prayer[:-1]
        else:
            result['essay_body'] = body_and_prayer

    return result


def tts_prep(text: str) -> str:
    """Prepare text for TTS: convert references, dates, clean."""
    text = convert_bible_reference(text)
    text = convert_dates_in_text(text)
    text = clean_text(text)
    return text


async def generate_audio(text, voice, output_file):
    """Generate TTS audio using edge_tts."""
    print(f"  🔊 TTS ({voice}): {text[:60]}...")
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=TTS_RATE)
    await communicate.save(output_file)


async def main():
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

    voices = VOICES
    final_segments = []
    global_voice_idx = 0
    txt_lines = []  # For output.txt

    SILENCE_SHORT = AudioSegment.silent(duration=700)
    SILENCE_SECTION = AudioSegment.silent(duration=1000)

    # ─── Section 1: Title ───
    print(f"\n--- Section 1: Title ---")
    if sections['title']:
        temp_file = os.path.join(OUTPUT_DIR, "temp_votd_title.mp3")
        voice = voices[global_voice_idx % len(voices)]
        global_voice_idx += 1
        await generate_audio(tts_prep(sections['title']), voice, temp_file)
        try:
            seg = AudioSegment.from_mp3(temp_file)
            final_segments.append(seg)
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        txt_lines.append(sections['title'])
        txt_lines.append("")

    # ─── Section 2: Verse Translation TTS ───
    print(f"\n--- Section 2: Verse Translations ---")
    chapter_audio_segments = []  # Collect chapter audio for later (Section 7)
    chapter_txt_lines = []       # Collect chapter text for output.txt (Section 7)

    if expanded_blocks:
        for block_idx, block in enumerate(expanded_blocks):
            print(f"\n  📖 Verse Block {block_idx + 1}")
            book_num = block['book_num']
            chapter_num = block['chapter_num']

            # Collect chapter audio for Section 7 (after credits)
            ch_seg = _load_chapter_audio(book_num, chapter_num, speed=args.chapter_speed)
            if ch_seg is not None:
                # Boost volume if needed (Everest audio is quiet)
                if args.speech_volume != 0:
                    ch_seg = ch_seg + args.speech_volume
                chapter_audio_segments.append(ch_seg)

            # Collect chapter text for output.txt (Section 7)
            if block['chapter_text']:
                chapter_txt_lines.append(block['chapter_text'])
                chapter_txt_lines.append(f"({block['chapter_ref']})")
                chapter_txt_lines.append("")
            else:
                if block_idx < len(sections['verse_texts']):
                    chapter_txt_lines.append(sections['verse_texts'][block_idx])
                    chapter_txt_lines.append("")

            # Translation TTS
            if block['translations']:
                final_segments.append(SILENCE_SECTION)
                for t_idx, (code, label, text, ref_str) in enumerate(block['translations']):
                    voice = voices[global_voice_idx % len(voices)]
                    global_voice_idx += 1
                    tts_text = f"{text}\n({ref_str})"
                    temp_file = os.path.join(OUTPUT_DIR, f"temp_votd_trans_{block_idx}_{t_idx}.mp3")
                    await generate_audio(tts_prep(tts_text), voice, temp_file)
                    try:
                        seg = AudioSegment.from_mp3(temp_file)
                        final_segments.append(seg)
                        if t_idx < len(block['translations']) - 1:
                            final_segments.append(SILENCE_SHORT)
                    finally:
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                    txt_lines.append(text)
                    txt_lines.append(f"({ref_str})")

            txt_lines.append("")
    else:
        # No DB available — use original verse text with TTS only
        for v_idx, verse_text in enumerate(sections['verse_texts']):
            voice = voices[global_voice_idx % len(voices)]
            global_voice_idx += 1
            temp_file = os.path.join(OUTPUT_DIR, f"temp_votd_verse_{v_idx}.mp3")
            await generate_audio(tts_prep(verse_text), voice, temp_file)
            try:
                seg = AudioSegment.from_mp3(temp_file)
                final_segments.append(SILENCE_SECTION)
                final_segments.append(seg)
            finally:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            txt_lines.append(verse_text)
            txt_lines.append("")

    # ─── Section 3: Essay Titles ───
    print(f"\n--- Section 3: Essay Titles ---")
    for et_idx, essay_title in enumerate(sections['essay_titles']):
        voice = voices[global_voice_idx % len(voices)]
        global_voice_idx += 1
        temp_file = os.path.join(OUTPUT_DIR, f"temp_votd_et_{et_idx}.mp3")
        await generate_audio(tts_prep(essay_title), voice, temp_file)
        try:
            seg = AudioSegment.from_mp3(temp_file)
            final_segments.append(SILENCE_SECTION)
            final_segments.append(seg)
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        txt_lines.append(essay_title)
        txt_lines.append("")

    # ─── Section 4: Essay Body ───
    print(f"\n--- Section 4: Essay Body ---")
    if sections['essay_body']:
        essay_text = "\n\n".join(sections['essay_body'])
        voice = voices[global_voice_idx % len(voices)]
        global_voice_idx += 1
        temp_file = os.path.join(OUTPUT_DIR, "temp_votd_essay.mp3")
        await generate_audio(tts_prep(essay_text), voice, temp_file)
        try:
            seg = AudioSegment.from_mp3(temp_file)
            final_segments.append(SILENCE_SECTION)
            final_segments.append(seg)
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        for eb in sections['essay_body']:
            txt_lines.append(eb)
            txt_lines.append("")

    # ─── Section 5: Prayer ───
    print(f"\n--- Section 5: Prayer ---")
    if sections['prayer']:
        voice = voices[global_voice_idx % len(voices)]
        global_voice_idx += 1
        temp_file = os.path.join(OUTPUT_DIR, "temp_votd_prayer.mp3")
        await generate_audio(tts_prep(sections['prayer']), voice, temp_file)
        try:
            seg = AudioSegment.from_mp3(temp_file)
            final_segments.append(SILENCE_SECTION)
            final_segments.append(seg)
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        txt_lines.append(sections['prayer'])
        txt_lines.append("")

    # ─── Section 6: Credits ───
    print(f"\n--- Section 6: Credits ---")
    for cr_idx, credit in enumerate(sections['credits']):
        voice = voices[global_voice_idx % len(voices)]
        global_voice_idx += 1
        temp_file = os.path.join(OUTPUT_DIR, f"temp_votd_credit_{cr_idx}.mp3")
        await generate_audio(tts_prep(credit), voice, temp_file)
        try:
            seg = AudioSegment.from_mp3(temp_file)
            final_segments.append(SILENCE_SECTION)
            final_segments.append(seg)
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        txt_lines.append(credit)
        txt_lines.append("")

    # ─── Section 7: Chapter Audio (Everest, after credits) ───
    if chapter_audio_segments:
        print(f"\n--- Section 7: Chapter Audio ({len(chapter_audio_segments)} chapters) ---")
        for ch_idx, ch_seg in enumerate(chapter_audio_segments):
            print(f"  📖 Appending chapter {ch_idx + 1} ({len(ch_seg)/1000:.1f}s)")
            final_segments.append(SILENCE_SECTION)
            final_segments.append(ch_seg)
        # Add chapter text to output.txt
        txt_lines.extend(chapter_txt_lines)

    # ─── Combine all segments ───
    print(f"\n--- Combining {len(final_segments)} segments ---")
    final = AudioSegment.empty()
    for seg in final_segments:
        final += seg

    # Optional: mix overall BGM for non-bible sections
    if ENABLE_BGM:
        print(f"🎵 Mixing Overall BGM (Vol={BGM_VOLUME}dB, Intro={BGM_INTRO_DELAY}ms)...")
        final = audio_mixer.mix_bgm(
            final,
            specific_filename=BGM_FILE,
            volume_db=BGM_VOLUME,
            intro_delay_ms=BGM_INTRO_DELAY
        )

    # ─── Export MP3 ───
    PRODUCER = "VI AI Foundation"
    TITLE = sections['title']
    ALBUM = "VOTD"
    bgm_info = os.path.basename(BGM_FILE) if ENABLE_BGM else "None"
    COMMENTS = f"Verse: {verse_ref}; BGM: {bgm_info}"

    final.export(OUTPUT_PATH, format="mp3", tags={
        'title': TITLE,
        'artist': PRODUCER,
        'album': ALBUM,
        'comments': COMMENTS
    })
    print(f"\n✅ Combined audio saved: {OUTPUT_PATH}")
    print(f"   Duration: {len(final)/1000:.1f}s")

    # ─── Generate output.txt ───
    txt_output = OUTPUT_PATH.replace(".mp3", ".txt")
    with open(txt_output, "w", encoding="utf-8") as f:
        f.write("\n".join(txt_lines))
    print(f"📝 Text saved: {txt_output}")

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
    asyncio.run(main())
