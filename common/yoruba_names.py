"""
Proper noun handling for code-switching.

The permanent solution: GPT handles all proper nouns via principled prompt
instructions. This module exists as an optional pre-processing hook, but
by default performs NO replacements — GPT's training knowledge covers:
- Places with Yoruba equivalents (Lagos→Ẹ̀kó, Ibadan→Ìbàdàn)
- Places without Yoruba names (Plateau, Ebonyi, Accra, London)
- Personal names (Pascal, Samuel — never translated)
- Brand names (Google, iPhone — never translated)
"""


def replace_known_names(text: str) -> str:
    """No-op placeholder. GPT handles proper nouns via prompt instructions."""
    return text
