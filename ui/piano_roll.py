import sys
import os
from typing import Optional, Tuple, Dict
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGraphicsView, QGraphicsScene, QGraphicsRectItem, QPushButton, QLabel,
    QSlider, QComboBox, QFrame, QAction
)
from PyQt6.QtGui import QBrush, QPen, QColor, QFont, QPainter, QKeySequence
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal

# Core MIDI and config imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.midi_data_model import MidiDocument, MidiNote
from config import AppSettings
from music_theory import KEY_NAMES

class NoteItem(QGraphicsRectItem):
    """Enhanced graphics item for MIDI notes."""
    def __init__(self, midi_note: MidiNote, note_height: float, seconds_per_pixel: float, parent=None):
        self.midi_note = midi_note
        self.note_height = note_height
        self.seconds_per_pixel = seconds_per_pixel
        x = midi_note.start / seconds_per_pixel
        y = self._pitch_to_y(midi_note.pitch)
        width = max(1, midi_note.duration / seconds_per_pixel)
        height = note_height
        super().__init__(QRectF(x, y, width, height), parent)
        self.setFlags(self.GraphicsItemFlag.ItemIsMovable | self.GraphicsItemFlag.ItemIsSelectable | self.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.update_appearance()

    def _pitch_to_y(self, pitch: int) -> float:
        return (127 - pitch) * self.note_height

    def _y_to_pitch(self, y: float) -> int:
        return max(0, min(127, 127 - int(y / self.note_height)))

    def update_appearance(self):
        if self.midi_note.selected:
            self.setBrush(QBrush(QColor(255, 200, 100, 200)))
            self.setPen(QPen(QColor(200, 150, 50)))
        else:
            velocity_ratio = self.midi_note.velocity / 127.0
            pitch_class = self.midi_note.pitch % 12
            hue = (pitch_class * 30) % 360
            saturation = int(100 + 100 * velocity_ratio)
            brightness = int(150 + 105 * velocity_ratio)
            brush_color = QColor.fromHsv(hue, saturation, brightness, 180)
            pen_color = QColor.fromHsv(hue, saturation, max(50, brightness - 50))
            self.setBrush(QBrush(brush_color))
            self.setPen(QPen(pen_color, 1))

    def itemChange(self, change, value):
        if change == self.GraphicsItemChange.ItemPositionChange:
            snapped_y = round(value.y() / self.note_height) * self.note_height
            snapped_x = max(0, value.x())
            self.midi_note.start = snapped_x * self.seconds_per_pixel
            self.midi_note.pitch = self._y_to_pitch(snapped_y)
            return QPointF(snapped_x, snapped_y)
        elif change == self.GraphicsItemChange.ItemSelectedChange:
            self.midi_note.selected = bool(value)
            self.update_appearance()
        return super().itemChange(change, value)

class PianoKeyboard(QWidget):
    """Enhanced piano keyboard widget."""
    def __init__(self, note_height: float, visible_range: Tuple[int, int], parent=None):
        super().__init__(parent)
        self.note_height = note_height
        self.visible_range = visible_range
        self.setFixedWidth(80)
        self.setMinimumHeight(int((visible_range[1] - visible_range[0] + 1) * note_height))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        white_key_width, black_key_width = self.width(), int(self.width() * 0.6)
        white_key_notes, black_key_notes = {0, 2, 4, 5, 7, 9, 11}, {1, 3, 6, 8, 10}
        low_pitch, high_pitch = self.visible_range
        
        # Draw keys
        for pitch in range(low_pitch, high_pitch + 1):
            y = (high_pitch - pitch) * self.note_height
            note_class = pitch % 12
            if note_class in white_key_notes:
                brush = QBrush(QColor(255, 255, 255) if pitch % 12 == 0 else QColor(248, 248, 248))
                painter.fillRect(0, int(y), white_key_width, int(self.note_height), brush)
                painter.setPen(QPen(QColor(200, 200, 200)))
                painter.drawRect(0, int(y), white_key_width - 1, int(self.note_height) - 1)
                if pitch % 12 == 0:
                    painter.setPen(Qt.GlobalColor.black)
                    painter.setFont(QFont("Arial", 8))
                    painter.drawText(5, int(y + self.note_height - 5), f"C{pitch // 12 - 1}")
            elif note_class in black_key_notes:
                brush = QBrush(QColor(30, 30, 30))
                painter.fillRect(0, int(y), black_key_width, int(self.note_height), brush)
                painter.setPen(QPen(QColor(100, 100, 100)))
                painter.drawRect(0, int(y), black_key_width - 1, int(self.note_height) - 1)

class PianoRollWidget(QGraphicsView):
    """Enhanced piano roll widget with pretty_midi integration."""
    note_added = pyqtSignal(MidiNote)
    note_removed = pyqtSignal(MidiNote)
    selection_changed = pyqtSignal()

    def __init__(self, document: MidiDocument, settings: AppSettings, parent=None):
        super().__init__(parent)
        self.document, self.settings = document, settings
        self.current_track_index, self.current_tool = 0, "pencil"
        self.note_height, self.seconds_per_pixel = 20, 0.1
        self.lowest_pitch, self.highest_pitch = 12, 127
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setMouseTracking(True)
        self.note_items: Dict[MidiNote, NoteItem] = {}
        self.setup_scene()
        self.refresh_notes()

    def setup_scene(self):
        scene_height = (self.highest_pitch - self.lowest_pitch + 1) * self.note_height
        scene_width = 32 / self.seconds_per_pixel
        self.scene.setSceneRect(0, 0, scene_width, scene_height)
        self.draw_grid()

    def draw_grid(self):
        for item in self.scene.items():
            if item.zValue() in [-1, -2]: self.scene.removeItem(item)
        scene_rect = self.scene.sceneRect()
        
        # Vertical lines (time grid)
        tempo_bpm = self.document.tempo_bpm
        seconds_per_beat = 60.0 / tempo_bpm
        seconds_per_measure = seconds_per_beat * self.document.time_signature[0]
        pen_measure = QPen(QColor(150, 150, 150), 2)
        pen_beat = QPen(QColor(200, 200, 200), 1)
        pen_subdivision = QPen(QColor(230, 230, 230), 1)
        for x in range(int(scene_rect.width())):
            time_seconds = x * self.seconds_per_pixel
            pen = pen_measure if abs(time_seconds % seconds_per_measure) < 1e-6 else \
                  pen_beat if abs(time_seconds % seconds_per_beat) < 1e-6 else \
                  pen_subdivision if abs(time_seconds % (seconds_per_beat / 4)) < 1e-6 else None
            if pen: self.scene.addLine(x, 0, x, scene_rect.height(), pen).setZValue(-2)

        # Horizontal lines (pitch grid)
        pen_octave = QPen(QColor(180, 180, 180), 1)
        pen_note = QPen(QColor(240, 240, 240), 1)
        for pitch in range(self.lowest_pitch, self.highest_pitch + 1):
            y = (self.highest_pitch - pitch) * self.note_height
            pen = pen_octave if pitch % 12 == 0 else pen_note
            self.scene.addLine(0, y, scene_rect.width(), y, pen).setZValue(-1)

    def get_current_track(self):
        return self.document.tracks[self.current_track_index] if 0 <= self.current_track_index < len(self.document.tracks) else None

    def set_current_track(self, index: int):
        self.current_track_index = index
        self.refresh_notes()

    def refresh_notes(self):
        for note_item in self.note_items.values(): self.scene.removeItem(note_item)
        self.note_items.clear()
        current_track = self.get_current_track()
        if current_track:
            for note in current_track.notes:
                note_item = NoteItem(note, self.note_height, self.seconds_per_pixel)
                self.scene.addItem(note_item)
                self.note_items[note] = note_item
    
    def mousePressEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        time, pitch = self._scene_to_time_and_pitch(scene_pos)
        if event.button() == Qt.MouseButton.LeftButton:
            if self.current_tool == "pencil": self._add_note_at(time, pitch)
            elif self.current_tool == "erase": self._remove_note_at(scene_pos)
            else: super().mousePressEvent(event)
        else: super().mousePressEvent(event)

    def _scene_to_time_and_pitch(self, scene_pos: QPointF) -> Tuple[float, int]:
        time = scene_pos.x() * self.seconds_per_pixel
        pitch = self.highest_pitch - int(scene_pos.y() / self.note_height)
        return time, max(0, min(127, pitch))

    def _add_note_at(self, time: float, pitch: int):
        track = self.get_current_track()
        if not track or any(note.pitch == pitch and note.start <= time < note.end for note in track.notes):
            return
        default_duration = 60.0 / (self.document.tempo_bpm * 4)
        new_note = MidiNote(time, time + default_duration, pitch, self.settings.default_velocity)
        track.add_note(new_note)
        self.refresh_notes()
        self.document.modified = True
        self.note_added.emit(new_note)

    def _remove_note_at(self, scene_pos: QPointF):
        item = self.scene.itemAt(scene_pos, self.transform())
        if isinstance(item, NoteItem) and self.get_current_track().remove_note(item.midi_note):
            self.refresh_notes()
            self.document.modified = True
            self.note_removed.emit(item.midi_note)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace): self.delete_selected_notes()
        elif event.key() == Qt.Key.Key_A and event.modifiers() & Qt.KeyboardModifier.ControlModifier: self.select_all_notes()
        elif event.key() == Qt.Key.Key_Escape: self.clear_selection()
        else: super().keyPressEvent(event)
    
    def delete_selected_notes(self):
        track = self.get_current_track()
        if not track: return
        notes_to_delete = [note for note in track.notes if note.selected]
        for note in notes_to_delete: track.remove_note(note)
        if notes_to_delete: self.refresh_notes(); self.document.modified = True; self.selection_changed.emit()

    def select_all_notes(self):
        for item in self.note_items.values(): item.setSelected(True)
        self.selection_changed.emit()

    def clear_selection(self):
        for item in self.note_items.values(): item.setSelected(False)
        self.selection_changed.emit()
    
    def quantize_selected_notes(self, grid_size_seconds: Optional[float] = None):
        track = self.get_current_track()
        if track:
            grid_size = grid_size_seconds or 60.0 / (self.document.tempo_bpm * 4)
            track.quantize_notes(grid_size, strength=1.0, selected_only=True)
            self.refresh_notes(); self.document.modified = True
    
    def document_changed(self):
        self.refresh_notes()
        max_time = self.document.get_time_bounds()[1]
        required_width = (max_time / self.seconds_per_pixel) + 1000 if max_time > 0 else 0
        if required_width > self.scene.width():
            self.scene.setSceneRect(0, 0, required_width, self.scene.height())
            self.draw_grid()

