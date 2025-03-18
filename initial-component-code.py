# main_window.py
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter, QFrame, QLabel, QStatusBar
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from components.sidebar import Sidebar
from components.command_center import CommandCenter
from components.output_canvas import OutputCanvas
from components.flow_selector import FlowSelector
from theme.style_manager import StyleManager


class OpenManusWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Set up the style manager
        self.style_manager = StyleManager()
        
        # Basic window setup
        self.setWindowTitle("OpenManus Redo")
        self.setMinimumSize(1200, 800)
        
        # Create main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Create sidebar
        self.sidebar = Sidebar(self)
        self.main_layout.addWidget(self.sidebar)
        
        # Create main content area
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        self.main_layout.addWidget(self.content_widget, stretch=1)
        
        # Create top toolbar with flow selector
        self.toolbar = QWidget()
        self.toolbar_layout = QHBoxLayout(self.toolbar)
        self.toolbar.setFixedHeight(60)
        self.toolbar.setObjectName("topToolbar")
        
        # Add flow selector
        self.flow_selector = FlowSelector()
        self.toolbar_layout.addWidget(self.flow_selector)
        self.toolbar_layout.addStretch()
        
        # Add user menu button (placeholder)
        self.user_button = QLabel("User")
        self.user_button.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.user_button.setFixedSize(40, 40)
        self.user_button.setObjectName("userButton")
        self.toolbar_layout.addWidget(self.user_button)
        self.toolbar_layout.setContentsMargins(20, 10, 20, 10)
        
        self.content_layout.addWidget(self.toolbar)
        
        # Create content splitter
        self.content_splitter = QSplitter(Qt.Orientation.Vertical)
        self.content_layout.addWidget(self.content_splitter, stretch=1)
        
        # Create command center
        self.command_center = CommandCenter()
        self.content_splitter.addWidget(self.command_center)
        
        # Create output canvas
        self.output_canvas = OutputCanvas()
        self.content_splitter.addWidget(self.output_canvas)
        
        # Set initial splitter sizes
        self.content_splitter.setSizes([300, 500])
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.status_bar.setObjectName("statusBar")
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Apply styles
        self.apply_styles()
        
    def apply_styles(self):
        """Apply the application styling"""
        self.setStyleSheet(self.style_manager.get_stylesheet())
        
    def toggle_theme(self):
        """Toggle between light and dark theme"""
        self.style_manager.toggle_theme()
        self.apply_styles()


# sidebar.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt


class Sidebar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(220)
        
        # Create layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 20, 10, 20)
        self.layout.setSpacing(20)
        
        # Add logo
        self.logo = QLabel("OpenManus")
        self.logo.setObjectName("sidebarLogo")
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.logo)
        
        # Add navigation buttons
        self.create_nav_buttons()
        
        # Add spacing
        self.layout.addStretch(1)
        
        # Add settings button
        self.settings_button = QPushButton("Settings")
        self.settings_button.setObjectName("sidebarButton")
        self.layout.addWidget(self.settings_button)
        
    def create_nav_buttons(self):
        # Create navigation buttons
        button_names = ["Home", "Sessions", "Templates", "Plugins", "Help"]
        
        for name in button_names:
            button = QPushButton(name)
            button.setObjectName("sidebarButton")
            self.layout.addWidget(button)


# command_center.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, 
    QPushButton, QFrame
)
from PyQt6.QtCore import Qt


class CommandCenter(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("commandCenter")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        
        # Create layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)
        
        # Header
        self.header = QLabel("Command Input")
        self.header.setObjectName("sectionHeader")
        self.layout.addWidget(self.header)
        
        # Text editor
        self.editor = QTextEdit()
        self.editor.setObjectName("commandEditor")
        self.editor.setPlaceholderText("Enter your prompt here...")
        self.layout.addWidget(self.editor, stretch=1)
        
        # Button row
        self.button_row = QWidget()
        self.button_layout = QHBoxLayout(self.button_row)
        self.button_layout.setContentsMargins(0, 0, 0, 0)
        self.button_layout.setSpacing(10)
        
        self.button_layout.addStretch(1)
        
        self.clear_button = QPushButton("Clear")
        self.clear_button.setObjectName("secondaryButton")
        self.clear_button.clicked.connect(self.clear_editor)
        self.button_layout.addWidget(self.clear_button)
        
        self.run_button = QPushButton("Run")
        self.run_button.setObjectName("primaryButton")
        self.button_layout.addWidget(self.run_button)
        
        self.layout.addWidget(self.button_row)
    
    def clear_editor(self):
        self.editor.clear()


# output_canvas.py
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, 
    QPushButton, QTabWidget, QWidget
)


