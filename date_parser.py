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

    def repl_md(m):
        mm, dd = m.groups()
        yyyy = datetime.now().year
        return f"{yyyy}年{int(mm)}月{int(dd)}日"

    text = re.sub(r'\b(\d{1,2})/(\d{1,2})\b(?!\d)', repl_md, text)

    def repl_yyyymmdd(m):
        yyyy, mm, dd = m.groups()
        try:
            datetime(int(yyyy), int(mm), int(dd))
            return f"{yyyy}年{int(mm)}月{int(dd)}日"
        except ValueError:
            return m.group(0)

    text = re.sub(r'\b(\d{4})(\d{2})(\d{2})\b', repl_yyyymmdd, text)

    def repl_mmddyyyy(m):
        mm, dd, yyyy = m.groups()
        try:
            datetime(int(yyyy), int(mm), int(dd))
            return f"{yyyy}年{int(mm)}月{int(dd)}日"
        except ValueError:
            return m.group(0)
            
    text = re.sub(r'\b(\d{2})(\d{2})(\d{4})\b', repl_mmddyyyy, text)

    return text