class PianoRollPanel(QWidget):
    """Container panel for the piano roll and its controls."""
    def __init__(self, document: MidiDocument, settings: AppSettings, parent=None):
        super().__init__(parent)
        self.document, self.settings = document, settings
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        controls = self._create_controls()
        layout.addWidget(controls)
        main_area = QHBoxLayout()
        self.keyboard = PianoKeyboard(note_height=20, visible_range=(12, 127), parent=self)
        self.piano_roll = PianoRollWidget(self.document, self.settings, self)
        main_area.addWidget(self.keyboard)
        main_area.addWidget(self.piano_roll, 1)
        main_widget = QWidget()
        main_widget.setLayout(main_area)
        layout.addWidget(main_widget, 1)
    
    def _create_controls(self) -> QWidget:
        controls = QFrame(frameShape=QFrame.Shape.StyledPanel, maximumHeight=80)
        layout = QVBoxLayout(controls)
        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("Track:")); self.track_combo = QComboBox(); top_row.addWidget(self.track_combo)
        top_row.addWidget(QLabel("Tempo:")); self.tempo_label = QLabel(f"{self.document.tempo_bpm:.1f} BPM"); self.tempo_label.setStyleSheet("font-weight: bold;"); top_row.addWidget(self.tempo_label)
        top_row.addWidget(QLabel("Key:")); self.key_label = QLabel("Unknown"); self.key_label.setStyleSheet("font-weight: bold;"); top_row.addWidget(self.key_label)
        top_row.addStretch(); layout.addLayout(top_row)
        
        bottom_row = QHBoxLayout()
        bottom_row.addWidget(QLabel("Tool:"))
        self.pencil_btn = QPushButton("✏️ Pencil"); self.pencil_btn.setCheckable(True); self.pencil_btn.setChecked(True); bottom_row.addWidget(self.pencil_btn)
        self.select_btn = QPushButton("🔍 Select"); self.select_btn.setCheckable(True); bottom_row.addWidget(self.select_btn)
        self.erase_btn = QPushButton("🗑️ Erase"); self.erase_btn.setCheckable(True); bottom_row.addWidget(self.erase_btn)
        bottom_row.addWidget(QFrame(frameShape=QFrame.Shape.VLine))
        
        bottom_row.addWidget(QLabel("Quantize:"))
        quantize_16_btn = QPushButton("⏱️ 1/16"); quantize_16_btn.clicked.connect(lambda: self.piano_roll.quantize_selected_notes()); bottom_row.addWidget(quantize_16_btn)
        quantize_8_btn = QPushButton("⏱️ 1/8"); quantize_8_btn.clicked.connect(lambda: self.piano_roll.quantize_selected_notes(60.0 / (self.document.tempo_bpm * 2))); bottom_row.addWidget(quantize_8_btn)
        bottom_row.addWidget(QFrame(frameShape=QFrame.Shape.VLine))
        
        bottom_row.addWidget(QLabel("Velocity:"))
        self.velocity_slider = QSlider(Qt.Orientation.Horizontal, range=(1, 127), value=self.settings.default_velocity, maximumWidth=100)
        bottom_row.addWidget(self.velocity_slider)
        self.velocity_label = QLabel(str(self.settings.default_velocity))
        bottom_row.addWidget(self.velocity_label); bottom_row.addStretch(); layout.addLayout(bottom_row)
        
        self.update_track_combo()
        try: key_root, key_mode = self.document.estimate_key(); self.key_label.setText(f"{key_root} {key_mode}")
        except: self.key_label.setText("Unknown")
        return controls
    
    def connect_signals(self):
        self.track_combo.currentIndexChanged.connect(self.on_track_changed)
        self.pencil_btn.clicked.connect(lambda: self._set_tool("pencil"))
        self.select_btn.clicked.connect(lambda: self._set_tool("select"))
        self.erase_btn.clicked.connect(lambda: self._set_tool("erase"))
        self.velocity_slider.valueChanged.connect(self.on_velocity_changed)
        self.piano_roll.note_added.connect(self.on_note_added)
        self.piano_roll.note_removed.connect(self.on_note_removed)
        self.piano_roll.selection_changed.connect(self.on_selection_changed)

    def update_track_combo(self):
        self.track_combo.clear()
        if not self.document.tracks:
            self.track_combo.addItem("No tracks")
            return
        for i, track in enumerate(self.document.tracks):
            display_name = f"{i+1}: {track.name}{' 🥁' if track.is_drum else ''}"
            self.track_combo.addItem(display_name)
    
    def on_track_changed(self, index: int):
        self.piano_roll.set_current_track(index)
    
    def on_velocity_changed(self, value: int):
        self.velocity_label.setText(str(value))
        self.settings.default_velocity = value
    
    def _set_tool(self, tool_name: str):
        self.piano_roll.current_tool = tool_name
        self.pencil_btn.setChecked(tool_name == "pencil")
        self.select_btn.setChecked(tool_name == "select")
        self.erase_btn.setChecked(tool_name == "erase")
    
    def on_note_added(self, note: MidiNote):
        print(f"Note added: {KEY_NAMES[note.pitch % 12]}{note.pitch // 12 - 1} at {note.start:.2f}s, vel: {note.velocity}")
    
    def on_note_removed(self, note: MidiNote):
        print(f"Note removed: {KEY_NAMES[note.pitch % 12]}{note.pitch // 12 - 1}")
    
    def on_selection_changed(self):
        selected_count = len(self.piano_roll.get_current_track().get_selected_notes())
        print(f"Selection changed: {selected_count} notes selected")

