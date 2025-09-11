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

def start_application():
    """Initialize and start MICO"""
    try:
        from midi_editor import MidiEditor
        from PyQt6.QtWidgets import QApplication
        
        app = QApplication(sys.argv)
        app.setApplicationName("MICO")
        app.setApplicationVersion("1.0")
        
        editor = MidiEditor()
        editor.show()
        
        logger.info("🎵 MICO started successfully")
        return app.exec()
        
    except ImportError as e:
        logger.error(f"Failed to import application modules: {e}")
        return 1
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