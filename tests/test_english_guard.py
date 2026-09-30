import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from common.english_guard import restore_english_words


class TestEnglishGuard:
    """Tests for restoring English words marred by Yoruba tone marks."""

    def test_english_words_with_stray_tone_marks(self):
        assert restore_english_words("nose") == "nose"
        assert restore_english_words("n\u00f3se") == "nose"          # nóse
        assert restore_english_words("cl\u00edn\u00edc") == "clinic"  # clíníc
        assert restore_english_words("h\u1ecdspital") == "hospital"  # họspital
        assert restore_english_words("bl\u00f3od group") == "blood group"
        assert restore_english_words("w\u00e0ter") == "water"        # wàter

    def test_title_case_preserved(self):
        assert restore_english_words("N\u00f3se") == "Nose"

    def test_yoruba_text_unchanged(self):
        samples = [
            "\u1ecd\u0300m\u1ecd r\u1eb9\u0301",          # ọ̀mọ rẹ́
            "\u1eb9\u0300k\u1ecd\u0301",                   # ẹ̀kọ́
            "b\u00e1wo ni n\u00edt\u00f3r\u00ed \u00ecl\u00fa",
            "il\u00e9 i\u1e63\u1eb9\u0301 \u1ecd\u0300m\u1ecd",
            "\u1ecd\u0300b\u1eb9\u0300",                   # ọ̀bẹ̀
            "f\u1eb9\u0301s\u1eb9\u0300",
            "awon",                                        # raw ASR output, must stay
            "awon omo ti mo ri",                           # mixed plain text
        ]
        for s in samples:
            assert restore_english_words(s) == s

    def test_yoruba_awon_not_stripped(self):
        """'Àwọn' must never be stripped to 'awon'."""
        assert restore_english_words("\u00c0w\u1ecdn") == "\u00c0w\u1ecdn"

    def test_already_clean_text_unchanged(self):
        assert restore_english_words("The body tests ran well") == "The body tests ran well"

    def test_empty_input(self):
        assert restore_english_words("") == ""
        assert restore_english_words(None) == ""


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])