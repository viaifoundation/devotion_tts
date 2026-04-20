"""
Per-source dB boost for recorded CUV chapter MP3s (Everest vs David Yen).

Tuned to match ting/scripts/concat_daily.py so VOTD and reading-plan audio level similarly.
Applied before --speech-volume in gen_votd_*.py.
"""

from __future__ import annotations

# David Yen (male) tends hotter; Everest (female) quieter — same baseline as ting.
NARRATION_BOOST_DAVIDYEN_DB = -1.0
NARRATION_BOOST_EVEREST_DB = 8.5

# Labels returned by votd_narration_chapter.load_narration_chapter_mp3 (used for gain lookup).
CHAPTER_VOICE_LABEL_EVEREST = "Everest"
CHAPTER_VOICE_LABEL_DAVIDYEN = "David Yen"

# argparse choices for --chapter-voice (rotate = male-first, same as historical default)
CHAPTER_VOICE_CHOICES = [
    "everest",
    "davidyen",
    "rotate",
    "rotate_male_first",
    "rotate_female_first",
]


def boost_db_for_chapter_voice(voice_label: str | None) -> float:
    """Map v_name from _load_chapter_audio to gain in dB. Unknown/None → 0 (no change)."""
    if voice_label == CHAPTER_VOICE_LABEL_EVEREST:
        return float(NARRATION_BOOST_EVEREST_DB)
    if voice_label == CHAPTER_VOICE_LABEL_DAVIDYEN:
        return float(NARRATION_BOOST_DAVIDYEN_DB)
    if voice_label not in (None, ""):
        print(f"  ⚠️ Unknown chapter voice label {voice_label!r}; using 0 dB narration boost")
    return 0.0
