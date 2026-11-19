import re
from datetime import datetime

def convert_dates_in_text(text):
    if not text:
        return text

    def repl_ymd(m):
        yyyy, mm, dd = m.groups()
        return f"{yyyy}年{int(mm)}月{int(dd)}日"

    # Use (?<!\d) and (?!\d) instead of \b because Python regex treats Chinese characters as \w,
    # causing \b to fail when a date like 1/8/2027 is immediately adjacent to Chinese text.
    text = re.sub(r'(?<!\d)(\d{4})\s*[-/／]\s*(\d{1,2})\s*[-/／]\s*(\d{1,2})(?!\d)', repl_ymd, text)

    def repl_mdy(m):
        mm, dd, yyyy = m.groups()
        return f"{yyyy}年{int(mm)}月{int(dd)}日"

    text = re.sub(r'(?<!\d)(\d{1,2})\s*[/／]\s*(\d{1,2})\s*[/／]\s*(\d{4})(?!\d)', repl_mdy, text)

    return text

def _extract_date_from_line(line):
    # 1. YYYY年MM月DD日
    match = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", line)
    if match:
        y, m, d = match.groups()
        return f"{y}-{int(m):02d}-{int(d):02d}"

    # 2. MM/DD/YYYY or M/D/YYYY
    match = re.search(r"(?<!\d)(\d{1,2})[/／](\d{1,2})[/／](\d{4})(?!\d)", line)
    if match:
        m, d, y = match.groups()
        return f"{y}-{int(m):02d}-{int(d):02d}"

    # 3. YYYY-MM-DD or YYYY/MM/DD
    match = re.search(r"(?<!\d)(\d{4})[-/／](\d{1,2})[-/／](\d{1,2})(?!\d)", line)
    if match:
        y, m, d = match.groups()
        return f"{y}-{int(m):02d}-{int(d):02d}"

    # 4. MM月DD日 (Implicit Year)
    match = re.search(r"(\d{1,2})月(\d{1,2})日", line)
    if match:
        m, d = match.groups()
        current_year = datetime.now().year
        return f"{current_year}-{int(m):02d}-{int(d):02d}"

    return None

def extract_date_from_text(text):
    """
    Extracts date from text in various formats:
    1. YYYY-MM-DD
    2. MM/DD/YYYY (or M/D/YYYY)
    3. YYYY年MM月DD日
    4. MM月DD日 (Assumes current year)
    
    Prioritizes the first non-empty line (title line) before scanning body paragraphs.
    Returns date as 'YYYY-MM-DD' string or None if not found.
    """
    if not text:
        return None

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        res = _extract_date_from_line(line)
        if res:
            return res

    return _extract_date_from_line(text)


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


def strip_date_from_title(text):
    """
    Strips explicit calendar dates and weekday labels ONLY from the first non-empty line (title line) of the text.
    Leaves all subsequent lines/paragraphs intact so dates in prayer/scripture body are preserved.
    """
    if not text:
        return text

    lines = text.split('\n')
    for i, line in enumerate(lines):
        if line.strip():
            # Apply date stripping only to the first non-empty line
            lines[i] = strip_all_dates(line)
            break

    return '\n'.join(lines)

