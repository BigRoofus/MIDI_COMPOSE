#!/usr/bin/env python3
"""
MIDI Application Entry Point
"""
import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
from core.midi_data import MidiDocument
from config.settings import AppSettings

def main():
    app = QApplication(sys.argv)
    
    # Initialize application settings
    settings = AppSettings()
    
    # Create main document
    document = MidiDocument()
    
    # Create and show main window
    main_window = MainWindow(document, settings)
    main_window.show()
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
