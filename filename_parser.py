from datetime import datetime, timedelta

# Full mapping: Chinese (Simplified + Traditional) → Standard English abbreviation
# Feel free to add more if you ever use rare books
CHINESE_TO_ENGLISH = {
    # Simplified Chinese (zh-cn)
    "创世记": "Genesis",   "创": "Genesis",
    "出埃及记": "Exodus",  "出": "Exodus",
    "利未记": "Leviticus", "利": "Leviticus",
    "民数记": "Numbers",   "民": "Numbers",
    "申命记": "Deuteronomy","申": "Deuteronomy",
    "约书亚记": "Joshua",  "书": "Joshua",
    "士师记": "Judges",    "士": "Judges",
    "路得记": "Ruth",      "得": "Ruth",
    "撒母耳记上": "1Samuel", "撒上": "1Samuel",
    "撒母耳记下": "2Samuel", "撒下": "2Samuel",
    "列王纪上": "1Kings",   "王上": "1Kings",
    "列王纪下": "2Kings",   "王下": "2Kings",
    "历代志上": "1Chronicles", "代上": "1Chron",
    "历代志下": "2Chronicles", "代下": "2Chron",
    "以斯拉记": "Ezra",    "拉": "Ezra",
    "尼希米记": "Nehemiah", "尼": "Nehemiah",
    "以斯帖记": "Esther",  "斯": "Esther",
    "约伯记": "Job",       "伯": "Job",
    "诗篇": "Psalm",       "诗": "Psalm",
    "箴言": "Proverbs",    "箴": "Proverbs",
    "传道书": "Ecclesiastes","传": "Ecclesiastes",
    "雅歌": "SongOfSolomon","歌": "SongOfSongs",
    "以赛亚书": "Isaiah",  "赛": "Isaiah",
    "耶利米书": "Jeremiah","耶": "Jeremiah",
    "耶利米哀歌": "Lamentations","哀": "Lamentations",
    "以西结书": "Ezekiel", "结": "Ezekiel",
    "但以理书": "Daniel",  "但": "Daniel",
    "何西阿书": "Hosea",   "何": "Hosea",
    "约珥书": "Joel",      "珥": "Joel",
    "阿摩司书": "Amos",    "摩": "Amos",
    "俄巴底亚书": "Obadiah","俄": "Obadiah",
    "约拿书": "Jonah",     "拿": "Jonah",
    "弥迦书": "Micah",     "弥": "Micah",
    "那鸿书": "Nahum",     "鸿": "Nahum",
    "哈巴谷书": "Habakkuk", "哈": "Habakkuk",
    "西番雅书": "Zephaniah","番": "Zephaniah",
    "哈该书": "Haggai",    "该": "Haggai",
    "撒迦利亚书": "Zechariah","亚": "Zechariah",
    "玛拉基书": "Malachi", "玛": "Malachi",

    "马太福音": "Matthew", "太": "Matthew",
    "马可福音": "Mark",   "可": "Mark",
    "路加福音": "Luke",   "路": "Luke",
    "约翰福音": "John",   "约": "John",
    "使徒行传": "Acts",   "徒": "Acts",
    "罗马书": "Romans",   "罗": "Romans",
    "哥林多前书": "1Corinthians", "林前": "1Cor",
    "哥林多后书": "2Corinthians", "林后": "2Cor",
    "加拉太书": "Galatians", "加": "Galatians",
    "以弗所书": "Ephesians", "弗": "Ephesians",
    "腓立比书": "Philippians","腓": "Philippians",
    "歌罗西书": "Colossians", "西": "Colossians",
    "帖撒罗尼迦前书": "1Thessalonians", "帖前": "1Thess",
    "帖撒罗尼迦后书": "2Thessalonians", "帖后": "2Thess",
    "提摩太前书": "1Timothy", "提前": "1Tim",
    "提摩太后书": "2Timothy", "提后": "2Tim",
    "提多书": "Titus",     "多": "Titus",
    "腓利门书": "Philemon", "门": "Philemon",
    "希伯来书": "Hebrews", "来": "Hebrews",
    "雅各书": "James",     "雅": "James",
    "彼得前书": "1Peter",  "彼前": "1Pet",
    "彼得后书": "2Peter",  "彼后": "2Pet",
    "约翰一书": "1John",   "约一": "1John",
    "约翰二书": "2John",   "约二": "2John",
    "约翰三书": "3John",   "约三": "3John",
    "犹大书": "Jude",      "犹": "Jude",
    "启示录": "Revelation","启": "Revelation",

    # Traditional Chinese (zh-tw) – most are the same, but a few differ
    "創世記": "Genesis", "出埃及記": "Exodus", "利未記": "Leviticus",
    "民數記": "Numbers", "申命記": "Deuteronomy",
    "約書亞記": "Joshua", "書": "Joshua", "士師記": "Judges", "路得記": "Ruth",
    "撒母耳記上": "1Samuel", "撒母耳記下": "2Samuel",
    "列王紀上": "1Kings", "列王紀下": "2Kings",
    "歷代志上": "1Chronicles", "歷代志下": "2Chronicles",
    "以斯拉記": "Ezra", "尼希米記": "Nehemiah", "以斯帖記": "Esther",
    "約伯記": "Job", "詩篇": "Psalm", "詩": "Psalm", "箴言": "Proverbs",
    "傳道書": "Ecclesiastes", "傳": "Ecclesiastes", "雅歌": "SongOfSongs",
    "以賽亞書": "Isaiah", "賽": "Isaiah", "耶利米書": "Jeremiah", "耶利米哀歌": "Lamentations",
    "以西結書": "Ezekiel", "結": "Ezekiel", "但以理書": "Daniel",
    "俄巴底亞書": "Obadiah", "約拿書": "Jonah", "彌迦書": "Micah", "彌": "Micah",
    "那鴻書": "Nahum", "鴻": "Nahum", "哈巴谷書": "Habakkuk", "西番雅書": "Zephaniah",
    "哈該書": "Haggai", "該": "Haggai", "撒迦利亞書": "Zechariah", "亞": "Zechariah",
    "瑪拉基書": "Malachi", "瑪": "Malachi",
    "馬太福音": "Matthew", "馬可福音": "Mark", "路加福音": "Luke",
    "約翰福音": "John", "約": "John", "使徒行傳": "Acts", "羅馬書": "Romans", "羅": "Romans",
    "哥林多前書": "1Corinthians", "哥林多後書": "2Corinthians", "林後": "2Cor",
    "加拉太書": "Galatians", "以弗所書": "Ephesians", "腓立比書": "Philippians",
    "歌羅西書": "Colossians", "帖撒羅尼迦前書": "1Thessalonians",
    "帖撒羅尼迦後書": "2Thessalonians", "帖後": "2Thess",
    "提摩太前書": "1Timothy", "提摩太後書": "2Timothy", "提後": "2Tim",
    "提多書": "Titus", "腓利門書": "Philemon", "門": "Philemon",
    "希伯來書": "Hebrews", "來": "Hebrews", "雅各書": "James",
    "彼得前書": "1Peter", "彼得後書": "2Peter", "彼後": "2Pet",
    "約翰一書": "1John", "約一": "1John", "約翰二書": "2John", "約二": "2John",
    "約翰三書": "3John", "約三": "3John", "猶大書": "Jude", "猶": "Jude",
    "啟示錄": "Revelation", "啟": "Revelation", "創": "Genesis"
}

