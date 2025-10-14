import re

def convert_bible_reference(text):
    """
    Parse text and convert Bible chapter:verse format from 'Book Chapter:Verse' to 'Book Chapter章Verse節'.
    Handles single verses (e.g., '罗马书 1:17'), ranges (e.g., '罗马书 3:23-24'), and comma-separated verses/ranges (e.g., '罗马书 3:21,23-24').
    Args:
        text (str): Input text containing Bible references like '罗马书 1:17' or '罗马书 3:21,23-24'.
    Returns:
        str: Text with references converted to '罗马书 1章17節' or '罗马书 3章21，23至24節'.
    """
    # Pattern to match Bible references like "罗马书 1:17" or "罗马书 3:21,23-24"
    # Captures book name (Chinese characters), chapter (digits), and verse (single, range, or comma-separated like 21,23-24)
    pattern = r'([^\s]+?)\s*(\d+):(\d+(?:,\d+(?:-\d+)?)?(?:-\d+)?)'
    # Function to format the verse part
    def format_verse(match):
        book, chapter, verse = match.groups()
        # Replace commas with Chinese comma and hyphens with Chinese '至'
        verse = verse.replace(',', '，').replace('-', '至')
        return f'{book} {chapter}章{verse}節'
    return re.sub(pattern, format_verse, text)