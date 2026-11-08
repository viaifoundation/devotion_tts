import asyncio
import sys
import edge_tts
from pydub import AudioSegment
import os
import json
import subprocess
import urllib.parse
from pathlib import Path
from bible_parser import convert_bible_reference
from date_parser import convert_dates_in_text, extract_date_from_text, strip_all_dates, strip_date_from_title
from text_cleaner import clean_text_basic, clean_text_for_tts, clean_text
import filename_parser
import re
from datetime import datetime
import audio_mixer
from caption_generator import parse_caption_flag, parse_caption_scale, generate_srt_from_paragraphs, create_subtitles_from_edge_cues
from audio_to_mp4 import create_mp4, generate_soh_dated_background, DEFAULT_BG, DEFAULT_SOH_BG

import argparse

VERSION = "1.2.0"
ENABLE_BGM = True
BGM_FILE = "AmazingGrace.MP3"
TTS_RATE = "+0%"  # Default Speed (normal)
BGM_VOLUME = -10   # Default dB relative to speech (audible & balanced)
BGM_INTRO_DELAY = 4000 # Default ms

# ——————————————————————————————————————————————————————————————————————————
# Secrets Loader (~/.secrets fallback, matching ting/scripts/daily.py setup)
# ——————————————————————————————————————————————————————————————————————————
def load_soh_wp_credentials():
    """Load SOH WordPress credentials from environment or ~/.secrets."""
    secrets_file = os.path.expanduser("~/.secrets")
    if os.path.exists(secrets_file):
        try:
            with open(secrets_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("export ") and "=" in line:
                        kv = line[len("export "):].strip()
                        k, v = kv.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k not in os.environ:
                            os.environ[k] = v
        except Exception as e:
            print(f"⚠️ Notice reading ~/.secrets: {e}")

    wp_url = os.environ.get("SOH_WP_URL", "https://prayer.tianlumusic.org/wp-json/wp/v2").rstrip("/")
    wp_user = os.environ.get("SOH_WP_USERNAME", "tianlumusic")
    wp_pass = os.environ.get("SOH_WP_APP_PASSWORD", "")
    return wp_url, wp_user, wp_pass


# ——————————————————————————————————————————————————————————————————————————
# Custom handling for -? / -h / --help
# ——————————————————————————————————————————————————————————————————————————
if "-?" in sys.argv or "-h" in sys.argv or "--help" in sys.argv:
    print(f"Usage: python {sys.argv[0]} [OPTIONS]")
    print("\nOptions:")
    print("  --input FILE, -i     Text file to read input from (Default: prayer.txt)")
    print("  --lang LANG, -l      Caption language: tw (zh_TW) or cn (zh_CN) (Default: tw)")
    print("  --tw                 Shortcut for --lang tw (Traditional Chinese captions, Default)")
    print("  --cn                 Shortcut for --lang cn (Simplified Chinese captions)")
    print("  --voice MODE         Voice mode: male, female, two, four, six (Default: two)")
    print("  --voices LIST        Custom voices (CSV, overrides --voice)")
    print("                       e.g. zh-CN-YunyangNeural,zh-CN-XiaoxiaoNeural")
    print("  --speed SPEED        Speech rate: +10%, --speed=-10% (Default: +0%)")
    print("  --bgm                Enable background music (Default: True)")
    print("  --no-bgm             Disable background music")
    print("  --bgm-track TRACK    BGM filename (Default: AmazingGrace.MP3)")
    print("  --bgm-volume VOL     BGM volume in dB relative to speech (Default: -10)")
    print("  --bgm-intro MS       BGM intro delay in ms (Default: 4000)")
    print("  --mp4                Generate MP4 video from audio (Default: True)")
    print("  --no-mp4             Skip MP4 video generation")
    print(f"  --mp4-bg IMAGE       Background image for MP4 (Default: {DEFAULT_SOH_BG})")
    print("  --mp4-res RES        MP4 resolution (Default: 1920x1080)")
    print("  --caption [true/false]       Enable burned-in captions on video (Default: true)")
    print("  --no-caption                 Disable burned-in captions on video")
    print("  --caption-scale SCALE        Caption font scale multiplier: 1x, 2x, 3x, 4x, etc. (Default: 2x)")
    print("  --caption-large [true/false] Make burned-in caption font size 3x larger (Default: false)")
    print("  --caption-file FILE          Explicit SRT/VTT caption file")
    print("  --upload                     Upload image, MP3, MP4 & prayer text to prayer.tianlumusic.org (Default: True)")
    print("  --no-upload, --skip-upload   Skip uploading to WordPress")
    print("  --upload-only                Skip TTS/MP4 generation and only upload existing files for the date")
    print("  -?, -h, --help       Show this help")
    print("\nExamples:")
    print(f"  python {sys.argv[0]} -i prayer.txt                       # Generate image, MP3, MP4 & auto-upload to prayer.tianlumusic.org")
    print(f"  python {sys.argv[0]} -i prayer.txt --no-upload           # Generate locally only, skip WP upload")
    print(f"  python {sys.argv[0]} -i prayer.txt --upload-only         # Upload already-generated files to WP")
    sys.exit(0)

parser = argparse.ArgumentParser(description="Generate Prayer Audio/Video with Edge TTS & Auto-Upload to prayer.tianlumusic.org", add_help=False)
parser.add_argument("--input", "-i", type=str, help="Input text file (Default: prayer.txt)")
parser.add_argument("--lang", "-l", type=str, default="zh_TW",
                    help="Language: tw (zh_TW) or cn (zh_CN) (Default: zh_TW)")
parser.add_argument("--tw", "-tw", action="store_true", help="Shortcut for --lang tw (Traditional Chinese, Default)")
parser.add_argument("--cn", "-cn", action="store_true", help="Shortcut for --lang cn (Simplified Chinese)")
parser.add_argument("--voice", type=str, default="two", choices=["male", "female", "two", "four", "six"],
                    help="Voice mode: male, female, two, four, six")
parser.add_argument("--voices", type=str, default=None,
                    help="Custom voices (CSV format, overrides --voice)")
parser.add_argument("--speed", type=str, default=None, help="Speech rate (e.g. +10%%)")
parser.add_argument("--bgm", action="store_true", default=True, help="Enable background music (Default: True)")
parser.add_argument("--no-bgm", action="store_true", help="Disable background music")
parser.add_argument("--bgm-track", type=str, default="AmazingGrace.MP3", help="BGM filename")
parser.add_argument("--bgm-volume", type=int, default=-10, help="BGM volume in dB relative to speech")
parser.add_argument("--bgm-intro", type=int, default=4000, help="BGM intro delay in ms")
parser.add_argument("--mp4", action="store_true", default=True, help="Generate MP4 video from audio (Default: True)")
parser.add_argument("--no-mp4", action="store_true", help="Disable MP4 video generation")
parser.add_argument("--mp4-bg", type=str, default=DEFAULT_SOH_BG, help=f"Background image for MP4 (Default: {DEFAULT_SOH_BG})")
parser.add_argument("--mp4-res", type=str, default="1920x1080", help="MP4 resolution")
parser.add_argument("--caption", "--captions", nargs="?", const="true", default=None,
                    help="Enable burned-in captions on video (true/false, default: true)")
parser.add_argument("--no-caption", "--no-captions", action="store_true",
                    help="Disable burned-in captions on video")
parser.add_argument("--caption-scale", "--caption-size", type=str, default=None,
                    help="Caption font scale multiplier: 1x, 2x, 3x, 4x, etc. (Default: 2x)")
parser.add_argument("--caption-large", "--large-caption", "--caption-3x", nargs="?", const="true", default=None,
                    help="Make burned-in caption font size 3x larger (true/false, default: false)")
parser.add_argument("--caption-file", type=str, default=None, help="Explicit SRT/VTT caption file")
parser.add_argument("--upload", action="store_true", default=True, help="Upload to prayer.tianlumusic.org (Default: True)")
parser.add_argument("--no-upload", "--skip-upload", dest="no_upload", action="store_true", help="Skip uploading to WordPress")
parser.add_argument("--upload-only", action="store_true", help="Skip TTS/MP4 generation and only upload existing files")

args, unknown = parser.parse_known_args()

# Update global config based on CLI
ENABLE_BGM = not args.no_bgm
ENABLE_MP4 = not args.no_mp4
ENABLE_UPLOAD = not args.no_upload

# Speed parsing
if args.speed:
    if not "%" in args.speed and (args.speed.startswith("+") or args.speed.startswith("-") or args.speed.isdigit()):
        TTS_RATE = f"{args.speed}%"
    else:
        TTS_RATE = args.speed

BGM_VOLUME = args.bgm_volume
BGM_INTRO_DELAY = args.bgm_intro
BGM_FILE = args.bgm_track

# Language Normalization
def normalize_lang(lang_arg: str, is_tw: bool = False, is_cn: bool = False) -> str:
    if is_cn:
        return "zh_CN"
    if is_tw:
        return "zh_TW"
    if not lang_arg:
        return "zh_TW"
    s = str(lang_arg).strip().lower().replace("-", "_")
    if s in ("cn", "zh_cn", "simplified", "s", "chs", "hans"):
        return "zh_CN"
    return "zh_TW"

TARGET_LANG = normalize_lang(args.lang, args.tw, args.cn)
lang_desc = "Traditional Chinese (zh_TW)" if TARGET_LANG == "zh_TW" else "Simplified Chinese (zh_CN)"
print(f"🌐 Caption Language: {lang_desc}")

# Voice presets (Consistent SOH standard voices)
VOICE_MALE_1 = "zh-CN-YunyangNeural"    # Professional, Reliable
VOICE_MALE_2 = "zh-CN-YunxiNeural"      # Lively, Sunshine
VOICE_MALE_3 = "zh-CN-YunjianNeural"    # Passion
VOICE_FEMALE_1 = "zh-CN-XiaoxiaoNeural"  # Warm
VOICE_FEMALE_2 = "zh-CN-XiaoyiNeural"    # Lively
VOICE_FEMALE_3 = "zh-CN-YunxiaNeural"    # Cute

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
    print(f"🎤 Voice mode: two ({VOICE_MALE_1}, {VOICE_FEMALE_1})")
elif args.voice == "four":
    VOICES = [VOICE_MALE_1, VOICE_FEMALE_1, VOICE_MALE_2, VOICE_FEMALE_2]
    print(f"🎤 Voice mode: four (rotating 4 voices)")
else:  # six
    VOICES = [VOICE_MALE_1, VOICE_FEMALE_1, VOICE_MALE_2, VOICE_FEMALE_2, VOICE_MALE_3, VOICE_FEMALE_3]
    print(f"🎤 Voice mode: six (rotating 6 voices)")


# 1. Try --input argument
default_prayer_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prayer.txt")
if args.input:
    print(f"Reading text from file: {args.input}")
    with open(args.input, "r", encoding="utf-8") as f:
        TEXT = f.read()
# 2. Try Stdin (Piped)
elif not sys.stdin.isatty():
    print("Reading text from Stdin...")
    TEXT = sys.stdin.read()
# 3. Default to prayer.txt if present
elif os.path.exists("prayer.txt"):
    print("Reading text from default file: prayer.txt")
    with open("prayer.txt", "r", encoding="utf-8") as f:
        TEXT = f.read()
elif os.path.exists(default_prayer_file):
    print(f"Reading text from default file: {default_prayer_file}")
    with open(default_prayer_file, "r", encoding="utf-8") as f:
        TEXT = f.read()
else:
    TEXT = """
“　神爱世人，甚至将他的独生子赐给他们，叫一切信他的，不至灭亡，反得永生。因为　神差他的儿子降世，不是要定世人的罪，乃是要叫世人因他得救。信他的人，不被定罪；不信的人，罪已经定了，因为他不信　神独生子的名。
(约翰福音 3:16-18)
"""

# Extract raw org name from original text BEFORE it is cleaned (so it preserves Simplified/Traditional)
raw_title_line = TEXT.strip().splitlines()[0] if TEXT.strip() else ""
m_raw = re.search(r"(\d{4})[年\-](\d{1,2})[月\-](\d{1,2})[日]*\s*(.*)", raw_title_line)
raw_org_name = m_raw.group(4).strip() if m_raw and m_raw.group(4).strip() else None

# Generate filename dynamically
TEXT = clean_text_basic(TEXT)

# Extract date for filename BEFORE stripping date from spoken text
date_str_dash = extract_date_from_text(TEXT)

if not date_str_dash:
    try:
        import zoneinfo
        target_tz = zoneinfo.ZoneInfo("Asia/Shanghai")
        date_str_dash = datetime.now(target_tz).strftime("%Y-%m-%d")
    except Exception:
        date_str_dash = datetime.today().strftime("%Y-%m-%d")

# Convert YYYY-MM-DD to YYYYMMDD
date_obj = datetime.strptime(date_str_dash, "%Y-%m-%d")
date_str_compact = date_obj.strftime("%Y%m%d")
date_display = f"{date_obj.year} 年 {date_obj.month} 月 {date_obj.day} 日"

# SOH Convention: 乡音情_{yyyymmdd}.mp3
filename = f"乡音情_{date_str_compact}.mp3"

OUTPUT_DIR = os.path.join(os.getcwd(), "output")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
OUTPUT_PATH = os.path.join(OUTPUT_DIR, filename)
IMAGE_OUTPUT_PATH = OUTPUT_PATH.replace(".mp3", ".jpg")
THUMB_OUTPUT_PATH = OUTPUT_PATH.replace(".mp3", "_thumb.jpg")
MP4_OUTPUT_PATH = OUTPUT_PATH.replace(".mp3", ".mp4")
print(f"Target Output: {OUTPUT_PATH}")

# Convert script according to TARGET_LANG (zh_TW -> Traditional, zh_CN -> Simplified)
try:
    import opencc
    if TARGET_LANG == "zh_TW":
        cc = opencc.OpenCC('s2tw')
        TEXT = cc.convert(TEXT)
    else:
        cc = opencc.OpenCC('t2s')
        TEXT = cc.convert(TEXT)
except Exception as e:
    print(f"⚠️ OpenCC conversion notice: {e}")

# Extract first line for MP3/Post title (retaining date as requested)
TEXT_DISPLAY = clean_text_basic(TEXT)
first_line = TEXT_DISPLAY.strip().split('\n')[0] if TEXT_DISPLAY.strip() else f"天路音樂「鄉音情」為鄉音禱告 {date_str_dash}"

# Convert Bible references and dates with RAG/phonetic pronunciation fixes for TTS
TEXT_TTS = convert_bible_reference(TEXT_DISPLAY)
TEXT_TTS = convert_dates_in_text(TEXT_TTS)
TEXT_TTS = clean_text_for_tts(TEXT_TTS)

# Split the text into paragraphs for TTS
paragraphs = [p.strip() for p in re.split(r'\n{2,}', TEXT_TTS.strip()) if p.strip()]

# Save companion text output for TTS with RAG (matching VOTD convention)
TXT_OUTPUT_PATH = OUTPUT_PATH.replace(".mp3", ".txt")
with open(TXT_OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write(TEXT_TTS)
print(f"📄 Saved TTS RAG text output to: {TXT_OUTPUT_PATH}")

# Clean up legacy prayer_output.txt if present
for legacy_path in [os.path.join(OUTPUT_DIR, "prayer_output.txt"), os.path.join(os.getcwd(), "prayer_output.txt")]:
    if os.path.exists(legacy_path):
        try:
            os.remove(legacy_path)
        except Exception:
            pass

voices = VOICES
TEMP_DIR = OUTPUT_DIR + os.sep 


# ——————————————————————————————————————————————————————————————————————————
# WordPress Auto-Uploader for prayer.tianlumusic.org
# ——————————————————————————————————————————————————————————————————————————
def _resolve_host_ip(hostname: str) -> str | None:
    """Resolve hostname via 1.1.1.1 if local DNS cache has stale NXDOMAIN."""
    try:
        import socket
        socket.gethostbyname(hostname)
        return None  # Local DNS works fine
    except Exception:
        pass
    try:
        res = subprocess.run(
            ["dig", "+short", hostname, "@1.1.1.1"],
            capture_output=True, text=True, timeout=5
        )
        for line in res.stdout.splitlines():
            line = line.strip()
            if re.match(r"^\d+\.\d+\.\d+\.\d+$", line):
                return line
    except Exception:
        pass
    return None


def _wp_curl_json(method: str, url: str, user: str, password: str,
                  headers: list[str] | None = None,
                  data_bytes: bytes | None = None,
                  data_file: str | None = None,
                  timeout: int = 300) -> dict | list | None:
    """Execute a WordPress REST API call via curl with automatic DNS fallback."""
    parsed = urllib.parse.urlparse(url)
    host = parsed.hostname or "prayer.tianlumusic.org"
    ip = _resolve_host_ip(host)

    cmd = [
        "curl", "-sS",
        "-X", method,
        "-u", f"{user}:{password}",
        "-A", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "--max-time", str(timeout),
    ]
    if ip:
        cmd.extend(["--resolve", f"{host}:443:{ip}"])
    if headers:
        for h in headers:
            cmd.extend(["-H", h])
    if data_file:
        cmd.extend(["--data-binary", f"@{data_file}"])
    elif data_bytes is not None:
        cmd.extend(["--data-binary", "@-"])

    proc = subprocess.run(
        cmd + [url],
        input=data_bytes,
        capture_output=True,
        timeout=timeout + 10,
    )
    out = proc.stdout.decode("utf-8", errors="replace").strip()
    if not out:
        return None
    try:
        return json.loads(out)
    except Exception:
        print(f"⚠️ Non-JSON response from {url}: {out[:300]}")
        return None


def _upload_wp_media(wp_url: str, user: str, password: str,
                     file_path: str, mime_type: str, ascii_filename: str,
                     title: str) -> tuple[int | None, str | None]:
    """Upload a media file (image, mp3, or mp4) to WordPress, replacing any prior copy with the same filename."""
    if not file_path or not os.path.exists(file_path):
        print(f"⚠️ Media file not found, skipping: {file_path}")
        return None, None

    # Clean up any prior media items with the same base filename to avoid -1/-2 duplicates
    stem = os.path.splitext(ascii_filename)[0]
    existing_media = _wp_curl_json(
        "GET",
        f"{wp_url}/media?search={stem}&per_page=20",
        user,
        password,
    )
    if isinstance(existing_media, list):
        for item in existing_media:
            if not isinstance(item, dict):
                continue
            src = item.get("source_url", "")
            mid = item.get("id")
            if mid and (ascii_filename in src or f"{stem}-" in src):
                _wp_curl_json("DELETE", f"{wp_url}/media/{mid}?force=true", user, password)

    size_mb = os.path.getsize(file_path) / (1024 * 1024)
    print(f"  ⬆️ Uploading {os.path.basename(file_path)} ({size_mb:.1f} MB) as {ascii_filename}...")

    headers = [
        f"Content-Type: {mime_type}",
        f'Content-Disposition: attachment; filename="{ascii_filename}"',
    ]
    res = _wp_curl_json(
        "POST",
        f"{wp_url}/media",
        user,
        password,
        headers=headers,
        data_file=file_path,
        timeout=300,
    )
    if isinstance(res, dict) and res.get("id") and res.get("source_url"):
        media_id = res["id"]
        source_url = res["source_url"]
        print(f"  ✓ Uploaded {ascii_filename} -> ID {media_id} ({source_url})")
        return media_id, source_url
    else:
        msg = res.get("message") if isinstance(res, dict) else str(res)
        print(f"  ❌ Failed to upload {ascii_filename}: {msg}")
        return None, None


def build_prayer_post_html(prayer_text_display: str,
                           image_id: int | None, image_url: str | None,
                           mp3_id: int | None, mp3_url: str | None,
                           mp4_id: int | None, mp4_url: str | None) -> str:
    """Build WordPress Gutenberg block HTML with Image, MP3 audio, MP4 video, and Prayer text."""
    blocks = []

    # 1. Audio Block (MP3)
    if mp3_url:
        id_attr = f' {{"id":{mp3_id}}}' if mp3_id else ''
        blocks.append(
            f'<!-- wp:audio{id_attr} -->\n'
            f'<figure class="wp-block-audio"><audio controls src="{mp3_url}"></audio>'
            f'<figcaption class="wp-element-caption">🎧 語音守望禱告 (MP3)</figcaption></figure>\n'
            f'<!-- /wp:audio -->'
        )

    # 2. Video Block (MP4 with poster cover image)
    if mp4_url:
        id_attr = f' {{"id":{mp4_id}}}' if mp4_id else ''
        poster_attr = f' poster="{image_url}"' if image_url else ''
        blocks.append(
            f'<!-- wp:video{id_attr} -->\n'
            f'<figure class="wp-block-video"><video controls{poster_attr} src="{mp4_url}"></video>'
            f'<figcaption class="wp-element-caption">🎬 字幕禱告視頻 (MP4)</figcaption></figure>\n'
            f'<!-- /wp:video -->'
        )

    # 3. Prayer Text Content
    lines = [ln.strip() for ln in prayer_text_display.strip().splitlines()]
    # Skip the first line if it duplicates the post title
    body_lines = lines[1:] if len(lines) > 1 else lines

    html_paras = []
    for idx, ln in enumerate(body_lines):
        if not ln:
            continue
        # Treat first non-empty subheading line (e.g. 天路音樂鄉音情週六守望禱告) as h3
        if not html_paras and len(ln) <= 30 and ("禱告" in ln or "祷告" in ln):
            html_paras.append(f'<!-- wp:heading {{"level":3}} -->\n<h3 class="wp-block-heading">{ln}</h3>\n<!-- /wp:heading -->')
        else:
            html_paras.append(f'<!-- wp:paragraph -->\n<p>{ln}</p>\n<!-- /wp:paragraph -->')

    blocks.extend(html_paras)

    # 4. Cover Image at bottom if not already shown as theme featured image
    if image_url:
        id_attr = f' {{"id":{image_id},"sizeSlug":"large","linkDestination":"none"}}' if image_id else ''
        img_class = f' class="wp-image-{image_id}"' if image_id else ''
        blocks.append(
            f'<!-- wp:image{id_attr} -->\n'
            f'<figure class="wp-block-image size-large"><img src="{image_url}" alt="為鄉音禱告"{img_class}/></figure>\n'
            f'<!-- /wp:image -->'
        )

    return "\n\n".join(blocks)


def upload_prayer_to_wordpress(date_str_compact: str,
                               date_obj: datetime,
                               post_title: str,
                               prayer_text_display: str,
                               image_path: str,
                               mp3_path: str,
                               mp4_path: str) -> bool:
    """Upload image, MP3, MP4 and publish/update the prayer post on prayer.tianlumusic.org."""
    wp_url, wp_user, wp_pass = load_soh_wp_credentials()
    if not wp_pass:
        print("❌ SOH_WP_APP_PASSWORD is not set in environment or ~/.secrets. Cannot upload to WordPress.")
        return False

    print("\n" + "═" * 68)
    print(f"🌐 Uploading SOH Prayer ({date_str_compact}) to {wp_url}")
    print("═" * 68)

    # Ensure cover image exists even if --no-mp4 was used
    if not os.path.exists(image_path):
        bg_src = args.mp4_bg or DEFAULT_SOH_BG
        if bg_src and os.path.exists(bg_src):
            generate_soh_dated_background(
                base_bg_path=bg_src,
                date_text=f"{date_obj.year} 年 {date_obj.month} 月 {date_obj.day} 日",
                output_path=image_path,
                resolution=args.mp4_res,
                org_name_text=raw_org_name,
            )

    # 1. Upload Image, MP3, MP4
    img_id, img_url = _upload_wp_media(
        wp_url, wp_user, wp_pass,
        image_path, "image/jpeg", f"soh_prayer_{date_str_compact}.jpg",
        f"{post_title} - Cover"
    )
    mp3_id, mp3_url = _upload_wp_media(
        wp_url, wp_user, wp_pass,
        mp3_path, "audio/mpeg", f"soh_prayer_{date_str_compact}.mp3",
        f"{post_title} - Audio"
    )
    mp4_id, mp4_url = (None, None)
    if os.path.exists(mp4_path):
        mp4_id, mp4_url = _upload_wp_media(
            wp_url, wp_user, wp_pass,
            mp4_path, "video/mp4", f"soh_prayer_{date_str_compact}.mp4",
            f"{post_title} - Video"
        )

    # 2. Build post HTML
    post_html = build_prayer_post_html(
        prayer_text_display=prayer_text_display,
        image_id=img_id, image_url=img_url,
        mp3_id=mp3_id, mp3_url=mp3_url,
        mp4_id=mp4_id, mp4_url=mp4_url,
    )

    slug = f"soh-prayer-{date_str_compact}"
    post_date_iso = f"{date_obj.strftime('%Y-%m-%d')}T08:00:00"

    payload = {
        "title": post_title,
        "slug": slug,
        "content": post_html,
        "status": "publish",
        "date": post_date_iso,
    }

    # 3. Check if post with this slug already exists
    existing = _wp_curl_json(
        "GET",
        f"{wp_url}/posts?slug={slug}&status=any",
        wp_user,
        wp_pass,
    )
    existing_id = None
    if isinstance(existing, list) and len(existing) > 0 and isinstance(existing[0], dict):
        existing_id = existing[0].get("id")

    headers = ["Content-Type: application/json; charset=utf-8"]

    if existing_id:
        if img_id:
            payload["featured_media"] = img_id
        body_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        print(f"  🔄 Updating existing WordPress post ID {existing_id} (slug: {slug})...")
        post_res = _wp_curl_json(
            "POST",
            f"{wp_url}/posts/{existing_id}",
            wp_user,
            wp_pass,
            headers=headers,
            data_bytes=body_bytes,
        )
    else:
        # Note: Hostinger AI Theme throws a TypeError if featured_media is passed during initial POST /posts
        # because $post_id is null inside rest_pre_insert_post. Create first, then attach featured_media.
        body_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        print(f"  ✨ Creating new WordPress post (slug: {slug})...")
        post_res = _wp_curl_json(
            "POST",
            f"{wp_url}/posts",
            wp_user,
            wp_pass,
            headers=headers,
            data_bytes=body_bytes,
        )
        if isinstance(post_res, dict) and post_res.get("id") and img_id:
            new_post_id = post_res["id"]
            fm_bytes = json.dumps({"featured_media": img_id}, ensure_ascii=False).encode("utf-8")
            _wp_curl_json(
                "POST",
                f"{wp_url}/posts/{new_post_id}",
                wp_user,
                wp_pass,
                headers=headers,
                data_bytes=fm_bytes,
            )

    if isinstance(post_res, dict) and post_res.get("id"):
        link = post_res.get("link", f"https://prayer.tianlumusic.org/?p={post_res['id']}")
        print(f"🎉 WordPress Post Published Successfully: {link}")
        print("═" * 68)
        return True
    else:
        print(f"❌ Failed to publish WordPress post: {post_res}")
        print("═" * 68)
        return False


# ——————————————————————————————————————————————————————————————————————————
# TTS & Audio/Video Generation Pipeline
# ——————————————————————————————————————————————————————————————————————————
async def generate_audio(text, voice, output_file, max_retries=3):
    print(f"DEBUG: Text to read: {text[:100]}...")
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            communicate = edge_tts.Communicate(text=text, voice=voice, rate=TTS_RATE)
            submaker = edge_tts.SubMaker()
            has_audio = False
            with open(output_file, "wb") as f:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        f.write(chunk["data"])
                        has_audio = True
                    elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                        submaker.feed(chunk)
            if has_audio and os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                return submaker
            else:
                raise RuntimeError("Empty audio output received.")
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                wait_sec = attempt * 1.5
                print(f"⚠️ TTS error on attempt {attempt}/{max_retries} ({e}). Retrying in {wait_sec:.1f}s...")
                await asyncio.sleep(wait_sec)
    raise last_error


async def main():
    if not args.upload_only:
        final_audio = AudioSegment.empty()
        silence = AudioSegment.silent(duration=800) 
        paragraph_durations = []
        paragraph_submakers = []

        print(f"Processing {len(paragraphs)} paragraphs with voice rotation...")
        
        for i, para in enumerate(paragraphs):
            voice = voices[i % len(voices)]
            print(f"  > Para {i+1} ({len(para)} chars) - {voice}")
            
            temp_file = f"{TEMP_DIR}temp_prayer_p{i}.mp3"
            submaker = await generate_audio(para, voice, temp_file)
            paragraph_submakers.append(submaker)
            
            try:
                segment = AudioSegment.from_mp3(temp_file)
                paragraph_durations.append(len(segment))
                final_audio += segment
                if i < len(paragraphs) - 1:
                    final_audio += silence
            finally:
                if os.path.exists(temp_file):
                    os.remove(temp_file)

        # Add Background Music (Optional)
        bgm_info_str = "None"
        if ENABLE_BGM:
            print(f"🎵 Mixing Background Music (Vol={BGM_VOLUME}dB, Intro={BGM_INTRO_DELAY}ms)...")
            final_audio = audio_mixer.mix_bgm(
                final_audio, 
                specific_filename=BGM_FILE,
                volume_db=BGM_VOLUME,
                intro_delay_ms=BGM_INTRO_DELAY
            )
            bgm_info_str = os.path.basename(BGM_FILE)
        else:
            print("🎵 Background Music: Disabled (ENABLE_BGM=False)")

        # Metadata extraction
        PRODUCER = "VI AI Foundation"
        TITLE = first_line
        ALBUM = "SOH Prayer"
        
        # Extract Verse for metadata
        verse_ref = filename_parser.extract_verse_from_text(TEXT_DISPLAY)
        COMMENTS = f"Verse: {verse_ref}; BGM: {bgm_info_str}"

        final_audio.export(OUTPUT_PATH, format="mp3", tags={
            'title': TITLE, 
            'artist': PRODUCER,
            'album': ALBUM,
            'comments': COMMENTS
        })
        print(f"✅ Saved: {OUTPUT_PATH}")

        # Generate subtitles (.srt) using frame-accurate Edge-TTS timestamps
        srt_output_path = OUTPUT_PATH.replace(".mp3", ".srt")
        intro_offset = BGM_INTRO_DELAY if ENABLE_BGM else 0
        create_subtitles_from_edge_cues(
            paragraph_submakers=paragraph_submakers,
            output_path=srt_output_path,
            intro_delay_ms=intro_offset,
            silence_ms=800,
            show_title_during_intro=True,
        )
        print(f"📄 Saved frame-accurate subtitles to: {srt_output_path}")

        # Generate MP4 Video & Dated Cover Image
        if ENABLE_MP4:
            try:
                if args.no_caption:
                    enable_caption = False
                elif args.caption is not None:
                    enable_caption = parse_caption_flag(args.caption, default=True)
                else:
                    enable_caption = True  # Captions are ON by default when --mp4 is used!

                enable_caption_large = parse_caption_flag(args.caption_large, default=False) if args.caption_large is not None else False
                scale_val = parse_caption_scale(args.caption_scale, default=2.0)
                if enable_caption_large:
                    scale_val = 3.0
                caption_scale_str = f"{scale_val:g}x"
            except ValueError as e:
                print(f"❌ {e}")
                sys.exit(1)

            create_mp4(
                input_mp3=OUTPUT_PATH,
                bg_image=args.mp4_bg,
                output_mp4=MP4_OUTPUT_PATH,
                resolution=args.mp4_res,
                caption=enable_caption,
                caption_file=args.caption_file or srt_output_path,
                is_soh=True,
                caption_scale=caption_scale_str,
                caption_large=enable_caption_large,
                date_text=date_display,
                org_name_text=raw_org_name,
            )
    else:
        print(f"⏭️ --upload-only specified: skipping TTS/MP4 generation and using existing files for {date_str_compact}.")

    # Auto-Upload to prayer.tianlumusic.org
    if ENABLE_UPLOAD:
        upload_prayer_to_wordpress(
            date_str_compact=date_str_compact,
            date_obj=date_obj,
            post_title=first_line,
            prayer_text_display=TEXT_DISPLAY,
            image_path=IMAGE_OUTPUT_PATH,
            mp3_path=OUTPUT_PATH,
            mp4_path=MP4_OUTPUT_PATH,
        )
    else:
        print("\n⏭️ Skipping WordPress upload (--no-upload specified).")


if __name__ == "__main__":
    asyncio.run(main())
