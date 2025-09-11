#!/usr/bin/env python3
"""
MICO - MIDI Compose Application Entry Point
Simple dependency checking and application startup
"""
import sys
import os
import logging
import subprocess
from pathlib import Path

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def check_python_version():
    """Check Python version compatibility"""
    if sys.version_info < (3, 8):
        print(f"Python 3.8+ required. Current: {sys.version_info.major}.{sys.version_info.minor}")
        return False
    return True

def check_dependencies():
    """Check for required packages"""
    required = ['PyQt6', 'numpy', 'pretty_midi', 'scipy', 'matplotlib']
    missing = []
    
    for pkg in required:
        try:
            if pkg == 'PyQt6':
                import PyQt6.QtWidgets
            else:
                __import__(pkg)
            logger.info(f"✅ {pkg}")
        except ImportError:
            missing.append(pkg)
            logger.warning(f"❌ {pkg} missing")
    
    return missing

def install_packages(packages):
    """Auto-install missing packages"""
    print(f"Installing: {', '.join(packages)}")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--user"
        ] + packages)
        print("✅ Installation complete")
        # Restart application
        os.execv(sys.executable, ['python'] + sys.argv)
    except subprocess.CalledProcessError as e:
        print(f"❌ Install failed: {e}")
        print(f"Manual install: pip install {' '.join(packages)}")
        return False
    return True

class MidiEditor:
    """Main MICO application window"""
    def __init__(self):
        from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                                   QHBoxLayout, QPushButton, QFileDialog,
                                   QMenuBar, QStatusBar, QSplitter)
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QAction
        
        self.window = QMainWindow()
        self.window.setWindowTitle("MICO - MIDI Compose")
        self.window.setGeometry(100, 100, 1200, 800)
        
        # Create menu bar
        self.setup_menu()
        
        # Main layout with splitter
        central_widget = QWidget()
        self.window.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Piano roll area (left side - main area)
        self.piano_roll = self.create_piano_roll()
        splitter.addWidget(self.piano_roll)
        
        # Velocity editor (right side)
        self.velocity_editor = self.create_velocity_editor()
        splitter.addWidget(self.velocity_editor)
        
        # Set splitter proportions (80% piano roll, 20% velocity editor)
        splitter.setSizes([800, 200])
        
        main_layout.addWidget(splitter)
        
        # Status bar
        self.window.setStatusBar(QStatusBar())
        self.window.statusBar().showMessage("Ready")
        
        # Initialize MIDI data
        self.current_midi = None
        self.suggestions_enabled = True
    
    def setup_menu(self):
        """Create application menu"""
        from PyQt6.QtGui import QAction
        
        menubar = self.window.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        open_action = QAction('Open MIDI...', self.window)
        open_action.triggered.connect(self.open_midi_file)
        file_menu.addAction(open_action)
        
        save_action = QAction('Save', self.window)
        save_action.triggered.connect(self.save_midi_file)
        file_menu.addAction(save_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('Tools')
        
        suggestions_action = QAction('Toggle Suggestions', self.window)
        suggestions_action.setCheckable(True)
        suggestions_action.setChecked(True)
        suggestions_action.triggered.connect(self.toggle_suggestions)
        tools_menu.addAction(suggestions_action)
    
    def create_piano_roll(self):
        """Create the piano roll widget"""
        from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Placeholder for now
        label = QLabel("Piano Roll Area")
        label.setStyleSheet("border: 2px dashed #ccc; padding: 20px;")
        layout.addWidget(label)
        
        return widget
    
    def create_velocity_editor(self):
        """Create the velocity editor panel"""
        from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Placeholder for now
        label = QLabel("Velocity Editor")
        label.setStyleSheet("border: 2px dashed #ccc; padding: 20px;")
        layout.addWidget(label)
        
        return widget
    
    def open_midi_file(self):
        """Open MIDI file dialog"""
        from PyQt6.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getOpenFileName(
            self.window, "Open MIDI File", "", "MIDI Files (*.mid *.midi)"
        )
        if filename:
            try:
                import pretty_midi
                self.current_midi = pretty_midi.PrettyMIDI(filename)
                self.window.statusBar().showMessage(f"Loaded: {filename}")
                logger.info(f"Loaded MIDI file: {filename}")
            except Exception as e:
                self.window.statusBar().showMessage(f"Error loading file: {e}")
                logger.error(f"Failed to load MIDI: {e}")
    
    def save_midi_file(self):
        """Save current MIDI data"""
        if not self.current_midi:
            self.window.statusBar().showMessage("No MIDI data to save")
            return
        
        from PyQt6.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getSaveFileName(
            self.window, "Save MIDI File", "", "MIDI Files (*.mid)"
        )
        if filename:
            try:
                self.current_midi.write(filename)
                self.window.statusBar().showMessage(f"Saved: {filename}")
                logger.info(f"Saved MIDI file: {filename}")
            except Exception as e:
                self.window.statusBar().showMessage(f"Error saving file: {e}")
                logger.error(f"Failed to save MIDI: {e}")
    
    def toggle_suggestions(self, checked):
        """Toggle real-time suggestions on/off"""
        self.suggestions_enabled = checked
        status = "enabled" if checked else "disabled"
        self.window.statusBar().showMessage(f"Suggestions {status}")
        logger.info(f"Suggestions {status}")
    
    def show(self):
        """Show the main window"""
        self.window.show()

def start_application():
    """Initialize and start MICO"""
    try:
        from PyQt6.QtWidgets import QApplication
        
        app = QApplication(sys.argv)
        app.setApplicationName("MICO")
        app.setApplicationVersion("1.0")
        
        editor = MidiEditor()
        editor.show()
        
        logger.info("🎵 MICO started successfully")
        return app.exec()
        
    except Exception as e:
        logger.error(f"Application startup error: {e}")
        return 1

def main():
    """Main entry point"""
    print("🎵 MICO - MIDI Compose")
    
    if not check_python_version():
        return 1
    
    missing = check_dependencies()
    if missing:
        print("\n📦 Missing dependencies detected")
        install_packages(missing)
        return 1
    
    return start_application()

if __name__ == "__main__":
    sys.exit(main())