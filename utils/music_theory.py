"""Music theory constants and basic functions"""

# Key names for display
KEY_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# Dissonance ranking from most to least dissonant
DISSONANCE_RANKING = {
    6: 'Tritone',           # Most dissonant
    10: 'Minor Seventh',
    11: 'Major Seventh', 
    1: 'Minor Second',
    2: 'Major Second',
    8: 'Minor Sixth',
    9: 'Major Sixth',
    3: 'Minor Third',
    4: 'Major Third',
    5: 'Perfect Fourth',
    7: 'Perfect Fifth',
    12: 'Octave'            # Least dissonant
}

# Key profiles for major and minor keys (Krumhansl-Schmuckler)
MAJOR_KEY_PROFILE = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
MINOR_KEY_PROFILE = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]

def get_key_name(root: int, mode: str) -> str:
    """Convert key root and mode to readable name"""
    return f"{KEY_NAMES[root]} {mode}"
