import re

def remove_space_before_god(text):
    """
    Removes half-width and full-width spaces before the character '神'.
    Args:
        text (str): Input text.
    Returns:
        str: Text with spaces removed before '神'.
    """
    text = re.sub(r'[ 　]+(神)', r'\1', text)
    return text

def remove_control_characters(text):
    """
    Removes invisible control characters, specifically Bidirectional Text controls
    like U+202D (LRO), U+202C (PDF), etc.
    """
    # Range U+202A to U+202E (LRE, RLE, PDF, LRO, RLO)
    # U+200E, U+200F (LRM, RLM)
    # U+2066 to U+2069 (Isolates)
    pattern = r'[\u202a-\u202e\u200e\u200f\u2066-\u2069]'
    return re.sub(pattern, '', text)

def remove_bracketed_emojis(text):
    """
    Removes bracketed emojis like [玫瑰], [爱心], [合十] and tags like [WH].
    """
    text = re.sub(r'\[(玫瑰|爱心|合十|WH)\]', '', text)
    # Collapse double spaces that might result from tag removal
    return re.sub(r' +', ' ', text)

def remove_angle_bracket_tags(text):
    """
    Removes all angle bracket tags like <WH>, <WG>, <FR>, etc.
    and strips any remaining '<' or '>' characters.
    """
    if not text:
        return text
    text = re.sub(r'<[^>]*>', '', text)
    text = text.replace('<', '').replace('>', '')
    return text

def convert_urls_to_speech(text):
    """
    Convert URLs to TTS-friendly pronunciation.
    
    Examples:
        https://votd.vi.fyi -> v o t d 点 v i 点 f y i
        votd.vi.fyi         -> v o t d 点 v i 点 f y i
        http://example.com  -> example 点 com
    """
    # Step 1: Remove protocols (https://, http://)
    text = re.sub(r'https?://', '', text)
    
    # Step 2: Handle known domain patterns
    # Use '点' for periods in known domains, no extra spaces.
    text = re.sub(r'\.vi\.fyi\b', '点vi点fyi', text)
    text = re.sub(r'\.weiai\.ai\b', '点weiai点ai', text)
    
    # Step 3: Handle votd/ting prefixes
    # Removed spelling spaces to avoid extra gaps.
    text = re.sub(r'\bvotd\b', 'votd', text)
    text = re.sub(r'\bting\b', 'ting', text)
    
    return text.strip()


def fix_pronunciation(text):
    """
    Substitutes characters to force correct TTS pronunciation.
    """
    # 祢 (Nǐ) -> 你 (Nǐ) for God
    text = text.replace("祢", "你")
    
    # 使徒行傳 -> 使徒行賺 (force pronunciation "Zhuàn" instead of "Chuán")
    # Using '賺' as a phonetic guide for the TTS.
    text = text.replace("使徒行傳", "使徒行賺")
    text = text.replace("使徒行传", "使徒行赚")

    # 撒母耳 -> 薩母耳 (ensure correct pronunciation of '撒')
    text = text.replace("撒母耳", "薩母耳")

    # 俄巴底亞 -> 額巴底亞 (ensure 'É' sound)
    text = text.replace("俄巴底亞", "額巴底亞")
    text = text.replace("俄巴底亚", "额巴底亚")

    # 音乐 (Yīnyuè) -> 音悦 (force pronunciation "Yuè" instead of "Lè")
    text = text.replace("音乐", "音悦")
    text = text.replace("音樂", "音悅")
    text = text.replace("配乐", "配悦")
    text = text.replace("配樂", "配悅")
    text = text.replace("圣乐", "圣悦")
    text = text.replace("聖樂", "聖悅")
    text = text.replace("器乐", "器悦")
    text = text.replace("器樂", "器悅")
    text = text.replace("声乐", "声悦")
    text = text.replace("聲樂", "聲悅")
    text = text.replace("乐曲", "悦曲")
    text = text.replace("樂曲", "悅曲")
    text = text.replace("乐器", "悦器")
    text = text.replace("樂器", "悅器")
    text = text.replace("乐团", "悦团")
    text = text.replace("樂團", "悅團")
    text = text.replace("乐谱", "悦谱")
    text = text.replace("樂譜", "悅譜")
    text = text.replace("奏乐", "奏悦")
    text = text.replace("奏樂", "奏悅")
    text = text.replace("交响乐", "交响悦")
    text = text.replace("交響樂", "交響悅")
    text = text.replace("管弦乐", "管弦悦")
    text = text.replace("管弦樂", "管弦悅")
    text = text.replace("弦乐", "弦悦")
    text = text.replace("弦樂", "弦悅")
    text = text.replace("天籁之乐", "天籁之悦")
    text = text.replace("天籟之樂", "天籟之悅")

    return text


