#!/usr/bin/env python3
"""
MIDI_COMPOSE Application Entry Point
Enhanced version with proper dependency management and error handling
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

# Dependency availability flags
DEPENDENCIES = {
    'PyQt6': False,
    'pretty_midi': False,
    'numpy': False,
    'core_modules': False,
    'ui_modules': False
}

def check_dependencies():
    """Check and report on dependency availability"""
    logger.info("Checking dependencies...")
    
    # Check PyQt6
    try:
        import PyQt6.QtWidgets
        import PyQt6.QtCore
        import PyQt6.QtGui
        DEPENDENCIES['PyQt6'] = True
        logger.info("✅ PyQt6 successfully loaded")
    except ImportError as e:
        logger.warning(f"❌ PyQt6 not available: {e}")
        logger.info("Install PyQt6 for full GUI: pip install PyQt6")

    # Check pretty_midi and numpy
    try:
        import pretty_midi
        import numpy
        DEPENDENCIES['pretty_midi'] = True
        DEPENDENCIES['numpy'] = True
        logger.info("✅ pretty_midi and numpy successfully loaded")
    except ImportError as e:
        logger.warning(f"❌ pretty_midi/numpy not available: {e}")
        logger.info("Install with: pip install pretty_midi numpy")

    # Check core modules
    try:
        from core.midi_data import MidiDocument, MidiTrack, MidiNote
        from config.settings import AppSettings
        DEPENDENCIES['core_modules'] = True
        logger.info("✅ Core modules successfully loaded")
    except ImportError as e:
        logger.error(f"❌ Core modules not available: {e}")

    # Check UI modules
    try:
        from ui.piano_roll import PianoRollPanel
        DEPENDENCIES['ui_modules'] = True
        logger.info("✅ UI modules successfully loaded")
    except ImportError as e:
        logger.warning(f"❌ UI modules not available: {e}")

    return DEPENDENCIES

def print_dependency_status():
    """Print human-readable dependency status"""
    print("🎼 MIDI_COMPOSE - Dependency Status")
    print("=" * 50)
    
    for dep_name, available in DEPENDENCIES.items():
        status = "✅ Available" if available else "❌ Missing"
        print(f"• {dep_name}: {status}")
    
    print()
    
    if not DEPENDENCIES['PyQt6']:
        print("📝 To install missing GUI dependencies:")
        print("   pip install PyQt6")
    
    if not DEPENDENCIES['pretty_midi']:
        print("📝 To install missing MIDI dependencies:")
        print("   pip install pretty_midi numpy")
    
    print()

def create_console_application():
    """Create a minimal console-based application"""
    logger.info("Starting console mode...")
    
    if not DEPENDENCIES['core_modules']:
        print("❌ Cannot start console mode - core modules missing")
        return 1
    
    try:
        from core.application import MidiApplication
        
        print("🎼 MIDI_COMPOSE - Console Mode")
        print("Core MIDI functionality available")
        
        # Test basic functionality
        app = MidiApplication()
        print(f"✅ Application initialized successfully")
        print("Console mode ready (limited functionality)")
        
        return 0
        
    except ImportError:
        # Fallback if application module isn't available
        from core.midi_data import MidiDocument
        
        print("🎼 MIDI_COMPOSE - Console Mode (Basic)")  
        print("Testing core MIDI functionality...")
        
        doc = MidiDocument()
        track = doc.add_track()
        track.name = "Test Track"
        
        print(f"✅ Created document with {len(doc.tracks)} track(s)")
        print("Basic console mode ready")
        
        return 0
        
    except Exception as e:
        logger.error(f"Console mode failed: {e}")
        return 1

def create_gui_application():
    """Create the full GUI application"""
    if not DEPENDENCIES['PyQt6']:
        logger.error("Cannot start GUI mode - PyQt6 not available")
        return 1
    
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QIcon
        from ui.main_window_enhanced import EnhancedMainWindow
        
        logger.info("Starting GUI mode...")
        
        # Create QApplication
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        
        # Set application properties
        app.setApplicationName("MIDI_COMPOSE")
        app.setApplicationVersion("2.1.0")
        app.setOrganizationName("MIDI_COMPOSE")
        
        # Try to set application icon
        icon_path = PROJECT_ROOT / "assets" / "favicon.ico"
        if icon_path.exists():
            app.setWindowIcon(QIcon(str(icon_path)))
        
        # Create main window
        window = EnhancedMainWindow(DEPENDENCIES)
        window.show()
        
        logger.info("✅ GUI application started successfully")
        print_feature_summary()
        
        return app.exec()
        
    except Exception as e:
        logger.error(f"GUI application failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

def print_feature_summary():
    """Print summary of available features"""
    print("🚀 Available Features:")
    print(f"  • Piano Roll: {'Yes' if DEPENDENCIES['ui_modules'] else 'No'}")
    print(f"  • MIDI I/O: {'Yes' if DEPENDENCIES['pretty_midi'] else 'No'}")
    print(f"  • Analysis: {'Yes' if DEPENDENCIES['pretty_midi'] and DEPENDENCIES['core_modules'] else 'No'}")
    print()

def show_help():
    """Show help information"""
    print("""
🎼 MIDI_COMPOSE - Musical MIDI Sequencer

Usage: python main.py [options]

Options:
  -h, --help     Show this help message
  -c, --console  Force console mode (no GUI)
  -v, --verbose  Enable verbose logging
  --check-deps   Only check dependencies and exit

Features:
  • Real-time MIDI editing with piano roll interface
  • Advanced music analysis (key detection, harmony analysis)
  • MusicDNA - unique musical blueprint generation
  • VST instrument support
  • Advanced velocity editing with mathematical curves

Dependencies:
  • PyQt6: GUI interface
  • pretty_midi: MIDI file processing
  • numpy: Mathematical operations

For more information, visit the project documentation.
    """)

def main():
    """Main application entry point with proper error handling"""
    # Parse command line arguments
    args = sys.argv[1:]
    
    if '-h' in args or '--help' in args:
        show_help()
        return 0
    
    if '-v' in args or '--verbose' in args:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")
    
    # Check dependencies
    check_dependencies()
    
    if '--check-deps' in args:
        print_dependency_status()
        return 0
    
    print_dependency_status()
    
    # Determine run mode
    force_console = '-c' in args or '--console' in args
    
    if force_console or not DEPENDENCIES['PyQt6']:
        if force_console:
            logger.info("Console mode forced by user")
        else:
            logger.info("GUI not available, falling back to console mode")
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
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)