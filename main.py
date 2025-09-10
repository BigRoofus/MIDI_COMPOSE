#!/usr/bin/env python3
"""
MIDI Application Entry Point - pretty_midi Version
Updated for pretty_midi migration
"""
import sys
import os
import subprocess

# Global variables to track availability
QT_AVAILABLE = False
PRETTY_MIDI_AVAILABLE = False  
CORE_AVAILABLE = False

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
    import pretty_midi
    import numpy as np
    PRETTY_MIDI_AVAILABLE = True
except ImportError as e:
    print(f"pretty_midi not available: {e}")
    print("Install pretty_midi for enhanced MIDI support: pip install pretty_midi")
    PRETTY_MIDI_AVAILABLE = False

try:
    from core.midi_data import MidiDocument
    from config.settings import AppSettings
    CORE_AVAILABLE = True
except ImportError as e:
    print(f"Core modules not available: {e}")
    CORE_AVAILABLE = False

class SimpleMidiWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.document = MidiDocument() if CORE_AVAILABLE else None
        self.settings = AppSettings() if CORE_AVAILABLE else None
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("MIDI_COMPOSE - pretty_midi Version")
        self.setGeometry(100, 100, 900, 700)
        
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
        
        if PRETTY_MIDI_AVAILABLE:
            status_text += " | ✅ pretty_midi Ready"
        else:
            status_text += " | ❌ pretty_midi Missing (pip install pretty_midi)"
        
        if CORE_AVAILABLE:
            status_text += " | ✅ Core Systems Ready"
        else:
            status_text += " | ❌ Core Systems Error"
        
        status_label = QLabel(status_text)
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(status_label)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Load MIDI button
        load_btn = QPushButton("Load MIDI File")
        load_btn.clicked.connect(self.load_midi_file)
        load_btn.setEnabled(PRETTY_MIDI_AVAILABLE and CORE_AVAILABLE)
        button_layout.addWidget(load_btn)
        
        # New document button
        new_btn = QPushButton("New Document")
        new_btn.clicked.connect(self.new_document)
        new_btn.setEnabled(CORE_AVAILABLE)
        button_layout.addWidget(new_btn)
        
        # Save button
        save_btn = QPushButton("Save MIDI")
        save_btn.clicked.connect(self.save_midi_file)
        save_btn.setEnabled(PRETTY_MIDI_AVAILABLE and CORE_AVAILABLE)
        button_layout.addWidget(save_btn)
        
        # Analysis button (new feature!)
        analyze_btn = QPushButton("🎵 Analyze Music")
        analyze_btn.clicked.connect(self.analyze_document)
        analyze_btn.setEnabled(PRETTY_MIDI_AVAILABLE and CORE_AVAILABLE)
        button_layout.addWidget(analyze_btn)
        
        layout.addLayout(button_layout)
        
        # Info display
        self.info_display = QTextEdit()
        self.info_display.setReadOnly(True)
        self.info_display.setMaximumHeight(400)
        layout.addWidget(self.info_display)
        
        # Show initial info
        self.update_info_display()
    
    def new_document(self):
        if not CORE_AVAILABLE:
            return
            
        self.document = MidiDocument()
        # Add a default track
        track = self.document.add_track()
        track.name = "Piano"
        self.update_info_display()
        QMessageBox.information(self, "New Document", "Created new MIDI document with 1 track")
    
    def load_midi_file(self):
        if not PRETTY_MIDI_AVAILABLE or not CORE_AVAILABLE:
            QMessageBox.warning(self, "Error", "MIDI support not available. Install pretty_midi: pip install pretty_midi")
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
        if not CORE_AVAILABLE or not PRETTY_MIDI_AVAILABLE:
            QMessageBox.warning(self, "Error", "MIDI support not available. Install pretty_midi: pip install pretty_midi")
            return
        
        if not self.document:
            QMessageBox.warning(self, "Error", "No document to save")
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
    
    def analyze_document(self):
        """New analysis feature using pretty_midi capabilities"""
        if not self.document or not PRETTY_MIDI_AVAILABLE:
            return
        
        try:
            # Estimate key
            key_root, key_mode = self.document.estimate_key()
            
            # Get time bounds
            start_time, end_time = self.document.get_time_bounds()
            
            # Get tempo
            tempo = self.document.tempo_bpm
            
            # Count total notes
            total_notes = sum(len(track.notes) for track in self.document.tracks)
            
            # Analysis results
            analysis_text = f"""🎵 Musical Analysis Results:

Key: {key_root} {key_mode}
Tempo: {tempo:.1f} BPM  
Duration: {end_time:.2f} seconds
Total Notes: {total_notes}
Tracks: {len(self.document.tracks)}

"""
            
            if self.document.tracks:
                analysis_text += "📊 Track Analysis:\n"
                for i, track in enumerate(self.document.tracks):
                    note_count = len(track.notes)
                    if note_count > 0:
                        pitches = [note.pitch for note in track.notes]
                        avg_pitch = sum(pitches) / len(pitches)
                        pitch_range = max(pitches) - min(pitches)
                        analysis_text += f"  • {track.name}: {note_count} notes, avg pitch: {avg_pitch:.1f}, range: {pitch_range} semitones\n"
            
            # Show analysis in a popup
            msg = QMessageBox(self)
            msg.setWindowTitle("Musical Analysis")
            msg.setText(analysis_text)
            msg.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Analysis Error", f"Failed to analyze document:\n{str(e)}")
    
    def update_info_display(self):
        info_text = f"""🐍 Python Environment:
• Python Version: {sys.version}
• Python Executable: {sys.executable}
• PyQt6 Available: {'Yes' if QT_AVAILABLE else 'No'}
• pretty_midi Available: {'Yes' if PRETTY_MIDI_AVAILABLE else 'No'}
• Core Available: {'Yes' if CORE_AVAILABLE else 'No'}

"""
        
        if self.document and CORE_AVAILABLE:
            info_text += f"""📊 Document Information:
• Filename: {self.document.filename}
• Tracks: {len(self.document.tracks)}
• Tempo: {self.document.tempo_bpm:.1f} BPM
• Time Signature: {self.document.time_signature[0]}/{self.document.time_signature[1]}
• Modified: {'Yes' if self.document.modified else 'No'}

"""
            
            if self.document.tracks:
                info_text += "🎵 Track Details:\n"
                for i, track in enumerate(self.document.tracks):
                    note_count = len(track.notes)
                    event_count = len(track.events)
                    start_time, end_time = track.get_time_bounds()
                    info_text += f"  Track {i+1}: {track.name}\n"
                    info_text += f"    • Program: {track.program} ({'Drum Kit' if track.is_drum else 'Instrument'})\n"
                    info_text += f"    • Notes: {note_count}\n"
                    info_text += f"    • Events: {event_count}\n"
                    info_text += f"    • Duration: {start_time:.2f}s - {end_time:.2f}s\n\n"
        
        info_text += """🚀 Next Steps:
• Install dependencies: pip install PyQt6 pretty_midi numpy
• Load a MIDI file to explore enhanced music analysis
• Try the new "Analyze Music" button for key detection!
• The enhanced pretty_midi engine provides advanced features
• UI components (piano roll, etc.) ready for enhanced analysis

💡 This is the enhanced pretty_midi version - More powerful than ever!
"""
        
        if hasattr(self, 'info_display'):
            self.info_display.setText(info_text)

def main():
    if not QT_AVAILABLE:
        print("🎼 MIDI_COMPOSE - Console Mode")
        print("❌ PyQt6 not available. Install with: pip install PyQt6")
        
        # Basic console test
        print("Testing core components...")
        try:
            if CORE_AVAILABLE:
                doc = MidiDocument()
                track = doc.add_track()
                print("✅ Core MIDI data structures working")
                
                settings = AppSettings()
                print("✅ Configuration system working")
            else:
                print("❌ Core modules not available")
            
            if PRETTY_MIDI_AVAILABLE:
                print("✅ Enhanced pretty_midi support available")
                
                # Test pretty_midi directly
                pm = pretty_midi.PrettyMIDI()
                print("✅ pretty_midi initialization working")
            else:
                print("❌ pretty_midi support missing")
            
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