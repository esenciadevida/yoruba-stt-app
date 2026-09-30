import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from common import nllb
from common.nllb import LANG_CODES, _looks_like_echo


class TestNllbModule:
    def test_lang_codes(self):
        assert LANG_CODES["en"] == "eng_Latn"
        assert LANG_CODES["yo"] == "yor_Latn"

    def test_is_available(self):
        """The NLLB checkpoint should exist in models/ (downloaded)."""
        assert nllb.is_available() is True

    def test_looks_like_echo(self):
        assert _looks_like_echo("Mo nlo si oja lola", "Mo nlo si oja lola") is True
        assert _looks_like_echo("mo fe lo si oja", "I want to go to the market") is False

    def test_echo_guard_ignores_short_outputs(self):
        assert _looks_like_echo("mo wa", "mo wa") is True
        assert _looks_like_echo("bawo ni o se wa", "How are you today?") is False


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
