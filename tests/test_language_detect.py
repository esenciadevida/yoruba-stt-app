import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from common.language_detect import detect_language


class TestLanguageDetection:
    """Tests for Yoruba/English language detection."""

    def test_empty_input(self):
        assert detect_language("") == "en"
        assert detect_language(None) == "en"

    def test_yoruba_with_diacritics(self):
        """Text with Yoruba-specific characters should be detected as Yoruba."""
        assert detect_language("ẹ káàárọ̀") == "yo"
        assert detect_language("ọmọ") == "yo"
        assert detect_language("ilé") == "yo"

    def test_yoruba_high_confidence_words(self):
        """Unambiguous Yoruba words should be detected."""
        assert detect_language("lati") == "yo"
        assert detect_language("nitori") == "yo"
        assert detect_language("nigbati") == "yo"

    def test_english_text(self):
        assert detect_language("hello world") == "en"
        assert detect_language("good morning") == "en"
        assert detect_language("how are you") == "en"

    def test_mixed_language(self):
        """Mostly Yoruba with some English words."""
        assert detect_language("bawo ni my friend") == "yo"

    def test_short_text(self):
        """Very short text should default to English unless clearly Yoruba."""
        assert detect_language("a") == "en"
        assert detect_language("o") == "en"

    def test_yoruba_sentences(self):
        assert detect_language("mo wa") == "yo"
        assert detect_language("mo fe") == "yo"
        assert detect_language("o n lo") == "yo"

    def test_english_sentences(self):
        assert detect_language("I am going to the market") == "en"
        assert detect_language("The quick brown fox") == "en"

    def test_yoruba_with_numbers(self):
        assert detect_language("mo n lo 2 ojo") == "yo"

    def test_longer_common_short_phrases(self):
        """Common-short words must count in scoring for 4+ word phrases."""
        assert detect_language("E seun pupo fun iranlowo re") == "yo"
        assert detect_language("e seun pupo") == "yo"
        assert detect_language("e seun gan") == "yo"

    def test_english_with_ambiguous_words(self):
        """Words like 'won'/'e' must not flip English to Yoruba."""
        assert detect_language("she won the race yesterday") == "en"
        assert detect_language("we won") == "en"

    def test_standard_yoruba_phrases(self):
        assert detect_language("kini o n se loni") == "yo"
        assert detect_language("awon omo de n sere ni ita") == "yo"
        assert detect_language("mo nlo si oja lola") == "yo"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
