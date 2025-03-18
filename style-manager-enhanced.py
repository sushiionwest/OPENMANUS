# desktop/theme/style_manager.py
import json
import os
from PyQt6.QtCore import QObject, pyqtSignal, QSettings

class StyleManager(QObject):
    """
    Manages application styling and theming with support for 
    light/dark mode and custom color schemes.
    """
    
    # Signal emitted when theme changes
    theme_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.settings = QSettings("OpenManus", "OpenManusRedo")
        self.theme_name = self.settings.value("theme/current", "light")
        self.custom_colors = {}
        self.define_color_schemes()
        self.load_custom_colors()
    
    def define_color_schemes(self):
        """Define the base color schemes for light and dark modes"""
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
            "error": "#ff5f57",
            "cardBg": "#ffffff",
            "inputBg": "#f8f9fc",
            "hover": "#f0f2f5",
            "focus": "#e6f0ff",
            "disabled": "#f0f2f5",
            "disabledText": "#a0a8b8"
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
            "error": "#ff6b6b",
            "cardBg": "#252a3d",
            "inputBg": "#2c324a",
            "hover": "#323a54",
            "focus": "#3a4161",
            "disabled": "#2a304a",
            "disabledText": "#788198"
        }
    
    def load_custom_colors(self):
        """Load any custom color overrides from settings"""
        custom_colors_json = self.settings.value("theme/customColors", "{}")
        try:
            self.custom_colors = json.loads(custom_colors_json)
        except json.JSONDecodeError:
            self.custom_colors = {}
    
    def save_custom_colors(self):
        """Save custom color overrides to settings"""
        self.settings.setValue("theme/customColors", json.dumps(self.custom_colors))
    
    def get_colors(self):
        """Get the current color scheme with any custom overrides applied"""
        base_colors = self.dark if self.theme_name == "dark" else self.light
        
        # Apply any custom color overrides
        colors = base_colors.copy()
        if self.theme_name in self.custom_colors:
            colors.update(self.custom_colors[self.theme_name])
            
        return colors
    
    def set_theme(self, theme_name):
        """Set the current theme by name"""
        if theme_name in ["light", "dark"]:
            self.theme_name = theme_name
            self.settings.setValue("theme/current", theme_name)
            self.theme_changed.emit(theme_name)
    
    def toggle_theme(self):
        """Toggle between light and dark mode"""
        new_theme = "light" if self.theme_name == "dark" else "dark"
        self.set_theme(new_theme)
    
    def set_custom_color(self, color_key, color_value):
        """Set a custom color override for the current theme"""
        if self.theme_name not in self.custom_colors:
            self.custom_colors[self.theme_name] = {}
        
        self.custom_colors[self.theme_name][color_key] = color_value
        self.save_custom_colors()
        self.theme_changed.emit(self.theme_name)
    
    def reset_custom_colors(self):
        """Reset all custom color overrides for the current theme"""
        if self.theme_name in self.custom_colors:
            del self.custom_colors[self.theme_name]
            self.save_custom_colors()
            self.theme_changed.emit(self.theme_name)
    
    def get_font_styles(self):
        """Define font styles for the application"""
        return {
            "default": "font-family: 'Segoe UI', 'Arial', sans-serif; font-size: 14px;",
            "heading1": "font-family: 'Segoe UI', 'Arial', sans-serif; font-size: 24px; font-weight: bold;",
            "heading2": "font-family: 'Segoe UI', 'Arial', sans-serif; font-size: 20px; font-weight: bold;",
            "heading3": "font-family: 'Segoe UI', 'Arial', sans-serif; font-size: 16px; font-weight: bold;",
            "mono": "font-family: 'Consolas', 'Monaco', 'Courier New', monospace; font-size: 14px;",
            "small": "font-family: 'Segoe UI', 'Arial', sans-serif; font-size: 12px;",
        }
    
    def get_stylesheet(self):
        """Generate the application stylesheet based on current theme"""
        colors = self.get_colors()
        fonts = self.get_font_styles()
        
        return f"""
            /* Global styles */
            QWidget {{
                {fonts["default"]}
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
                background-color: {colors["hover"]};
            }}
            
            #sidebarButton:checked {{
                background-color: {colors["primary"] + "30"};
                color: {colors["primary"]};
                font-weight: bold;
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
            
            #userButton:hover {{
                background-color: {colors["hover"]};
            }}
            
            /* Flow selector */
            #flowSelector {{
                background-color: {colors["inputBg"]};
                border: 1px solid {colors["border"]};
                border-radius: 6px;
                padding: 6px 10px;
                color: {colors["text"]};
            }}
            
            #flowSelector::drop-down {{
                border: none;
                width: 20px;
            }}
            
            #flowSelector QAbstractItemView {{
                background-color: {colors["surface"]};
                border: 1px solid {colors["border"]};
                border-radius: 6px;
                selection-background-color: {colors["primary"]};
                selection-color: white;
            }}
            
            /* Command center */
            #commandCenter {{
                background-color: {colors["cardBg"]};
                border: 1px solid {colors["border"]};
                border-radius: 8px;
            }}
            
            #commandEditor {{
                background-color: {colors["inputBg"]};
                border: 1px solid {colors["border"]};
                border-radius: 6px;
                padding: 10px;
                selection-background-color: {colors["primary"]};
                selection-color: white;
                {fonts["mono"]}
            }}
            
            /* Output canvas */
            #outputCanvas {{
                background-color: {colors["cardBg"]};
                border: 1px solid {colors["border"]};
                border-radius: 8px;
            }}
            
            #outputText {{
                background-color: {colors["inputBg"]};
                border: 1px solid {colors["border"]};
                border-radius: 6px;
                padding: 10px;
                selection-background-color: {colors["primary"]};
                selection-color: white;
                {fonts["mono"]}
            }}
            
            #outputTabs {{
                background-color: {colors["cardBg"]};
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
                background-color: {colors["cardBg"]};
                border-bottom: 1px solid {colors["cardBg"]};
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
            
            #primaryButton:disabled {{
                background-color: {colors["disabled"]};
                color: {colors["disabledText"]};
            }}
            
            #secondaryButton {{
                background-color: transparent;
                color: {colors["text"]};
                border: 1px solid {colors["border"]};
                border-radius: 18px;
                padding: 8px 24px;
            }}
            
            #secondaryButton:hover {{
                background-color: {colors["hover"]};
            }}
            
            #secondaryButton:pressed {{
                background-color: {colors["border"]};
            }}
            
            #secondaryButton:disabled {{
                border-color: {colors["disabled"]};
                color: {colors["disabledText"]};
            }}
            
            #toolButton {{
                background-color: transparent;
                color: {colors["secondary"]};
                border: 1px solid {colors["border"]};
                border-radius: 4px;
                padding: 4px 8px;
            }}
            
            #toolButton:hover {{
                background-color: {colors["hover"]};
            }}
            
            #toolButton:pressed {{
                background-color: {colors["border"]};
            }}
            
            /* Headers */
            #sectionHeader {{
                {fonts["heading3"]}
                color: {colors["text"]};
            }}
            
            /* Status indicators */
            #statusIndicator {{
                color: {colors["textLight"]};
                padding: 4px 8px;
                border-radius: 4px;
            }}
            
            #statusProcessing {{
                color: {colors["primary"]};
                background-color: {colors["primary"] + "20"};
                padding: 4px 8px;
                border-radius: 4px;
            }}
            
            #statusSuccess {{
                color: {colors["success"]};
                background-color: {colors["success"] + "20"};
                padding: 4px 8px;
                border-radius: 4px;
            }}
            
            #statusError {{
                color: {colors["error"]};
                background-color: {colors["error"] + "20"};
                padding: 4px 8px;
                border-radius: 4px;
            }}
            
            #statusWarning {{
                color: {colors["warning"]};
                background-color: {colors["warning"] + "20"};
                padding: 4px 8px;
                border-radius: 4px;
            }}
            
            /* Status bar */
            #statusBar {{
                background-color: {colors["sidebar"]};
                color: {colors["textLight"]};
                border-top: 1px solid {colors["border"]};
            }}
            
            /* Scrollbars */
            QScrollBar:vertical {{
                background-color: {colors["surface"]};
                width: 14px;
                margin: 0px;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {colors["border"]};
                min-height: 20px;
                border-radius: 7px;
                margin: 2px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: {colors["secondary"]};
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            QScrollBar:horizontal {{
                background-color: {colors["surface"]};
                height: 14px;
                margin: 0px;
            }}
            
            QScrollBar::handle:horizontal {{
                background-color: {colors["border"]};
                min-width: 20px;
                border-radius: 7px;
                margin: 2px;
            }}
            
            QScrollBar::handle:horizontal:hover {{
                background-color: {colors["secondary"]};
            }}
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
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
