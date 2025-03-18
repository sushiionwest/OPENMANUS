import sys
import asyncio
import threading
import time
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QTextEdit, QLabel, QComboBox, QSplitter, 
    QStatusBar, QFrame, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QObject, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QTextCursor, QFont, QPixmap

# Import OpenManus components
from app.agent.manus import Manus
from app.flow.base import FlowType
from app.flow.flow_factory import FlowFactory
from app.logger import logger

# Custom stream to redirect logger outputs to QTextEdit
class LogStream(QObject):
    text_written = pyqtSignal(str)

    def write(self, text):
        self.text_written.emit(str(text))

    def flush(self):
        pass


class OpenManusGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.initUI()
        self.agents = {"manus": Manus()}
        self.task_thread = None
        self.running = False
        
        # Configure custom logging to GUI
        self.log_stream = LogStream()
        self.log_stream.text_written.connect(self.append_log)
        logger.add(self.log_stream, format="{message}", level="INFO")

    def initUI(self):
        self.setWindowTitle('OpenManus Desktop')
        self.setMinimumSize(900, 600)
        
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        
        # Header with logo and title
        header = QWidget()
        header_layout = QHBoxLayout(header)
        
        logo_label = QLabel()
        logo_label.setFixedSize(48, 48)
        try:
            # Try to load logo if exists
            logo_pixmap = QPixmap("assets/logo.png")
            logo_label.setPixmap(logo_pixmap.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio))
        except:
            # Use text if logo not found
            logo_label.setText("📝")
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            logo_label.setStyleSheet("font-size: 24px;")
        
        title_label = QLabel("OpenManus")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        header_layout.addWidget(logo_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch(1)
        
        # Flow type selection
        flow_layout = QHBoxLayout()
        flow_label = QLabel("Flow Type:")
        self.flow_combo = QComboBox()
        self.flow_combo.addItems([flow_type.name for flow_type in FlowType])
        flow_layout.addWidget(flow_label)
        flow_layout.addWidget(self.flow_combo)
        flow_layout.addStretch(1)
        
        # Splitter to allow resizing of input and output areas
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Input area
        input_frame = QFrame()
        input_frame.setFrameShape(QFrame.Shape.StyledPanel)
        input_layout = QVBoxLayout(input_frame)
        
        input_label = QLabel("Enter your prompt:")
        input_label.setStyleSheet("font-weight: bold;")
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Type your prompt here...")
        self.input_text.setMinimumHeight(100)
        
        input_layout.addWidget(input_label)
        input_layout.addWidget(self.input_text)
        
        # Button area
        button_layout = QHBoxLayout()
        
        self.run_button = QPushButton("Run")
        self.run_button.clicked.connect(self.run_openmanus)
        self.run_button.setMinimumWidth(100)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_openmanus)
        self.stop_button.setEnabled(False)
        self.stop_button.setMinimumWidth(100)
        
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_output)
        self.clear_button.setMinimumWidth(100)
        
        button_layout.addStretch(1)
        button_layout.addWidget(self.run_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch(1)
        
        input_layout.addLayout(button_layout)
        
        # Output area
        output_frame = QFrame()
        output_frame.setFrameShape(QFrame.Shape.StyledPanel)
        output_layout = QVBoxLayout(output_frame)
        
        output_label = QLabel("Output:")
        output_label.setStyleSheet("font-weight: bold;")
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMinimumHeight(200)
        
        output_layout.addWidget(output_label)
        output_layout.addWidget(self.output_text)
        
        # Add widgets to splitter
        splitter.addWidget(input_frame)
        splitter.addWidget(output_frame)
        splitter.setSizes([200, 400])  # Initial sizes
        
        # Add all components to main layout
        main_layout.addWidget(header)
        main_layout.addLayout(flow_layout)
        main_layout.addWidget(splitter, 1)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Set the main widget
        self.setCentralWidget(main_widget)
        
        # Set application stylesheet
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #f5f5f5;
            }
            QTextEdit {
                background-color: white;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Courier New';
            }
            QPushButton {
                background-color: #4a86e8;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a76d8;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QLabel {
                color: #333333;
            }
            QFrame {
                background-color: white;
                border-radius: 6px;
            }
        """)
        
    def run_openmanus(self):
        prompt = self.input_text.toPlainText().strip()
        
        if not prompt:
            QMessageBox.warning(self, "Empty Prompt", "Please enter a prompt before running.")
            return
        
        # UI updates
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_bar.showMessage("Processing...")
        self.running = True
        
        # Clear the output first
        self.output_text.clear()
        
        # Start the OpenManus execution in a separate thread
        self.task_thread = threading.Thread(target=self.run_openmanus_task, args=(prompt,))
        self.task_thread.daemon = True
        self.task_thread.start()
        
    def run_openmanus_task(self, prompt):
        # Create event loop for the thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Get the selected flow type
            flow_type_name = self.flow_combo.currentText()
            flow_type = FlowType[flow_type_name]
            
            # Create the flow
            flow = FlowFactory.create_flow(
                flow_type=flow_type,
                agents=self.agents,
            )
            
            # Execute the flow with a timeout
            start_time = time.time()
            try:
                result = loop.run_until_complete(asyncio.wait_for(
                    flow.execute(prompt),
                    timeout=3600,  # 60 minute timeout
                ))
                elapsed_time = time.time() - start_time
                logger.info(f"Request processed in {elapsed_time:.2f} seconds")
                logger.info(result)
            except asyncio.TimeoutError:
                logger.error("Request processing timed out after 1 hour")
                logger.info("Operation terminated due to timeout. Please try a simpler request.")
        except Exception as e:
            logger.error(f"Error: {str(e)}")
        finally:
            # UI updates in the main thread
            QApplication.instance().processEvents()
            self.running = False
            self.run_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.status_bar.showMessage("Completed")
            loop.close()
        
    def stop_openmanus(self):
        if self.running:
            logger.warning("Operation cancelled by user.")
            self.running = False
            # Note: This doesn't actually stop the task immediately - it just sets a flag
            # A proper implementation would require more complex thread management
            self.status_bar.showMessage("Stopping...")
            
            # UI updates
            self.run_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.status_bar.showMessage("Stopped")
        
    def clear_output(self):
        self.output_text.clear()
        
    def append_log(self, text):
        self.output_text.moveCursor(QTextCursor.MoveOperation.End)
        self.output_text.insertPlainText(text)
        self.output_text.ensureCursorVisible()
        # Force UI update
        QApplication.processEvents()


def main():
    app = QApplication(sys.argv)
    window = OpenManusGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
