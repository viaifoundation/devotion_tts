"""
bible_db.py – Query Bible text from local SQLite database.

The SQLite file is at assets/bible/bible.sqlite (exported from BibleEngine MySQL).

Table schema:
  verses(book INT, chapter INT, verse INT, cuvt TEXT, ncvs TEXT, ccsb TEXT, clbs TEXT)

Translation codes:
  cuvt = 和合本 (CUV Traditional)
  ncvs = 新譯本 (CNV)
  ccsb = 標準譯本 (CSBS)
  clbs = 當代譯本 (CCB / 當代聖經)
"""

import os
import re
import sqlite3
import filename_parser

# Optional: opencc for simplified → traditional Chinese conversion
try:
    import opencc
    _S2T = opencc.OpenCC('s2t')
    def _s2t(text: str) -> str:
        return _S2T.convert(text) if text else text
except ImportError:
    _S2T = None
    def _s2t(text: str) -> str:
        return text  # No conversion available

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB = os.path.join(SCRIPT_DIR, "assets", "bible", "db", "bible.sqlite")

# Translation codes → display labels (Traditional Chinese)
TRANSLATION_LABELS = {
    "cuvt": "和合本",
    "ncvs": "新譯本",
    "ccsb": "標準譯本",
    "clbs": "當代譯本",
}

# Book number (1-66) from English name
BOOK_NUMBER = {
    "Genesis": 1, "Exodus": 2, "Leviticus": 3, "Numbers": 4, "Deuteronomy": 5,
    "Joshua": 6, "Judges": 7, "Ruth": 8, "1Samuel": 9, "2Samuel": 10,
    "1Kings": 11, "2Kings": 12, "1Chronicles": 13, "1Chron": 13, "2Chronicles": 14, "2Chron": 14,
    "Ezra": 15, "Nehemiah": 16, "Esther": 17, "Job": 18, "Psalm": 19,
    "Proverbs": 20, "Ecclesiastes": 21, "SongOfSolomon": 22, "SongOfSongs": 22,
    "Isaiah": 23, "Jeremiah": 24, "Lamentations": 25, "Ezekiel": 26, "Daniel": 27,
    "Hosea": 28, "Joel": 29, "Amos": 30, "Obadiah": 31, "Jonah": 32,
    "Micah": 33, "Nahum": 34, "Habakkuk": 35, "Zephaniah": 36, "Haggai": 37,
    "Zechariah": 38, "Malachi": 39, "Matthew": 40, "Mark": 41, "Luke": 42,
    "John": 43, "Acts": 44, "Romans": 45, "1Corinthians": 46, "1Cor": 46,
    "2Corinthians": 47, "2Cor": 47, "Galatians": 48, "Ephesians": 49,
    "Philippians": 50, "Colossians": 51, "1Thessalonians": 52, "1Thess": 52,
    "2Thessalonians": 53, "2Thess": 53, "1Timothy": 54, "1Tim": 54,
    "2Timothy": 55, "2Tim": 55, "Titus": 56, "Philemon": 57, "Hebrews": 58,
    "James": 59, "1Peter": 60, "1Pet": 60, "2Peter": 61, "2Pet": 61,
    "1John": 62, "2John": 63, "3John": 64, "Jude": 65, "Revelation": 66,
}

# Reverse: book number → Traditional Chinese name
# Built from filename_parser.CHINESE_TO_ENGLISH
_ENGLISH_TO_CHINESE_TW = {}
for cn_name, en_name in filename_parser.CHINESE_TO_ENGLISH.items():
    if en_name in BOOK_NUMBER:
        num = BOOK_NUMBER[en_name]
        # Prefer Traditional Chinese (contains 書/記/音 etc.)
        if num not in _ENGLISH_TO_CHINESE_TW or '書' in cn_name or '記' in cn_name or '音' in cn_name or '篇' in cn_name:
            _ENGLISH_TO_CHINESE_TW[num] = cn_name

