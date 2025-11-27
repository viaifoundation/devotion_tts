import re

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
