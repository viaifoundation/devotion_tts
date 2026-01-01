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
        http://example.com  -> example 点 com
    """
    # Known domain mappings for better pronunciation
    domain_mappings = {
        'vi.fyi': 'v i 点 f y i',  # Spell out to avoid "six"
        'votd.vi.fyi': 'v o t d 点 v i 点 f y i',
    }
    
    def url_to_speech(match):
        url = match.group(0)
        # Remove protocol
        clean_url = re.sub(r'^https?://', '', url)
        # Remove trailing slash
        clean_url = clean_url.rstrip('/')
        
        # Check for known domain mappings
        for domain, pronunciation in domain_mappings.items():
            if clean_url == domain or clean_url.endswith('/' + domain):
                return pronunciation
        
        # Default: spell out domain parts
        # Replace dots with "点" (Chinese for "dot")
        result = clean_url.replace('.', ' 点 ')
        # Remove path components after domain
        result = result.split('/')[0]
        return result
    
    # Match URLs
    url_pattern = r'https?://[^\s<>"\'\]\)]+[^\s<>"\'\]\),.]'
    text = re.sub(url_pattern, url_to_speech, text)
    
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

