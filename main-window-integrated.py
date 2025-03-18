# desktop/components/main_window.py
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter, QStackedWidget, QFrame, QLabel,
    QStatusBar, QPushButton, QMessageBox, QDialog,
    QDialogButtonBox, QApplication
)
from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal, QSettings
from PyQt6.QtGui import QAction, QIcon, QKeySequence

from desktop.components.sidebar import Sidebar
from desktop.components.command_center import CommandCenter
from desktop.components.output_canvas import OutputCanvas
from desktop.components.flow_selector import FlowSelector
from desktop.components.session_browser import SessionBrowser
from desktop.controllers.task_controller import TaskController
from desktop.controllers.session_manager import SessionManager
from desktop.theme.style_manager import StyleManager
from desktop.theme.animation_manager import AnimationManager
from desktop.models.session_model import SessionItem


class SaveSessionDialog(QDialog):
    """Dialog for saving a session with title and tags"""
    
    def __init__(self, session_manager, parent=None):
        super().__init__(parent)
        self.session_manager = session_manager
        
        self.setWindowTitle("Save Session")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Title input
        self.title_layout = QHBoxLayout()
        self.title_label = QLabel("Title:")
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Enter a title for this session...")
        self.title_layout.addWidget(self.title_label)
        self.title_layout.addWidget(self.title_edit)
        layout.addLayout(self.title_layout)
        
        # Tags input
        self.tags_layout = QHBoxLayout()
        self.tags_label = QLabel("Tags:")
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("Enter tags separated by commas...")
        self.tags_layout.addWidget(self.tags_label)
        self.tags_layout.addWidget(self.tags_edit)
        layout.addLayout(self.tags_layout)
        
        # Favorite checkbox
        self.favorite_check = QCheckBox("Add to Favorites")
        layout.addWidget(self.favorite_check)
        
        # Buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
    
    def set_suggested_title(self, title):
        """Set a suggested title"""
        self.title_edit.setText(title)
        # Select all text so user can easily replace it
        self.title_edit.selectAll()
    
    def get_session_info(self):
        """Get the session information"""
        tags = [tag.strip() for tag in self.tags_edit.text().split(',') if tag.strip()]
        return {
            'title': self.title_edit.text(),
            'tags': tags,
            'favorite': self.favorite_check.isChecked()
        }


