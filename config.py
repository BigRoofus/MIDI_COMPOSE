from dataclasses import dataclass, field
from typing import Dict, Any, List
import json
import os

# Music Theory Constants
KEY_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
FLAT_NAMES = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']

# Key profiles for analysis (Krumhansl-Schmuckler)
MAJOR_KEY_PROFILE = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
MINOR_KEY_PROFILE = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]

# MIDI Constants
MIDDLE_C = 60
MIN_MIDI_NOTE = 0
MAX_MIDI_NOTE = 127

@dataclass
class AppSettings:
    # Audio settings
    sample_rate: float = 48000
    bit_depth: int = 24
    buffer_size: int = 512
    audio_device: str = "system"
    
    # MIDI settings
    default_velocity: int = 90
    default_tempo: int = 90
    quantize_strength: float = 1.0
    
    # Analysis settings
    key_confidence_threshold: float = 0.65
    max_voices: int = 4
    consonance_preference: float = 0  # -1.000 = max dissonance, 0 = neutral, 1.000 = max consonance

    # Color settings
    main_colors: List[str] = field(default_factory=lambda: ["#404040", "#606060", "#808080", "#A0A0A0", "#C0C0C0"])
    track_colors: List[str] = field(default_factory=lambda: ["#4A90E2", "#E94B3C", "#6AB04C", "#F79F1F"])
            
    @classmethod
    def load(cls, config_path: str = "config.json") -> 'AppSettings':
        """Load settings from file"""
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    data = json.load(f)
                return cls(**data)
            except Exception as e:
                print(f"Error loading settings: {e}")
        return cls()  # Return defaults
    
    def save(self, config_path: str = "config.json"):
        """Save settings to file"""
        try:
            with open(config_path, 'w') as f:
                json.dump(self.__dict__, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")