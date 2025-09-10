#!/usr/bin/env python3
"""
MIDI Application Entry Point - Enhanced Version with Piano Roll
Updated to integrate piano roll widget and fix dependency checking
"""
import sys
import os
import subprocess

# Global variables to track availability
QT_AVAILABLE = False
PRETTY_MIDI_AVAILABLE = False  
CORE_AVAILABLE = False
UI_AVAILABLE = False

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

# Check PyQt6 availability
try:
    from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, 
                                QWidget, QLabel, QPushButton, QFileDialog,
                                QHBoxLayout, QTextEdit, QMessageBox, QSplitter,
                                QMenuBar, QStatusBar, QFrame, QTabWidget)
    from PyQt6.QtCore import Qt, QTimer
    from PyQt6.QtGui import QAction, QKeySequence, QIcon
    QT_AVAILABLE = True
    print("✅ PyQt6 successfully loaded")
except ImportError as e:
    print(f"❌ PyQt6 not available: {e}")
    print("Install PyQt6 for full GUI: pip install PyQt6")
    QT_AVAILABLE = False

# Check pretty_midi availability
try:
    import pretty_midi
    import numpy as np
    PRETTY_MIDI_AVAILABLE = True
    print("✅ pretty_midi successfully loaded")
except ImportError as e:
    print(f"❌ pretty_midi not available: {e}")
    print("Install pretty_midi for enhanced MIDI support: pip install pretty_midi")
    PRETTY_MIDI_AVAILABLE = False

# Check core modules
try:
    from core.midi_data import MidiDocument, MidiTrack, MidiNote
    from config.settings import AppSettings
    CORE_AVAILABLE = True
    print("✅ Core modules successfully loaded")
except ImportError as e:
    print(f"❌ Core modules not available: {e}")
    CORE_AVAILABLE = False

# Check UI modules
try:
    from ui.piano_roll import PianoRollPanel
    UI_AVAILABLE = True
    print("✅ UI modules successfully loaded")
except ImportError as e:
    print(f"❌ UI modules not available: {e}")
    UI_AVAILABLE = False

