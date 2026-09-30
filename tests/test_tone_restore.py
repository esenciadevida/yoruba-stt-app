import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from common.tone_restore import restore_tones, TONE_MAP


class TestToneRestore:
    """Tests for Yoruba tone restoration."""

    def test_empty_input(self):
        assert restore_tones("") == ""
        assert restore_tones(None) == ""

    def test_single_greeting(self):
        result = restore_tones("bawo ni")
        assert "báwo" in result

    def test_multiple_greetings(self):
        result = restore_tones("e kaaro e se jowo")
        assert "ẹ" in result
        assert "káàárọ̀" in result

    def test_case_insensitive(self):
        result = restore_tones("BAWO NI")
        assert "báwo" in result

    def test_verb_tones(self):
        result = restore_tones("je mu lo wa ri")
        assert "jẹ" in result
        assert "mú" in result
        assert "lọ" in result

    def test_family_words(self):
        result = restore_tones("iya baba omo ore")
        assert "ìyá" in result
        assert "bàbá" in result
        assert "ọmọ" in result

    def test_food_words(self):
        result = restore_tones("ounje omi amala")
        assert "oúnjẹ" in result
        assert "àmàlà" in result

    def test_longest_match_first(self):
        """Ensure longer phrases are matched before shorter ones."""
        result = restore_tones("mo wa daadaa")
        assert "dáadáa" in result

    def test_partial_match_no_replacement(self):
        """Words not in the map should remain unchanged."""
        result = restore_tones("xyz123")
        assert "xyz123" in result

    def test_mixed_text(self):
        """Text with some mapped and some unmapped words."""
        result = restore_tones("bawo ni friend")
        assert "báwo" in result
        assert "friend" in result

    def test_map_size(self):
        """Verify the tone map has been expanded significantly."""
        assert len(TONE_MAP) >= 200

    def test_pronoun_tones(self):
        result = restore_tones("emi iwọ awa")
        assert "èmi" in result
        assert "ìwọ" in result

    def test_question_words(self):
        result = restore_tones("kini nibo")
        assert "kí ni" in result
        assert "níbo" in result

    def test_religion_words(self):
        result = restore_tones("olorun oluwa yoruba")
        assert "olórun" in result
        assert "olúwa" in result
        assert "yorùbá" in result

    def test_animal_words(self):
        result = restore_tones("aja ologbo adiye")
        assert "ajá" in result
        assert "ológbò" in result

    def test_time_words(self):
        result = restore_tones("oni ola bayii")
        assert "òní" in result
        assert "ọ̀la" in result

    def test_awon_pronoun_tones(self):
        """The user's core case: 'awon' must become 'àwọn'."""
        result = restore_tones("awon omo")
        assert "àwọn" in result

    def test_awon_with_capital_in_map(self):
        result = restore_tones("Awon ti mo ri")
        assert "àwọn" in result

    def test_common_verb_phrases(self):
        result = restore_tones("mo ri gbogbo")
        assert "mọ̀ rí" in result

    def test_lati_preposition(self):
        result = restore_tones("lati ibe")
        assert "láti" in result


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
