import sys
import os

# Add parent directory to path for shared module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from common.tone_restore import restore_tones as _restore_tones, TONE_MAP as tone_map, SORTED_KEYS

# Backward compatibility: keep the old function name
def add_yoruba_tones(text):
    return _restore_tones(text)