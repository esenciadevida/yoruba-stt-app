import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from common.code_switch import contains_mixed_language


class TestContainsMixedLanguage:
    """Tests for conservative Yoruba/English code-switch detection."""

    def test_pure_english_with_yoruba_mention(self):
        """An English sentence that mentions the Yoruba language must NOT be
        treated as code-switched (this caused garbled pseudo-Yoruba output)."""
        text = ("Test of a person who wants to use a tool that captures human "
                "voice to translate it into Yoruba and transcribe it into "
                "Yoruba from English.")
        assert contains_mixed_language(text) is False

    def test_pure_english_single_letter_words(self):
        """single 'a' / 'o' / 'e' letters must not flip English to mixed."""
        assert contains_mixed_language("I want to buy bread and a phone.") is False
        assert contains_mixed_language("A man and a woman went to the store.") is False

    def test_pure_english_plain(self):
        assert contains_mixed_language("The government lighted the streets.") is False
        assert contains_mixed_language("Good morning, how are you?") is False

    def test_genuine_code_switch(self):
        """Real Yoruba+English mixes must still be detected."""
        assert contains_mixed_language("Mo fẹ́ lọ sí ọjà láti ra ẹ̀fọ̀ àti bread.") is True
        assert contains_mixed_language("She is going to the market, mo fẹ́ lọ pẹ̀lú rẹ.") is True

    def test_plain_ascii_yoruba_with_english_borrowing(self):
        """Plain-ASCII Yoruba (no diacritics) with a real English loanword."""
        assert contains_mixed_language("awon omo de n sere ni street") is True

    def test_empty_and_short_input(self):
        assert contains_mixed_language("") is False
        assert contains_mixed_language("mo") is False


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])