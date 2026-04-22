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
    return re.sub(r'\[(玫瑰|爱心|合十|WH)\]', '', text)

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
    # .vi.fyi should be pronounced as "点 v i 点 f y i" (spell out to avoid "six")
    text = re.sub(r'\.vi\.fyi\b', ' 点 v i 点 f y i', text)
    
    # Step 3: Handle votd prefix (spell it out)
    text = re.sub(r'\bvotd\b', 'v o t d', text)
    
    return text


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
    text = remove_space_before_god(text)
    return text


def clean_text_for_tts(text):
    """
    Full cleaning for TTS engines.
    Includes basic cleaning plus URL-to-speech, classical punctuation handling,
    and pronunciation fixes.
    """
    text = clean_text_basic(text)
    text = handle_classical_punctuation(text)
    text = convert_urls_to_speech(text)
    text = fix_pronunciation(text)
    return text


def clean_text(text):
    """
    Legacy alias for clean_text_for_tts to maintain backward compatibility
    with scripts not yet updated.
    """
    return clean_text_for_tts(text)

