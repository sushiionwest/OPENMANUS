# desktop/components/command_center.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, 
    QPushButton, QFrame, QMessageBox, QToolButton, QMenu,
    QActionGroup, QAction, QComboBox, QToolBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QRegularExpression
from PyQt6.QtGui import (
    QTextCharFormat, QFont, QSyntaxHighlighter, QColor,
    QTextCursor, QTextBlockFormat
)

class SyntaxHighlighter(QSyntaxHighlighter):
    """
    Syntax highlighter for the command editor with support for
    markdown-style formatting and code blocks.
    """
    
    def __init__(self, document, theme_colors):
        super().__init__(document)
        self.theme_colors = theme_colors
        self.highlighting_rules = []
        
        # Define text formats for different syntax elements
        self.init_formats()
        
        # Add highlighting rules
        self.add_highlighting_rules()
    
    def init_formats(self):
        """Initialize the text formats for different syntax elements"""
        # Normal text format (reference)
        self.normal_format = QTextCharFormat()
        self.normal_format.setForeground(QColor(self.theme_colors["text"]))
        
        # Heading format (# Heading)
        self.heading1_format = QTextCharFormat()
        self.heading1_format.setForeground(QColor(self.theme_colors["primary"]))
        self.heading1_format.setFontWeight(QFont.Weight.Bold)
        self.heading1_format.setFontPointSize(16)
        
        # Subheading format (## Subheading)
        self.heading2_format = QTextCharFormat()
        self.heading2_format.setForeground(QColor(self.theme_colors["primary"]))
        self.heading2_format.setFontWeight(QFont.Weight.Bold)
        self.heading2_format.setFontPointSize(14)
        
        # Emphasis format (*text* or _text_)
        self.emphasis_format = QTextCharFormat()
        self.emphasis_format.setFontItalic(True)
        
        # Strong format (**text** or __text__)
        self.strong_format = QTextCharFormat()
        self.strong_format.setFontWeight(QFont.Weight.Bold)
        
        # Code format (`code`)
        self.code_format = QTextCharFormat()
        self.code_format.setFontFamily("Consolas, Monaco, Courier New, monospace")
        self.code_format.setForeground(QColor(self.theme_colors["secondary"]))
        self.code_format.setBackground(QColor(self.theme_colors["surface"]))
        
        # Code block format (```code block```)
        self.code_block_format = QTextCharFormat()
        self.code_block_format.setFontFamily("Consolas, Monaco, Courier New, monospace")
        self.code_block_format.setForeground(QColor(self.theme_colors["text"]))
        self.code_block_format.setBackground(QColor(self.theme_colors["surface"]))
        
        # List item format (- item or * item or 1. item)
        self.list_format = QTextCharFormat()
        self.list_format.setForeground(QColor(self.theme_colors["primary"]))
        self.list_format.setFontWeight(QFont.Weight.Bold)
    
    def add_highlighting_rules(self):
        """Add regex-based rules for syntax highlighting"""
        # Heading 1 rule (# Heading)
        heading1_regex = QRegularExpression(r"^#\s+.+$")
        self.highlighting_rules.append((heading1_regex, self.heading1_format))
        
        # Heading 2 rule (## Subheading)
        heading2_regex = QRegularExpression(r"^##\s+.+$")
        self.highlighting_rules.append((heading2_regex, self.heading2_format))
        
        # Emphasis rule (*text* or _text_)
        emphasis_regex = QRegularExpression(r"(\*|_)[^\*_]+(\*|_)")
        self.highlighting_rules.append((emphasis_regex, self.emphasis_format))
        
        # Strong rule (**text** or __text__)
        strong_regex = QRegularExpression(r"(\*\*|__)[^\*_]+(\*\*|__)")
        self.highlighting_rules.append((strong_regex, self.strong_format))
        
        # Inline code rule (`code`)
        code_regex = QRegularExpression(r"`[^`]+`")
        self.highlighting_rules.append((code_regex, self.code_format))
        
        # List item rule (- item or * item)
        list_regex = QRegularExpression(r"^\s*[-*]\s+")
        self.highlighting_rules.append((list_regex, self.list_format))
        
        # Numbered list item rule (1. item)
        numbered_list_regex = QRegularExpression(r"^\s*\d+\.\s+")
        self.highlighting_rules.append((numbered_list_regex, self.list_format))
    
    def highlightBlock(self, text):
        """Apply syntax highlighting to a block of text"""
        # Apply regular rules
        for pattern, format_type in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format_type)
        
        # Special handling for code blocks
        self.highlight_code_blocks(text)
    
    def highlight_code_blocks(self, text):
        """Handle multi-line code blocks"""
        # Check if this block is part of a code block
        # (This would need to track state between blocks for complete implementation)
        if text.startsWith("```") or text.endsWith("```"):
            self.setFormat(0, len(text), self.code_block_format)
        
        # More advanced implementation would track code block state across multiple blocks


