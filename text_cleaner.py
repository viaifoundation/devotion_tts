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

def clean_text(text):
    """
    Master cleaning function.
    """
    text = remove_control_characters(text)
    text = remove_bracketed_emojis(text)
    text = remove_space_before_god(text)
    return text

