#!/usr/bin/env python3
"""
download_davidyen_bible.py - Download David Yen's Bible audio from Google Drive
and rename to match Everest format (NNN_NNN.mp3).

Google Drive folder: https://drive.google.com/drive/folders/1VBIPqL15rK6p9Ip5fQysQExvTW7Kxt6E

Structure:
  02 和合本聖經朗讀192k/
  ├── 舊約朗讀（無配樂分章節）/
  │   ├── 01 創世記/
  │   │   ├── 舊約聖經-【01】創世紀_第001章.mp3
  │   │   └── ...
  │   └── ...
  └── 新約朗讀（無配樂分章節）/
      ├── 01 馬太福音/
      │   ├── 新約聖經-【01】馬太福音_第001章.mp3
      │   └── ...
      └── ...

Output: assets/bible/audio/chapters_davidyen/{book:03d}_{chapter:03d}.mp3
        (Same format as Everest: 001_001.mp3 = Genesis 1)

Usage:
  pip install gdown
  python scripts/download_davidyen_bible.py
  python scripts/download_davidyen_bible.py --output-dir /custom/path
"""

import os
import re
import sys
import argparse
import subprocess
import shutil

# David Yen's Chinese book numbering → standard Bible book number
# Old Testament: his numbering is already in Bible order
# New Testament: his numbering starts at 01, but Bible book number starts at 40
OT_BOOK_MAP = {
    1: 1,    # 創世記 Genesis
    2: 2,    # 出埃及記 Exodus
    3: 3,    # 利未記 Leviticus
    4: 4,    # 民數記 Numbers
    5: 5,    # 申命記 Deuteronomy
    6: 6,    # 約書亞記 Joshua
    7: 7,    # 士師記 Judges
    8: 8,    # 路得記 Ruth
    9: 9,    # 撒母耳記上 1 Samuel
    10: 10,  # 撒母耳記下 2 Samuel
    11: 11,  # 列王紀上 1 Kings
    12: 12,  # 列王紀下 2 Kings
    13: 13,  # 歷代志上 1 Chronicles
    14: 14,  # 歷代志下 2 Chronicles
    15: 15,  # 以斯拉記 Ezra
    16: 16,  # 尼希米記 Nehemiah
    17: 17,  # 以斯帖記 Esther
    18: 18,  # 約伯記 Job
    19: 19,  # 詩篇 Psalms
    20: 20,  # 箴言 Proverbs
    21: 21,  # 傳道書 Ecclesiastes
    22: 22,  # 雅歌 Song of Songs
    23: 23,  # 以賽亞書 Isaiah
    24: 24,  # 耶利米書 Jeremiah
    25: 25,  # 耶利米哀歌 Lamentations
    26: 26,  # 以西結書 Ezekiel
    27: 27,  # 但以理書 Daniel
    28: 28,  # 何西阿書 Hosea
    29: 29,  # 約珥書 Joel
    30: 30,  # 阿摩司書 Amos
    31: 31,  # 俄巴底亞書 Obadiah
    32: 32,  # 約拿書 Jonah
    33: 33,  # 彌迦書 Micah
    34: 34,  # 那鴻書 Nahum
    35: 35,  # 哈巴谷書 Habakkuk
    36: 36,  # 西番雅書 Zephaniah
    37: 37,  # 哈該書 Haggai
    38: 38,  # 撒迦利亞書 Zechariah
    39: 39,  # 瑪拉基書 Malachi
}

NT_BOOK_MAP = {
    1: 40,   # 馬太福音 Matthew
    2: 41,   # 馬可福音 Mark
    3: 42,   # 路加福音 Luke
    4: 43,   # 約翰福音 John
    5: 44,   # 使徒行傳 Acts
    6: 45,   # 羅馬書 Romans
    7: 46,   # 哥林多前書 1 Corinthians
    8: 47,   # 哥林多後書 2 Corinthians
    9: 48,   # 加拉太書 Galatians
    10: 49,  # 以弗所書 Ephesians
    11: 50,  # 腓立比書 Philippians
    12: 51,  # 歌羅西書 Colossians
    13: 52,  # 帖撒羅尼迦前書 1 Thessalonians
    14: 53,  # 帖撒羅尼迦後書 2 Thessalonians
    15: 54,  # 提摩太前書 1 Timothy
    16: 55,  # 提摩太後書 2 Timothy
    17: 56,  # 提多書 Titus
    18: 57,  # 腓利門書 Philemon
    19: 58,  # 希伯來書 Hebrews
    20: 59,  # 雅各書 James
    21: 60,  # 彼得前書 1 Peter
    22: 61,  # 彼得後書 2 Peter
    23: 62,  # 約翰一書 1 John
    24: 63,  # 約翰二書 2 John
    25: 64,  # 約翰三書 3 John
    26: 65,  # 猶大書 Jude
    27: 66,  # 啟示錄 Revelation
}


