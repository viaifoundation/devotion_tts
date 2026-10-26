import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from text_cleaner import fix_pronunciation, restore_pronunciation_for_display, clean_text_for_tts

class TextCleanerTests(unittest.TestCase):
    def test_mupalm_pronunciation_fix(self):
        # Traditional Chinese
        text_trad = "賜給「鄉音」無論是牧長、所有同工們"
        tts_trad = fix_pronunciation(text_trad)
        self.assertIn("牧掌", tts_trad)
        self.assertNotIn("牧長", tts_trad)
        restored_trad = restore_pronunciation_for_display(tts_trad)
        self.assertIn("牧長", restored_trad)

        # Simplified Chinese
        text_simp = "无论是牧长、所有同工们"
        tts_simp = fix_pronunciation(text_simp)
        self.assertIn("牧掌", tts_simp)
        self.assertNotIn("牧长", tts_simp)
        restored_simp = restore_pronunciation_for_display(tts_simp)
        self.assertIn("牧长", restored_simp)

    def test_other_biblical_pronunciation_fixes(self):
        text = "使徒行傳記載，神對撒母耳說話，俄巴底亞也領受異象。"
        tts = fix_pronunciation(text)
        self.assertIn("使徒行賺", tts)
        self.assertIn("薩母耳", tts)
        self.assertIn("額巴底亞", tts)
        restored = restore_pronunciation_for_display(tts)
        self.assertIn("使徒行傳", restored)
        self.assertIn("撒母耳", restored)
        self.assertIn("俄巴底亞", restored)

if __name__ == '__main__':
    unittest.main()
