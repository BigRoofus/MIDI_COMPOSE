#!/usr/bin/env python3
"""
MIDI_COMPOSE (mico) Application Entry Point
"""
import sys
import os
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def create_application():
    """Create and configure the Qt application"""
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QIcon
    
    # Enable high DPI support
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    app.setApplicationName("mico")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("MIDI_COMPOSE")
    
    # Set application icon if available
    icon_path = PROJECT_ROOT / "resources" / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    return app

def create_main_window():
    """Create and configure the main application window"""
    try:
        from midi_editor import MidiEditorMainWindow
        main_window = MidiEditorMainWindow()
        return main_window
    except ImportError as e:
        logger.error(f"Failed to import main window: {e}")
        # Fallback to basic window for development
        from PyQt6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget
        
        class FallbackWindow(QMainWindow):
            def __init__(self):
                super().__init__()
                self.setWindowTitle("mico")
                self.setGeometry(100, 100, 1200, 800)
                
                central_widget = QWidget()
                layout = QVBoxLayout()
                
                label = QLabel("mico\n\nDevelopment Mode\nMain components not yet implemented")
                label.setStyleSheet("font-size: 18px; text-align: center; padding: 50px;")
                
                layout.addWidget(label)
                central_widget.setLayout(layout)
                self.setCentralWidget(central_widget)
        
        return FallbackWindow()

def setup_exception_handling():
    """Setup global exception handling"""
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
        
        # Show error dialog if Qt is available
        try:
            from PyQt6.QtWidgets import QMessageBox, QApplication
            if QApplication.instance():
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Icon.Critical)
                msg.setWindowTitle("Application Error")
                msg.setText(f"An unexpected error occurred:\n\n{exc_type.__name__}: {exc_value}")
                msg.setDetailedText(f"Exception traceback:\n{''.join(traceback.format_tb(exc_traceback))}")
                msg.exec()
        except ImportError:
            pass
    
    import traceback
    sys.excepthook = handle_exception

def main():
    """Main application entry point"""
    print("mico is starting up...")
    print("=" * 40)
    
    # Setup exception handling
    setup_exception_handling()
    
    try:
        # Create Qt application
        logger.info("Creating Qt application...")
        app = create_application()
        
        # Create main window
        logger.info("Creating main window...")
        main_window = create_main_window()
        
        # Show main window
        main_window.show()
        
        # Center window on screen
        screen = app.primaryScreen().availableGeometry()
        window_geometry = main_window.geometry()
        x = (screen.width() - window_geometry.width()) // 2
        y = (screen.height() - window_geometry.height()) // 2
        main_window.move(x, y)
        
        logger.info("✅ Application started successfully")
        print("🚀 mico is ready!")
        
        # Start the event loop
        return app.exec()
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        print(f"❌ Startup failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)