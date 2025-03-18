# main.py
import sys
import os
import logging
from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QTimer

# Set up logging before importing other modules
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='openmanus_redo.log'
)

# Add parent directory to path to find OpenManus modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import desktop application modules
from desktop.components.main_window import OpenManusWindow
from desktop.utils.config import load_config


def show_splash_screen():
    """Show a splash screen while the application loads"""
    splash_pixmap = QPixmap("assets/splash.png")
    if not splash_pixmap.isNull():
        splash = QSplashScreen(splash_pixmap, Qt.WindowType.WindowStaysOnTopHint)
        splash.setMask(splash_pixmap.mask())
        splash.show()
        return splash
    return None


def main():
    """Main entry point for the application"""
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("OpenManus Redo")
    
    # Show splash screen
    splash = show_splash_screen()
    
    # Load configuration
    config = load_config()
    
    # Create and show main window after a short delay
    def show_main_window():
        window = OpenManusWindow()
        window.show()
        if splash:
            splash.finish(window)
    
    if splash:
        # Show splash for at least 1.5 seconds
        QTimer.singleShot(1500, show_main_window)
    else:
        # No splash, show window immediately
        show_main_window()
    
    # Start the event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