class CommandEditor(QTextEdit):
    """
    Enhanced text editor for entering commands with syntax highlighting
    and auto-formatting features.
    """
    
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.setObjectName("commandEditor")
        self.setAcceptRichText(False)  # We want plain text with our custom highlighting
        
        # Set monospace font
        font = QFont("Consolas, Monaco, Courier New, monospace")
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)
        
        # Set line wrapping
        self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        
        # Add syntax highlighter
        self.highlighter = SyntaxHighlighter(self.document(), self.theme_manager.get_colors())
        
        # Connect to theme changes
        self.theme_manager.theme_changed.connect(self.update_highlighter)
    
    def update_highlighter(self, theme_name):
        """Update highlighter when theme changes"""
        # Recreate the highlighter with new colors
        self.highlighter.setDocument(None)  # Detach from document
        self.highlighter = SyntaxHighlighter(self.document(), self.theme_manager.get_colors())
    
    def insert_heading(self, level=1):
        """Insert a heading at the current cursor position"""
        prefix = "#" * level + " "
        cursor = self.textCursor()
        cursor.insertText(prefix)
    
    def insert_list_item(self, numbered=False):
        """Insert a list item at the current cursor position"""
        cursor = self.textCursor()
        if numbered:
            # Look back to determine the number for this item
            block = cursor.block().previous()
            number = 1
            if block.isValid():
                text = block.text()
                if text.strip().startswith(tuple("0123456789")):
                    try:
                        number = int(text.split('.')[0]) + 1
                    except:
                        number = 1
            prefix = f"{number}. "
        else:
            prefix = "- "
        cursor.insertText(prefix)
    
    def insert_code_block(self):
        """Insert a code block at the current cursor position"""
        cursor = self.textCursor()
        # Insert a new line if we're not at the beginning of a line
        if cursor.positionInBlock() > 0:
            cursor.insertText("\n")
        cursor.insertText("```\n\n```")
        # Move cursor to the middle line
        cursor.movePosition(QTextCursor.MoveOperation.PreviousBlock)
        self.setTextCursor(cursor)