def download_gdrive_folder(folder_url, output_dir, max_retries=3):
    """Download entire Google Drive folder using gdown with retry logic."""
    import time

    print(f"📥 Downloading from Google Drive...")
    print(f"   URL: {folder_url}")
    print(f"   To:  {output_dir}")
    print(f"   (This may take 30-60 minutes for the entire Bible)")
    print()

    os.makedirs(output_dir, exist_ok=True)

    try:
        import gdown
    except ImportError:
        print("❌ gdown not installed. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "gdown"], check=True)
        import gdown

    # Extract folder ID from URL
    folder_id = folder_url.rstrip("/").split("/")[-1]

    # Download with retry logic (Google Drive can timeout on large folders)
    for attempt in range(1, max_retries + 1):
        try:
            print(f"   Attempt {attempt}/{max_retries}...")
            gdown.download_folder(
                id=folder_id,
                output=output_dir,
                quiet=False,
                use_cookies=False,
            )
            print(f"\n✅ Download complete to: {output_dir}")
            return
        except Exception as e:
            error_msg = str(e)
            if "timed out" in error_msg.lower() or "timeout" in error_msg.lower() or "ReadTimeout" in error_msg:
                wait = 10 * attempt
                print(f"\n⚠️ Timeout on attempt {attempt}/{max_retries}. Waiting {wait}s before retry...")
                print(f"   (Already-downloaded files are preserved)")
                time.sleep(wait)
            else:
                print(f"\n❌ Download error: {e}")
                if attempt < max_retries:
                    wait = 10 * attempt
                    print(f"   Retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    raise

    print(f"\n⚠️ Download may be incomplete after {max_retries} attempts.")
    print(f"   Run again — gdown will skip already-downloaded files.")


def rename_to_everest_format(download_dir, output_dir):
    """
    Walk downloaded folder and rename files to Everest format: {book:03d}_{chapter:03d}.mp3
    """
    os.makedirs(output_dir, exist_ok=True)
    count = 0
    errors = []

    for root, dirs, files in os.walk(download_dir):
        for fname in sorted(files):
            if not fname.endswith(".mp3"):
                continue

            src_path = os.path.join(root, fname)

            # Detect OT vs NT from path or filename
            is_nt = "新約" in root or "新約" in fname
            book_map = NT_BOOK_MAP if is_nt else OT_BOOK_MAP

            # Extract book number and chapter from filename
            # Pattern: 舊約聖經-【01】創世紀_第001章.mp3
            # or:      新約聖經-【04】約翰福音_第008（修改）.mp3 (missing '章')
            # or:      舊約聖經-【19】詩篇_第090篇.mp3
            book_match = re.search(r'【(\d+)】', fname)
            chapter_match = re.search(r'第(\d+)', fname)

            if book_match:
                local_book_num = int(book_match.group(1))
                if chapter_match:
                    chapter_num = int(chapter_match.group(1))
                else:
                    # Books with only one chapter might not have "第" in the name
                    # e.g., 舊約聖經-【31】俄巴底亞書.mp3 -> Chapter 1
                    chapter_num = 1
            else:
                # Try alternate: folder name has "01 創世記" pattern
                folder_name = os.path.basename(root)
                folder_match = re.match(r'(\d+)\s+', folder_name)
                # Look for chapter number after the book name or in "第...章" format
                chapter_match = re.search(r'第(\d+)', fname)
                if not chapter_match:
                    # Last resort: find any number that ISN'T the book number
                    nums = re.findall(r'(\d+)', fname)
                    if folder_match and nums:
                        local_book_num = int(folder_match.group(1))
                        # Pick the first number that isn't the book number, or 1 if only book number exists
                        chapter_num = 1
                        for n in nums:
                            if int(n) != local_book_num:
                                chapter_num = int(n)
                                break
                    else:
                        errors.append(f"Cannot parse: {fname}")
                        continue
                else:
                    if folder_match:
                        local_book_num = int(folder_match.group(1))
                        chapter_num = int(chapter_match.group(1))
                    else:
                        errors.append(f"Cannot parse: {fname}")
                        continue

            # Map to Bible book number
            bible_book_num = book_map.get(local_book_num)
            if bible_book_num is None:
                errors.append(f"Unknown book number {local_book_num} ({'NT' if is_nt else 'OT'}): {fname}")
                continue

            # Generate Everest-format filename
            new_fname = f"{bible_book_num:03d}_{chapter_num:03d}.mp3"
            dst_path = os.path.join(output_dir, new_fname)

            shutil.copy2(src_path, dst_path)
            count += 1

            if count % 50 == 0:
                print(f"  📄 Renamed {count} files...")

    print(f"\n✅ Renamed {count} files to Everest format in: {output_dir}")

    if errors:
        print(f"\n⚠️ {len(errors)} files could not be parsed:")
        for e in errors[:10]:
            print(f"  - {e}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")


def verify(output_dir, everest_dir=None):
    """Verify the output and optionally compare with Everest."""
    files = sorted([f for f in os.listdir(output_dir) if f.endswith(".mp3")])
    print(f"\n📊 Verification:")
    print(f"  David Yen files: {len(files)}")
    print(f"  First: {files[0] if files else 'N/A'}")
    print(f"  Last:  {files[-1] if files else 'N/A'}")

    if everest_dir and os.path.exists(everest_dir):
        everest_files = sorted([f for f in os.listdir(everest_dir) if f.endswith(".mp3")])
        print(f"  Everest files:   {len(everest_files)}")

        dy_set = set(files)
        ev_set = set(everest_files)
        missing = ev_set - dy_set
        extra = dy_set - ev_set

        if missing:
            print(f"  ⚠️ Missing (in Everest but not DY): {len(missing)}")
            for f in sorted(missing)[:5]:
                print(f"    - {f}")
        if extra:
            print(f"  ℹ️ Extra (in DY but not Everest): {len(extra)}")
            for f in sorted(extra)[:5]:
                print(f"    - {f}")
        if not missing and not extra:
            print(f"  ✅ Perfect match! All 1189 chapters accounted for.")


def main():
    parser = argparse.ArgumentParser(description="Download David Yen Bible audio and rename to Everest format")
    parser.add_argument("--url", default="https://drive.google.com/drive/folders/1VBIPqL15rK6p9Ip5fQysQExvTW7Kxt6E",
                        help="Google Drive folder URL")
    parser.add_argument("--download-dir", default="assets/bible/audio/raw_davidyen",
                        help="Where to download raw files (Default: assets/bible/audio/raw_davidyen)")
    parser.add_argument("--output-dir", default="assets/bible/audio/chapters_davidyen",
                        help="Output dir for renamed files (Default: assets/bible/audio/chapters_davidyen)")
    parser.add_argument("--skip-download", action="store_true",
                        help="Skip download, only rename existing files")
    parser.add_argument("--verify", action="store_true",
                        help="Verify output against Everest chapters")

    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)

    download_dir = os.path.join(project_dir, args.download_dir) if not os.path.isabs(args.download_dir) else args.download_dir
    output_dir = os.path.join(project_dir, args.output_dir) if not os.path.isabs(args.output_dir) else args.output_dir
    everest_dir = os.path.join(project_dir, "assets", "bible", "audio", "chapters")

    # Step 1: Download
    if not args.skip_download:
        download_gdrive_folder(args.url, download_dir)
    else:
        print(f"⏭️ Skipping download (using existing files in {download_dir})")

    # Step 2: Rename
    print(f"\n--- Renaming to Everest format ---")
    rename_to_everest_format(download_dir, output_dir)

    # Step 3: Verify
    if args.verify:
        verify(output_dir, everest_dir)
    else:
        verify(output_dir)

    print(f"\n═══════════════════════════════════════════════")
    print(f"  ✅ David Yen Bible audio ready!")
    print(f"  Output: {output_dir}")
    print(f"  Format: {{book:03d}}_{{chapter:03d}}.mp3 (same as Everest)")
    print(f"═══════════════════════════════════════════════")


if __name__ == "__main__":
    main()
