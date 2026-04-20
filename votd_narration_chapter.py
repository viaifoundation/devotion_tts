"""
Shared loader for recorded CUV narration chapters (Everest / David Yen) used by gen_votd_*.

Rotation index rules (strict):
  - Advance rotation only after a segment is successfully decoded (MP3 load + optional speedup).
  - If neither primary nor fallback file exists, or load raises, the rotation index is unchanged.
"""

from __future__ import annotations

import os
from typing import Callable, Optional, Tuple

from pydub import AudioSegment

from chapter_narration_gain import (
    CHAPTER_VOICE_CHOICES,
    CHAPTER_VOICE_LABEL_DAVIDYEN,
    CHAPTER_VOICE_LABEL_EVEREST,
)

# Enforce single source of truth: CLI choices must match _pick_path_and_label branches.
_HANDLED_MODES = frozenset(
    ("everest", "davidyen", "rotate", "rotate_male_first", "rotate_female_first")
)
assert _HANDLED_MODES == frozenset(CHAPTER_VOICE_CHOICES), (
    "votd_narration_chapter._pick_path_and_label out of sync with CHAPTER_VOICE_CHOICES"
)


def _pick_path_and_label(
    chapter_voice: str,
    fname: str,
    everest_dir: str,
    davidyen_dir: str,
    rotation_idx: int,
) -> Tuple[str, str, int]:
    """
    Resolve filesystem path and narration label. For rotate modes, returns
    rotation_idx + 1 as the index to commit only after successful load.
    """
    if chapter_voice == "everest":
        return os.path.join(everest_dir, fname), CHAPTER_VOICE_LABEL_EVEREST, rotation_idx
    if chapter_voice == "davidyen":
        return os.path.join(davidyen_dir, fname), CHAPTER_VOICE_LABEL_DAVIDYEN, rotation_idx
    if chapter_voice in ("rotate", "rotate_male_first"):
        if rotation_idx % 2 == 0:
            return os.path.join(davidyen_dir, fname), CHAPTER_VOICE_LABEL_DAVIDYEN, rotation_idx + 1
        return os.path.join(everest_dir, fname), CHAPTER_VOICE_LABEL_EVEREST, rotation_idx + 1
    if chapter_voice == "rotate_female_first":
        if rotation_idx % 2 == 0:
            return os.path.join(everest_dir, fname), CHAPTER_VOICE_LABEL_EVEREST, rotation_idx + 1
        return os.path.join(davidyen_dir, fname), CHAPTER_VOICE_LABEL_DAVIDYEN, rotation_idx + 1
    raise ValueError(
        f"Unhandled --chapter-voice {chapter_voice!r}; must be one of {CHAPTER_VOICE_CHOICES!r}"
    )


def _resolve_with_fallback(
    path: str,
    v_name: str,
    fname: str,
    everest_dir: str,
    davidyen_dir: str,
) -> Tuple[Optional[str], Optional[str]]:
    """Return (path, v_name) or (None, None) if neither side exists."""
    if os.path.exists(path):
        return path, v_name
    alt_path = os.path.join(
        everest_dir if v_name == CHAPTER_VOICE_LABEL_DAVIDYEN else davidyen_dir,
        fname,
    )
    if os.path.exists(alt_path):
        print(f"  ⚠️ {v_name} audio not found for {fname}, falling back...")
        flipped = (
            CHAPTER_VOICE_LABEL_EVEREST
            if v_name == CHAPTER_VOICE_LABEL_DAVIDYEN
            else CHAPTER_VOICE_LABEL_DAVIDYEN
        )
        return alt_path, flipped
    print(f"  ⚠️ Chapter audio not found for {fname}")
    return None, None


def load_narration_chapter_mp3(
    chapter_voice: str,
    book_num: int,
    chapter_num: int,
    everest_dir: str,
    davidyen_dir: str,
    rotation_idx: int,
    speed: float,
    speedup_ffmpeg: Callable[[AudioSegment, float], AudioSegment],
) -> Tuple[Optional[AudioSegment], Optional[str], int]:
    """
    Load one chapter MP3. Returns (segment, v_name, new_rotation_idx).

    new_rotation_idx equals the incoming rotation_idx unless rotate modes succeed,
    in which case it is the post-pick index from _pick_path_and_label.
    """
    fname = f"{book_num:03d}_{chapter_num:03d}.mp3"
    path, v_name, idx_after_success = _pick_path_and_label(
        chapter_voice, fname, everest_dir, davidyen_dir, rotation_idx
    )

    resolved = _resolve_with_fallback(path, v_name, fname, everest_dir, davidyen_dir)
    if resolved[0] is None:
        return None, None, rotation_idx

    path, v_name = resolved[0], resolved[1]

    try:
        seg = AudioSegment.from_mp3(path)
        orig_len = len(seg) / 1000
        if speed != 1.0 and speed > 0:
            seg = speedup_ffmpeg(seg, speed)
        print(
            f"  📖 Loaded chapter audio: {fname} [{v_name}] "
            f"({orig_len:.1f}s → {len(seg) / 1000:.1f}s @ {speed}x)"
        )
        return seg, v_name, idx_after_success
    except Exception as e:
        print(f"  ❌ Error loading {fname}: {e}")
        return None, None, rotation_idx