class PianoRollTestWindow(QMainWindow):
    """Test window for the piano roll."""
    def __init__(self):
        super().__init__()
        self.document, self.settings = MidiDocument(), AppSettings()
        self.create_test_data()
        self.init_ui()
    
    def create_test_data(self):
        piano_track, bass_track, drum_track = self.document.add_track(name="Piano", program=0), self.document.add_track(name="Bass", program=32), self.document.add_track(name="Drums", is_drum=True)
        chords = [([60, 64, 67], 0.0, 2.0), ([57, 60, 64], 2.0, 4.0), ([53, 57, 60], 4.0, 6.0), ([55, 59, 62], 6.0, 8.0)]
        for pitches, start, end in chords:
            for pitch in pitches: piano_track.add_note(MidiNote(start=start, end=end, pitch=pitch, velocity=80))
        bass_notes = [(36, 0.0, 0.5), (33, 2.0, 0.5), (29, 4.0, 0.5), (31, 6.0, 0.5)]
        for pitch, start, duration in bass_notes: bass_track.add_note(MidiNote(start=start, end=start + duration, pitch=pitch, velocity=90))
        drum_pattern = [(36, [0.0, 2.0, 4.0, 6.0]), (38, [1.0, 3.0, 5.0, 7.0]), (42, [t * 0.5 for t in range(16)])]
        for pitch, times in drum_pattern:
            for time in times: drum_track.add_note(MidiNote(start=time, end=time + 0.1, pitch=pitch, velocity=70))

    def init_ui(self):
        self.setWindowTitle("MIDI_COMPOSE - Piano Roll")
        self.setGeometry(100, 100, 1600, 900)
        self.piano_roll_panel = PianoRollPanel(self.document, self.settings)
        self.setCentralWidget(self.piano_roll_panel)
        self.create_menus()
        self.statusBar().showMessage("Ready")
    
    def create_menus(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu('File')
        file_menu.addAction(QAction('New', self, shortcut=QKeySequence.StandardKey.New, triggered=self.new_document))
        edit_menu = menubar.addMenu('Edit')
        edit_menu.addAction(QAction('Select All', self, shortcut=QKeySequence.StandardKey.SelectAll, triggered=self.piano_roll_panel.piano_roll.select_all_notes))
        edit_menu.addAction(QAction('Delete Selected', self, shortcut=QKeySequence.StandardKey.Delete, triggered=self.piano_roll_panel.piano_roll.delete_selected_notes))
        analysis_menu = menubar.addMenu('Analysis')
        analysis_menu.addAction(QAction('Analyze Key', self, triggered=self.analyze_key))
        analysis_menu.addAction(QAction('Analyze Tempo', self, triggered=self.analyze_tempo))
    
    def new_document(self):
        self.document = MidiDocument()
        self.piano_roll_panel.document = self.document
        self.piano_roll_panel.piano_roll.document = self.document
        self.piano_roll_panel.update_track_combo()
        self.piano_roll_panel.piano_roll.document_changed()
    
    def analyze_key(self):
        try: key_root, key_mode = self.document.estimate_key(); self.statusBar().showMessage(f"Estimated key: {key_root} {key_mode}"); self.piano_roll_panel.key_label.setText(f"{key_root} {key_mode}")
        except Exception as e: self.statusBar().showMessage(f"Key analysis failed: {e}")
    
    def analyze_tempo(self):
        try: tempo = self.document.tempo_bpm; self.statusBar().showMessage(f"Estimated tempo: {tempo:.1f} BPM"); self.piano_roll_panel.tempo_label.setText(f"{tempo:.1f} BPM")
        except Exception as e: self.statusBar().showMessage(f"Tempo analysis failed: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = PianoRollTestWindow()
    window.show()
    sys.exit(app.exec())