# Number of chapters per book (1-66)
BOOK_CHAPTER_COUNT = [
    0,  # placeholder for index 0
    50, 40, 27, 36, 34,  # Gen-Deut
    24, 21, 4, 31, 24, 22, 25, 29, 36,  # Josh-2Chr
    10, 13, 10, 42, 150, 31, 12, 8,  # Ezra-Song
    66, 52, 5, 48, 12,  # Isa-Dan
    14, 3, 9, 1, 4, 7, 3, 3, 3, 2, 14, 4,  # Hos-Mal
    28, 16, 24, 21, 28,  # Matt-Acts
    16, 16, 13, 6, 6, 4, 4, 5, 3, 6, 4, 3, 1,  # Rom-Phlm
    13, 5, 5, 3, 5, 1, 1, 1, 22  # Heb-Rev
]


def chinese_book_to_number(book_name: str) -> int:
    """Convert Chinese book name to book number 1-66."""
    english = filename_parser.CHINESE_TO_ENGLISH.get(book_name)
    if english and english in BOOK_NUMBER:
        return BOOK_NUMBER[english]
    return None


def book_number_to_chinese(book_num: int) -> str:
    """Convert book number (1-66) to Traditional Chinese name."""
    return _ENGLISH_TO_CHINESE_TW.get(book_num, str(book_num))


def parse_verse_reference(ref_text: str):
    """
    Parse a verse reference like '(詩篇 77:12 和合本)' or '詩篇 77:12'.
    Returns (book_num, chapter, verse_start, verse_end) or None.
    """
    # Strip parentheses and translation labels
    text = ref_text.strip().strip("(（）)")
    for label in TRANSLATION_LABELS.values():
        text = text.replace(label, "").strip()

    # Try to match: BookName Chapter:Verse or BookName Chapter:Verse-Verse2
    m = re.match(r'(.+?)\s+(\d+)\s*[:：]\s*(\d+)(?:\s*[-–—]\s*(\d+))?', text)
    if not m:
        return None

    book_name = m.group(1).strip()
    chapter = int(m.group(2))
    verse_start = int(m.group(3))
    verse_end = int(m.group(4)) if m.group(4) else verse_start

    # Resolve book name
    book_num = chinese_book_to_number(book_name)
    if not book_num:
        # Try suffixes
        for i in range(len(book_name)):
            suffix = book_name[i:]
            book_num = chinese_book_to_number(suffix)
            if book_num:
                break

    if not book_num:
        return None

    return (book_num, chapter, verse_start, verse_end)


# Regex to strip tags from Bible text (matching bibleengine PHP logic):
#   <WH\w+> = Hebrew Strong's numbers, <WG\w+> = Greek Strong's numbers
#   <FR>, <Fr> = formatting markers in CUV/KJV/NASB
_STRONGS_RE = re.compile(r'<W[HG]\w+>', re.IGNORECASE)
_FORMAT_RE = re.compile(r'<FR>|<Fr>', re.IGNORECASE)

def _clean_verse_text(text: str) -> str:
    """Clean verse text: strip Strong's/formatting tags and convert simplified → traditional."""
    if not text:
        return text
    # Strip formatting tags (FR/Fr)
    text = _FORMAT_RE.sub('', text)
    # Strip Strong's number tags
    text = _STRONGS_RE.sub('', text)
    # Convert simplified → traditional Chinese
    text = _s2t(text)
    return text.strip()


