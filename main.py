#!/usr/bin/env python3
"""
MIDI Application Entry Point
"""
import sys
try:
    from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel
    QT_AVAILABLE = True
except ImportError:
    print("PyQt6 not available. Running in console mode.")
    QT_AVAILABLE = False

from core.midi_data import MidiDocument
from config.settings import AppSettings

def main():
    if not QT_AVAILABLE:
        print("🎼 MIDI_COMPOSE - Console Mode")
        print("Install PyQt6 for full GUI: pip install PyQt6")
        return 0
    
    app = QApplication(sys.argv)
    
    # Initialize application settings
    settings = AppSettings()
    
    # Create main document
    document = MidiDocument()
    
    # Temporary simple window until UI is implemented
    window = QMainWindow()
    window.setWindowTitle("MIDI_COMPOSE")
    window.setCentralWidget(QLabel("MIDI_COMPOSE - UI Coming Soon"))
    window.show()
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())