class CommandCenter(QFrame):
    """
    Enhanced command input area with formatting tools and execution controls.
    """
    
    def __init__(self, task_controller, theme_manager, parent=None):
        super().__init__(parent)
        self.task_controller = task_controller
        self.theme_manager = theme_manager
        
        self.setObjectName("commandCenter")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        
        # Create layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)
        
        # Create header with formatting toolbar
        self.create_header()
        
        # Create editor for entering commands
        self.create_editor()
        
        # Create button row for actions
        self.create_action_buttons()
        
        # Connect signals from task controller
        self.task_controller.status_changed.connect(self.on_status_changed)
        
        # Use animation for state transitions
        self.is_processing = False
    
    def create_header(self):
        """Create header with title and formatting options"""
        # Header container
        header_container = QWidget()
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        self.header = QLabel("Command Input")
        self.header.setObjectName("sectionHeader")
        header_layout.addWidget(self.header)
        
        # Create formatting toolbar
        self.toolbar = QToolBar()
        self.toolbar.setIconSize(Qt.QSize(16, 16))
        self.toolbar.setObjectName("formatToolbar")
        
        # Heading menu
        heading_button = QToolButton()
        heading_button.setText("Heading")
        heading_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        
        heading_menu = QMenu(heading_button)
        h1_action = heading_menu.addAction("Heading 1")
        h1_action.triggered.connect(lambda: self.editor.insert_heading(1))
        
        h2_action = heading_menu.addAction("Heading 2")
        h2_action.triggered.connect(lambda: self.editor.insert_heading(2))
        
        heading_button.setMenu(heading_menu)
        self.toolbar.addWidget(heading_button)
        
        # List buttons
        list_button = QToolButton()
        list_button.setText("Bullet List")
        list_button.clicked.connect(lambda: self.editor.insert_list_item(False))
        self.toolbar.addWidget(list_button)
        
        num_list_button = QToolButton()
        num_list_button.setText("Numbered List")
        num_list_button.clicked.connect(lambda: self.editor.insert_list_item(True))
        self.toolbar.addWidget(num_list_button)
        
        # Code block button
        code_button = QToolButton()
        code_button.setText("Code Block")
        code_button.clicked.connect(self.editor.insert_code_block)
        self.toolbar.addWidget(code_button)
        
        header_layout.addWidget(self.toolbar)
        
        # Template selector
        header_layout.addStretch(1)
        
        template_label = QLabel("Template:")
        header_layout.addWidget(template_label)
        
        self.template_selector = QComboBox()
        self.template_selector.addItem("None")
        self.template_selector.addItem("Research Question")
        self.template_selector.addItem("Creative Writing")
        self.template_selector.addItem("Data Analysis")
        self.template_selector.currentTextChanged.connect(self.on_template_selected)
        header_layout.addWidget(self.template_selector)
        
        self.layout.addWidget(header_container)
    
    def create_editor(self):
        """Create the command editor with syntax highlighting"""
        self.editor = CommandEditor(self.theme_manager)
        self.editor.setPlaceholderText("Enter your prompt here...")
        self.layout.addWidget(self.editor, stretch=1)
    
    def create_action_buttons(self):
        """Create the action button row"""
        self.button_row = QWidget()
        self.button_layout = QHBoxLayout(self.button_row)
        self.button_layout.setContentsMargins(0, 0, 0, 0)
        self.button_layout.setSpacing(10)
        
        # Token counter (placeholder)
        self.token_counter = QLabel("0 tokens")
        self.token_counter.setObjectName("tokenCounter")
        self.button_layout.addWidget(self.token_counter)
        
        self.button_layout.addStretch(1)
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setObjectName("secondaryButton")
        self.cancel_button.clicked.connect(self.cancel_execution)
        self.cancel_button.setEnabled(False)
        self.button_layout.addWidget(self.cancel_button)
        
        # Clear button
        self.clear_button = QPushButton("Clear")
        self.clear_button.setObjectName("secondaryButton")
        self.clear_button.clicked.connect(self.clear_editor)
        self.button_layout.addWidget(self.clear_button)
        
        # Run button
        self.run_button = QPushButton("Run")
        self.run_button.setObjectName("primaryButton")
        self.run_button.clicked.connect(self.run_prompt)
        self.button_layout.addWidget(self.run_button)
        
        self.layout.addWidget(self.button_row)
    
    def clear_editor(self):
        """Clear the editor content"""
        self.editor.clear()
        self.update_token_count()
    
    def run_prompt(self):
        """Execute the current prompt"""
        prompt = self.editor.toPlainText().strip()
        
        if not prompt:
            QMessageBox.warning(self, "Empty Prompt", "Please enter a prompt before running.")
            return
        
        # Get selected flow type from parent window
        flow_type = self.parent().flow_selector.currentText()
        
        # Execute task
        success = self.task_controller.execute_task(prompt, flow_type)
        if success:
            self.set_processing_state(True)
    
    def cancel_execution(self):
        """Cancel the current execution"""
        success = self.task_controller.cancel_task()
        if success:
            self.set_processing_state(False)
    
    def on_status_changed(self, status):
        """Handle status changes"""
        if status == "Completed" or status == "Error" or status == "Cancelled":
            self.set_processing_state(False)
    
    def set_processing_state(self, is_processing):
        """Update UI to reflect processing state"""
        self.is_processing = is_processing
        self.run_button.setEnabled(not is_processing)
        self.cancel_button.setEnabled(is_processing)
        self.clear_button.setEnabled(not is_processing)
        self.editor.setReadOnly(is_processing)
        
        # Update UI feedback
        if is_processing:
            self.run_button.setText("Processing...")
        else:
            self.run_button.setText("Run")
    
    def update_token_count(self):
        """Update the token count (simplified estimation)"""
        text = self.editor.toPlainText()
        # Rough estimate - in a real implementation this would use the model's tokenizer
        tokens = len(text.split())
        self.token_counter.setText(f"{tokens} tokens")
    
    def on_template_selected(self, template_name):
        """Handle template selection"""
        if template_name == "None" or not template_name:
            return
            
        templates = {
            "Research Question": (
                "# Research Question\n\n"
                "I need information about [TOPIC] with focus on:\n\n"
                "1. Historical context and development\n"
                "2. Current state of research\n"
                "3. Future trends and implications\n\n"
                "Please provide detailed analysis with examples and citations."
            ),
            "Creative Writing": (
                "# Creative Writing Request\n\n"
                "Please write a short [GENRE] story with the following elements:\n\n"
                "- Setting: [SETTING]\n"
                "- Main character: [CHARACTER]\n"
                "- Theme: [THEME]\n"
                "- Conflict: [CONFLICT]\n\n"
                "The story should be approximately [LENGTH] words."
            ),
            "Data Analysis": (
                "# Data Analysis\n\n"
                "I need to analyze data about [DATASET] to understand:\n\n"
                "1. Key trends and patterns\n"
                "2. Correlations between [VARIABLE_A] and [VARIABLE_B]\n"
                "3. Anomalies or outliers\n\n"
                "Please suggest appropriate analysis methods and visualization techniques."
            )
        }
        
        if template_name in templates:
            # Ask user if they want to replace existing content
            if self.editor.toPlainText().strip():
                reply = QMessageBox.question(
                    self, 
                    "Replace Content", 
                    "This will replace your current content. Continue?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    # Reset the selector to "None"
                    self.template_selector.setCurrentText("None")
                    return
            
            # Set the template content
            self.editor.setPlainText(templates[template_name])
            self.update_token_count()
            
            # Reset the template selector to "None" for next use
            self.template_selector.setCurrentText("None")