class BibleDB:
    """Query Bible verses from local SQLite database."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or DEFAULT_DB
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(
                f"Bible SQLite not found: {self.db_path}\n"
                f"Run scripts/export_bible_sqlite.py on your VPS to create it."
            )
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def close(self):
        if self.conn:
            self.conn.close()

    def get_verse(self, book: int, chapter: int, verse: int, translation: str = "cuvt") -> str:
        """Get a single verse text."""
        if translation not in TRANSLATION_LABELS:
            raise ValueError(f"Unknown translation: {translation}")
        row = self.conn.execute(
            f"SELECT {translation} FROM verses WHERE book=? AND chapter=? AND verse=?",
            (book, chapter, verse)
        ).fetchone()
        return _clean_verse_text(row[0]) if row else None

    def get_verses(self, book: int, chapter: int, verse_start: int, verse_end: int,
                   translation: str = "cuvt") -> list:
        """Get a range of verses. Returns list of (verse_num, text)."""
        if translation not in TRANSLATION_LABELS:
            raise ValueError(f"Unknown translation: {translation}")
        rows = self.conn.execute(
            f"SELECT verse, {translation} FROM verses WHERE book=? AND chapter=? AND verse>=? AND verse<=? ORDER BY verse",
            (book, chapter, verse_start, verse_end)
        ).fetchall()
        return [(r[0], _clean_verse_text(r[1])) for r in rows if r[1]]

    def get_chapter(self, book: int, chapter: int, translation: str = "cuvt") -> list:
        """Get all verses of a chapter. Returns list of (verse_num, text)."""
        if translation not in TRANSLATION_LABELS:
            raise ValueError(f"Unknown translation: {translation}")
        rows = self.conn.execute(
            f"SELECT verse, {translation} FROM verses WHERE book=? AND chapter=? ORDER BY verse",
            (book, chapter)
        ).fetchall()
        return [(r[0], _clean_verse_text(r[1])) for r in rows if r[1]]

    def get_chapter_text(self, book: int, chapter: int, translation: str = "cuvt") -> str:
        """Get full chapter as a single text block with verse numbers removed."""
        verses = self.get_chapter(book, chapter, translation)
        if not verses:
            return ""
        return "\n".join(text for _, text in verses)

    def get_verse_text(self, book: int, chapter: int, verse_start: int, verse_end: int,
                       translation: str = "cuvt") -> str:
        """Get verse range as a single text block."""
        verses = self.get_verses(book, chapter, verse_start, verse_end, translation)
        if not verses:
            return ""
        return "\n".join(text for _, text in verses)

    def get_verse_in_all_translations(self, book: int, chapter: int,
                                       verse_start: int, verse_end: int) -> list:
        """
        Get a verse range in all 4 translations (CUV appears twice: first and last).
        Returns list of (translation_code, label, text).
        Order: 和合本, 新譯本, 標準譯本, 當代譯本, 和合本
        """
        result = []
        # CUV bookends: CUV, CNV, CSBS, CCB, CUV
        for code in ["cuvt", "ncvs", "ccsb", "clbs", "cuvt"]:
            text = self.get_verse_text(book, chapter, verse_start, verse_end, code)
            if text:
                label = TRANSLATION_LABELS[code]
                result.append((code, label, text))
        return result

    def expand_verse_block(self, book: int, chapter: int,
                           verse_start: int, verse_end: int) -> dict:
        """
        Given a verse reference, produce the full expanded block:
        - Full chapter text in 和合本 (for Everest audio alignment)
        - The specific verse in 4 translations

        Returns dict with:
          chapter_text: str (full chapter in 和合本)
          chapter_ref: str (e.g. "詩篇 86:1-17 和合本")
          translations: [(code, label, text, ref_str), ...]
        """
        book_name = book_number_to_chinese(book)

        # Determine chapter verse range for the full chapter reference
        chapter_verses = self.get_chapter(book, chapter, "cuvt")
        if chapter_verses:
            ch_v_start = chapter_verses[0][0]
            ch_v_end = chapter_verses[-1][0]
            chapter_text = "\n".join(text for _, text in chapter_verses)
            chapter_ref = f"{book_name} {chapter}:{ch_v_start}-{ch_v_end} 和合本"
        else:
            chapter_text = ""
            chapter_ref = f"{book_name} {chapter} 和合本"

        # Get verse in all translations (CUV bookends)
        translations = []
        for code in ["cuvt", "ncvs", "ccsb", "clbs", "cuvt"]:
            text = self.get_verse_text(book, chapter, verse_start, verse_end, code)
            if text:
                label = TRANSLATION_LABELS[code]
                if verse_start == verse_end:
                    ref_str = f"{book_name} {chapter}:{verse_start} {label}"
                else:
                    ref_str = f"{book_name} {chapter}:{verse_start}-{verse_end} {label}"
                translations.append((code, label, text, ref_str))

        return {
            "chapter_text": chapter_text,
            "chapter_ref": chapter_ref,
            "translations": translations,
            "book_num": book,
            "chapter_num": chapter,
        }