class MainWindow(QMainWindow):
    """
    Main application window that integrates all components.
    """
    
    def __init__(self):
        super().__init__()
        
        # Set up managers and controllers
        self.setup_managers()
        
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
        self.create_sidebar()
        
        # Create main content panel with stacked layout
        self.content_stack = QStackedWidget()
        
        # Create editor view
        self.editor_view = self.create_editor_view()
        self.content_stack.addWidget(self.editor_view)
        
        # Create session browser view
        self.browser_view = self.create_browser_view()
        self.content_stack.addWidget(self.browser_view)
        
        # Add the content stack to the main layout
        self.main_layout.addWidget(self.content_stack)
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.status_bar.setObjectName("statusBar")
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Connect task controller to status bar
        self.task_controller.status_changed.connect(self.update_status_bar)
        
        # Set up menu bar
        self.create_menu_bar()
        
        # Set up keyboard shortcuts
        self.create_shortcuts()
        
        # Apply styles
        self.apply_styles()
        
        # Connect signals between components
        self.connect_signals()
        
        # Start with editor view
        self.show_editor_view()
    
    def setup_managers(self):
        """Set up managers and controllers"""
        # Style manager for theming
        self.style_manager = StyleManager()
        
        # Session manager for persistence
        self.session_manager = SessionManager()
        
        # Task controller for OpenManus integration
        self.task_controller = TaskController()
        
        # Current session tracking
        self.current_session = None
        self.is_session_modified = False
    
    def create_sidebar(self):
        """Create the sidebar navigation"""
        self.sidebar = Sidebar(self)
        self.sidebar.navigation_changed.connect(self.on_navigation_changed)
        self.main_layout.addWidget(self.sidebar)
    
    def create_editor_view(self):
        """Create the main editor view with command center and output canvas"""
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(0)
        
        # Create top toolbar with flow selector
        self.toolbar = QWidget()
        self.toolbar_layout = QHBoxLayout(self.toolbar)
        self.toolbar.setFixedHeight(60)
        self.toolbar.setObjectName("topToolbar")
        
        # Add flow selector
        self.flow_selector = FlowSelector(self.task_controller.get_available_flow_types())
        self.toolbar_layout.addWidget(self.flow_selector)
        
        # Add spacer
        self.toolbar_layout.addStretch()
        
        # Add action buttons
        self.save_button = QPushButton("Save Session")
        self.save_button.setObjectName("toolButton")
        self.save_button.clicked.connect(self.save_current_session)
        self.toolbar_layout.addWidget(self.save_button)
        
        # User menu button (placeholder)
        self.user_button = QLabel("User")
        self.user_button.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.user_button.setFixedSize(40, 40)
        self.user_button.setObjectName("userButton")
        self.toolbar_layout.addWidget(self.user_button)
        
        self.toolbar_layout.setContentsMargins(20, 10, 20, 10)
        editor_layout.addWidget(self.toolbar)
        
        # Create content splitter
        self.content_splitter = QSplitter(Qt.Orientation.Vertical)
        self.content_splitter.setHandleWidth(1)
        self.content_splitter.setChildrenCollapsible(False)
        
        # Create command center with task controller
        self.command_center = CommandCenter(self.task_controller, self.style_manager, self)
        self.content_splitter.addWidget(self.command_center)
        
        # Create output canvas with task controller
        self.output_canvas = OutputCanvas(self.task_controller, self.style_manager, self)
        self.content_splitter.addWidget(self.output_canvas)
        
        # Set initial splitter sizes (40% input, 60% output)
        self.content_splitter.setSizes([400, 600])
        
        editor_layout.addWidget(self.content_splitter, 1)
        
        return editor_widget
    
    def create_browser_view(self):
        """Create the session browser view"""
        self.session_browser = SessionBrowser(self.session_manager, self.style_manager, self)
        return self.session_browser
    
    def create_menu_bar(self):
        """Create the application menu bar"""
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("&File")
        
        new_action = QAction("&New Session", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self.new_session)
        file_menu.addAction(new_action)
        
        open_action = QAction("&Open Sessions", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.show_browser_view)
        file_menu.addAction(open_action)
        
        save_action = QAction("&Save Session", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_current_session)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        import_action = QAction("&Import Sessions", self)
        import_action.triggered.connect(self.import_sessions)
        file_menu.addAction(import_action)
        
        export_action = QAction("&Export Sessions", self)
        export_action.triggered.connect(self.export_sessions)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menu_bar.addMenu("&Edit")
        
        undo_action = QAction("&Undo", self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("&Redo", self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        cut_action = QAction("Cu&t", self)
        cut_action.setShortcut(QKeySequence.StandardKey.Cut)
        edit_menu.addAction(cut_action)
        
        copy_action = QAction("&Copy", self)
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        edit_menu.addAction(copy_action)
        
        paste_action = QAction("&Paste", self)
        paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        edit_menu.addAction(paste_action)
        
        # View menu
        view_menu = menu_bar.addMenu("&View")
        
        editor_action = QAction("&Editor", self)
        editor_action.setShortcut(QKeySequence("Ctrl+1"))
        editor_action.triggered.connect(self.show_editor_view)
        view_menu.addAction(editor_action)
        
        browser_action = QAction("Session &Browser", self)
        browser_action.setShortcut(QKeySequence("Ctrl+2"))
        browser_action.triggered.connect(self.show_browser_view)
        view_menu.addAction(browser_action)
        
        view_menu.addSeparator()
        
        theme_menu = view_menu.addMenu("&Theme")
        
        light_theme_action = QAction("&Light", self)
        light_theme_action.triggered.connect(lambda: self.set_theme("light"))
        theme_menu.addAction(light_theme_action)
        
        dark_theme_action = QAction("&Dark", self)
        dark_theme_action.triggered.connect(lambda: self.set_theme("dark"))
        theme_menu.addAction(dark_theme_action)
        
        # Help menu
        help_menu = menu_bar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
    
    def create_shortcuts(self):
        """Create application-wide keyboard shortcuts"""
        # Run shortcut
        self.run_shortcut = QShortcut(QKeySequence("Ctrl+Enter"), self)
        self.run_shortcut.activated.connect(self.run_command)
        
        # Clear shortcut
        self.clear_shortcut = QShortcut(QKeySequence("Ctrl+L"), self)
        self.clear_shortcut.activated.connect(self.clear_command)
        
        # Save shortcut (already in menu but adding here for clarity)
        self.save_shortcut = QShortcut(QKeySequence.StandardKey.Save, self)
        self.save_shortcut.activated.connect(self.save_current_session)
        
        # New session shortcut
        self.new_shortcut = QShortcut(QKeySequence.StandardKey.New, self)
        self.new_shortcut.activated.connect(self.new_session)
    
    def apply_styles(self):
        """Apply the application styling"""
        self.setStyleSheet(self.style_manager.get_stylesheet())
        
        # Connect theme changes to update styles
        self.style_manager.theme_changed.connect(self.on_theme_changed)
    
    def on_theme_changed(self, theme_name):
        """Handle theme changes"""
        self.setStyleSheet(self.style_manager.get_stylesheet())
    
    def set_theme(self, theme_name):
        """Set the application theme"""
        self.style_manager.set_theme(theme_name)
    
    def update_status_bar(self, status):
        """Update the main window status bar"""
        self.status_bar.showMessage(status)
    
    def on_navigation_changed(self, item_name):
        """Handle sidebar navigation changes"""
        if item_name == "Home":
            self.show_editor_view()
        elif item_name == "Sessions":
            self.show_browser_view()
        elif item_name == "Settings":
            self.show_settings_dialog()
        # Other navigation options would be handled here
    
    def connect_signals(self):
        """Connect signals between components"""
        # Connect session browser selection to editor
        self.session_browser.session_selected.connect(self.load_session)
        
        # Connect command editor changes to track modifications
        self.command_center.editor.textChanged.connect(self.on_command_changed)
        
        # Connect task execution completion to handle saving
        self.task_controller.task_completed.connect(self.on_task_completed)
    
    def on_command_changed(self):
        """Track modifications to the current session"""
        if self.current_session:
            self.is_session_modified = True
    
    def on_task_completed(self, result):
        """Handle task completion"""
        # Show save button with animation to encourage saving
        animation = AnimationManager.pulse_widget(self.save_button)
        animation.start()
    
    def show_editor_view(self):
        """Switch to the editor view"""
        self.content_stack.setCurrentWidget(self.editor_view)
        self.sidebar.select_navigation("Home")
    
    def show_browser_view(self):
        """Switch to the session browser view"""
        # Check for unsaved changes before switching
        if self.check_unsaved_changes():
            self.content_stack.setCurrentWidget(self.browser_view)
            self.sidebar.select_navigation("Sessions")
    
    def check_unsaved_changes(self):
        """Check if there are unsaved changes and prompt user"""
        if self.current_session and self.is_session_modified:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Save before continuing?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save
            )
            
            if reply == QMessageBox.StandardButton.Save:
                return self.save_current_session()
            elif reply == QMessageBox.StandardButton.Cancel:
                return False
        
        return True
    
    def new_session(self):
        """Create a new session"""
        # Check for unsaved changes
        if not self.check_unsaved_changes():
            return
        
        # Clear editor and output
        self.command_center.clear_editor()
        self.output_canvas.clear_output()
        
        # Reset current session
        self.current_session = None
        self.is_session_modified = False
        
        # Switch to editor view
        self.show_editor_view()
    
    def load_session(self, session):
        """Load a session into the editor"""
        # Check for unsaved changes
        if not self.check_unsaved_changes():
            return
        
        # Set session content
        self.command_center.editor.setPlainText(session.prompt)
        self.output_canvas.process_output(session.response)
        
        # Set flow type if available
        if session.flow_type:
            index = self.flow_selector.findText(session.flow_type)
            if index >= 0:
                self.flow_selector.setCurrentIndex(index)
        
        # Update current session
        self.current_session = session
        self.is_session_modified = False
        
        # Switch to editor view
        self.show_editor_view()
    
    def save_current_session(self):
        """Save the current session"""
        # Get current content
        prompt = self.command_center.editor.toPlainText()
        
        # Check if there's anything to save
        if not prompt.strip():
            QMessageBox.warning(self, "Empty Session", "Nothing to save. Please enter a prompt first.")
            return False
        
        try:
            # Get response from output canvas
            response = self.output_canvas.text_output.toPlainText()
            
            # Get flow type
            flow_type = self.flow_selector.currentText()
            
            # Show save dialog
            dialog = SaveSessionDialog(self.session_manager, self)
            
            # Set suggested title (first line or part of prompt)
            suggested_title = prompt.split('\n')[0][:30].strip()
            if len(suggested_title) < 3:
                suggested_title = prompt[:30].strip()
            
            dialog.set_suggested_title(suggested_title)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # Get session info
                info = dialog.get_session_info()
                
                if self.current_session:
                    # Update existing session
                    self.current_session.update_title(info['title'])
                    self.current_session.update_content(prompt, response, flow_type)
                    self.current_session.tags = info['tags']
                    self.current_session.favorite = info['favorite']
                    
                    # Save the session
                    self.session_manager.save_session(self.current_session)
                else:
                    # Create new session
                    session = SessionItem(
                        title=info['title'],
                        prompt=prompt,
                        response=response,
                        flow_type=flow_type,
                        tags=info['tags'],
                        favorite=info['favorite']
                    )
                    
                    # Save the session
                    session_id = self.session_manager.save_session(session)
                    
                    # Update current session
                    self.current_session = session
                
                # Reset modified flag
                self.is_session_modified = False
                
                # Show confirmation
                self.status_bar.showMessage("Session saved successfully", 3000)
                
                return True
            else:
                # User cancelled
                return False
                
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Error saving session: {str(e)}")
            return False
    
    def run_command(self):
        """Run the current command"""
        # Forward to command center
        self.command_center.run_prompt()
    
    def clear_command(self):
        """Clear the current command"""
        # Forward to command center
        self.command_center.clear_editor()
    
    def import_sessions(self):
        """Import sessions"""
        # Forward to session browser
        self.session_browser.import_sessions()
    
    def export_sessions(self):
        """Export sessions"""
        # Forward to session browser
        self.session_browser.export_sessions()
    
    def show_settings_dialog(self):
        """Show settings dialog"""
        # This would be implemented with a proper settings dialog
        QMessageBox.information(self, "Settings", "Settings dialog would appear here.")
    
    def show_about_dialog(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About OpenManus Redo",
            "OpenManus Redo v0.1.0\n\n"
            "A modern desktop interface for the OpenManus AI agent framework.\n\n"
            "© 2025 OpenManus Redo Team"
        )
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Check for unsaved changes
        if self.check_unsaved_changes():
            event.accept()
        else:
            event.ignore()


# Missing imports to make the code work
from PyQt6.QtWidgets import QLineEdit, QCheckBox, QShortcut
from PyQt6.QtGui import QShortcut
