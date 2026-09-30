import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from common.nllb_quality import (
    assess_en_to_yo,
    has_combining_dot_corruption,
    normalize_combining,
    _greeting_mismatch,
)


class TestNormalizeCombining:
    def test_combining_forms_to_precomposed(self):
        assert normalize_combining("Jọ̀wọ́ wá.") == "Jọ̀wọ́ wá."
        assert normalize_combining("fẹ́") == "fẹ́"
        assert normalize_combining("Mo fẹ́ lọ") == "Mo fẹ́ lọ"

    def test_please_combining_passes(self):
        # NLLB's "Jọ̀wọ́ wá." normalizes to jọ̀wọ́, satisfying the please rule.
        good, reason = assess_en_to_yo("Please come here.", "Jọ̀wọ́ wá.")
        assert good is True, reason


class TestAssessEnToYo:
    def test_good_idiomatic_output_passes(self):
        good, reason = assess_en_to_yo(
            "I want to go to the market to buy yam.",
            "Mo fẹ́ lọ sí ọjà kí n lè ra yàmì.",
        )
        assert good is True, reason

    def test_combining_tone_marks_are_valid(self):
        # NLLB renders ẹ́/ọ́ as base + combining dot ("fẹ́"); must NOT be
        # treated as corruption or the good yam translation would escalate.
        good, reason = assess_en_to_yo(
            "I want to go to the market to buy yam.",
            "Mo fẹ́ lọ sí ọjà kí n lè ra yàmì.",
        )
        assert good is True, reason

    def test_mangled_greeting_fails(self):
        # "Àárọ̀, báwo..." does not contain a káàárọ form for good morning.
        good, reason = assess_en_to_yo(
            "Good morning, how are you doing today?",
            "Àárọ̀, báwo ló ṣe rí fún ẹ lónìí?",
        )
        assert good is False
        assert "greeting" in reason

    def test_plain_ascii_no_tone_marks_fails(self):
        good, reason = assess_en_to_yo(
            "Good morning, how are you doing today?",
            "E kaaro, bawo ni o se wa loni?",
        )
        assert good is False
        assert "tone" in reason

    def test_missing_greeting_form_fails(self):
        # "good night" must keep a dàárọ form, even when tone-marked.
        good, reason = assess_en_to_yo("Good night", "Ó dàbọ̀")
        assert good is False
        assert "greeting" in reason

    def test_correct_greeting_passes(self):
        good, reason = assess_en_to_yo(
            "Good morning, how are you doing today?",
            "Ẹ káàárọ̀, báwo ni o ṣe ń ṣe lónìí?",
        )
        assert good is True, reason

    def test_echo_fails(self):
        good, reason = assess_en_to_yo("I am going home", "I am going home")
        assert good is False
        assert "echo" in reason

    def test_empty_output_fails(self):
        good, reason = assess_en_to_yo("Hello there", "")
        assert good is False

    def test_short_tone_less_output_allowed(self):
        good, reason = assess_en_to_yo("Please", "Dákun.")
        assert good is True, reason

    def test_greeting_mismatch_rule_lookup(self):
        assert _greeting_mismatch("Good morning, sir", "Ẹ káàárọ̀") is False
        assert _greeting_mismatch("Good morning, sir", "Àárọ̀") is True

    def test_nllb_natural_alternatives_pass(self):
        # NLLB's "Mo dúpẹ́..." and "Alẹ́ tó dáa..." are valid, idiomatic ways
        # to express thanks / good night and must NOT escalate to GPT.
        good, _ = assess_en_to_yo(
            "Thank you very much for your help.",
            "Mo dúpẹ́ gan-an fún ìrànlọ́wọ́ yín.",
        )
        assert good is True
        good, _ = assess_en_to_yo(
            "Good night, see you tomorrow.",
            "Alẹ́ tó dáa, a máa rí yín lọ́jọ́ ọ̀la.",
        )
        assert good is True

    def test_english_transliteration_fails(self):
        """NLLB output that 'Yorubizes' English words must escalate to GPT."""
        good, reason = assess_en_to_yo(
            "Test of a person who wants to use a tool that captures human voice.",
            "Tẹ́st ojẹ́ ènìyàn kan búfẹ́ sí àlílò òhún mẹ́jìn tó gba ohùn ènìyàn.",
        )
        assert good is False
        assert "transliterat" in reason

    def test_mild_transliteration_single_token_allowed(self):
        """A single English-looking token must not be enough to condemn good
        Yoruba, to avoid false positives on real loanwords."""
        good, _ = assess_en_to_yo(
            "I want to buy a phone and bread.",
            "Mo fẹ́ ra phone àti búrẹ́dì.",
        )
        assert good is True

    def test_real_loanword_output_passes(self):
        good, reason = assess_en_to_yo(
            "The meeting is tomorrow at the office.",
            "Ìpàdé náà ni ọ̀la ní ọ́fíìsì.",
        )
        assert good is True, reason


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
