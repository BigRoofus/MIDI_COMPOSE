"""
Get dissonance score considering key context and user preference.
Higher score = more dissonant (what we want to keep for dissonant preference).
"""

from .get_interval_from_root import get_interval_from_root
from .dissonance_ranking import DISSONANCE_RANKING
from .get_key_contextual_dissonance import get_key_contextual_dissonance

def get_key_aware_dissonance_score(root_note, note, context_notes, current_key=None, 
                                 key_confidence=0.0, consonance_preference=0):
    interval = get_interval_from_root(root_note, note)
    
    if current_key and key_confidence > 0.6:
        key_root, mode = current_key[:2]
        base_score = get_key_contextual_dissonance(note, key_root, mode, interval)
    else:
        if interval in DISSONANCE_RANKING:
            base_score = list(DISSONANCE_RANKING.keys()).index(interval)
        else:
            base_score = 12
    
    # Apply consonance preference adjustments
    if consonance_preference < 0:
        adjusted_score = 15 - base_score  # Prefer dissonant
    elif consonance_preference > 0:
        adjusted_score = base_score  # Prefer consonant
    else:
        adjusted_score = base_score  # Neutral
    
    return adjusted_score
