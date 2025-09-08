"""Music analysis and processing tools"""
from .key_analysis import KeyAnalyzer
from .harmony import HarmonicAnalyzer
from .dissonance import DissonanceCalculator
from .voice_reduction import VoiceReducer

__all__ = [
    'KeyAnalyzer', 'HarmonicAnalyzer', 
    'DissonanceCalculator', 'VoiceReducer'
]