def restore_pronunciation_for_display(text):
    """
    Restores phonetic character substitutions back to original characters for display and subtitles.
    """
    if not text:
        return text

    # 音乐
    text = text.replace("音悦", "音乐")
    text = text.replace("音悅", "音樂")
    text = text.replace("配悦", "配乐")
    text = text.replace("配悅", "配樂")
    text = text.replace("圣悦", "圣乐")
    text = text.replace("聖悅", "聖樂")
    text = text.replace("器悦", "器乐")
    text = text.replace("器悅", "器樂")
    text = text.replace("声悦", "声乐")
    text = text.replace("聲悅", "聲樂")
    text = text.replace("悦曲", "乐曲")
    text = text.replace("悅曲", "樂曲")
    text = text.replace("悦器", "乐器")
    text = text.replace("悅器", "樂器")
    text = text.replace("悦团", "乐团")
    text = text.replace("悅團", "樂團")
    text = text.replace("悦谱", "乐谱")
    text = text.replace("悅譜", "樂譜")
    text = text.replace("奏悦", "奏乐")
    text = text.replace("奏悅", "奏樂")
    text = text.replace("交响悦", "交响乐")
    text = text.replace("交響悅", "交響樂")
    text = text.replace("管弦悦", "管弦乐")
    text = text.replace("管弦悅", "管弦樂")
    text = text.replace("弦悦", "弦乐")
    text = text.replace("弦悅", "弦樂")
    text = text.replace("天籁之悦", "天籁之乐")
    text = text.replace("天籟之悅", "天籟之樂")

    # Biblical book/person phonetic substitutions
    text = text.replace("使徒行賺", "使徒行傳")
    text = text.replace("使徒行赚", "使徒行传")
    text = text.replace("使徒行轉", "使徒行傳")
    text = text.replace("使徒行转", "使徒行传")
    text = text.replace("薩母耳", "撒母耳")
    text = text.replace("額巴底亞", "俄巴底亞")
    text = text.replace("额巴底亚", "俄巴底亚")

    return text


def handle_classical_punctuation(text):
    """
    Handles classical Chinese punctuation (e.g. CUVC).
    Replaces old-style marks with modern equivalents for correct TTS pauses.
    """
    # Circles (periods)
    text = text.replace("○", "。")
    text = text.replace("◯", "。")
    
    # Dots/Commas
    # In CUVC, 、 acts as a general comma. 
    # We replace it with ， for more consistent pause handling in some TTS.
    text = text.replace("、", "，")
    text = text.replace("．", "；")
    
    # Quotes
    text = text.replace("『", "「").replace("』", "」")
    
    # Special marks (hyphenation/translator dots)
    text = text.replace("‧", "")
    
    return text


def clean_text_basic(text):
    """
    Basic cleaning for display and saving to text files.
    Removes control characters, bracketed emojis, and fixes spacing,
    but does NOT change pronunciation or convert URLs to speech.
    """
    text = remove_control_characters(text)
    text = remove_bracketed_emojis(text)
    text = remove_angle_bracket_tags(text)
    text = remove_space_before_god(text)
    return text.strip()


def clean_text_for_tts(text):
    """
    Full cleaning for TTS engines.
    Includes basic cleaning, classical punctuation handling, URL-to-speech,
    Bible reference conversion, date conversion, and RAG pronunciation fixes.
    Note: Bible reference conversion strictly precedes pronunciation fixes (RAG).
    """
    text = clean_text_basic(text)
    text = handle_classical_punctuation(text)
    text = convert_urls_to_speech(text)

    # Convert Bible references before phonetic replacement (RAG)
    try:
        from bible_parser import convert_bible_reference
        text = convert_bible_reference(text)
    except Exception:
        pass

    try:
        from date_parser import convert_dates_in_text
        text = convert_dates_in_text(text)
    except Exception:
        try:
            from date_converter import convert_dates_in_text
            text = convert_dates_in_text(text)
        except Exception:
            pass

    text = fix_pronunciation(text)
    # Final pass to ensure no double spaces or trailing whitespace
    text = re.sub(r' +', ' ', text)
    return text.strip()


def clean_text(text):
    """
    Basic text cleaning alias to prevent premature phonetic substitution (RAG)
    before Bible verse, date, or filename extraction.
    """
    return clean_text_basic(text)

