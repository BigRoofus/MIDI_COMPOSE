"""MIDI file import/export functionality"""

from typing import Optional
from .midi_data_model import MidiDocument

class MidiImporter:
    @staticmethod
    def load_file(filename: str) -> Optional[MidiDocument]:
        """Load MIDI file and return MidiDocument"""
        try:
            return MidiDocument.from_midi_file(filename)
        except Exception as e:
            print(f"Import error: {e}")
            return None

class MidiExporter:
    @staticmethod
    def save_file(document: MidiDocument, filename: str) -> bool:
        """Save MidiDocument to MIDI file"""
        return document.to_midi_file(filename)