def translate_chinese_book(book_name: str) -> str:
    """Return English book name if input is Chinese, otherwise return original."""
    return CHINESE_TO_ENGLISH.get(book_name.strip(), book_name)

def generate_filename(verse: str, date: str = None, prefix: str = None, base_name: str = "VOTD") -> str:
    if date is None:
        date_obj = datetime.today()
    else:
        date_obj = datetime.strptime(date, "%Y-%m-%d")

    # Split verse into book + chapter:verse
    # Accepts many formats: 約翰福音 3:16, John 3:16, 约3:16, 詩篇23:1 etc.
    parts = verse.replace("：", ":").split()
    chapter_verse = parts[-1]                     # last part is always chapter:verse
    book_parts = parts[:-1]

    # Re-join book name in case it has multiple words (e.g. 撒母耳記上)
    full_book = "".join(book_parts)
    english_book = translate_chinese_book(full_book)

    # Final reference: Psalm-23-1 or 1Cor-3-16 etc.
    reference = f"{english_book}-{chapter_verse.replace(':', '-')}"

    date_str = date_obj.strftime("%Y-%m-%d")
    
    basename = f"{base_name}_{reference}_{date_str}.mp3"
    
    # If a prefix is provided (and not empty), prepend it
    if prefix:
         return f"{prefix}_{basename}"
    return basename

def extract_filename_prefix(text: str) -> str:
    """
    Scan text for a specific prefix parameter like '鄉音情SOH_Sound_of_Home'.
    Currently, the rule is to search for a specific known identifier or a pattern.
    Based on request: "if we have that param in text as '鄉音情SOH_Sound_of_Home'"
    
    Let's implement a generic search for "FilenamePrefix: <value>" OR 
    if the text contains the specific string "鄉音情SOH_Sound_of_Home", return it?
    
    Actually, user said: "if we have that param in text as '鄉音情SOH_Sound_of_Home' the filename should have a prefix with the string".
    It implies if the string exists in the text, use it as prefix.
    """
    # Specific known prefixes to scan for
    KNOWN_PREFIXES = ["鄉音情SOH_Sound_of_Home"]
    
    for prefix in KNOWN_PREFIXES:
        if prefix in text:
            return prefix
            
    # Generic parameter parsing: "FilenamePrefix: MyPrefix"
    match = re.search(r"FilenamePrefix:\s*([^\n\r]+)", text)
    if match:
        return match.group(1).strip()
        
    return None

