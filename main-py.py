# main.py
import sys
import os
import logging
from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtGui import QPixmap, QIcon
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
from desktop.components.main_window import MainWindow
from desktop.utils.config import load_config


def show_splash_screen():
    """Show a splash screen while the application loads"""
    # Path to splash image
    splash_path = os.path.join(os.path.dirname(__file__), "assets", "splash.png")
    
    # Default splash if file not found
    if not os.path.exists(splash_path):
        # Create a simple colored pixmap for splash
        pixmap = QPixmap(600, 400)
        pixmap.fill(Qt.GlobalColor.white)
        splash = QSplashScreen(pixmap, Qt.WindowType.WindowStaysOnTopHint)
        
        # Add logo text
        splash.showMessage(
            "OpenManus Redo",
            Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom,
            Qt.GlobalColor.darkBlue
        )
    else:
        # Use the actual splash image
        splash_pixmap = QPixmap(splash_path)
        splash = QSplashScreen(splash_pixmap, Qt.WindowType.WindowStaysOnTopHint)
    
    splash.show()
    return splash


def main():
    """Main entry point for the application"""
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("OpenManus Redo")
    app.setOrganizationName("OpenManus")
    
    # Set application icon
    icon_path = os.path.join(os.path.dirname(__file__), "assets", "images", "icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Show splash screen
    splash = show_splash_screen()
    
    # Process events to ensure splash is displayed
    app.processEvents()
    
    # Load configuration
    try:
        config = load_config()
        # Configure app based on loaded settings
        # (This would be expanded as needed)
    except Exception as e:
        logging.error(f"Error loading configuration: {e}")
    
    # Create assets directories if they don't exist
    assets_dir = os.path.join(os.path.dirname(__file__), "assets")
    os.makedirs(os.path.join(assets_dir, "images"), exist_ok=True)
    os.makedirs(os.path.join(assets_dir, "icons"), exist_ok=True)
    
    # Create and show main window after a short delay
    def show_main_window():
        try:
            window = MainWindow()
            window.show()
            if splash:
                splash.finish(window)
        except Exception as e:
            logging.error(f"Error creating main window: {e}")
            if splash:
                splash.close()
    
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
