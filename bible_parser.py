import re
from filename_parser import CHINESE_TO_ENGLISH, SINGLE_CHAPTER_BOOKS

def convert_bible_reference(text):
    """
    Parse text and convert Bible references to a TTS-friendly format.
    
    Strategy:
    1. Identify candidate patterns usually looking like "Book Chap:Verse" or "Book Verse".
    2. Validate if the 'Book' part is a known Bible book (Simplified/Traditional/English).
    3. If valid, format as "Book Chap章 Verse节".
    """
    
    # helper for verse dash normalization
    def format_verses(v_str):
        # Normalize dashes to '至'
        v_str = re.sub(r"[-—–]+", "至", v_str)
        # Normalize commas to Chinese comma
        v_str = v_str.replace(",", "，")
        return v_str

    # ---------------------------------------------------------
    # Pattern A: Standard (Book Chap:Verse)
    # capture reasonable book name candidates (Chinese or English)
    # ---------------------------------------------------------
    # Group 1: Book Name (1-10 chars, Chinese/English/Numbers allowed e.g. 1John)
    # Group 2: Chapter
    # Group 3: Verses
    # We use non-greedy matching for book name to avoid eating preceding text, 
    # but since we split by spaces/punctuation usually, \S+ might be too aggressive.
    # Let's use [\u4e00-\u9fa5a-zA-Z0-9]{1,15}
    
    # dash_pattern = r"[-—–]+"  # Don't use this inside []
    
    # 1. Standard Pattern with Colon
    # e.g. 约翰福音 3:16, 1 John 4:16
    # Verses part: digits, dashes (all types), commas. 
    # Note: Put hyphen at end of [] to avoid range ambiguity.
    # regex for verses: [\d—–,-]+
    
    pat_col = re.compile(rf"([\u4e00-\u9fa5a-zA-Z0-9]+?)\s*(\d+)\s*[:：]\s*([\d—–,-]+)")
    
    def repl_col(m):
        book_candidate = m.group(1)
        chapter = m.group(2)
        verses = m.group(3)
        
        # Validation with Suffix Check
        # e.g. "参考申命记" -> prefix="参考", book="申命记"
        
        valid_book = None
        prefix = ""
        
        if book_candidate in CHINESE_TO_ENGLISH:
            valid_book = book_candidate
        else:
            # Check suffixes
            for i in range(len(book_candidate)):
                suffix = book_candidate[i:]
                if suffix in CHINESE_TO_ENGLISH:
                    valid_book = suffix
                    prefix = book_candidate[:i]
                    break
        
        if valid_book:
            return f"{prefix}{valid_book}{chapter}章{format_verses(verses)}节"
        else:
            # Check English names or unexpected keys? 
            # If not in dict, leave as is.
            return m.group(0)

    text = pat_col.sub(repl_col, text)

    # 2. Single Chapter Pattern (Book Verse) - No Colon
    # Riskier, so strictly validate against SINGLE_CHAPTER_BOOKS
    # e.g. 犹大书 24
    pat_single = re.compile(rf"([\u4e00-\u9fa5a-zA-Z0-9]+)\s*([\d—–,-]+)(?![0-9:：])")

    def repl_single(m):
        book_candidate = m.group(1)
        verses = m.group(2)
        
        valid_book = None
        prefix = ""
        
        # Check candidate
        if book_candidate in CHINESE_TO_ENGLISH and book_candidate in SINGLE_CHAPTER_BOOKS:
             valid_book = book_candidate
        else:
             # Suffix check
             for i in range(len(book_candidate)):
                 suffix = book_candidate[i:]
                 if suffix in CHINESE_TO_ENGLISH and suffix in SINGLE_CHAPTER_BOOKS:
                     valid_book = suffix
                     prefix = book_candidate[:i]
                     break
        
        if valid_book:
             return f"{prefix}{valid_book}{format_verses(verses)}节"
        
        return m.group(0)

    text = pat_single.sub(repl_single, text)

    return text