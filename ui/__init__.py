"""User interface components for MIDI_COMPOSE"""

# Import main UI components
try:
    from .main_window import MainWindow
    from .piano_roll import PianoRollWidget, PianoRollPanel, PianoRollTestWindow
    # transport.py doesn't have classes yet, so skip for now
    # from .transport import TransportWidget
    
    __all__ = [
        'MainWindow',
        'PianoRollWidget', 
        'PianoRollPanel',
        'PianoRollTestWindow'
    ]
    
except ImportError as e:
    # Graceful degradation if PyQt6 not available
    print(f"UI components not available: {e}")
    __all__ = []