class EnhancedMidiWindow(QMainWindow):
    """Enhanced main window with integrated piano roll"""
    
    def __init__(self):
        super().__init__()
        self.document = MidiDocument() if CORE_AVAILABLE else None
        self.settings = AppSettings() if CORE_AVAILABLE else None
        self.piano_roll_panel = None
        
        # Initialize with some test data if no document loaded
        if self.document:
            self.create_default_track()
        
        self.init_ui()
        self.setup_menus()
        self.setup_status_bar()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.update_status)
        self.refresh_timer.start(1000)  # Update every second
    
    def create_default_track(self):
        """Create a default track if document is empty"""
        if not self.document.tracks:
            track = self.document.add_track()
            track.name = "Piano"
            track.program = 0  # Acoustic Grand Piano
            
            # Add a simple test chord
            chord_notes = [60, 64, 67]  # C major chord
            for i, pitch in enumerate(chord_notes):
                note = MidiNote(
                    start=0.0,
                    end=2.0,
                    pitch=pitch,
                    velocity=80
                )
                track.add_note(note)
    
    def init_ui(self):
        """Initialize the enhanced UI with piano roll integration"""
        self.setWindowTitle("🎼 MIDI_COMPOSE - Enhanced Piano Roll")
        self.setGeometry(50, 50, 1400, 900)
        
        # Central widget with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create tab widget for different views
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Piano Roll Tab
        if UI_AVAILABLE and CORE_AVAILABLE:
            try:
                self.piano_roll_panel = PianoRollPanel(self.document, self.settings)
                self.tab_widget.addTab(self.piano_roll_panel, "🎹 Piano Roll")
            except Exception as e:
                print(f"Error creating piano roll panel: {e}")
                self.add_error_tab(f"Piano Roll Error: {e}")
        else:
            self.add_error_tab("Piano Roll not available - missing dependencies")
        
        # Info Tab
        info_tab = self.create_info_tab()
        self.tab_widget.addTab(info_tab, "ℹ️ Info")
        
        # Set default tab
        if self.piano_roll_panel:
            self.tab_widget.setCurrentIndex(0)  # Piano roll
        else:
            self.tab_widget.setCurrentIndex(1)  # Info tab
    
    def add_error_tab(self, error_message: str):
        """Add an error tab when piano roll can't be created"""
        error_widget = QWidget()
        layout = QVBoxLayout(error_widget)
        
        error_label = QLabel(f"❌ {error_message}")
        error_label.setStyleSheet("color: red; font-size: 14px; padding: 20px;")
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(error_label)
        
        # Add install instructions
        instructions = QLabel("""
To fix this, install the missing dependencies:

pip install PyQt6 pretty_midi numpy

Then restart the application.
        """)
        instructions.setStyleSheet("font-family: monospace; padding: 20px;")
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(instructions)
        
        self.tab_widget.addTab(error_widget, "❌ Error")
    
    def create_info_tab(self) -> QWidget:
        """Create the info tab with system status"""
        info_widget = QWidget()
        layout = QVBoxLayout(info_widget)
        
        # Title
        title = QLabel("🎼 MIDI_COMPOSE - System Information")
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # System status
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        layout.addWidget(self.status_text)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        load_btn = QPushButton("📂 Load MIDI File")
        load_btn.clicked.connect(self.load_midi_file)
        load_btn.setEnabled(PRETTY_MIDI_AVAILABLE and CORE_AVAILABLE)
        button_layout.addWidget(load_btn)
        
        save_btn = QPushButton("💾 Save MIDI")
        save_btn.clicked.connect(self.save_midi_file)
        save_btn.setEnabled(PRETTY_MIDI_AVAILABLE and CORE_AVAILABLE)
        button_layout.addWidget(save_btn)
        
        new_btn = QPushButton("📄 New Document")
        new_btn.clicked.connect(self.new_document)
        new_btn.setEnabled(CORE_AVAILABLE)
        button_layout.addWidget(new_btn)
        
        analyze_btn = QPushButton("🔍 Analyze")
        analyze_btn.clicked.connect(self.analyze_document)
        analyze_btn.setEnabled(PRETTY_MIDI_AVAILABLE and CORE_AVAILABLE)
        button_layout.addWidget(analyze_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Update status initially
        self.update_status_display()
        
        return info_widget
    
    def setup_menus(self):
        """Setup enhanced menu bar"""
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu('File')
        
        new_action = QAction('New Document', self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self.new_document)
        new_action.setEnabled(CORE_AVAILABLE)
        file_menu.addAction(new_action)
        
        open_action = QAction('Open MIDI...', self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.load_midi_file)
        open_action.setEnabled(PRETTY_MIDI_AVAILABLE and CORE_AVAILABLE)
        file_menu.addAction(open_action)
        
        save_action = QAction('Save MIDI...', self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_midi_file)
        save_action.setEnabled(PRETTY_MIDI_AVAILABLE and CORE_AVAILABLE)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        quit_action = QAction('Quit', self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)
        
        # View Menu
        view_menu = menubar.addMenu('View')
        
        piano_roll_action = QAction('Piano Roll', self)
        piano_roll_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(0))
        piano_roll_action.setEnabled(self.piano_roll_panel is not None)
        view_menu.addAction(piano_roll_action)
        
        info_action = QAction('System Info', self)
        info_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(-1))  # Last tab
        view_menu.addAction(info_action)
        
        # Tools Menu
        tools_menu = menubar.addMenu('Tools')
        
        analyze_action = QAction('Analyze Music', self)
        analyze_action.triggered.connect(self.analyze_document)
        analyze_action.setEnabled(PRETTY_MIDI_AVAILABLE and CORE_AVAILABLE)
        tools_menu.addAction(analyze_action)
    
    def setup_status_bar(self):
        """Setup enhanced status bar"""
        status = self.statusBar()
        
        if not QT_AVAILABLE:
            status.showMessage("❌ PyQt6 missing")
        elif not PRETTY_MIDI_AVAILABLE:
            status.showMessage("❌ pretty_midi missing - install with: pip install pretty_midi")
        elif not CORE_AVAILABLE:
            status.showMessage("❌ Core modules error")
        elif not UI_AVAILABLE:
            status.showMessage("❌ UI modules error")
        else:
            status.showMessage("✅ All systems ready - MIDI_COMPOSE enhanced mode active")
    
    def new_document(self):
        """Create a new document"""
        if not CORE_AVAILABLE:
            QMessageBox.warning(self, "Error", "Core modules not available")
            return
        
        try:
            self.document = MidiDocument()
            self.create_default_track()
            
            # Update piano roll if available
            if self.piano_roll_panel:
                self.piano_roll_panel.document = self.document
                self.piano_roll_panel.piano_roll.document = self.document
                self.piano_roll_panel.update_track_combo()
                self.piano_roll_panel.piano_roll.document_changed()
                
                # Switch to piano roll tab
                self.tab_widget.setCurrentIndex(0)
            
            self.update_status_display()
            QMessageBox.information(self, "Success", "New document created with default piano track")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create new document:\n{str(e)}")
    
    def load_midi_file(self):
        """Load a MIDI file"""
        if not PRETTY_MIDI_AVAILABLE or not CORE_AVAILABLE:
            QMessageBox.warning(self, "Error", "MIDI support not available")
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load MIDI File", "", "MIDI Files (*.mid *.midi);;All Files (*)"
        )
        
        if file_path:
            try:
                self.document = MidiDocument.from_midi_file(file_path)
                
                # Update piano roll if available
                if self.piano_roll_panel:
                    self.piano_roll_panel.document = self.document
                    self.piano_roll_panel.piano_roll.document = self.document
                    self.piano_roll_panel.update_track_combo()
                    self.piano_roll_panel.piano_roll.document_changed()
                    
                    # Switch to piano roll tab
                    self.tab_widget.setCurrentIndex(0)
                
                self.update_status_display()
                QMessageBox.information(
                    self, "Success", 
                    f"Loaded: {os.path.basename(file_path)}\n"
                    f"Tracks: {len(self.document.tracks)}\n"
                    f"Duration: {self.document.get_time_bounds()[1]:.2f}s"
                )
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load MIDI file:\n{str(e)}")
    
    def save_midi_file(self):
        """Save the current document"""
        if not CORE_AVAILABLE or not PRETTY_MIDI_AVAILABLE:
            QMessageBox.warning(self, "Error", "MIDI support not available")
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
                    QMessageBox.information(self, "Success", f"Saved: {os.path.basename(file_path)}")
                    self.update_status_display()
                else:
                    QMessageBox.critical(self, "Error", "Failed to save MIDI file")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save MIDI file:\n{str(e)}")
    
    def analyze_document(self):
        """Analyze the current document"""
        if not self.document or not PRETTY_MIDI_AVAILABLE:
            QMessageBox.warning(self, "Error", "No document to analyze or pretty_midi not available")
            return
        
        try:
            # Comprehensive analysis
            key_root, key_mode = self.document.estimate_key()
            start_time, end_time = self.document.get_time_bounds()
            tempo = self.document.tempo_bpm
            total_notes = sum(len(track.notes) for track in self.document.tracks)
            
            analysis_text = f"""🎵 Musical Analysis Results

🎼 Basic Information:
• Key: {key_root} {key_mode}
• Tempo: {tempo:.1f} BPM
• Duration: {end_time:.2f} seconds ({end_time/60:.1f} minutes)
• Time Signature: {self.document.time_signature[0]}/{self.document.time_signature[1]}
• Total Notes: {total_notes:,}
• Tracks: {len(self.document.tracks)}

📊 Track Details:"""
            
            for i, track in enumerate(self.document.tracks):
                if len(track.notes) > 0:
                    pitches = [note.pitch for note in track.notes]
                    velocities = [note.velocity for note in track.notes]
                    
                    analysis_text += f"""
  🎹 Track {i+1}: {track.name}
    • Instrument: {track.program} ({'Drum Kit' if track.is_drum else 'Melodic'})
    • Notes: {len(track.notes):,}
    • Pitch range: {min(pitches)} - {max(pitches)} (span: {max(pitches) - min(pitches)} semitones)
    • Average pitch: {sum(pitches) / len(pitches):.1f}
    • Average velocity: {sum(velocities) / len(velocities):.0f}
    • Duration: {track.get_time_bounds()[0]:.2f}s - {track.get_time_bounds()[1]:.2f}s"""
            
            # Show in message box
            msg = QMessageBox(self)
            msg.setWindowTitle("🔍 Musical Analysis")
            msg.setText(analysis_text)
            msg.setDetailedText("Analysis performed using pretty_midi engine")
            msg.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Analysis Error", f"Failed to analyze document:\n{str(e)}")
    
    def update_status(self):
        """Update status periodically"""
        if hasattr(self, 'status_text'):
            self.update_status_display()
    
    def update_status_display(self):
        """Update the status text display"""
        status_info = f"""🐍 System Status:
• Python Version: {sys.version.split()[0]}
• Python Path: {sys.executable}

📦 Dependencies:
• PyQt6: {'✅ Available' if QT_AVAILABLE else '❌ Missing (pip install PyQt6)'}
• pretty_midi: {'✅ Available' if PRETTY_MIDI_AVAILABLE else '❌ Missing (pip install pretty_midi)'}
• NumPy: {'✅ Available' if PRETTY_MIDI_AVAILABLE else '❌ Missing (pip install numpy)'}
• Core Modules: {'✅ Available' if CORE_AVAILABLE else '❌ Error'}
• UI Modules: {'✅ Available' if UI_AVAILABLE else '❌ Error'}

🎼 Document Status:"""
        
        if self.document and CORE_AVAILABLE:
            start_time, end_time = self.document.get_time_bounds()
            total_notes = sum(len(track.notes) for track in self.document.tracks)
            
            status_info += f"""
• File: {self.document.filename}
• Modified: {'Yes' if self.document.modified else 'No'}
• Tracks: {len(self.document.tracks)}
• Total Notes: {total_notes:,}
• Duration: {end_time:.2f}s
• Tempo: {self.document.tempo_bpm:.1f} BPM
• Time Signature: {self.document.time_signature[0]}/{self.document.time_signature[1]}

🎹 Track Summary:"""
            
            for i, track in enumerate(self.document.tracks):
                note_count = len(track.notes)
                track_start, track_end = track.get_time_bounds()
                status_info += f"""
  Track {i+1}: {track.name}
    • Program: {track.program} ({'Drums' if track.is_drum else 'Instrument'})
    • Notes: {note_count:,}
    • Duration: {track_start:.2f}s - {track_end:.2f}s"""
        else:
            status_info += """
• No document loaded or core modules unavailable"""
        
        status_info += f"""

🚀 Features Available:
• Piano Roll Editor: {'✅ Ready' if self.piano_roll_panel else '❌ Not Available'}
• MIDI Import/Export: {'✅ Ready' if PRETTY_MIDI_AVAILABLE and CORE_AVAILABLE else '❌ Not Available'}
• Musical Analysis: {'✅ Ready' if PRETTY_MIDI_AVAILABLE and CORE_AVAILABLE else '❌ Not Available'}
• Real-time Editing: {'✅ Ready' if UI_AVAILABLE and CORE_AVAILABLE else '❌ Not Available'}

💡 Usage Tips:
• Use the Piano Roll tab for note editing
• Load MIDI files to explore existing compositions
• The analysis tool provides key and tempo detection
• All editing is done in real-time with immediate feedback"""
        
        if hasattr(self, 'status_text'):
            self.status_text.setPlainText(status_info)

