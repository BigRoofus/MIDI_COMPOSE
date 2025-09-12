from dataclasses import dataclass, field
from typing import Dict, Any, List, Tuple
import json
import os

# Music Theory Constants
KEY_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
FLAT_NAMES = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']

# Key profiles for analysis (Krumhansl-Schmuckler)
MAJOR_KEY_PROFILE = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
MINOR_KEY_PROFILE = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]

# MIDI Constants
MIDDLE_C = 60
MIN_MIDI_NOTE = 0
MAX_MIDI_NOTE = 127

# UI Constants and Styling
@dataclass
class UIConstants:
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
    
    # Tool Button Icons
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
    
    # CSS Styles
    bold_label_style: str = "font-weight: bold;"
    control_frame_style: str = "QFrame { background-color: #f0f0f0; border: 1px solid #ccc; }"

@dataclass
class PianoRollConfig:
    """Configuration specifically for piano roll UI elements"""
    
    # Widget dimensions and ranges
    keyboard_visible_range: Tuple[int, int] = (12, 127)
    scene_width_bars: int = 32  # Default scene width in bars
    
    # Control panel layout
    control_labels: Dict[str, str] = field(default_factory=lambda: {
        "track": "Track:",
        "tempo": "Tempo:",
        "key": "Key:",
        "tool": "Tool:",
        "quantize": "Quantize:",
        "velocity": "Velocity:"
    })
    
    # Tool configuration
    available_tools: List[str] = field(default_factory=lambda: ["pencil", "select", "erase"])
    default_tool: str = "pencil"
    
    # Quantize options (in beat divisions)
    quantize_options: Dict[str, float] = field(default_factory=lambda: {
        "16th": 4.0,  # 1/16th note = 1/4 of a beat
        "8th": 2.0,   # 1/8th note = 1/2 of a beat
        "quarter": 1.0 # 1/4 note = 1 beat
    })
    
    # Default unknown values
    unknown_key_text: str = "Unknown"
    no_tracks_text: str = "No tracks"

@dataclass
class UILayout:
    """UI Layout helper methods and configurations"""
    
    # Spacing and margins
    default_spacing: int = 6
    default_margin: int = 9
    control_spacing: int = 3
    
    # Widget proportions
    main_area_piano_roll_stretch: int = 1  # Piano roll takes remaining space
    
    @staticmethod
    def create_button_config(text: str, checkable: bool = False, checked: bool = False, 
                           tooltip: str = None) -> Dict[str, Any]:
        """Helper to create button configuration"""
        config = {
            "text": text,
            "checkable": checkable,
            "checked": checked
        }
        if tooltip:
            config["tooltip"] = tooltip
        return config
    
    @staticmethod 
    def get_tool_button_configs(ui_constants: UIConstants) -> Dict[str, Dict[str, Any]]:
        """Get configuration for all tool buttons"""
        return {
            "pencil": UILayout.create_button_config(
                f"{ui_constants.tool_icons['pencil']} Pencil", 
                checkable=True, checked=True,
                tooltip="Add notes by clicking (P)"
            ),
            "select": UILayout.create_button_config(
                f"{ui_constants.tool_icons['select']} Select",
                checkable=True, checked=False,
                tooltip="Select and move notes (S)"  
            ),
            "erase": UILayout.create_button_config(
                f"{ui_constants.tool_icons['erase']} Erase",
                checkable=True, checked=False,
                tooltip="Remove notes by clicking (E)"
            )
        }
    
    @staticmethod
    def get_quantize_button_configs(ui_constants: UIConstants, 
                                  piano_roll_config: PianoRollConfig) -> Dict[str, Dict[str, Any]]:
        """Get configuration for quantize buttons"""
        configs = {}
        for key, label in ui_constants.quantize_labels.items():
            division = piano_roll_config.quantize_options.get(key, 4.0)
            configs[key] = {
                "text": label,
                "division": division,
                "tooltip": f"Quantize selected notes to {key} note grid"
            }
        return configs

@dataclass
class AppSettings:
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
    consonance_preference: float = 0  # -1.000 = max dissonance, 0 = neutral, 1.000 = max consonance

    # Color settings
    main_colors: List[str] = field(default_factory=lambda: ["#404040", "#606060", "#808080", "#A0A0A0", "#C0C0C0"])
    track_colors: List[str] = field(default_factory=lambda: ["#4A90E2", "#E94B3C", "#6AB04C", "#F79F1F"])
    
    # UI Configuration
    ui_constants: UIConstants = field(default_factory=UIConstants)
    piano_roll_config: PianoRollConfig = field(default_factory=PianoRollConfig)
    ui_layout: UILayout = field(default_factory=UILayout)
    
    @classmethod
    def load(cls, config_path: str = "config.json") -> 'AppSettings':
        """Load settings from file"""
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    data = json.load(f)
                # Note: This basic implementation doesn't handle nested dataclasses
                # You might want to use dataclasses-json or similar for full serialization
                settings = cls()
                for key, value in data.items():
                    if hasattr(settings, key) and not key.startswith('ui_'):
                        setattr(settings, key, value)
                return settings
            except Exception as e:
                print(f"Error loading settings: {e}")
        return cls()  # Return defaults
    
    def save(self, config_path: str = "config.json"):
        """Save settings to file"""
        try:
            # Basic serialization - exclude UI objects for now
            data = {k: v for k, v in self.__dict__.items() 
                   if not k.startswith('ui_') and not isinstance(v, (UIConstants, PianoRollConfig, UILayout))}
            with open(config_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
            
    def get_grid_pen_configs(self) -> Dict[str, Tuple[Tuple[int, int, int], int]]:
        """Get grid pen configurations as (color, width) tuples"""
        ui = self.ui_constants
        return {
            "measure": (ui.grid_measure_color, 2),
            "beat": (ui.grid_beat_color, 1), 
            "subdivision": (ui.grid_subdivision_color, 1),
            "octave": (ui.grid_octave_color, 1),
            "note": (ui.grid_note_color, 1)
        }
    
    def get_piano_key_colors(self) -> Dict[str, Tuple[int, int, int]]:
        """Get piano keyboard color configuration"""
        ui = self.ui_constants
        return {
            "white_key": ui.white_key_color,
            "white_key_alt": ui.white_key_alt_color,
            "white_key_border": ui.white_key_border_color,
            "black_key": ui.black_key_color,
            "black_key_border": ui.black_key_border_color
        }