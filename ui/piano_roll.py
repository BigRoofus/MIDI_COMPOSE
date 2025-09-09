"""
Fully integrated piano roll widget with MIDI_COMPOSE core functionality
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
    """Custom graphics item for MIDI notes"""
    
    def __init__(self, midi_note: MidiNote, note_height: float, ticks_per_pixel: float, parent=None):
        self.midi_note = midi_note
        self.note_height = note_height
        self.ticks_per_pixel = ticks_per_pixel
        
        # Calculate rectangle dimensions
        x = midi_note.start_time / ticks_per_pixel
        y = self.pitch_to_y(midi_note.pitch)
        width = max(1, midi_note.duration / ticks_per_pixel)
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
        """Update visual appearance based on note state"""
        if self.midi_note.selected:
            brush_color = QColor(255, 200, 100, 200)  # Orange for selected
            pen_color = QColor(200, 150, 50)
        else:
            # Color based on velocity
            velocity_ratio = self.midi_note.velocity / 127.0
            blue_intensity = int(100 + 155 * velocity_ratio)
            brush_color = QColor(74, 144, blue_intensity, 180)
            pen_color = QColor(50, 100, 150)
        
        self.setBrush(QBrush(brush_color))
        self.setPen(QPen(pen_color, 1))
    
    def itemChange(self, change, value):
        """Handle item changes (movement, selection, etc.)"""
        if change == QGraphicsRectItem.GraphicsItemChange.ItemPositionChange:
            # Snap to grid and update MIDI note
            new_pos = value
            
            # Snap to grid
            grid_y = round(new_pos.y() / self.note_height) * self.note_height
            grid_x = max(0, new_pos.x())  # Don't allow negative time
            
            snapped_pos = QPointF(grid_x, grid_y)
            
            # Update MIDI note data
            self.midi_note.start_time = int(grid_x * self.ticks_per_pixel)
            self.midi_note.pitch = self.y_to_pitch(grid_y)
            
            return snapped_pos
        
        elif change == QGraphicsRectItem.GraphicsItemChange.ItemSelectedChange:
            self.midi_note.selected = bool(value)
            self.update_appearance()
        
        return super().itemChange(change, value)

class PianoKeyboard(QWidget):
    """Piano keyboard widget for the left side of the piano roll"""
    
    def __init__(self, note_height: float, visible_range: Tuple[int, int], parent=None):
        super().__init__(parent)
        self.note_height = note_height
        self.visible_range = visible_range  # (lowest_pitch, highest_pitch)
        self.setFixedWidth(80)
        self.setMinimumHeight(int((visible_range[1] - visible_range[0] + 1) * note_height))
        
    def paintEvent(self, event):
        """Draw the piano keyboard"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        white_key_width = self.width()
        black_key_width = int(self.width() * 0.6)
        
        # White keys pattern (C, D, E, F, G, A, B have no sharps after them in layout)
        white_key_notes = [0, 2, 4, 5, 7, 9, 11]  # C, D, E, F, G, A, B
        black_key_notes = [1, 3, 6, 8, 10]  # C#, D#, F#, G#, A#
        
        low_pitch, high_pitch = self.visible_range
        
        # Draw white keys first
        for pitch in range(low_pitch, high_pitch + 1):
            note_class = pitch % 12
            if note_class in white_key_notes:
                y = (high_pitch - pitch) * self.note_height
                
                # Alternate white key colors for visual clarity
                if pitch % 12 == 0:  # C notes
                    brush = QBrush(QColor(250, 250, 250))
                else:
                    brush = QBrush(QColor(240, 240, 240))
                
                painter.fillRect(0, int(y), white_key_width, int(self.note_height), brush)
                painter.drawRect(0, int(y), white_key_width - 1, int(self.note_height) - 1)
                
                # Add note name for C notes
                if pitch % 12 == 0:
                    painter.setPen(Qt.GlobalColor.black)
                    painter.drawText(5, int(y + self.note_height - 5), f"C{pitch // 12 - 1}")
        
        # Draw black keys on top
        for pitch in range(low_pitch, high_pitch + 1):
            note_class = pitch % 12
            if note_class in black_key_notes:
                y = (high_pitch - pitch) * self.note_height
                
                brush = QBrush(QColor(40, 40, 40))
                painter.fillRect(0, int(y), black_key_width, int(self.note_height), brush)
                painter.setPen(Qt.GlobalColor.white)
                painter.drawRect(0, int(y), black_key_width - 1, int(self.note_height) - 1)

