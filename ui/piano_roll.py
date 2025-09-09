import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsSimpleTextItem)
from PyQt6.QtGui import QBrush, QPen, QColor, QFont
from PyQt6.QtCore import Qt, QRectF

class PianoRollWidget(QGraphicsView):
    """A simple, interactive piano roll widget."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QGraphicsView.RenderHint.Antialiasing)
        
        self.note_height = 20
        self.note_width_mult = 100
        self.notes_in_octave = 12
        self.visible_octaves = 2
        
        # Note mapping (C, C#, D, etc.)
        self.note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

        self.setup_ui()
        self.draw_piano_keyboard()

    def setup_ui(self):
        """Sets up the basic structure and layout."""
        self.setMouseTracking(True)
        # Set a fixed size for the scene
        scene_width = 1200
        scene_height = self.note_height * self.notes_in_octave * self.visible_octaves
        self.scene.setSceneRect(0, 0, scene_width, scene_height)

        # Draw the grid background
        self.draw_grid()

    def draw_piano_keyboard(self):
        """Draws the fixed vertical piano keyboard on the left side."""
        keyboard_width = 80
        black_key_width = keyboard_width * 0.6
        white_key_indices = [0, 2, 4, 5, 7, 9, 11]
        
        # Calculate the starting pitch to match a standard C3 to C5 range
        start_pitch = 60 - (self.notes_in_octave * self.visible_octaves) + 12 # Start at C3 (MIDI 60) for 2 octaves

        for i in range(self.notes_in_octave * self.visible_octaves):
            pitch = start_pitch + (self.notes_in_octave * self.visible_octaves - 1 - i)
            note_name = self.note_names[pitch % self.notes_in_octave]
            
            x = 0
            y = i * self.note_height
            
            # Draw keys
            is_black_key = note_name.endswith('#')
            if is_black_key:
                brush = QBrush(QColor(40, 40, 40))
                key_rect = QRectF(x, y, black_key_width, self.note_height)
            else:
                brush = QBrush(QColor(240, 240, 240))
                key_rect = QRectF(x, y, keyboard_width, self.note_height)

            key_item = self.scene.addRect(key_rect, QPen(Qt.GlobalColor.black, 1), brush)
            key_item.setZValue(1) # Bring keyboard to the front

            # Add note name text
            text_item = QGraphicsSimpleTextItem(note_name)
            font = QFont("Arial", 8)
            text_item.setFont(font)
            text_item.setPos(x + 5, y + 2)
            if is_black_key:
                text_item.setBrush(QBrush(Qt.GlobalColor.white))
            self.scene.addItem(text_item)
            text_item.setZValue(2)

    def draw_grid(self):
        """Draws the grid lines for the piano roll notes."""
        pen = QPen(QColor(200, 200, 200))
        pen.setWidth(1)
        
        # Vertical lines (beats)
        num_beats = 16
        for i in range(num_beats):
            line = self.scene.addLine(i * self.note_width_mult, 0, i * self.note_width_mult, self.scene.height(), pen)
            
        # Horizontal lines (notes)
        pen.setStyle(Qt.PenStyle.DotLine)
        for i in range(self.notes_in_octave * self.visible_octaves):
            line = self.scene.addLine(0, i * self.note_height, self.scene.width(), i * self.note_height, pen)
    
    def mousePressEvent(self, event):
        """Adds a new note at the clicked position."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Map the mouse position from view coordinates to scene coordinates
            scene_pos = self.mapToScene(event.pos())
            
            # Calculate grid position
            grid_x = int(scene_pos.x() / self.note_width_mult) * self.note_width_mult
            grid_y = int(scene_pos.y() / self.note_height) * self.note_height
            
            if grid_x < 80: # Avoid placing notes on the keyboard part
                return

            # Create a new note item
            note_rect = QRectF(grid_x, grid_y, self.note_width_mult, self.note_height)
            note_item = QGraphicsRectItem(note_rect)
            note_item.setBrush(QBrush(QColor(74, 144, 226, 200))) # Blue with transparency
            note_item.setPen(QPen(QColor(50, 100, 180)))
            self.scene.addItem(note_item)

            print(f"Added note at x:{grid_x}, y:{grid_y}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simple Piano Roll Example")
        self.setGeometry(100, 100, 1000, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        
        # Create and add the piano roll widget
        self.piano_roll = PianoRollWidget()
        layout.addWidget(self.piano_roll)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
