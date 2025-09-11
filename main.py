#!/usr/bin/env python3
"""
MIDI_COMPOSE (mico) Application Entry Point
Enhanced version with improved dependency management and startup flow
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

# Add current directory to path for module imports
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def check_python_version():
    """Ensure we're running on a compatible Python version"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    logger.info(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} compatible")
    return True

def install_missing_packages():
    """Attempt to install missing packages automatically"""
    import subprocess
    
    packages_to_install = []
    
    # Check and install pretty_midi
    try:
        import pretty_midi
        logger.info("✅ pretty_midi already available")
    except ImportError:
        packages_to_install.append("pretty_midi")
        logger.info("📦 pretty_midi needs to be installed")
    
    # Check and install PyQt6
    try:
        import PyQt6.QtWidgets
        logger.info("✅ PyQt6 already available")
    except ImportError:
        packages_to_install.append("PyQt6")
        logger.info("📦 PyQt6 needs to be installed")
    
    # Check and install numpy
    try:
        import numpy
        logger.info("✅ numpy already available")
    except ImportError:
        packages_to_install.append("numpy")
        logger.info("📦 numpy needs to be installed")
    
    # Check and install scipy
    try:
        import scipy
        logger.info("✅ scipy already available")
    except ImportError:
        packages_to_install.append("scipy")
        logger.info("📦 scipy needs to be installed")
    
    # Check and install matplotlib
    try:
        import matplotlib
        logger.info("✅ matplotlib already available")
    except ImportError:
        packages_to_install.append("matplotlib")
        logger.info("📦 matplotlib needs to be installed")
    
    if packages_to_install:
        print(f"🔧 Installing missing packages: {', '.join(packages_to_install)}")
        print("This may take a moment...")
        
        try:
            # Try to install the packages
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "--user"
            ] + packages_to_install)
            
            print("✅ Installation completed successfully!")
            print("🔄 Restarting application with new packages...")
            
            # Restart the application
            os.execv(sys.executable, ['python'] + sys.argv)
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install packages automatically: {e}")
            print("\n📝 Please install manually:")
            print(f"   pip install {' '.join(packages_to_install)}")
            return False
        except Exception as e:
            print(f"❌ Installation error: {e}")
            print("\n📝 Please install manually:")
            print(f"   pip install {' '.join(packages_to_install)}")
            return False
    
    return True

def check_dependencies():
    """Check that all required dependencies are available"""
    missing = []
    
    try:
        import pretty_midi
        logger.info("✅ pretty_midi loaded successfully")
    except ImportError:
        missing.append("pretty_midi")
        logger.error("❌ pretty_midi not available")
    
    try:
        import numpy
        logger.info("✅ numpy loaded successfully")
    except ImportError:
        missing.append("numpy")
        logger.error("❌ numpy not available")
    
    try:
        import PyQt6.QtWidgets
        import PyQt6.QtCore
        import PyQt6.QtGui
        logger.info("✅ PyQt6 loaded successfully")
    except ImportError:
        missing.append("PyQt6")
        logger.error("❌ PyQt6 not available")
    
    try:
        import scipy
        logger.info("✅ scipy loaded successfully")
    except ImportError:
        missing.append("scipy")
        logger.error("❌ scipy not available")
    
    try:
        import matplotlib
        logger.info("✅ matplotlib loaded successfully")
    except ImportError:
        missing.append("matplotlib")
        logger.error("❌ matplotlib not available")
    
    return missing

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
                self.setWindowTitle("mico - MIDI Compose")
                self.setGeometry(100, 100, 1200, 800)
                
                central_widget = QWidget()
                layout = QVBoxLayout()
                
                label = QLabel("mico MIDI Sequencer\n\nDevelopment Mode\nMain components not yet implemented")
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
    print("🎵 Starting mico - MIDI Compose")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install missing packages if needed
    if not install_missing_packages():
        print("\n❌ Cannot proceed without required packages")
        sys.exit(1)
    
    # Final dependency check
    missing = check_dependencies()
    if missing:
        print(f"\n❌ Missing dependencies: {', '.join(missing)}")
        print("Please install them manually and try again.")
        sys.exit(1)
    
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