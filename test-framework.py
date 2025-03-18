# tests/test_framework.py
import unittest
import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt, QTimer

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import application modules
from desktop.components.main_window import MainWindow
from desktop.controllers.session_manager import SessionManager
from desktop.controllers.task_controller import TaskController
from desktop.theme.style_manager import StyleManager


class ApplicationTest(unittest.TestCase):
    """Base class for application tests"""
    
    app = None
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests"""
        # Create application instance if it doesn't exist
        if ApplicationTest.app is None:
            ApplicationTest.app = QApplication(sys.argv)
    
    def setUp(self):
        """Set up test environment before each test"""
        # Create test directory
        self.test_dir = os.path.join(os.path.dirname(__file__), 'test_data')
        os.makedirs(self.test_dir, exist_ok=True)
        
        # Configure application to use test directory
        os.environ['OPENMANUS_TEST'] = '1'
        os.environ['OPENMANUS_DATA_DIR'] = self.test_dir
    
    def tearDown(self):
        """Clean up after each test"""
        # Process pending events
        QApplication.processEvents()
        
        # Allow time for cleanup
        QTest.qWait(100)
    
    def create_main_window(self):
        """Create a main window instance for testing"""
        window = MainWindow()
        return window


class StyleManagerTest(unittest.TestCase):
    """Tests for the StyleManager class"""
    
    def setUp(self):
        """Set up test environment"""
        self.style_manager = StyleManager()
    
    def test_theme_switching(self):
        """Test theme switching functionality"""
        # Default should be light
        self.assertEqual(self.style_manager.theme_name, "light")
        
        # Switch to dark
        self.style_manager.set_theme("dark")
        self.assertEqual(self.style_manager.theme_name, "dark")
        
        # Switch back to light
        self.style_manager.set_theme("light")
        self.assertEqual(self.style_manager.theme_name, "light")
        
        # Toggle should switch to dark
        self.style_manager.toggle_theme()
        self.assertEqual(self.style_manager.theme_name, "dark")
    
    def test_color_schemes(self):
        """Test color scheme functionality"""
        # Get light scheme colors
        self.style_manager.set_theme("light")
        light_colors = self.style_manager.get_colors()
        self.assertEqual(light_colors["background"], "#ffffff")
        
        # Get dark scheme colors
        self.style_manager.set_theme("dark")
        dark_colors = self.style_manager.get_colors()
        self.assertEqual(dark_colors["background"], "#1e2233")
    
    def test_custom_colors(self):
        """Test custom color overrides"""
        # Set a custom color
        self.style_manager.set_theme("light")
        self.style_manager.set_custom_color("primary", "#ff0000")
        
        # Verify it was applied
        colors = self.style_manager.get_colors()
        self.assertEqual(colors["primary"], "#ff0000")
        
        # Reset and verify
        self.style_manager.reset_custom_colors()
        colors = self.style_manager.get_colors()
        self.assertNotEqual(colors["primary"], "#ff0000")


class SessionManagerTest(unittest.TestCase):
    """Tests for the SessionManager class"""
    
    def setUp(self):
        """Set up test environment"""
        # Create test directory
        self.test_dir = os.path.join(os.path.dirname(__file__), 'test_data')
        os.makedirs(self.test_dir, exist_ok=True)
        
        # Configure session manager to use test directory
        os.environ['OPENMANUS_TEST'] = '1'
        os.environ['OPENMANUS_DATA_DIR'] = self.test_dir
        
        # Create session manager
        self.session_manager = SessionManager()
    
    def tearDown(self):
        """Clean up after each test"""
        # Clean up test directory
        if os.path.exists(self.test_dir):
            for root, dirs, files in os.walk(self.test_dir, topdown=False):
                for file in files:
                    os.remove(os.path.join(root, file))
                for dir in dirs:
                    os.rmdir(os.path.join(root, dir))
    
    def test_create_session(self):
        """Test session creation"""
        # Create a session
        session_id = self.session_manager.create_session_from_current(
            "Test Session",
            "Test prompt",
            "Test response",
            "PLANNING",
            ["test", "unit"]
        )
        
        # Verify it was created
        self.assertIsNotNone(session_id)
        
        # Verify it can be retrieved
        session = self.session_manager.model.get_session(session_id)
        self.assertEqual(session.title, "Test Session")
        self.assertEqual(session.prompt, "Test prompt")
        self.assertEqual(session.response, "Test response")
        self.assertEqual(session.flow_type, "PLANNING")
        self.assertEqual(session.tags, ["test", "unit"])
    
    def test_delete_session(self):
        """Test session deletion"""
        # Create a session
        session_id = self.session_manager.create_session_from_current(
            "Test Session",
            "Test prompt",
            "Test response",
            "PLANNING"
        )
        
        # Verify it was created
        self.assertIsNotNone(session_id)
        
        # Delete it
        success = self.session_manager.delete_session(session_id)
        self.assertTrue(success)
        
        # Verify it was deleted
        session = self.session_manager.model.get_session(session_id)
        self.assertIsNone(session)
    
    def test_folder_management(self):
        """Test folder creation and management"""
        # Create a folder
        folder_id = self.session_manager.create_folder("Test Folder")
        self.assertIsNotNone(folder_id)
        
        # Rename folder
        success = self.session_manager.rename_folder(folder_id, "Renamed Folder")
        self.assertTrue(success)
        
        # Verify rename
        folder = self.session_manager.model.get_folder(folder_id)
        self.assertEqual(folder.name, "Renamed Folder")
        
        # Delete folder
        success = self.session_manager.delete_folder(folder_id)
        self.assertTrue(success)
        
        # Verify deletion
        folder = self.session_manager.model.get_folder(folder_id)
        self.assertIsNone(folder)


class MainWindowTest(ApplicationTest):
    """Tests for the MainWindow class"""
    
    def test_window_creation(self):
        """Test window creation"""
        window = self.create_main_window()
        self.assertIsNotNone(window)
        
        # Verify key components exist
        self.assertIsNotNone(window.sidebar)
        self.assertIsNotNone(window.command_center)
        self.assertIsNotNone(window.output_canvas)
        self.assertIsNotNone(window.session_browser)
    
    def test_view_switching(self):
        """Test view switching functionality"""
        window = self.create_main_window()
        
        # Default should be editor view
        self.assertEqual(window.content_stack.currentWidget(), window.editor_view)
        
        # Switch to browser view
        window.show_browser_view()
        self.assertEqual(window.content_stack.currentWidget(), window.browser_view)
        
        # Switch back to editor view
        window.show_editor_view()
        self.assertEqual(window.content_stack.currentWidget(), window.editor_view)
    
    def test_new_session(self):
        """Test new session functionality"""
        window = self.create_main_window()
        
        # Set some content
        window.command_center.editor.setPlainText("Test content")
        window.is_session_modified = True
        window.current_session = None
        
        # Create new session (this should clear content)
        # Mock the check_unsaved_changes method to always return True
        window.check_unsaved_changes = lambda: True
        window.new_session()
        
        # Verify content was cleared
        self.assertEqual(window.command_center.editor.toPlainText(), "")
        self.assertIsNone(window.current_session)
        self.assertFalse(window.is_session_modified)


class IntegrationTest(ApplicationTest):
    """Integration tests for the application"""
    
    def test_session_workflow(self):
        """Test the complete session workflow"""
        window = self.create_main_window()
        
        # Enter text in command center
        test_prompt = "This is a test prompt"
        window.command_center.editor.setPlainText(test_prompt)
        
        # Mock the output response
        window.output_canvas.text_output.setPlainText("This is a test response")
        
        # Mock the save dialog
        def mock_save_dialog(*args, **kwargs):
            # Create a class with the required interface
            class MockDialog:
                def exec(self):
                    return QDialog.DialogCode.Accepted
                
                def get_session_info(self):
                    return {
                        'title': 'Test Session',
                        'tags': ['test'],
                        'favorite': False
                    }
            
            return MockDialog()
        
        # Replace the save dialog with our mock
        window.SaveSessionDialog = mock_save_dialog
        
        # Save the session
        success = window.save_current_session()
        
        # Verify it was saved
        self.assertTrue(success)
        self.assertIsNotNone(window.current_session)
        self.assertEqual(window.current_session.title, "Test Session")
        self.assertEqual(window.current_session.prompt, test_prompt)
        self.assertFalse(window.is_session_modified)


def run_tests():
    """Run all tests"""
    unittest.main()


if __name__ == "__main__":
    run_tests()