class OutputCanvas(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("outputCanvas")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        
        # Create layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)
        
        # Header row
        self.header_row = QWidget()
        self.header_layout = QHBoxLayout(self.header_row)
        self.header_layout.setContentsMargins(0, 0, 0, 0)
        
        self.header = QLabel("Output")
        self.header.setObjectName("sectionHeader")
        self.header_layout.addWidget(self.header)
        
        self.header_layout.addStretch(1)
        
        self.export_button = QPushButton("Export")
        self.export_button.setObjectName("toolButton")
        self.header_layout.addWidget(self.export_button)
        
        self.layout.addWidget(self.header_row)
        
        # Tab widget for different output views
        self.tabs = QTabWidget()
        self.tabs.setObjectName("outputTabs")
        
        # Text tab
        self.text_tab = QWidget()
        self.text_layout = QVBoxLayout(self.text_tab)
        self.text_output = QTextEdit()
        self.text_output.setObjectName("outputText")
        self.text_output.setReadOnly(True)
        self.text_layout.addWidget(self.text_output)
        self.tabs.addTab(self.text_tab, "Text")
        
        # Data tab
        self.data_tab = QWidget()
        self.data_layout = QVBoxLayout(self.data_tab)
        self.data_label = QLabel("Data visualization will appear here")
        self.data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.data_layout.addWidget(self.data_label)
        self.tabs.addTab(self.data_tab, "Data")
        
        # Visual tab
        self.visual_tab = QWidget()
        self.visual_layout = QVBoxLayout(self.visual_tab)
        self.visual_label = QLabel("Visual output will appear here")
        self.visual_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.visual_layout.addWidget(self.visual_label)
        self.tabs.addTab(self.visual_tab, "Visual")
        
        self.layout.addWidget(self.tabs, stretch=1)


# flow_selector.py
from PyQt6.QtWidgets import QComboBox


class FlowSelector(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("flowSelector")
        self.setMinimumWidth(200)
        
        # Add flow options
        flow_types = ["Planning Flow", "Research Flow", "Creative Flow", "Analysis Flow"]
        self.addItems(flow_types)


# style_manager.py
class StyleManager:
    def __init__(self):
        self.is_dark_mode = False
        self.define_color_schemes()
        
    def define_color_schemes(self):
        # Light mode colors
        self.light = {
            "background": "#ffffff",
            "surface": "#f8f9fc",
            "sidebar": "#f5f7fa",
            "primary": "#4a76f5",
            "secondary": "#6e7891",
            "text": "#3a3f51",
            "textLight": "#6e7891",
            "border": "#e1e4e8",
            "success": "#28c840",
            "warning": "#febc2e",
            "error": "#ff5f57"
        }
        
        # Dark mode colors
        self.dark = {
            "background": "#1e2233",
            "surface": "#252a3d",
            "sidebar": "#1a1f2e",
            "primary": "#5d8afe",
            "secondary": "#8e99b7",
            "text": "#ffffff",
            "textLight": "#b4bdce",
            "border": "#323a54",
            "success": "#30d649",
            "warning": "#ffca3a",
            "error": "#ff6b6b"
        }
    
    def get_colors(self):
        """Get the current color scheme"""
        return self.dark if self.is_dark_mode else self.light
    
    def toggle_theme(self):
        """Toggle between light and dark mode"""
        self.is_dark_mode = not self.is_dark_mode
    
    def get_stylesheet(self):
        """Generate the application stylesheet based on current theme"""
        colors = self.get_colors()
        
        return f"""
            /* Global styles */
            QWidget {{
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-size: 14px;
                color: {colors["text"]};
                background-color: {colors["background"]};
            }}
            
            /* Main window */
            QMainWindow {{
                background-color: {colors["background"]};
            }}
            
            /* Sidebar */
            #sidebar {{
                background-color: {colors["sidebar"]};
                border-right: 1px solid {colors["border"]};
            }}
            
            #sidebarLogo {{
                font-size: 18px;
                font-weight: bold;
                color: {colors["primary"]};
                padding: 10px;
            }}
            
            #sidebarButton {{
                background-color: transparent;
                border: none;
                border-radius: 6px;
                padding: 10px;
                text-align: left;
            }}
            
            #sidebarButton:hover {{
                background-color: {colors["surface"]};
            }}
            
            /* Top toolbar */
            #topToolbar {{
                background-color: {colors["background"]};
                border-bottom: 1px solid {colors["border"]};
            }}
            
            #userButton {{
                background-color: {colors["surface"]};
                border-radius: 20px;
            }}
            
            /* Flow selector */
            #flowSelector {{
                background-color: {colors["surface"]};
                border: 1px solid {colors["border"]};
                border-radius: 6px;
                padding: 6px;
                selection-background-color: {colors["primary"]};
            }}
            
            #flowSelector::drop-down {{
                border: none;
                width: 20px;
            }}
            
            /* Command center */
            #commandCenter {{
                background-color: {colors["background"]};
                border: 1px solid {colors["border"]};
                border-radius: 8px;
            }}
            
            #commandEditor {{
                background-color: {colors["surface"]};
                border: 1px solid {colors["border"]};
                border-radius: 6px;
                padding: 10px;
                selection-background-color: {colors["primary"]};
                selection-color: white;
            }}
            
            /* Output canvas */
            #outputCanvas {{
                background-color: {colors["background"]};
                border: 1px solid {colors["border"]};
                border-radius: 8px;
            }}
            
            #outputText {{
                background-color: {colors["surface"]};
                border: 1px solid {colors["border"]};
                border-radius: 6px;
                padding: 10px;
                selection-background-color: {colors["primary"]};
                selection-color: white;
            }}
            
            #outputTabs {{
                background-color: {colors["background"]};
            }}
            
            #outputTabs::pane {{
                border: 1px solid {colors["border"]};
                border-radius: 6px;
                top: -1px;
            }}
            
            #outputTabs::tab-bar {{
                alignment: left;
            }}
            
            #outputTabs QTabBar::tab {{
                background-color: {colors["surface"]};
                border: 1px solid {colors["border"]};
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 8px 16px;
                margin-right: 4px;
            }}
            
            #outputTabs QTabBar::tab:selected {{
                background-color: {colors["background"]};
                border-bottom: 1px solid {colors["background"]};
            }}
            
            /* Buttons */
            #primaryButton {{
                background-color: {colors["primary"]};
                color: white;
                border: none;
                border-radius: 18px;
                padding: 8px 24px;
                font-weight: bold;
            }}
            
            #primaryButton:hover {{
                background-color: {colors["primary"] + "dd"};
            }}
            
            #primaryButton:pressed {{
                background-color: {colors["primary"] + "aa"};
            }}
            
            #secondaryButton {{
                background-color: transparent;
                color: {colors["text"]};
                border: 1px solid {colors["border"]};
                border-radius: 18px;
                padding: 8px 24px;
            }}
            
            #secondaryButton:hover {{
                background-color: {colors["surface"]};
            }}
            
            #secondaryButton:pressed {{
                background-color: {colors["border"]};
            }}
            
            #toolButton {{
                background-color: transparent;
                color: {colors["secondary"]};
                border: 1px solid {colors["border"]};
                border-radius: 4px;
                padding: 4px 8px;
            }}
            
            #toolButton:hover {{
                background-color: {colors["surface"]};
            }}
            
            /* Headers */
            #sectionHeader {{
                font-size: 16px;
                font-weight: bold;
                color: {colors["text"]};
            }}
            
            /* Status bar */
            #statusBar {{
                background-color: {colors["sidebar"]};
                color: {colors["textLight"]};
                border-top: 1px solid {colors["border"]};
            }}
            
            /* Splitter */
            QSplitter::handle {{
                background-color: {colors["border"]};
                height: 1px;
            }}
            
            QSplitter::handle:hover {{
                background-color: {colors["primary"]};
            }}
        """


# app.py (main entry point)
import sys
from PyQt6.QtWidgets import QApplication
from main_window import OpenManusWindow

def main():
    app = QApplication(sys.argv)
    window = OpenManusWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
