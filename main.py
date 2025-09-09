# Global variables to track availability
QT_AVAILABLE = False
MIDO_AVAILABLE = False  
CORE_AVAILABLE = False#!/usr/bin/env python3
"""
MIDI Application Entry Point - MVP Version
"""
import sys
import os
import subprocess

# Force Python 3.13 if not already running it
def ensure_python_313():
    if sys.version_info[:2] != (3, 13):
        python313_path = r"C:\Users\Snows\AppData\Local\Programs\Python\Python313\python.exe"
        if os.path.exists(python313_path):
            print(f"Current Python: {sys.version}")
            print(f"Switching to Python 3.13...")
            # Re-run this script with Python 3.13
            subprocess.run([python313_path] + sys.argv)
            sys.exit(0)
        else:
            print(f"Warning: Python 3.13 not found at {python313_path}")
            print(f"Running with current Python {sys.version}")

# Check Python version at startup
ensure_python_313()

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, 
                                QWidget, QLabel, QPushButton, QFileDialog,
                                QHBoxLayout, QTextEdit, QMessageBox)
    from PyQt6.QtCore import Qt
    QT_AVAILABLE = True
except ImportError as e:
    print(f"PyQt6 not available: {e}")
    print("Install PyQt6 for full GUI: pip install PyQt6")
    QT_AVAILABLE = False

try:
    import mido
    MIDO_AVAILABLE = True
except ImportError as e:
    print(f"mido not available: {e}")
    print("Install mido for MIDI support: pip install mido")
    MIDO_AVAILABLE = False

from core.midi_data import MidiDocument
from config.settings import AppSettings

class SimpleMidiWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.document = MidiDocument()
        self.settings = AppSettings()
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("MIDI_COMPOSE - MVP")
        self.setGeometry(100, 100, 800, 600)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("🎼 MIDI_COMPOSE")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Status
        status_text = "✅ PyQt6 Ready" if QT_AVAILABLE else "❌ PyQt6 Missing"
        if MIDO_AVAILABLE:
            status_text += " | ✅ MIDI Support Ready"
        else:
            status_text += " | ❌ MIDI Support Missing (install mido)"
        
        status_label = QLabel(status_text)
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(status_label)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Load MIDI button
        load_btn = QPushButton("Load MIDI File")
        load_btn.clicked.connect(self.load_midi_file)
        load_btn.setEnabled(MIDO_AVAILABLE)
        button_layout.addWidget(load_btn)
        
        # New document button
        new_btn = QPushButton("New Document")
        new_btn.clicked.connect(self.new_document)
        button_layout.addWidget(new_btn)
        
        # Save button
        save_btn = QPushButton("Save MIDI")
        save_btn.clicked.connect(self.save_midi_file)
        save_btn.setEnabled(MIDO_AVAILABLE)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        
        # Info display
        self.info_display = QTextEdit()
        self.info_display.setReadOnly(True)
        self.info_display.setMaximumHeight(300)
        layout.addWidget(self.info_display)
        
        # Show initial info
        self.update_info_display()
    
    def new_document(self):
        self.document = MidiDocument()
        # Add a default track
        track = self.document.add_track()
        track.name = "Piano"
        self.update_info_display()
        QMessageBox.information(self, "New Document", "Created new MIDI document with 1 track")
    
    def load_midi_file(self):
        if not MIDO_AVAILABLE:
            QMessageBox.warning(self, "Error", "MIDI support not available. Install mido: pip install mido")
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load MIDI File", "", "MIDI Files (*.mid *.midi);;All Files (*)"
        )
        
        if file_path:
            try:
                self.document = MidiDocument.from_midi_file(file_path)
                self.update_info_display()
                QMessageBox.information(self, "Success", f"Loaded MIDI file: {os.path.basename(file_path)}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load MIDI file:\n{str(e)}")
    
    def save_midi_file(self):
        if not CORE_AVAILABLE or not MIDO_AVAILABLE:
            QMessageBox.warning(self, "Error", "MIDI support not available. Install mido: pip install mido")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save MIDI File", "untitled.mid", "MIDI Files (*.mid);;All Files (*)"
        )
        
        if file_path:
            try:
                success = self.document.to_midi_file(file_path)
                if success:
                    QMessageBox.information(self, "Success", f"Saved MIDI file: {os.path.basename(file_path)}")
                else:
                    QMessageBox.critical(self, "Error", "Failed to save MIDI file")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save MIDI file:\n{str(e)}")
    
    def update_info_display(self):
        info_text = f"""🐍 Python Environment:
• Python Version: {sys.version}
• Python Executable: {sys.executable}
• PyQt6 Available: {'Yes' if QT_AVAILABLE else 'No'}
• Mido Available: {'Yes' if MIDO_AVAILABLE else 'No'}
• Core Available: {'Yes' if CORE_AVAILABLE else 'No'}

📊 Document Information:
• Filename: {self.document.filename}
• Tracks: {len(self.document.tracks)}
• Tempo: {self.document.tempo_bpm} BPM
• Ticks per beat: {self.document.ticks_per_beat}
• Time signature: {self.document.time_signature[0]}/{self.document.time_signature[1]}
• Modified: {'Yes' if self.document.modified else 'No'}

"""
        
        if self.document.tracks:
            info_text += "🎵 Track Details:\n"
            for i, track in enumerate(self.document.tracks):
                note_count = len(track.notes)
                event_count = len(track.events)
                start_time, end_time = track.get_time_bounds()
                info_text += f"  Track {i+1}: {track.name}\n"
                info_text += f"    • Channel: {track.channel}\n"
                info_text += f"    • Notes: {note_count}\n"
                info_text += f"    • Events: {event_count}\n"
                info_text += f"    • Duration: {start_time}-{end_time} ticks\n\n"
        
        info_text += """🚀 Next Steps:
• Install dependencies: pip install PyQt6 mido
• Load a MIDI file to explore your music
• The core engine is ready for advanced features
• UI components (piano roll, etc.) coming soon!

💡 This is the MVP - Core functionality is working!
"""
        
        self.info_display.setText(info_text)

def main():
    if not QT_AVAILABLE:
        print("🎼 MIDI_COMPOSE - Console Mode")
        print("❌ PyQt6 not available. Install with: pip install PyQt6")
        
        # Basic console test
        print("Testing core components...")
        try:
            doc = MidiDocument()
            track = doc.add_track()
            print("✅ Core MIDI data structures working")
            
            settings = AppSettings()
            print("✅ Configuration system working")
            
            if MIDO_AVAILABLE:
                print("✅ MIDI file support available")
            else:
                print("❌ MIDI file support missing - install mido")
            
        except Exception as e:
            print(f"❌ Error testing components: {e}")
        
        return 0
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern look
    
    # Set application icon (shows in taskbar, alt-tab, etc.)
    icon_path = os.path.join(os.path.dirname(__file__), "favicon.ico")
    if os.path.exists(icon_path):
        from PyQt6.QtGui import QIcon
        app.setWindowIcon(QIcon(icon_path))
    
    window = SimpleMidiWindow()
    window.show()
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())