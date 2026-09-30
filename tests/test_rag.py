import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from common import translation
from common import translation_rag


class TestRagIndex:
    def test_is_available(self):
        """The prebuilt RAG index should exist under models/rag/."""
        assert translation_rag.is_available() is True

    def test_retrieval_returns_pairs(self):
        examples = translation_rag.get_few_shot_examples(
            "I want to go to the market to buy yam.", "en2yo", k=3
        )
        assert 0 < len(examples) <= 3
        for src, tgt in examples:
            assert isinstance(src, str) and src
            assert isinstance(tgt, str) and tgt

    def test_retrieval_yoruba_side(self):
        examples = translation_rag.get_few_shot_examples(
            "Mo fẹ́ lọ sí ọjà láti ra yàmì.", "yo2en", k=3
        )
        assert 0 < len(examples) <= 3
        for src, tgt in examples:
            assert src and tgt

    def test_empty_text_returns_nothing(self):
        assert translation_rag.get_few_shot_examples("", "en2yo") == []
        assert translation_rag.get_few_shot_examples("   ", "yo2en") == []


class TestFewShotPrompt:
    def test_en2yo_injects_examples(self, monkeypatch):
        def fake_get(text, direction, k):
            assert direction == "en2yo"
            return [("I want to go to the market.", "Mo fẹ́ lọ sí ọjà.")]
        monkeypatch.setattr(translation_rag, "get_few_shot_examples", fake_get)
        msg = translation._with_few_shot("I want to go to the market.", "en", "Translate:")
        assert "reference translations" in msg
        assert "Mo fẹ́ lọ sí ọjà." in msg

    def test_yoruba_source_uses_yo2en(self, monkeypatch):
        captured = {}
        def fake_get(text, direction, k):
            captured["direction"] = direction
            return [("Mo fẹ́ lọ sí ọjà.", "I want to go to the market.")]
        monkeypatch.setattr(translation_rag, "get_few_shot_examples", fake_get)
        translation._with_few_shot("Mo fẹ́ lọ sí ọjà.", "yo", "Translate:")
        assert captured["direction"] == "yo2en"

    def test_no_examples_returns_original(self, monkeypatch):
        monkeypatch.setattr(translation_rag, "get_few_shot_examples", lambda *a, **k: [])
        msg = translation._with_few_shot("hello", "en", "Translate: hello")
        assert msg == "Translate: hello"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
