"""
Enhanced Piano Roll Widget - pretty_midi Integration
Updated to work with the new pretty_midi-based MidiDocument
"""
import sys
import os
from typing import List, Optional, Tuple, Dict, Set
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsSimpleTextItem,
    QGraphicsLineItem, QPushButton, QLabel, QSpinBox, QSlider, QCheckBox,
    QComboBox, QFrame, QSplitter, QScrollArea
)
from PyQt6.QtGui import QBrush, QPen, QColor, QFont, QPainter, QKeySequence, QAction
from PyQt6.QtCore import Qt, QRectF, QPointF, QTimer, pyqtSignal

# Import core MIDI components
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.midi_data import MidiDocument, MidiTrack, MidiNote
from config.settings import AppSettings
from utils.music_theory import KEY_NAMES

class NoteItem(QGraphicsRectItem):
    """Enhanced graphics item for MIDI notes with pretty_midi integration"""
    
    def __init__(self, midi_note: MidiNote, note_height: float, seconds_per_pixel: float, parent=None):
        self.midi_note = midi_note
        self.note_height = note_height
        self.seconds_per_pixel = seconds_per_pixel
        
        # Calculate rectangle dimensions using seconds
        x = midi_note.start / seconds_per_pixel
        y = self.pitch_to_y(midi_note.pitch)
        width = max(1, midi_note.duration / seconds_per_pixel)
        height = note_height
        
        super().__init__(QRectF(x, y, width, height), parent)
        
        self.setFlags(
            QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsRectItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        
        self.update_appearance()
    
    def pitch_to_y(self, pitch: int) -> float:
        """Convert MIDI pitch to Y coordinate (higher pitches = lower Y values)"""
        return (127 - pitch) * self.note_height
    
    def y_to_pitch(self, y: float) -> int:
        """Convert Y coordinate to MIDI pitch"""
        pitch = 127 - int(y / self.note_height)
        return max(0, min(127, pitch))
    
    def update_appearance(self):
        """Update visual appearance based on note state and velocity"""
        if self.midi_note.selected:
            brush_color = QColor(255, 200, 100, 200)  # Orange for selected
            pen_color = QColor(200, 150, 50)
        else:
            # Enhanced color based on velocity and pitch class
            velocity_ratio = self.midi_note.velocity / 127.0
            pitch_class = self.midi_note.pitch_class
            
            # Color variations based on pitch class for visual harmony
            hue_offset = pitch_class * 30  # Different hues for different pitch classes
            saturation = int(100 + 100 * velocity_ratio)
            brightness = int(150 + 105 * velocity_ratio)
            
            brush_color = QColor()
            brush_color.setHsv(hue_offset % 360, saturation, brightness, 180)
            pen_color = QColor()
            pen_color.setHsv(hue_offset % 360, saturation, max(50, brightness - 50))
        
        self.setBrush(QBrush(brush_color))
        self.setPen(QPen(pen_color, 1))
    
    def itemChange(self, change, value):
        """Handle item changes with enhanced snapping"""
        if change == QGraphicsRectItem.GraphicsItemChange.ItemPositionChange:
            new_pos = value
            
            # Snap to grid
            grid_y = round(new_pos.y() / self.note_height) * self.note_height
            grid_x = max(0, new_pos.x())  # Don't allow negative time
            
            snapped_pos = QPointF(grid_x, grid_y)
            
            # Update MIDI note data (now in seconds)
            self.midi_note.start = grid_x * self.seconds_per_pixel
            self.midi_note.pitch = self.y_to_pitch(grid_y)
            
            return snapped_pos
        
        elif change == QGraphicsRectItem.GraphicsItemChange.ItemSelectedChange:
            self.midi_note.selected = bool(value)
            self.update_appearance()
        
        return super().itemChange(change, value)

class PianoKeyboard(QWidget):
    """Enhanced piano keyboard with better visual design"""
    
    def __init__(self, note_height: float, visible_range: Tuple[int, int], parent=None):
        super().__init__(parent)
        self.note_height = note_height
        self.visible_range = visible_range
        self.setFixedWidth(80)
        self.setMinimumHeight(int((visible_range[1] - visible_range[0] + 1) * note_height))
        
    def paintEvent(self, event):
        """Enhanced piano keyboard drawing with better contrast"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        white_key_width = self.width()
        black_key_width = int(self.width() * 0.6)
        
        # White and black key patterns
        white_key_notes = [0, 2, 4, 5, 7, 9, 11]  # C, D, E, F, G, A, B
        black_key_notes = [1, 3, 6, 8, 10]        # C#, D#, F#, G#, A#
        
        low_pitch, high_pitch = self.visible_range
        
        # Draw white keys first
        for pitch in range(low_pitch, high_pitch + 1):
            note_class = pitch % 12
            if note_class in white_key_notes:
                y = (high_pitch - pitch) * self.note_height
                
                # Enhanced white key colors
                if pitch % 12 == 0:  # C notes - slightly different shade
                    brush = QBrush(QColor(255, 255, 255))
                else:
                    brush = QBrush(QColor(248, 248, 248))
                
                painter.fillRect(0, int(y), white_key_width, int(self.note_height), brush)
                painter.setPen(QPen(QColor(200, 200, 200)))
                painter.drawRect(0, int(y), white_key_width - 1, int(self.note_height) - 1)
                
                # Add note name for C notes with octave
                if pitch % 12 == 0:
                    painter.setPen(Qt.GlobalColor.black)
                    octave = pitch // 12 - 1
                    font = QFont("Arial", 8)
                    painter.setFont(font)
                    painter.drawText(5, int(y + self.note_height - 5), f"C{octave}")
        
        # Draw black keys on top
        for pitch in range(low_pitch, high_pitch + 1):
            note_class = pitch % 12
            if note_class in black_key_notes:
                y = (high_pitch - pitch) * self.note_height
                
                brush = QBrush(QColor(30, 30, 30))
                painter.fillRect(0, int(y), black_key_width, int(self.note_height), brush)
                painter.setPen(QPen(QColor(100, 100, 100)))
                painter.drawRect(0, int(y), black_key_width - 1, int(self.note_height) - 1)

class PianoRollWidget(QGraphicsView):
    """Enhanced piano roll widget with pretty_midi integration"""
    
    note_added = pyqtSignal(MidiNote)
    note_removed = pyqtSignal(MidiNote)
    selection_changed = pyqtSignal()
    
    def __init__(self, document: MidiDocument, settings: AppSettings, parent=None):
        super().__init__(parent)
        
        self.document = document
        self.settings = settings
        self.current_track_index = 0
        
        # Enhanced visual parameters
        self.note_height = 20
        self.seconds_per_pixel = 0.1  # More intuitive time scaling
        self.visible_octaves = 10
        self.lowest_pitch = 12   # C0
        self.highest_pitch = 127 # G9
        
        # UI state
        self.dragging_note = None
        self.drag_start_pos = None
        self.selection_rect = None
        self.current_tool = "pencil"
        
        # Setup graphics scene
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setMouseTracking(True)
        
        # Note items cache
        self.note_items: Dict[MidiNote, NoteItem] = {}
        
        self.setup_scene()
        self.refresh_notes()
        self.document_changed()
    
    def setup_scene(self):
        """Setup the enhanced graphics scene"""
        # Calculate scene dimensions
        num_pitches = self.highest_pitch - self.lowest_pitch + 1
        scene_height = num_pitches * self.note_height
        
        # Set width to show 32 seconds initially (expandable)
        seconds_to_show = 32
        scene_width = seconds_to_show / self.seconds_per_pixel
        
        self.scene.setSceneRect(0, 0, scene_width, scene_height)
        self.draw_grid()
    
    def draw_grid(self):
        """Draw enhanced background grid with beat and measure markers"""
        scene_rect = self.scene.sceneRect()
        
        # Clear existing grid
        for item in self.scene.items():
            if isinstance(item, QGraphicsLineItem):
                self.scene.removeItem(item)
        
        # Get tempo for beat calculation
        tempo_bpm = self.document.tempo_bpm
        seconds_per_beat = 60.0 / tempo_bpm
        beats_per_measure = self.document.time_signature[0]
        seconds_per_measure = seconds_per_beat * beats_per_measure
        
        # Vertical lines (time grid)
        pen_beat = QPen(QColor(200, 200, 200), 1)      # Beat lines
        pen_measure = QPen(QColor(150, 150, 150), 2)   # Measure lines
        pen_subdivision = QPen(QColor(230, 230, 230), 1)  # Subdivision lines
        
        # Draw measure lines
        x = 0
        measure_count = 0
        while x < scene_rect.width():
            time_seconds = x * self.seconds_per_pixel
            
            # Measure lines
            if measure_count == 0 or time_seconds % seconds_per_measure < self.seconds_per_pixel:
                pen = pen_measure
            # Beat lines
            elif time_seconds % seconds_per_beat < self.seconds_per_pixel:
                pen = pen_beat
            # Subdivision lines (16th notes)
            elif time_seconds % (seconds_per_beat / 4) < self.seconds_per_pixel:
                pen = pen_subdivision
            else:
                x += 1
                continue
            
            line = self.scene.addLine(x, 0, x, scene_rect.height(), pen)
            line.setZValue(-2)
            x += 1
        
        # Horizontal lines (pitch grid)
        pen_octave = QPen(QColor(180, 180, 180), 1)
        pen_note = QPen(QColor(240, 240, 240), 1)
        
        for pitch in range(self.lowest_pitch, self.highest_pitch + 1):
            y = (self.highest_pitch - pitch) * self.note_height
            pen = pen_octave if pitch % 12 == 0 else pen_note
            line = self.scene.addLine(0, y, scene_rect.width(), y, pen)
            line.setZValue(-1)
    
    def get_current_track(self) -> Optional[MidiTrack]:
        """Get the currently active track"""
        if 0 <= self.current_track_index < len(self.document.tracks):
            return self.document.tracks[self.current_track_index]
        return None
    
    def set_current_track(self, index: int):
        """Set the active track and refresh display"""
        if 0 <= index < len(self.document.tracks):
            self.current_track_index = index
            self.refresh_notes()
    
    def refresh_notes(self):
        """Refresh all note items in the scene"""
        # Clear existing note items
        for note_item in self.note_items.values():
            self.scene.removeItem(note_item)
        self.note_items.clear()
        
        # Add notes from current track
        current_track = self.get_current_track()
        if current_track:
            for note in current_track.notes:
                self.add_note_item(note)
    
    def add_note_item(self, midi_note: MidiNote):
        """Add a visual note item for a MIDI note"""
        if midi_note not in self.note_items:
            note_item = NoteItem(midi_note, self.note_height, self.seconds_per_pixel)
            self.scene.addItem(note_item)
            self.note_items[midi_note] = note_item
    
    def remove_note_item(self, midi_note: MidiNote):
        """Remove a visual note item"""
        if midi_note in self.note_items:
            note_item = self.note_items[midi_note]
            self.scene.removeItem(note_item)
            del self.note_items[midi_note]
    
    def scene_to_time_and_pitch(self, scene_pos: QPointF) -> Tuple[float, int]:
        """Convert scene coordinates to time (seconds) and pitch"""
        time = scene_pos.x() * self.seconds_per_pixel
        pitch = self.highest_pitch - int(scene_pos.y() / self.note_height)
        return time, max(0, min(127, pitch))
    
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            time, pitch = self.scene_to_time_and_pitch(scene_pos)
            
            if self.current_tool == "pencil":
                self.add_note_at_position(time, pitch)
            elif self.current_tool == "erase":
                self.remove_note_at_position(scene_pos)
            elif self.current_tool == "select":
                super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)
    
    def add_note_at_position(self, time: float, pitch: int):
        """Add a new note at the specified time and pitch"""
        current_track = self.get_current_track()
        if not current_track:
            return
        
        # Check if there's already a note at this position
        for note in current_track.notes:
            if (note.pitch == pitch and 
                note.start <= time < note.end):
                return  # Don't add overlapping notes
        
        # Create new note with default duration (16th note equivalent)
        tempo_bpm = self.document.tempo_bpm
        default_duration = 60.0 / (tempo_bpm * 4)  # 16th note in seconds
        
        new_note = MidiNote(
            start=time,
            end=time + default_duration,
            pitch=pitch,
            velocity=self.settings.default_velocity
        )
        
        current_track.add_note(new_note)
        self.add_note_item(new_note)
        self.document.modified = True
        self.note_added.emit(new_note)
    
    def remove_note_at_position(self, scene_pos: QPointF):
        """Remove note at the specified position"""
        item = self.scene.itemAt(scene_pos, self.transform())
        if isinstance(item, NoteItem):
            current_track = self.get_current_track()
            if current_track and current_track.remove_note(item.midi_note):
                self.remove_note_item(item.midi_note)
                self.document.modified = True
                self.note_removed.emit(item.midi_note)
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key.Key_Delete or event.key() == Qt.Key.Key_Backspace:
            self.delete_selected_notes()
        elif event.key() == Qt.Key.Key_A and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.select_all_notes()
        elif event.key() == Qt.Key.Key_Escape:
            self.clear_selection()
        else:
            super().keyPressEvent(event)
    
    def delete_selected_notes(self):
        """Delete all selected notes"""
        current_track = self.get_current_track()
        if not current_track:
            return
        
        selected_notes = [note for note in current_track.notes if note.selected]
        for note in selected_notes:
            current_track.remove_note(note)
            self.remove_note_item(note)
        
        if selected_notes:
            self.document.modified = True
            self.selection_changed.emit()
    
    def select_all_notes(self):
        """Select all notes in the current track"""
        for note_item in self.note_items.values():
            note_item.setSelected(True)
        self.selection_changed.emit()
    
    def clear_selection(self):
        """Clear all selections"""
        for note_item in self.note_items.values():
            note_item.setSelected(False)
        self.selection_changed.emit()
    
    def quantize_selected_notes(self, grid_size_seconds: Optional[float] = None):
        """Quantize selected notes to grid (in seconds)"""
        if grid_size_seconds is None:
            # Default to 16th note grid
            tempo_bpm = self.document.tempo_bpm
            grid_size_seconds = 60.0 / (tempo_bpm * 4)
        
        current_track = self.get_current_track()
        if current_track:
            current_track.quantize_notes(grid_size_seconds, strength=1.0, selected_only=True)
            self.refresh_notes()
            self.document.modified = True
    
    def transpose_selected_notes(self, semitones: int):
        """Transpose selected notes"""
        current_track = self.get_current_track()
        if current_track:
            current_track.transpose_notes(semitones, selected_only=True)
            self.refresh_notes()
            self.document.modified = True
    
    def document_changed(self):
        """Handle document changes"""
        self.refresh_notes()
        # Expand scene if needed
        _, max_time = self.document.get_time_bounds()
        if max_time > 0:
            required_width = (max_time / self.seconds_per_pixel) + 1000  # Extra padding
            if required_width > self.scene.width():
                self.scene.setSceneRect(0, 0, required_width, self.scene.height())
                self.draw_grid()

class PianoRollPanel(QWidget):
    """Enhanced piano roll panel with pretty_midi integration"""
    
    def __init__(self, document: MidiDocument, settings: AppSettings, parent=None):
        super().__init__(parent)
        self.document = document
        self.settings = settings
        
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        """Setup the enhanced UI"""
        layout = QVBoxLayout(self)
        
        # Enhanced control panel
        controls = self.create_controls()
        layout.addWidget(controls)
        
        # Main piano roll area
        main_area = QHBoxLayout()
        
        # Piano keyboard
        self.keyboard = PianoKeyboard(
            note_height=20,
            visible_range=(12, 127),
            parent=self
        )
        main_area.addWidget(self.keyboard)
        
        # Piano roll view
        self.piano_roll = PianoRollWidget(self.document, self.settings, self)
        main_area.addWidget(self.piano_roll, 1)  # Stretch factor
        
        main_widget = QWidget()
        main_widget.setLayout(main_area)
        layout.addWidget(main_widget, 1)
    
    def create_controls(self) -> QWidget:
        """Create enhanced control panel"""
        controls = QFrame()
        controls.setFrameStyle(QFrame.Shape.StyledPanel)
        controls.setMaximumHeight(80)
        
        layout = QVBoxLayout(controls)
        
        # Top row - Track and tempo info
        top_row = QHBoxLayout()
        
        # Track selector
        top_row.addWidget(QLabel("Track:"))
        self.track_combo = QComboBox()
        self.update_track_combo()
        top_row.addWidget(self.track_combo)
        
        # Tempo display
        top_row.addWidget(QLabel("Tempo:"))
        self.tempo_label = QLabel(f"{self.document.tempo_bpm:.1f} BPM")
        self.tempo_label.setStyleSheet("font-weight: bold;")
        top_row.addWidget(self.tempo_label)
        
        # Key display
        top_row.addWidget(QLabel("Key:"))
        try:
            key_root, key_mode = self.document.estimate_key()
            self.key_label = QLabel(f"{key_root} {key_mode}")
        except:
            self.key_label = QLabel("Unknown")
        self.key_label.setStyleSheet("font-weight: bold;")
        top_row.addWidget(self.key_label)
        
        top_row.addStretch()
        layout.addLayout(top_row)
        
        # Bottom row - Tools and controls
        bottom_row = QHBoxLayout()
        
        # Tool buttons
        bottom_row.addWidget(QLabel("Tool:"))
        self.pencil_btn = QPushButton("✏️ Pencil")
        self.pencil_btn.setCheckable(True)
        self.pencil_btn.setChecked(True)
        bottom_row.addWidget(self.pencil_btn)
        
        self.select_btn = QPushButton("🔍 Select")
        self.select_btn.setCheckable(True)
        bottom_row.addWidget(self.select_btn)
        
        self.erase_btn = QPushButton("🗑️ Erase")
        self.erase_btn.setCheckable(True)
        bottom_row.addWidget(self.erase_btn)
        
        # Separator
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.Shape.VLine)
        bottom_row.addWidget(separator1)
        
        # Quantize options
        bottom_row.addWidget(QLabel("Quantize:"))
        quantize_16_btn = QPushButton("⏱️ 1/16")
        quantize_16_btn.clicked.connect(lambda: self.piano_roll.quantize_selected_notes())
        bottom_row.addWidget(quantize_16_btn)
        
        quantize_8_btn = QPushButton("⏱️ 1/8")
        quantize_8_btn.clicked.connect(lambda: self.quantize_to_8th())
        bottom_row.addWidget(quantize_8_btn)
        
        # Separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.VLine)
        bottom_row.addWidget(separator2)
        
        # Velocity control
        bottom_row.addWidget(QLabel("Velocity:"))
        self.velocity_slider = QSlider(Qt.Orientation.Horizontal)
        self.velocity_slider.setRange(1, 127)
        self.velocity_slider.setValue(self.settings.default_velocity)
        self.velocity_slider.setMaximumWidth(100)
        bottom_row.addWidget(self.velocity_slider)
        
        self.velocity_label = QLabel(str(self.settings.default_velocity))
        bottom_row.addWidget(self.velocity_label)
        
        bottom_row.addStretch()
        layout.addLayout(bottom_row)
        
        return controls
    
    def quantize_to_8th(self):
        """Quantize to 8th note grid"""
        tempo_bpm = self.document.tempo_bpm
        eighth_note_seconds = 60.0 / (tempo_bpm * 2)
        self.piano_roll.quantize_selected_notes(eighth_note_seconds)
    
    def connect_signals(self):
        """Connect UI signals"""
        self.track_combo.currentIndexChanged.connect(self.on_track_changed)
        
        # Tool buttons
        self.pencil_btn.clicked.connect(lambda: self.set_tool("pencil"))
        self.select_btn.clicked.connect(lambda: self.set_tool("select"))
        self.erase_btn.clicked.connect(lambda: self.set_tool("erase"))
        
        # Velocity slider
        self.velocity_slider.valueChanged.connect(self.on_velocity_changed)
        
        # Piano roll signals
        self.piano_roll.note_added.connect(self.on_note_added)
        self.piano_roll.note_removed.connect(self.on_note_removed)
        self.piano_roll.selection_changed.connect(self.on_selection_changed)
    
    def update_track_combo(self):
        """Update track combo box"""
        self.track_combo.clear()
        for i, track in enumerate(self.document.tracks):
            display_name = f"{i+1}: {track.name}"
            if track.is_drum:
                display_name += " 🥁"
            self.track_combo.addItem(display_name)
        
        if not self.document.tracks:
            self.track_combo.addItem("No tracks")
    
    def on_track_changed(self, index: int):
        """Handle track selection change"""
        self.piano_roll.set_current_track(index)
    
    def on_velocity_changed(self, value: int):
        """Handle velocity slider change"""
        self.velocity_label.setText(str(value))
        self.settings.default_velocity = value
    
    def set_tool(self, tool_name: str):
        """Set the current editing tool"""
        self.piano_roll.current_tool = tool_name
        
        # Update button states
        self.pencil_btn.setChecked(tool_name == "pencil")
        self.select_btn.setChecked(tool_name == "select")
        self.erase_btn.setChecked(tool_name == "erase")
    
    def on_note_added(self, note: MidiNote):
        """Handle note addition with enhanced feedback"""
        note_name = KEY_NAMES[note.pitch % 12]
        octave = note.pitch // 12 - 1
        print(f"Note added: {note_name}{octave} at {note.start:.2f}s, vel: {note.velocity}")
    
    def on_note_removed(self, note: MidiNote):
        """Handle note removal with enhanced feedback"""
        note_name = KEY_NAMES[note.pitch % 12]
        octave = note.pitch // 12 - 1
        print(f"Note removed: {note_name}{octave}")
    
    def on_selection_changed(self):
        """Handle selection changes"""
        current_track = self.piano_roll.get_current_track()
        if current_track:
            selected_count = len(current_track.get_selected_notes())
            print(f"Selection changed: {selected_count} notes selected")

class PianoRollTestWindow(QMainWindow):
    """Enhanced test window for the pretty_midi piano roll"""
    
    def __init__(self):
        super().__init__()
        self.document = MidiDocument()
        self.settings = AppSettings()
        
        # Add enhanced test tracks
        self.create_test_data()
        self.init_ui()
    
    def create_test_data(self):
        """Create enhanced test data showcasing pretty_midi features"""
        # Piano track with chord progression
        piano_track = self.document.add_track()
        piano_track.name = "Piano"
        piano_track.program = 0  # Acoustic Grand Piano
        
        # Bass track
        bass_track = self.document.add_track()
        bass_track.name = "Bass"
        bass_track.program = 32  # Acoustic Bass
        
        # Drum track
        drum_track = self.document.add_track()
        drum_track.name = "Drums"
        drum_track.is_drum = True
        
        # Add chord progression (C - Am - F - G)
        chords = [
            ([60, 64, 67], 0.0, 2.0),    # C major
            ([57, 60, 64], 2.0, 4.0),   # A minor
            ([53, 57, 60], 4.0, 6.0),   # F major
            ([55, 59, 62], 6.0, 8.0),   # G major
        ]
        
        for pitches, start, end in chords:
            for pitch in pitches:
                note = MidiNote(
                    start=start,
                    end=end,
                    pitch=pitch,
                    velocity=80
                )
                piano_track.add_note(note)
        
        # Add bass line
        bass_notes = [
            (36, 0.0, 0.5),   # C2
            (33, 2.0, 0.5),   # A1
            (29, 4.0, 0.5),   # F1
            (31, 6.0, 0.5),   # G1
        ]
        
        for pitch, start, duration in bass_notes:
            note = MidiNote(
                start=start,
                end=start + duration,
                pitch=pitch,
                velocity=90
            )
            bass_track.add_note(note)
        
        # Add simple drum pattern
        drum_pattern = [
            (36, [0.0, 2.0, 4.0, 6.0]),  # Kick drum
            (38, [1.0, 3.0, 5.0, 7.0]),  # Snare
            (42, [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5,
                  4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5]),  # Hi-hat
        ]
        
        for pitch, times in drum_pattern:
            for time in times:
                note = MidiNote(
                    start=time,
                    end=time + 0.1,
                    pitch=pitch,
                    velocity=70
                )
                drum_track.add_note(note)
    
    def init_ui(self):
        """Initialize the enhanced UI"""
        self.setWindowTitle("MIDI_COMPOSE - Enhanced Piano Roll (pretty_midi)")
        self.setGeometry(100, 100, 1600, 900)
        
        # Create piano roll panel
        self.piano_roll_panel = PianoRollPanel(self.document, self.settings)
        self.setCentralWidget(self.piano_roll_panel)
        
        # Add enhanced menu bar
        self.create_menus()
        
        # Status bar with enhanced info
        self.statusBar().showMessage("Ready - Enhanced pretty_midi integration active")
    
    def create_menus(self):
        """Create enhanced menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        new_action = QAction('New', self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self.new_document)
        file_menu.addAction(new_action)
        
        # Edit menu
        edit_menu = menubar.addMenu('Edit')
        
        select_all_action = QAction('Select All', self)
        select_all_action.setShortcut(QKeySequence.StandardKey.SelectAll)
        select_all_action.triggered.connect(self.piano_roll_panel.piano_roll.select_all_notes)
        edit_menu.addAction(select_all_action)
        
        delete_action = QAction('Delete Selected', self)
        delete_action.setShortcut(QKeySequence.StandardKey.Delete)
        delete_action.triggered.connect(self.piano_roll_panel.piano_roll.delete_selected_notes)
        edit_menu.addAction(delete_action)
        
        # Analysis menu (new!)
        analysis_menu = menubar.addMenu('Analysis')
        
        analyze_key_action = QAction('Analyze Key', self)
        analyze_key_action.triggered.connect(self.analyze_key)
        analysis_menu.addAction(analyze_key_action)
        
        analyze_tempo_action = QAction('Analyze Tempo', self)
        analyze_tempo_action.triggered.connect(self.analyze_tempo)
        analysis_menu.addAction(analyze_tempo_action)
    
    def new_document(self):
        """Create a new document"""
        self.document = MidiDocument()
        self.piano_roll_panel.document = self.document
        self.piano_roll_panel.piano_roll.document = self.document
        self.piano_roll_panel.update_track_combo()
        self.piano_roll_panel.piano_roll.document_changed()
    
    def analyze_key(self):
        """Analyze and display the estimated key"""
        try:
            key_root, key_mode = self.document.estimate_key()
            self.statusBar().showMessage(f"Estimated key: {key_root} {key_mode}")
            self.piano_roll_panel.key_label.setText(f"{key_root} {key_mode}")
        except Exception as e:
            self.statusBar().showMessage(f"Key analysis failed: {e}")
    
    def analyze_tempo(self):
        """Analyze and display the estimated tempo"""
        try:
            tempo = self.document.tempo_bpm
            self.statusBar().showMessage(f"Estimated tempo: {tempo:.1f} BPM")
            self.piano_roll_panel.tempo_label.setText(f"{tempo:.1f} BPM")
        except Exception as e:
            self.statusBar().showMessage(f"Tempo analysis failed: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = PianoRollTestWindow()
    window.show()
    
    sys.exit(app.exec())