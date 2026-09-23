#!/usr/bin/env python3
# mp3_to_mp4.py
# Create MP4 video from audio with static background image for YouTube upload
# Supports: .mp3, .m4a, .wav, .aac, .flac, etc.
# Usage: python mp3_to_mp4.py input.mp3 [--bg image.jpg]

import argparse
import os
import subprocess
import sys
from typing import Union
from caption_generator import (
    parse_caption_flag,
    parse_caption_scale,
    parse_srt_file,
    generate_srt_from_text,
    render_hardsub_video,
)

# Default background images (prefer specific, fallback to standard)
_BG_DIR = "assets/background"
DEFAULT_BG = (
    os.path.join(_BG_DIR, "background.jpg")
    if os.path.exists(os.path.join(_BG_DIR, "background.jpg"))
    else os.path.join(_BG_DIR, "background.png")
)

def find_soh_background() -> str:
    """Find SOH background image (background_soh.jpg/png), falling back to DEFAULT_BG."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(_BG_DIR, "background_soh.jpg"),
        os.path.join(_BG_DIR, "background_soh.png"),
        os.path.join(script_dir, _BG_DIR, "background_soh.jpg"),
        os.path.join(script_dir, _BG_DIR, "background_soh.png"),
        os.path.join("assets/bgm", "background_soh.jpg"),
        os.path.join("assets/bgm", "background_soh.png"),
        os.path.join(script_dir, "assets/bgm", "background_soh.jpg"),
        os.path.join(script_dir, "assets/bgm", "background_soh.png"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return DEFAULT_BG

DEFAULT_SOH_BG = find_soh_background()


def extract_date_from_filename_or_text(audio_path: str):
    """Extract date string formatted as 'YYYY 年 M 月 D 日' and org/name from filename or companion srt/txt."""
    import re
    import os
    base = os.path.basename(audio_path)
    
    # Check companion .txt or .srt first for date AND org/name
    base_no_ext = os.path.splitext(audio_path)[0]
    for ext in [".txt", ".srt"]:
        cand = f"{base_no_ext}{ext}"
        if os.path.exists(cand):
            try:
                with open(cand, "r", encoding="utf-8") as f:
                    content_file = f.read(500)
                m = re.search(r"(\d{4})年\s*(\d{1,2})月\s*(\d{1,2})日\s*(.*)", content_file)
                if m:
                    dt = f"{m.group(1)} 年 {int(m.group(2))} 月 {int(m.group(3))} 日"
                    org = m.group(4).strip()
                    return (dt, org if org else None)
            except Exception:
                pass
                
    # Fallback YYYYMMDD (e.g. 乡音情_20260906.mp3)
    m = re.search(r"(\d{4})(\d{2})(\d{2})", base)
    if m:
        return (f"{m.group(1)} 年 {int(m.group(2))} 月 {int(m.group(3))} 日", None)

    # Fallback YYYY-MM-DD
    m = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", base)
    if m:
        return (f"{m.group(1)} 年 {int(m.group(2))} 月 {int(m.group(3))} 日", None)

    return (None, None)


def get_cjk_font_for_text(text: str, font_size: int):
    """
    Finds a font that supports all characters in text (both Simplified and Traditional).
    Tries Songti with TC/SC indices first, then system CJK fonts.
    """
    from PIL import ImageFont
    from caption_generator import get_chinese_font

    candidates = [
        ("/System/Library/Fonts/Supplemental/Songti.ttc", 1),
        ("/System/Library/Fonts/Supplemental/Songti.ttc", 2),
        ("/System/Library/Fonts/Songti.ttc", 1),
        ("/System/Library/Fonts/Songti.ttc", 2),
        ("/System/Library/Fonts/Hiragino Sans GB.ttc", 0),
        ("/System/Library/Fonts/STHeiti Medium.ttc", 0),
        ("/System/Library/Fonts/STHeiti Light.ttc", 0),
        ("/System/Library/Fonts/Supplemental/Arial Unicode.ttf", 0),
        ("/Library/Fonts/Arial Unicode.ttf", 0),
        ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 0),
        ("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 0),
    ]
    for path, idx in candidates:
        if os.path.exists(path):
            try:
                f = ImageFont.truetype(path, font_size, index=idx)
                if text:
                    valid = True
                    for ch in text.strip():
                        if ch.isspace():
                            continue
                        bb = f.getbbox(ch)
                        if not bb or (bb[3] - bb[1] <= 1):
                            valid = False
                            break
                    if not valid:
                        continue
                return f
            except Exception:
                continue

    return get_chinese_font(font_size)


def generate_soh_dated_background(
    base_bg_path: str = None,
    date_text: str = None,
    output_path: str = None,
    resolution: str = "1920x1080",
    org_name_text: str = None,
) -> str:
    """
    Generates an elegant, professional SOH background image stamped with the date
    in a frosted glass pill badge with golden border.
    Also serves as the video cover / companion thumbnail page.
    """
    import re
    import tempfile
    from PIL import Image, ImageDraw, ImageFont, ImageFilter

    if not base_bg_path or not os.path.exists(base_bg_path):
        base_bg_path = find_soh_background()

    width, height = [int(v) for v in resolution.split("x")]
    im = Image.open(base_bg_path).convert("RGBA").resize((width, height), Image.Resampling.LANCZOS)

    if date_text:
        scale = height / 1080.0
        font_size = int(round(50 * scale))

        clean_date = date_text.strip()
        m = re.match(r"^(\d{4})年\s*(\d{1,2})月\s*(\d{1,2})日$", clean_date)
        if m:
            clean_date = f"{m.group(1)} 年 {int(m.group(2))} 月 {int(m.group(3))} 日"

        font = get_cjk_font_for_text(clean_date, font_size)

        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        bbox = draw.textbbox((0, 0), clean_date, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        # Placed in the top-left corner directly under the '2026' artwork
        # Leaves safe clearance before the center '每日禱告' text (starts at x=482)
        center_x = int(round(225 * (width / 1920)))
        center_y = int(round(255 * scale))

        pad_x = int(round(28 * scale))
        pad_y = int(round(12 * scale))

        box = (
            center_x - tw // 2 - pad_x,
            center_y - th // 2 - pad_y,
            center_x + tw // 2 + pad_x,
            center_y + th // 2 + pad_y + int(round(3 * scale))
        )
        radius = (box[3] - box[1]) // 2

        # 1. Soft diffused shadow beneath pill badge
        shadow_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        s_draw = ImageDraw.Draw(shadow_layer)
        s_draw.rounded_rectangle(
            (box[0], box[1] + int(round(5 * scale)), box[2], box[3] + int(round(5 * scale))),
            radius=radius,
            fill=(40, 20, 10, 45)
        )
        shadow_blur = max(2, int(round(10 * scale)))
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(shadow_blur))
        overlay = Image.alpha_composite(overlay, shadow_layer)
        draw = ImageDraw.Draw(overlay)

        # 2. Warm ivory-white frosted glass fill
        draw.rounded_rectangle(box, radius=radius, fill=(255, 253, 248, 230))

        # 3. Refined warm golden border
        border_width = max(2, int(round(2 * scale)))
        draw.rounded_rectangle(box, radius=radius, outline=(210, 165, 95, 205), width=border_width)

        # 4. Subtle inner highlight reflection
        draw.rounded_rectangle(
            (box[0] + 2, box[1] + 2, box[2] - 2, box[3] - 2),
            radius=max(1, radius - 2),
            outline=(255, 255, 255, 140),
            width=1
        )

        # 5. Deep royal navy typography
        tx = center_x - tw // 2
        ty = center_y - th // 2 - int(round(2 * scale))
        draw.text((tx, ty), clean_date, font=font, fill=(16, 52, 115, 255))
        
        # Merge shadow and overlay
        out = Image.alpha_composite(im, overlay)
        
        # 6. Draw org and name (if available) below the pill badge
        if org_name_text:
            print("DRAWING ORG NAME:", org_name_text)
            org_font_size = int(round(36 * scale))
            org_font = get_cjk_font_for_text(org_name_text, org_font_size)

            # Split into lines by whitespace if available (e.g. "遠東廣播電台 凌雲牧師")
            if ' ' in org_name_text.strip():
                lines = [p.strip() for p in org_name_text.strip().split() if p.strip()]
            else:
                lines = [org_name_text.strip()]

            # Max allowed width for each line to avoid collisions with center artwork
            max_allowed_w = int(round(400 * scale))
            for line in lines:
                line_bb = ImageDraw.Draw(out).textbbox((0, 0), line, font=org_font)
                line_w = line_bb[2] - line_bb[0]
                if line_w > max_allowed_w:
                    ratio = max_allowed_w / line_w
                    org_font_size = max(int(round(20 * scale)), int(round(org_font_size * ratio)))
                    org_font = get_cjk_font_for_text(org_name_text, org_font_size)
                    break

            curr_y = box[3] + int(round(14 * scale))
            final_draw = ImageDraw.Draw(out)
            for line in lines:
                line_bb = final_draw.textbbox((0, 0), line, font=org_font)
                line_w = line_bb[2] - line_bb[0]
                line_h = line_bb[3] - line_bb[1]
                line_x = center_x - line_w // 2
                if line_x < int(round(15 * scale)):
                    line_x = int(round(15 * scale))
                # Subtle drop shadow for readability
                final_draw.text((line_x + 2, curr_y + 2), line, font=org_font, fill=(0, 0, 0, 160))
                final_draw.text((line_x, curr_y), line, font=org_font, fill=(255, 255, 255, 255))
                curr_y += line_h + int(round(10 * scale))
            
        out = out.convert("RGB")
    else:
        out = im.convert("RGB")

    if not output_path:
        temp_file = tempfile.NamedTemporaryFile(suffix="_soh_bg.jpg", delete=False)
        output_path = temp_file.name
        temp_file.close()

    out.save(output_path, quality=95)
    return output_path



# CLI Help
if "-?" in sys.argv:
    print(f"Usage: python {sys.argv[0]} <audio_file_or_folder> [--bg image.jpg]")
    print("\nCreate MP4 video from audio with static background image for YouTube")
    print("Supports: .mp3, .m4a, .wav, .aac, .flac, .ogg, .opus")
    print("\nArguments:")
    print("  input                  Audio file OR folder (batch mode)")
    print("\nOptions:")
    print(f"  --bg, -b FILE          Background image (Default: {DEFAULT_BG}, SOH: {DEFAULT_SOH_BG})")
    print("  --resolution RES       Output resolution (Default: 1920x1080)")
    print("  --caption [true/false]       Enable burned-in captions on video (Default: true)")
    print("  --no-caption                 Disable burned-in captions on video")
    print("  --caption-scale SCALE        Caption font scale: 1x, 2x, 3x, 4x, etc. (Default: 2x)")
    print("  --caption-file FILE          Explicit SRT/VTT caption file (Default: auto <audio>.srt/.txt)")
    print("\nOutput: Auto-generated by replacing audio extension with .mp4")
    print("\nExamples:")
    print(f"  python {sys.argv[0]} output/devotion.mp3                 # Video with 2x captions (default)")
    print(f"  python {sys.argv[0]} output/devotion.mp3 --no-caption    # Video without captions")
    print(f"  python {sys.argv[0]} output/devotion.mp3 --caption-scale 3x  # 3x font")
    print(f"  python {sys.argv[0]} output/audio/                       # Batch folder with 2x captions")
    print(f"  python {sys.argv[0]} output/audio/ --no-caption          # Batch folder without captions")
    sys.exit(0)

def check_ffmpeg():
    """Check if ffmpeg is installed."""
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def generate_output_filename(input_mp3: str, output: str = None) -> str:
    """Generate output MP4 filename from input MP3."""
    if output:
        return output
    # Replace .mp3 with .mp4
    base = os.path.splitext(input_mp3)[0]
    return f"{base}.mp4"

def create_mp4(input_mp3: str, bg_image: str = None, output_mp4: str = None, 
               resolution: str = "1920x1080", audio_bitrate: str = "192k",
               metadata: dict = None, caption: bool = True,
               caption_file: str = None, is_soh: bool = False,
               caption_scale: Union[str, float] = "2x",
               caption_large: bool = False,
               date_text: str = None,
               org_name_text: str = None) -> bool:
    """
    Create MP4 video from MP3 audio with static background image.
    
    Args:
        input_mp3: Path to input audio file
        bg_image: Path or filename of background image (auto-resolves, falls back to SOH/default)
        output_mp4: Path to output MP4 video file
        resolution: Output video resolution (default: 1920x1080)
        audio_bitrate: Audio bitrate (default: 192k)
        metadata: Dict of ffmpeg metadata tags to embed (default: None)
        caption: Whether to add captions to the video (default: True)
        caption_file: Optional explicit path to .srt or .vtt subtitle file
        is_soh: Whether this is an SOH prayer video (defaults to auto-detection from filename)
        caption_scale: Caption font scale multiplier: '1x', '2x', '3x', '4x', etc. (default: '2x')
        caption_large: Shortcut for 3x font (default: False)
        date_text: Optional explicit date string (e.g. '2026年9月6日') to stamp on SOH background
    
    Returns:
        True if successful, False otherwise
    """
    is_soh = is_soh or ("soh" in os.path.basename(input_mp3).lower() or "乡音" in os.path.basename(input_mp3) or "鄉音" in os.path.basename(input_mp3))
    bg_image = resolve_bg_image(bg_image, is_soh=is_soh)
    if not bg_image or not os.path.exists(bg_image):
        print(f"❌ Background image not found: {bg_image}")
        return False

    output_mp4 = output_mp4 or generate_output_filename(input_mp3)

    # Automatically extract date for SOH if not explicitly passed
    if is_soh and not date_text:
        date_text, extracted_org = extract_date_from_filename_or_text(input_mp3)
        if not org_name_text:
            org_name_text = extracted_org

    # For SOH videos using the standard SOH background template, generate date-stamped background & thumbnail
    if is_soh and date_text and ("background_soh" in os.path.basename(bg_image) or bg_image == DEFAULT_SOH_BG):
        thumb_path = os.path.splitext(output_mp4)[0] + "_thumb.jpg"
        thumb_copy = os.path.splitext(output_mp4)[0] + ".jpg"
        bg_image = generate_soh_dated_background(
            base_bg_path=bg_image,
            date_text=date_text,
            output_path=thumb_path,
            resolution=resolution,
            org_name_text=org_name_text,
        )
        try:
            import shutil
            shutil.copyfile(bg_image, thumb_copy)
        except Exception:
            pass
        print(f"🖼️ Generated SOH thumbnail cover: {thumb_path}")

    # Parse resolution
    width, height = resolution.split("x")

    # If captions requested, render true burned-in hardsub video
    if caption:
        srt_file = None
        if caption_file and os.path.exists(caption_file):
            srt_file = caption_file
        else:
            base_without_ext = os.path.splitext(input_mp3)[0]
            if os.path.exists(f"{base_without_ext}.srt"):
                srt_file = f"{base_without_ext}.srt"
            elif os.path.exists(f"{base_without_ext}.vtt"):
                srt_file = f"{base_without_ext}.vtt"
            elif os.path.exists(f"{base_without_ext}.txt"):
                print(f"📄 Auto-generating subtitles from: {base_without_ext}.txt")
                with open(f"{base_without_ext}.txt", "r", encoding="utf-8") as f:
                    txt_content = f.read()
                srt_file = f"{base_without_ext}.srt"
                generate_srt_from_text(txt_content, input_mp3, srt_file)
            else:
                parent_dir = os.path.dirname(os.path.abspath(input_mp3))
                prayer_txt = os.path.join(parent_dir, "prayer_output.txt")
                if os.path.exists(prayer_txt):
                    print(f"📄 Auto-generating subtitles from: {prayer_txt}")
                    with open(prayer_txt, "r", encoding="utf-8") as f:
                        txt_content = f.read()
                    srt_file = f"{base_without_ext}.srt"
                    generate_srt_from_text(txt_content, input_mp3, srt_file)

        if srt_file and os.path.exists(srt_file):
            cues = parse_srt_file(srt_file)
            if cues:
                scale = parse_caption_scale(caption_scale, default=2.0)
                if caption_large:
                    scale = 3.0
                scale_label = f" [{scale:g}x Font]" if scale != 1.0 else ""
                print(f"🎬 Creating Hardsub MP4 (Burned-in Captions{scale_label})...")
                print(f"   Input audio: {input_mp3}")
                print(f"   Background:  {bg_image}")
                print(f"   Output:      {output_mp4}")
                print(f"   Resolution:  {resolution}")
                print(f"   Captions:    {srt_file} ({len(cues)} cues, Burned-in{scale_label})")
                if metadata:
                    print(f"   Metadata:    {', '.join(f'{k}={v}' for k, v in metadata.items())}")
                return render_hardsub_video(
                    input_mp3=input_mp3,
                    bg_image=bg_image,
                    output_mp4=output_mp4,
                    cues=cues,
                    resolution=resolution,
                    audio_bitrate=audio_bitrate,
                    metadata=metadata,
                    caption_scale=f"{scale:g}x",
                )
            else:
                print(f"⚠️ Caption file {srt_file} has no valid cues, falling back to static MP4.")
        else:
            print(f"⚠️ Caption requested, but no subtitle (.srt) or text (.txt) file found for: {input_mp3}")
    
    # Standard static image video generation (Captions disabled or unavailable)
    scale_filter = f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"

    cmd = [
        "ffmpeg",
        "-loop", "1",
        "-i", bg_image,
        "-i", input_mp3,
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-vf", scale_filter,
        "-c:a", "aac",
        "-b:a", audio_bitrate,
        "-pix_fmt", "yuv420p",
        "-shortest",
    ]

    # Add metadata if provided
    if metadata:
        for key, value in metadata.items():
            cmd.extend(["-metadata", f"{key}={value}"])

    cmd.extend(["-y", output_mp4])  # Overwrite output file if exists
    
    print(f"🎬 Creating MP4 video...")
    print(f"   Input audio: {input_mp3}")
    print(f"   Background:  {bg_image}")
    print(f"   Output:      {output_mp4}")
    print(f"   Resolution:  {resolution}")
    print(f"   Captions:    Disabled")
    if metadata:
        print(f"   Metadata:    {', '.join(f'{k}={v}' for k, v in metadata.items())}")
    if metadata:
        print(f"   Metadata:    {', '.join(f'{k}={v}' for k, v in metadata.items())}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            # Get file size
            size_mb = os.path.getsize(output_mp4) / (1024 * 1024)
            print(f"✅ Success! Created: {output_mp4} ({size_mb:.1f} MB)")
            return True
        else:
            print(f"❌ FFmpeg error:\n{result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


# Default metadata for ClawBible YouTube uploads
DEFAULT_METADATA = {
    "artist": "ClawBible · VI AI Foundation",
    "album_artist": "Michael Huo",
    "copyright": "© 2025-2026 VI AI Foundation · 501(c)(3)",
    "comment": "clawbible.us | michael@vi.team | VI AI Foundation",
    "url": "https://clawbible.us",
}

AUDIO_EXTENSIONS = {".mp3", ".m4a", ".wav", ".aac", ".flac", ".ogg", ".opus"}


def resolve_bg_image(bg_arg: str = None, is_soh: bool = False) -> str:
    """
    Resolve background image path.
    Supports:
      - Direct path (absolute or relative to current working directory)
      - Path relative to script directory
      - Search by filename in assets/background or assets/bgm
      - If bg_arg is None or empty: returns DEFAULT_SOH_BG if is_soh else DEFAULT_BG
      - If specified file not found, falls back gracefully to DEFAULT_SOH_BG / DEFAULT_BG
    """
    fallback = find_soh_background() if is_soh else DEFAULT_BG

    if not bg_arg:
        return fallback

    # Check direct path
    if os.path.exists(bg_arg):
        return bg_arg

    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Check relative to script dir
    script_rel = os.path.join(script_dir, bg_arg)
    if os.path.exists(script_rel):
        return script_rel

    # Search candidate directories by filename or basename
    fname = os.path.basename(bg_arg)
    candidate_dirs = [
        _BG_DIR,
        os.path.join(script_dir, _BG_DIR),
        "assets/bgm",
        os.path.join(script_dir, "assets/bgm"),
    ]
    for d in candidate_dirs:
        candidate_path = os.path.join(d, fname)
        if os.path.exists(candidate_path):
            return candidate_path

    # If specified file not found, warn and fallback
    print(f"⚠️ Background image '{bg_arg}' not found. Falling back to default: {fallback}")
    return fallback


def batch_convert(folder: str, bg_image: str, resolution: str, bitrate: str,
                  metadata: dict, output_dir: str = None,
                  caption: bool = True, caption_file: str = None,
                  caption_scale: Union[str, float] = "2x",
                  caption_large: bool = False) -> tuple[int, int]:
    """
    Convert all audio files in a folder to MP4 videos.

    Returns:
        Tuple of (success_count, fail_count)
    """
    audio_files = sorted(
        f for f in os.listdir(folder)
        if os.path.splitext(f)[1].lower() in AUDIO_EXTENSIONS
    )

    if not audio_files:
        print(f"❌ No audio files found in: {folder}")
        print(f"   Supported: {', '.join(sorted(AUDIO_EXTENSIONS))}")
        return 0, 0

    out_dir = output_dir or folder
    os.makedirs(out_dir, exist_ok=True)

    print(f"\n📂 Batch converting {len(audio_files)} file(s) from: {folder}")
    print(f"   Output dir: {out_dir}\n")

    ok, fail = 0, 0
    for i, fname in enumerate(audio_files, 1):
        print(f"── [{i}/{len(audio_files)}] {fname}")
        input_path = os.path.join(folder, fname)
        base = os.path.splitext(fname)[0]
        output_path = os.path.join(out_dir, f"{base}.mp4")

        # Add track-specific metadata
        track_meta = {**metadata, "title": base.replace("_", " ").replace("-", " ")}

        success = create_mp4(
            input_mp3=input_path,
            bg_image=bg_image,
            output_mp4=output_path,
            resolution=resolution,
            audio_bitrate=bitrate,
            metadata=track_meta,
            caption=caption,
            caption_file=caption_file,
            caption_scale=caption_scale,
            caption_large=caption_large,
        )
        if success:
            ok += 1
        else:
            fail += 1
        print()

    print(f"\n{'='*50}")
    print(f"📊 Batch complete: {ok} succeeded, {fail} failed out of {len(audio_files)}")
    return ok, fail


def main():
    parser = argparse.ArgumentParser(
        description="Create MP4 video from audio with static background image for YouTube"
    )
    parser.add_argument("input", type=str,
                        help="Input audio file OR folder for batch mode")
    parser.add_argument("--bg", "-b", type=str, default=None, 
                        help=f"Background image (Default: {DEFAULT_BG}, SOH auto-selects: {DEFAULT_SOH_BG})")
    parser.add_argument("--output", "-o", type=str, default=None,
                        help="Output MP4 file or directory (Default: auto)")
    parser.add_argument("--resolution", "-r", type=str, default="1920x1080",
                        help="Output resolution (Default: 1920x1080)")
    parser.add_argument("--bitrate", type=str, default="192k",
                        help="Audio bitrate (Default: 192k)")
    parser.add_argument("--no-meta", action="store_true",
                        help="Skip embedding default ClawBible metadata")
    parser.add_argument("--caption", "--captions", nargs="?", const="true", default=None,
                        help="Enable burned-in captions on video (true/false, default: true)")
    parser.add_argument("--no-caption", "--no-captions", action="store_true",
                        help="Disable burned-in captions on video")
    parser.add_argument("--caption-scale", "--caption-size", type=str, default=None,
                        help="Caption font scale multiplier: 1x, 2x, 3x, 4x, etc. (Default: 2x)")
    parser.add_argument("--caption-large", "--large-caption", "--caption-3x",
                        nargs="?", const="true", default=None,
                        help="Make burned-in caption font size 3x larger (true/false, default: false)")
    parser.add_argument("--caption-file", type=str, default=None,
                        help="Explicit SRT/VTT caption file (Default: auto-detect <audio>.srt/.txt)")
    
    args = parser.parse_args()
    
    # Check ffmpeg
    if not check_ffmpeg():
        print("❌ FFmpeg not found. Please install ffmpeg:")
        print("   macOS:  brew install ffmpeg")
        print("   Linux:  sudo apt install ffmpeg")
        sys.exit(1)
    
    # Resolve background image
    is_soh = False
    if not os.path.isdir(args.input):
        is_soh = "soh" in os.path.basename(args.input).lower() or "乡音" in args.input
    bg_path = resolve_bg_image(args.bg, is_soh=is_soh)
    if not bg_path or not os.path.exists(bg_path):
        print(f"❌ Background image not found: {args.bg or 'default'}")
        print(f"   Create: mkdir -p assets/background && cp your_image.jpg {DEFAULT_BG}")
        sys.exit(1)

    metadata = {} if args.no_meta else DEFAULT_METADATA.copy()

    try:
        if args.no_caption:
            enable_caption = False
        elif args.caption is not None:
            enable_caption = parse_caption_flag(args.caption, default=True)
        else:
            enable_caption = True

        enable_caption_large = parse_caption_flag(args.caption_large, default=False) if args.caption_large is not None else False
        scale_val = parse_caption_scale(args.caption_scale, default=2.0)
        if enable_caption_large:
            scale_val = 3.0
        caption_scale_str = f"{scale_val:g}x"
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)

    # --- Batch mode (input is a directory) ---
    if os.path.isdir(args.input):
        ok, fail = batch_convert(
            folder=args.input,
            bg_image=bg_path,
            resolution=args.resolution,
            bitrate=args.bitrate,
            metadata=metadata,
            output_dir=args.output,
            caption=enable_caption,
            caption_file=args.caption_file,
            caption_scale=caption_scale_str,
            caption_large=enable_caption_large,
        )
        sys.exit(0 if fail == 0 else 1)

    # --- Single file mode ---
    if not os.path.exists(args.input):
        print(f"❌ Input file not found: {args.input}")
        sys.exit(1)
    
    # Generate output filename
    output_mp4 = generate_output_filename(args.input, args.output)

    # Add title metadata from filename
    base = os.path.splitext(os.path.basename(args.input))[0]
    metadata["title"] = base.replace("_", " ").replace("-", " ")
    
    # Create MP4
    success = create_mp4(
        input_mp3=args.input,
        bg_image=bg_path,
        output_mp4=output_mp4,
        resolution=args.resolution,
        audio_bitrate=args.bitrate,
        metadata=metadata,
        caption=enable_caption,
        caption_file=args.caption_file,
        caption_scale=caption_scale_str,
        caption_large=enable_caption_large,
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