class PianoRollWidget(QGraphicsView):
    """Main piano roll widget integrated with MIDI_COMPOSE core"""
    
    note_added = pyqtSignal(MidiNote)
    note_removed = pyqtSignal(MidiNote)
    selection_changed = pyqtSignal()
    
    def __init__(self, document: MidiDocument, settings: AppSettings, parent=None):
        super().__init__(parent)
        
        self.document = document
        self.settings = settings
        self.current_track_index = 0
        
        # Visual parameters
        self.note_height = 20
        self.ticks_per_pixel = 10  # How many MIDI ticks per pixel
        self.visible_octaves = 10
        self.lowest_pitch = 12   # C0
        self.highest_pitch = 127 # G9
        
        # UI state
        self.dragging_note = None
        self.drag_start_pos = None
        self.selection_rect = None
        self.current_tool = "pencil"  # pencil, select, erase
        
        # Setup graphics scene
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setMouseTracking(True)
        
        # Note items cache
        self.note_items: Dict[MidiNote, NoteItem] = {}
        
        self.setup_scene()
        self.refresh_notes()
        
        # Connect to document changes
        self.document_changed()
    
    def setup_scene(self):
        """Setup the graphics scene with grid and boundaries"""
        # Calculate scene dimensions
        num_pitches = self.highest_pitch - self.lowest_pitch + 1
        scene_height = num_pitches * self.note_height
        
        # Set width to show 32 beats initially (expandable)
        beats_to_show = 32
        scene_width = beats_to_show * self.document.ticks_per_beat / self.ticks_per_pixel
        
        self.scene.setSceneRect(0, 0, scene_width, scene_height)
        
        self.draw_grid()
    
    def draw_grid(self):
        """Draw the background grid"""
        scene_rect = self.scene.sceneRect()
        
        # Clear existing grid
        for item in self.scene.items():
            if isinstance(item, QGraphicsLineItem):
                self.scene.removeItem(item)
        
        # Vertical lines (time grid)
        pen_beat = QPen(QColor(180, 180, 180), 1)  # Beat lines
        pen_measure = QPen(QColor(120, 120, 120), 2)  # Measure lines
        
        beat_width = self.document.ticks_per_beat / self.ticks_per_pixel
        beats_per_measure = self.document.time_signature[0]
        
        x = 0
        beat_count = 0
        while x < scene_rect.width():
            pen = pen_measure if beat_count % beats_per_measure == 0 else pen_beat
            line = self.scene.addLine(x, 0, x, scene_rect.height(), pen)
            line.setZValue(-2)  # Behind everything
            
            x += beat_width
            beat_count += 1
        
        # Horizontal lines (pitch grid)
        pen_octave = QPen(QColor(160, 160, 160), 1)
        pen_note = QPen(QColor(220, 220, 220), 1)
        
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
            note_item = NoteItem(midi_note, self.note_height, self.ticks_per_pixel)
            self.scene.addItem(note_item)
            self.note_items[midi_note] = note_item
    
    def remove_note_item(self, midi_note: MidiNote):
        """Remove a visual note item"""
        if midi_note in self.note_items:
            note_item = self.note_items[midi_note]
            self.scene.removeItem(note_item)
            del self.note_items[midi_note]
    
    def scene_to_time_and_pitch(self, scene_pos: QPointF) -> Tuple[int, int]:
        """Convert scene coordinates to time and pitch"""
        time = int(scene_pos.x() * self.ticks_per_pixel)
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
    
    def add_note_at_position(self, time: int, pitch: int):
        """Add a new note at the specified time and pitch"""
        current_track = self.get_current_track()
        if not current_track:
            return
        
        # Check if there's already a note at this position
        for note in current_track.notes:
            if (note.pitch == pitch and 
                note.start_time <= time < note.end_time):
                return  # Don't add overlapping notes
        
        # Create new note
        default_duration = self.document.ticks_per_beat // 4  # 16th note
        new_note = MidiNote(
            pitch=pitch,
            start_time=time,
            end_time=time + default_duration,
            velocity=self.settings.default_velocity,
            channel=current_track.channel
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
    
    def quantize_selected_notes(self, grid_size: Optional[int] = None):
        """Quantize selected notes to grid"""
        if grid_size is None:
            grid_size = self.document.ticks_per_beat // 4  # 16th note grid
        
        current_track = self.get_current_track()
        if current_track:
            current_track.quantize_notes(grid_size, strength=1.0, selected_only=True)
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
            required_width = (max_time / self.ticks_per_pixel) + 1000  # Extra padding
            if required_width > self.scene.width():
                self.scene.setSceneRect(0, 0, required_width, self.scene.height())
                self.draw_grid()

class PianoRollPanel(QWidget):
    """Complete piano roll panel with keyboard, controls, and piano roll"""
    
    def __init__(self, document: MidiDocument, settings: AppSettings, parent=None):
        super().__init__(parent)
        self.document = document
        self.settings = settings
        
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        """Setup the complete UI"""
        layout = QVBoxLayout(self)
        
        # Control panel
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
        """Create control panel"""
        controls = QFrame()
        controls.setFrameStyle(QFrame.Shape.StyledPanel)
        controls.setMaximumHeight(60)
        
        layout = QHBoxLayout(controls)
        
        # Track selector
        layout.addWidget(QLabel("Track:"))
        self.track_combo = QComboBox()
        self.update_track_combo()
        layout.addWidget(self.track_combo)
        
        layout.addWidget(QFrame())  # Separator
        
        # Tool buttons
        layout.addWidget(QLabel("Tool:"))
        self.pencil_btn = QPushButton("✏️ Pencil")
        self.pencil_btn.setCheckable(True)
        self.pencil_btn.setChecked(True)
        layout.addWidget(self.pencil_btn)
        
        self.select_btn = QPushButton("🔍 Select")
        self.select_btn.setCheckable(True)
        layout.addWidget(self.select_btn)
        
        self.erase_btn = QPushButton("🗑️ Erase")
        self.erase_btn.setCheckable(True)
        layout.addWidget(self.erase_btn)
        
        layout.addWidget(QFrame())  # Separator
        
        # Quantize
        layout.addWidget(QLabel("Quantize:"))
        quantize_btn = QPushButton("⏱️ 1/16")
        quantize_btn.clicked.connect(lambda: self.piano_roll.quantize_selected_notes())
        layout.addWidget(quantize_btn)
        
        # Velocity
        layout.addWidget(QLabel("Velocity:"))
        self.velocity_slider = QSlider(Qt.Orientation.Horizontal)
        self.velocity_slider.setRange(1, 127)
        self.velocity_slider.setValue(self.settings.default_velocity)
        self.velocity_slider.setMaximumWidth(100)
        layout.addWidget(self.velocity_slider)
        
        layout.addStretch()  # Push everything to the left
        
        return controls
    
    def connect_signals(self):
        """Connect UI signals"""
        self.track_combo.currentIndexChanged.connect(self.on_track_changed)
        
        # Tool buttons
        self.pencil_btn.clicked.connect(lambda: self.set_tool("pencil"))
        self.select_btn.clicked.connect(lambda: self.set_tool("select"))
        self.erase_btn.clicked.connect(lambda: self.set_tool("erase"))
        
        # Piano roll signals
        self.piano_roll.note_added.connect(self.on_note_added)
        self.piano_roll.note_removed.connect(self.on_note_removed)
        self.piano_roll.selection_changed.connect(self.on_selection_changed)
    
    def update_track_combo(self):
        """Update track combo box"""
        self.track_combo.clear()
        for i, track in enumerate(self.document.tracks):
            self.track_combo.addItem(f"{i+1}: {track.name}")
        
        if not self.document.tracks:
            self.track_combo.addItem("No tracks")
    
    def on_track_changed(self, index: int):
        """Handle track selection change"""
        self.piano_roll.set_current_track(index)
    
    def set_tool(self, tool_name: str):
        """Set the current editing tool"""
        self.piano_roll.current_tool = tool_name
        
        # Update button states
        self.pencil_btn.setChecked(tool_name == "pencil")
        self.select_btn.setChecked(tool_name == "select")
        self.erase_btn.setChecked(tool_name == "erase")
    
    def on_note_added(self, note: MidiNote):
        """Handle note addition"""
        print(f"Note added: {KEY_NAMES[note.pitch % 12]}{note.pitch // 12 - 1} at {note.start_time}")
    
    def on_note_removed(self, note: MidiNote):
        """Handle note removal"""
        print(f"Note removed: {KEY_NAMES[note.pitch % 12]}{note.pitch // 12 - 1}")
    
    def on_selection_changed(self):
        """Handle selection changes"""
        current_track = self.piano_roll.get_current_track()
        if current_track:
            selected_count = len(current_track.get_selected_notes())
            print(f"Selection changed: {selected_count} notes selected")

# Example usage and test window
class PianoRollTestWindow(QMainWindow):
    """Test window for the piano roll"""
    
    def __init__(self):
        super().__init__()
        self.document = MidiDocument()
        self.settings = AppSettings()
        
        # Add some test tracks
        track1 = self.document.add_track()
        track1.name = "Piano"
        
        track2 = self.document.add_track()
        track2.name = "Bass"
        
        # Add some test notes
        test_notes = [
            MidiNote(60, 0, 480, 90),      # C4 whole note
            MidiNote(64, 480, 720, 80),    # E4 half note
            MidiNote(67, 720, 960, 85),    # G4 half note
            MidiNote(72, 960, 1440, 75),   # C5 whole note
        ]
        
        for note in test_notes:
            track1.add_note(note)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle("MIDI_COMPOSE - Piano Roll Test")
        self.setGeometry(100, 100, 1400, 800)
        
        # Create piano roll panel
        self.piano_roll_panel = PianoRollPanel(self.document, self.settings)
        self.setCentralWidget(self.piano_roll_panel)
        
        # Add menu bar with basic functions
        self.create_menus()
    
    def create_menus(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = PianoRollTestWindow()
    window.show()
    
    sys.exit(app.exec())