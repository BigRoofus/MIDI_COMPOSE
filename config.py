from dataclasses import dataclass, field
from typing import Dict, Any, List, Tuple

# Music Theory Constants
KEY_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
FLAT_NAMES = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']
MAJOR_KEY_PROFILE = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
MINOR_KEY_PROFILE = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]

# MIDI Constants
MIDDLE_C = 60
MIN_MIDI_NOTE = 0
MAX_MIDI_NOTE = 127

# UI Constants and Styling
@dataclass
class UIConstants:
    """Stores all static UI-related styling and text."""
    # Piano Roll Settings
    piano_roll_note_height: float = 20.0
    piano_roll_seconds_per_pixel: float = 0.1
    piano_roll_lowest_pitch: int = 12
    piano_roll_highest_pitch: int = 127
    piano_keyboard_width: int = 80
    
    # Control Panel Settings
    control_panel_max_height: int = 80
    velocity_slider_max_width: int = 100
    
    # Grid Colors (RGB tuples)
    grid_measure_color: Tuple[int, int, int] = (150, 150, 150)
    grid_beat_color: Tuple[int, int, int] = (200, 200, 200)
    grid_subdivision_color: Tuple[int, int, int] = (230, 230, 230)
    grid_octave_color: Tuple[int, int, int] = (180, 180, 180)
    grid_note_color: Tuple[int, int, int] = (240, 240, 240)
    
    # Piano Key Colors
    white_key_color: Tuple[int, int, int] = (255, 255, 255)
    white_key_alt_color: Tuple[int, int, int] = (248, 248, 248)
    white_key_border_color: Tuple[int, int, int] = (200, 200, 200)
    black_key_color: Tuple[int, int, int] = (30, 30, 30)
    black_key_border_color: Tuple[int, int, int] = (100, 100, 100)
    
    # Note Selection Colors
    selected_note_color: Tuple[int, int, int, int] = (255, 200, 100, 200)  # RGBA
    selected_note_border_color: Tuple[int, int, int] = (200, 150, 50)
    
    # Tool Button Icons and Labels
    tool_icons: Dict[str, str] = field(default_factory=lambda: {
        "pencil": "✏️",
        "select": "🔍", 
        "erase": "🗑️"
    })
    
    # Quantize Button Labels
    quantize_labels: Dict[str, str] = field(default_factory=lambda: {
        "16th": "⏱️ 1/16",
        "8th": "⏱️ 1/8",
        "quarter": "⏱️ 1/4"
    })
    
    # Control panel labels
    control_labels: Dict[str, str] = field(default_factory=lambda: {
        "track": "Track:",
        "tempo": "Tempo:",
        "key": "Key:",
        "tool": "Tool:",
        "quantize": "Quantize:",
        "velocity": "Velocity:"
    })
    
    # Default unknown values
    unknown_key_text: str = "Unknown"
    no_tracks_text: str = "No tracks"
    
    # CSS Styles
    bold_label_style: str = "font-weight: bold;"
    control_frame_style: str = "QFrame { background-color: #f0f0f0; border: 1px solid #ccc; }"

@dataclass
class PianoRollConfig:
    """Configuration specifically for piano roll UI elements"""
    
    # Widget dimensions and ranges
    keyboard_visible_range: Tuple[int, int] = (12, 127)
    scene_width_bars: int = 32  # Default scene width in bars
    
    # Tool configuration
    available_tools: List[str] = field(default_factory=lambda: ["pencil", "select", "erase"])
    default_tool: str = "pencil"
    
    # Quantize options (in beat divisions)
    quantize_options: Dict[str, float] = field(default_factory=lambda: {
        "16th": 4.0,  # 1/16th note = 1/4 of a beat
        "8th": 2.0,   # 1/8th note = 1/2 of a beat
        "quarter": 1.0 # 1/4 note = 1 beat
    })

@dataclass
class AppSettings:
    """Top-level configuration class for the application, including UI settings."""
    # Audio settings
    sample_rate: float = 48000
    bit_depth: int = 24
    buffer_size: int = 512
    audio_device: str = "system"
    
    # MIDI settings
    default_velocity: int = 90
    default_tempo: int = 90
    quantize_strength: float = 1.0
    
    # Analysis settings
    key_confidence_threshold: float = 0.65
    max_voices: int = 4
    consonance_preference: float = 0
    
    # Color settings
    main_colors: List[str] = field(default_factory=lambda: ["#404040", "#606060", "#808080", "#A0A0A0", "#C0C0C0"])
    track_colors: List[str] = field(default_factory=lambda: ["#4A90E2", "#E94B3C", "#6AB04C", "#F79F1F"])
    
    # UI Configuration
    ui_constants: UIConstants = field(default_factory=UIConstants)
    piano_roll_config: PianoRollConfig = field(default_factory=PianoRollConfig)