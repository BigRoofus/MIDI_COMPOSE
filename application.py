import json
import os
from core.midi_data_model import MidiDocument
from config import AppSettings

class MidiApplication:
    """Central application controller"""
    
    def __init__(self):
        self.settings = self._load_settings()
        self.current_document = MidiDocument()
        
    def _load_settings(self, config_path: str = "config.json") -> AppSettings:
        """Load settings from file or return defaults"""
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    data = json.load(f)
                
                # Create settings with loaded data
                settings = AppSettings()
                for key, value in data.items():
                    if hasattr(settings, key):
                        setattr(settings, key, value)
                return settings
                
            except Exception as e:
                print(f"Error loading settings: {e}")
        
        return AppSettings()
    
    def save_settings(self, config_path: str = "config.json"):
        """Save current settings to file"""
        try:
            # Only save non-UI data
            data = {}
            for key, value in self.settings.__dict__.items():
                if not key.startswith('ui_') and not key.startswith('piano_roll_'):
                    data[key] = value
            
            with open(config_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def new_document(self):
        """Create new document"""
        self.current_document = MidiDocument()
    
    def load_document(self, filename: str):
        """Load MIDI file"""
        document = MidiDocument.from_midi_file(filename)
        if document:
            self.current_document = document
            return True
        return False
    
    def save_document(self, filename: str = None):
        """Save current document"""
        return self.current_document.to_midi_file(filename)