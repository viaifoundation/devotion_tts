import re

def remove_space_before_god(text):
    """
    Removes half-width and full-width spaces before the character '神'.
    Args:
        text (str): Input text.
    Returns:
        str: Text with spaces removed before '神'.
    """
    text = re.sub(r'　(神)', r'\1', text)
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
    Removes bracketed emojis like [玫瑰], [爱心], [合十].
    """
    return re.sub(r'\[(玫瑰|爱心|合十)\]', '', text)

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


def clean_text(text):
    """
    Master cleaning function.
    """
    text = remove_control_characters(text)
    text = remove_bracketed_emojis(text)
    text = remove_space_before_god(text)
    text = convert_urls_to_speech(text)
    return text

