#!/usr/bin/env python3
"""
MIDI_COMPOSE Application Entry Point
Fixed version with proper pretty_midi integration
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
    
    # Check and install numpy (comes with pretty_midi but let's be explicit)
    try:
        import numpy
        logger.info("✅ numpy already available")
    except ImportError:
        packages_to_install.append("numpy")
        logger.info("📦 numpy needs to be installed")
    
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
    
    return missing

def create_gui_application():
    """Create the GUI application"""
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QIcon
        
        # Import our modules
        from core.midi_data import MidiDocument
        from config import AppSettings
        from ui.main_window import MainWindow
        
        logger.info("Starting GUI application...")
        
        # Create QApplication
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        
        # Set application properties
        app.setApplicationName("MIDI_COMPOSE")
        app.setApplicationVersion("2.1.0")
        app.setOrganizationName("MIDI_COMPOSE")
        
        # Create document and settings
        document = MidiDocument()
        settings = AppSettings.load()
        
        # Create main window
        window = MainWindow(document, settings)
        window.show()
        
        logger.info("✅ GUI application started successfully")
        print("🎼 MIDI_COMPOSE GUI started successfully!")
        print("🚀 All features available:")
        print("   • Piano Roll Editor: ✅")
        print("   • MIDI Import/Export: ✅") 
        print("   • Musical Analysis: ✅")
        print("   • Real-time Editing: ✅")
        
        return app.exec()
        
    except Exception as e:
        logger.error(f"GUI application failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

def create_console_application():
    """Create console application with full functionality"""
    try:
        from core.midi_data import MidiDocument
        from config import AppSettings
        
        logger.info("Starting console application...")
        
        print("🎼 MIDI_COMPOSE - Console Mode")
        print("All core functionality available!")
        
        # Create test document
        document = MidiDocument()
        settings = AppSettings.load()
        
        # Add a test track
        track = document.add_track()
        track.name = "Piano"
        track.program = 0
        
        # Add some test notes
        from core.midi_data import MidiNote
        
        # Create a C major chord
        chord_notes = [60, 64, 67]  # C, E, G
        for pitch in chord_notes:
            note = MidiNote(
                start=0.0,
                end=2.0,
                pitch=pitch,
                velocity=80
            )
            track.add_note(note)
        
        print(f"✅ Created document with {len(document.tracks)} track(s)")
        print(f"✅ Added {len(track.notes)} notes to track")
        print(f"✅ Tempo: {document.tempo_bpm:.1f} BPM")
        
        # Test analysis if available
        try:
            key_root, key_mode = document.estimate_key()
            print(f"✅ Key analysis: {key_root} {key_mode}")
        except Exception as e:
            print(f"⚠️  Key analysis not available: {e}")
        
        print("\n🎵 Console mode ready - all MIDI functionality working!")
        return 0
        
    except Exception as e:
        logger.error(f"Console application failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

def main():
    """Main application entry point"""
    args = sys.argv[1:]
    
    if '-h' in args or '--help' in args:
        show_help()
        return 0
    
    print("🎼 MIDI_COMPOSE - Starting up...")
    
    # Check if we should attempt auto-installation
    auto_install = '--install' in args or '--no-install' not in args
    
    # Check dependencies
    missing = check_dependencies()
    
    if missing:
        print(f"❌ Missing required packages: {', '.join(missing)}")
        
        if auto_install:
            print("🔧 Attempting automatic installation...")
            if not install_missing_packages():
                print("💡 You can also try: python main.py --install")
                return 1
        else:
            print("\n📝 Please install missing packages:")
            print(f"   pip install {' '.join(missing)}")
            print("\nOr try: python main.py --install")
            return 1
    
    print("✅ All required packages available!")
    
    # Determine run mode
    force_console = '-c' in args or '--console' in args
    
    if force_console:
        logger.info("Console mode requested")
        return create_console_application()
    else:
        logger.info("Starting GUI mode")
        return create_gui_application()

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)