import re

# Books with only one chapter (where "Book Num" often means "Book Verse")
SINGLE_CHAPTER_BOOKS = {
    "俄巴底亚书", "俄", "Obadiah",
    "腓利门书", "门", "Philemon",
    "约翰二书", "约二", "2John",
    "约翰三书", "约三", "3John",
    "犹大书", "犹", "Jude"
}

def extract_verse_from_text(text: str) -> str:
    """
    Extracts the first valid Chinese Bible verse reference from text.
    Uses robust candidate finding + dictionary validation.
    
    Supports:
    1. Standard: Book Chapter:Verse(-Range)? (e.g., 罗马书 10:14-17)
    2. Single-Chapter: Book Verse(-Range)? (e.g., 犹大书 24-25 -> 犹大书 1:24-25)
    """
    
    # Clean text of invisible chars/parens for easier matching? 
    # Actually, Regex is powerful enough.
    
    dash_re = r"[-—–]+"
    
    # Pattern 1: Standard (Book Candidate + Chap + : + Verse)
    # Be relaxed on Book Candidate: [\u4e00-\u9fa5a-zA-Z0-9]{1,15}
    # But ensure we don't capture "参考申命记" as the book name.
    # We want to capture '申命记' inside '...'.
    # Since we validate against the dict, we can iterate over ALL matches of pattern.
    
    # Regex: (PossibleBook)\s*(\d+)\s*[:：]\s*(\d+(?:[-—–]+\d+)?)
    regex_std = re.compile(rf"([\u4e00-\u9fa5a-zA-Z0-9]*[\u4e00-\u9fa5a-zA-Z])\s*(\d+)\s*[:：]\s*(\d+(?:{dash_re}\d+)?)")
    
    for m in regex_std.finditer(text):
        book_candidate = m.group(1)
        chapter = m.group(2)
        verse_part = m.group(3)
        
        # Check if book_candidate ENDS with a valid book name
        # e.g. "参考申命记" -> ends with "申命记"
        # We need to find the longest suffix that IS a valid book.
        
        valid_book = None
        # Try full candidate first
        if book_candidate in CHINESE_TO_ENGLISH:
            valid_book = book_candidate
        else:
            # Try suffixes from longest to shortest
            # Optimization: Max book length is ~10 chars.
            for i in range(len(book_candidate)):
                suffix = book_candidate[i:]
                if suffix in CHINESE_TO_ENGLISH:
                    valid_book = suffix
                    break
        
        if valid_book:
            # Found one!
            # Normalize dashes
            verse_part = re.sub(dash_re, '-', verse_part)
            return f"{valid_book} {chapter}:{verse_part}"

    # Pattern 2: Single Chapter
    # Only if Book is in SINGLE_CHAPTER_BOOKS
    regex_single = re.compile(rf"([\u4e00-\u9fa5a-zA-Z0-9]*[\u4e00-\u9fa5a-zA-Z])\s*(\d+(?:{dash_re}\d+)?)(?![0-9:：])")
    
    for m in regex_single.finditer(text):
        book_candidate = m.group(1)
        verse_part = m.group(2)
        
        valid_book = None
        if book_candidate in CHINESE_TO_ENGLISH and book_candidate in SINGLE_CHAPTER_BOOKS:
             valid_book = book_candidate
        else:
            # Suffix check
            for i in range(len(book_candidate)):
                 suffix = book_candidate[i:]
                 if suffix in CHINESE_TO_ENGLISH and suffix in SINGLE_CHAPTER_BOOKS:
                     valid_book = suffix
                     break
        
        if valid_book:
             verse_part = re.sub(dash_re, '-', verse_part)
             return f"{valid_book} 1:{verse_part}"

    return None



# ———————————————————————
# Demo
# ———————————————————————
if __name__ == "__main__":
    test_verses = [
        "John 3:16",
        "約翰福音 3:16",      # Simplified
        "約翰福音 3：16",     # Full-width colon
        "約3:16",            # Common short form
        "詩篇 23:1",
        "馬太福音5:16",
        "啟示錄 22:21",       # Revelation
        "撒母耳記上 16:7",    # 1 Samuel
    ]

    for v in test_verses:
        print(f"{v:20} → {generate_filename(v)}")
