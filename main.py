#!/usr/bin/env python3
"""
MIDI_COMPOSE Application Entry Point
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