def main():
    """Enhanced main function with better error handling"""
    print("🎼 MIDI_COMPOSE - Enhanced Piano Roll Version")
    print("=" * 50)
    
    # Check if we have minimal requirements for GUI
    if not QT_AVAILABLE:
        print("❌ PyQt6 not available - running in console mode")
        print("To get the full GUI experience:")
        print("  pip install PyQt6 pretty_midi numpy")
        print("")
        
        # Minimal console test
        if CORE_AVAILABLE:
            print("Testing core functionality...")
            doc = MidiDocument()
            track = doc.add_track()
            print("✅ Basic MIDI functionality working")
        else:
            print("❌ Core MIDI functionality not working")
        
        return 0
    
    # Create QApplication
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern cross-platform style
    
    # Set application properties
    app.setApplicationName("MIDI_COMPOSE")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("MIDI_COMPOSE")
    
    # Try to set application icon
    icon_path = os.path.join(os.path.dirname(__file__), "favicon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Create and show main window
    try:
        window = EnhancedMidiWindow()
        window.show()
        
        print("✅ GUI application started successfully")
        print("Features available:")
        print(f"  • Piano Roll: {'Yes' if UI_AVAILABLE else 'No'}")
        print(f"  • MIDI I/O: {'Yes' if PRETTY_MIDI_AVAILABLE else 'No'}")
        print(f"  • Analysis: {'Yes' if PRETTY_MIDI_AVAILABLE and CORE_AVAILABLE else 'No'}")
        print("")
        
        return app.exec()
        
    except Exception as e:
        print(f"❌ Failed to start GUI application: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())