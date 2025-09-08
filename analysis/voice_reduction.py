"""Voice reduction and harmonic complexity management"""
from typing import List
from .dissonance import DissonanceCalculator
from .key_analysis import KeyAnalyzer

class VoiceReducer:
    def __init__(self, max_voices: int = 4):
        self.max_voices = max_voices
        self.dissonance_calc = DissonanceCalculator(max_voices)
        self.key_analyzer = KeyAnalyzer()
    
    def select_notes_by_dissonance(self, notes: List[int]) -> List[int]:
        """Select notes based on dissonance rules with key awareness"""
        # Your existing note selection logic here
        pass
