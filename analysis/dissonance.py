"""Dissonance calculation and ranking"""
from typing import List, Optional, Tuple
from utils.music_theory import DISSONANCE_RANKING, get_key_name

class DissonanceCalculator:
    def __init__(self, max_voices: int = 4):
        self.max_voices = max_voices
        self.current_key = None
        self.key_confidence = 0.0
    
    def get_interval_from_root(self, root_note: int, note: int) -> int:
        """Calculate semitone interval from root note"""
        return (note - root_note) % 12
    
    def get_key_aware_dissonance_score(self, root_note: int, note: int, 
                                     context_notes: List[int], 
                                     current_key: Optional[Tuple] = None,
                                     key_confidence: float = 0.0,
                                     consonance_preference: int = 0) -> float:
        """Get dissonance score considering key context"""
        # Your existing dissonance scoring logic here
        pass
    
    def get_key_contextual_dissonance(self, note: int, key_root: int, 
                                    mode: str, interval_from_chord_root: int) -> float:
        """Calculate dissonance based on key context"""
        # Your existing key contextual logic here
        pass
