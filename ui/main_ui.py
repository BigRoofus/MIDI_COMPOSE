try:
    from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QLabel
    from PyQt6.QtCore import Qt
except ImportError:
    # Graceful degradation if PyQt6 not available
    class QMainWindow:
        def __init__(self): pass
    class QVBoxLayout:
        def __init__(self): pass
    class QWidget:
        def __init__(self): pass

from core.midi_data_model import MidiDocument
from config import AppSettings
from ui.piano_roll import PianoRollPanel

class MainWindow(QMainWindow):
    def __init__(self, document: MidiDocument, settings: AppSettings):
        super().__init__()
        self.document = document
        self.settings = settings
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("MIDI_COMPOSE")
        self.setGeometry(100, 100, 1200, 800)
        
        # Main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Transport controls
        transport_widget = self.create_transport()
        layout.addWidget(transport_widget)
        
        # Piano roll (main editing area)
        self.piano_roll_panel = PianoRollPanel(self.document, self.settings)
        layout.addWidget(self.piano_roll_panel, 1)  # Stretch factor 1
    
    def create_transport(self):
        """Create the transport control section"""
        transport = QWidget()
        transport.setMaximumHeight(50)
        layout = QHBoxLayout(transport)
        
        # Play controls
        self.play_btn = QPushButton("▶")
        self.play_btn.setToolTip("Play (Space)")
        
        self.stop_btn = QPushButton("⏹")
        self.stop_btn.setToolTip("Stop")
        
        self.rewind_btn = QPushButton("⏮")
        self.rewind_btn.setToolTip("Rewind to start")
        
        # BPM display
        bpm_label = QLabel("BPM:")
        self.bpm_display = QLabel(f"{self.document.tempo_bpm:.1f}")
        
        layout.addWidget(self.rewind_btn)
        layout.addWidget(self.play_btn)
        layout.addWidget(self.stop_btn)
        layout.addStretch()
        layout.addWidget(bpm_label)
        layout.addWidget(self.bpm_display)
        
        return transport