import re
from datetime import datetime

def convert_dates_in_text(text):
    def repl_ymd(m):
        yyyy, mm, dd = m.groups()
        return f"{yyyy}年{int(mm)}月{int(dd)}日"

    text = re.sub(r'\b(\d{4})-(\d{1,2})-(\d{1,2})\b', repl_ymd, text)

    def repl_mdy(m):
        mm, dd, yyyy = m.groups()
        return f"{yyyy}年{int(mm)}月{int(dd)}日"

    text = re.sub(r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b', repl_mdy, text)

    return text

def extract_date_from_text(text):
    """
    Extracts date from text in various formats:
    1. YYYY-MM-DD
    2. MM/DD/YYYY
    3. YYYY年MM月DD日
    4. MM月DD日 (Assumes current year)
    
    Returns date as 'YYYY-MM-DD' string or None if not found.
    """
    if not text:
        return None
        
    # 1. YYYY年MM月DD日
    match = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", text)
    if match:
        y, m, d = match.groups()
        return f"{y}-{int(m):02d}-{int(d):02d}"

    # 2. MM月DD日 (Implicit Year)
    match = re.search(r"(\d{1,2})月(\d{1,2})日", text)
    if match:
        m, d = match.groups()
        current_year = datetime.now().year
        return f"{current_year}-{int(m):02d}-{int(d):02d}"

    # 3. MM/DD/YYYY
    match = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", text)
    if match:
        m, d, y = match.groups()
        return f"{y}-{int(m):02d}-{int(d):02d}"

    # 4. YYYY-MM-DD
    match = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", text)
    if match:
        y, m, d = match.groups()
        return f"{y}-{int(m):02d}-{int(d):02d}"

    return None


def strip_all_dates(text):
    """
    Strips all explicit calendar dates and weekday labels from text.
    Handles YYYY年MM月DD日, YYYY-MM-DD, YYYY/MM/DD, YYYY.MM.DD, MM月DD日, MM/DD,
    and associated weekday markers like (周六), 周一~周日, 星期一~星期日, Mon~Sun.
    """
    if not text:
        return text

    # 1. Full dates: 2026年7月25日, 2026-07-25, 2026/07/25, 2026.07.25, 2026-7-25, etc.
    text = re.sub(r'\d{4}\s*[-/年\.]\s*\d{1,2}\s*[-/月\.]\s*\d{1,2}\s*日?', '', text)
    
    # 2. Month-Day dates: 7月25日
    text = re.sub(r'\d{1,2}\s*月\s*\d{1,2}\s*日?', '', text)

    # 3. Weekdays: (週六), (周六), (星期六), 周一~周日, 週一~週日, Mon-Sun
    text = re.sub(r'[（(]?\s*(週|周|星期)[一二三四五六日七天]\s*[）)]?', '', text)
    text = re.sub(r'[（(]?\s*(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s*[）)]?', '', text, flags=re.IGNORECASE)

    # Clean up line spacing
    lines = []
    for line in text.split('\n'):
        line_clean = re.sub(r' +', ' ', line).strip()
        lines.append(line_clean)
    
    return '\n'.join(lines)
