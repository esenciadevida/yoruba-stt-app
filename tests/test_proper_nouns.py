import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from common.proper_nouns import contains_proper_nouns


class TestProperNouns:
    """Tests for proper-noun detection that routes en->yo to GPT."""

    def test_known_names(self):
        assert contains_proper_nouns("we are at Bioclinix clinic") is True
        assert contains_proper_nouns("in Lagos State") is True
        assert contains_proper_nouns("she works at Google") is True

    def test_camel_case(self):
        assert contains_proper_nouns("BioClinix is in Lagos") is True
        assert contains_proper_nouns("my iPhone is new") is True

    def test_plain_english(self):
        assert contains_proper_nouns("the test started from the nose") is False
        assert contains_proper_nouns("I went to the market yesterday") is False
        assert contains_proper_nouns("good morning everyone") is False
        assert contains_proper_nouns("the market opens early every day") is False

    def test_known_place_still_routed_to_gpt(self):
        # Sentence-initial proper nouns are routed to GPT too (best quality).
        assert contains_proper_nouns("Lagos is a big city") is True

    def test_empty_input(self):
        assert contains_proper_nouns("") is False
        assert contains_proper_nouns(None) is False


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])