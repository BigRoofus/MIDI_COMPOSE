"""Application settings and preferences"""
from dataclasses import dataclass
from typing import Dict, Any
import json
import os

@dataclass
class AppSettings:
    # Audio settings
    sample_rate: int = 44100
    buffer_size: int = 512
    audio_device: str = "default"
    
    # MIDI settings
    default_velocity: int = 64
    default_tempo: int = 120
    quantize_strength: float = 1.0
    
    # Analysis settings
    key_confidence_threshold: float = 0.65
    max_voices: int = 4
    consonance_preference: int = 0  # -1=dissonant, 0=neutral, 1=consonant
    
    # UI settings
    theme: str = "dark"
    piano_roll_height: int = 600
    track_colors: list = None
    
    def __post_init__(self):
        if self.track_colors is None:
            self.track_colors = ["#4A90E2", "#E94B3C", "#6AB04C", "#F79F1F"]
    
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
