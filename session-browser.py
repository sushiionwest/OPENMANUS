# desktop/components/session_browser.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTreeView, QListView, QSplitter, QFrame, QLineEdit,
    QMenu, QDialog, QDialogButtonBox, QMessageBox, 
    QInputDialog, QComboBox, QCheckBox, QStyledItemDelegate,
    QSizePolicy
)
from PyQt6.QtCore import (
    Qt, QAbstractItemModel, QModelIndex, QObject, 
    pyqtSignal, QSortFilterProxyModel, QSize, QDateTime
)
from PyQt6.QtGui import (
    QStandardItemModel, QStandardItem, QIcon, QFont,
    QAction, QKeySequence
)

from desktop.theme.style_manager import StyleManager
from desktop.controllers.session_manager import SessionManager
from desktop.models.session_model import SessionItem, SessionFolder
from desktop.theme.animation_manager import AnimationManager


class SessionItemDelegate(QStyledItemDelegate):
    """
    Custom delegate for rendering session items in the list view
    with more detailed information and formatting.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def sizeHint(self, option, index):
        """Return the size needed to display the item"""
        return QSize(option.rect.width(), 80)
    
    def paint(self, painter, option, index):
        """Paint the session item with custom styling"""
        # Get data from model
        title = index.data(Qt.ItemDataRole.DisplayRole)
        creation_date = index.data(Qt.ItemDataRole.UserRole + 1)
        preview = index.data(Qt.ItemDataRole.UserRole + 2)
        is_favorite = index.data(Qt.ItemDataRole.UserRole + 3)
        tags = index.data(Qt.ItemDataRole.UserRole + 4)
        
        # Convert creation date to readable format
        if isinstance(creation_date, str):
            try:
                # Parse ISO format
                date = QDateTime.fromString(creation_date, Qt.DateFormat.ISODate)
                formatted_date = date.toString("yyyy-MM-dd HH:mm")
            except:
                formatted_date = creation_date
        else:
            formatted_date = str(creation_date)
        
        # Prepare styling
        if option.state & QStyleOptionViewItem.StateFlag.Selected:
            painter.fillRect(option.rect, option.palette.highlight())
            title_color = option.palette.highlightedText().color()
            text_color = option.palette.highlightedText().color()
        else:
            painter.fillRect(option.rect, option.palette.base())
            title_color = option.palette.text().color()
            text_color = option.palette.text().color()
            text_color.setAlpha(180)  # Slightly transparent
        
        # Draw the content
        painter.save()
        
        # Title
        font = painter.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() + 1)
        painter.setFont(font)
        painter.setPen(title_color)
        title_rect = option.rect.adjusted(10, 5, -10, -45)
        
        # Add star for favorites
        if is_favorite:
            # Draw star or other favorite indicator
            painter.drawText(title_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, "★ " + title)
        else:
            painter.drawText(title_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, title)
        
        # Date
        font.setBold(False)
        font.setPointSize(font.pointSize() - 2)
        painter.setFont(font)
        painter.setPen(text_color)
        date_rect = option.rect.adjusted(10, 30, -10, -25)
        painter.drawText(date_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, formatted_date)
        
        # Preview text
        preview_rect = option.rect.adjusted(10, 45, -10, -5)
        elided_text = option.fontMetrics.elidedText(
            preview, Qt.TextElideMode.ElideRight, preview_rect.width()
        )
        painter.drawText(preview_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided_text)
        
        # Tags
        if tags:
            tags_rect = option.rect.adjusted(option.rect.width() - 150, 5, -10, -45)
            tags_text = ", ".join(tags[:2]) + ("..." if len(tags) > 2 else "")
            painter.drawText(tags_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, tags_text)
        
        painter.restore()


class FolderTreeModel(QAbstractItemModel):
    """
    Model for the folder tree that shows the hierarchy of session folders.
    """
    
    def __init__(self, session_manager, parent=None):
        super().__init__(parent)
        self.session_manager = session_manager
        self.root_item = None
        self.reload_data()
    
    def reload_data(self):
        """Reload data from session manager"""
        # Get folders from session manager
        folders = self.session_manager.model.get_all_folders()
        
        # Find the root folder
        root_folders = [f for f in folders if f.parent_id is None]
        if root_folders:
            self.root_item = root_folders[0]
        else:
            # Create a virtual root if none exists
            self.root_item = SessionFolder(name="Root")
    
    def index(self, row, column, parent=QModelIndex()):
        """Create index for item"""
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        
        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent.internalPointer()
        
        # Get children of parent
        child_folders = self.get_children(parent_item.id)
        
        if row < len(child_folders):
            child_item = child_folders[row]
            return self.createIndex(row, column, child_item)
        
        return QModelIndex()
    
    def parent(self, index):
        """Get parent index"""
        if not index.isValid():
            return QModelIndex()
        
        child_item = index.internalPointer()
        if not child_item or child_item.id == self.root_item.id:
            return QModelIndex()
        
        parent_id = child_item.parent_id
        if not parent_id:
            return QModelIndex()
        
        # Find parent folder
        parent_item = self.session_manager.model.get_folder(parent_id)
        if not parent_item:
            return QModelIndex()
        
        # Find row of parent
        if parent_item.parent_id:
            grandparent_children = self.get_children(parent_item.parent_id)
            row = grandparent_children.index(parent_item) if parent_item in grandparent_children else 0
        else:
            row = 0
        
        return self.createIndex(row, 0, parent_item)
    
    def rowCount(self, parent=QModelIndex()):
        """Get number of rows under parent"""
        if parent.column() > 0:
            return 0
        
        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent.internalPointer()
        
        return len(self.get_children(parent_item.id))
    
    def columnCount(self, parent=QModelIndex()):
        """Get number of columns"""
        return 1
    
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        """Get data for index"""
        if not index.isValid():
            return None
        
        item = index.internalPointer()
        
        if role == Qt.ItemDataRole.DisplayRole:
            return item.name
        elif role == Qt.ItemDataRole.UserRole:
            return item.id
        
        return None
    
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        """Get header data"""
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return "Folders"
        
        return None
    
    def get_children(self, folder_id):
        """Get children of a folder"""
        return self.session_manager.model.get_child_folders(folder_id)
    
    def get_folder_id(self, index):
        """Get folder ID from index"""
        if not index.isValid():
            return self.root_item.id
        
        item = index.internalPointer()
        return item.id


class SessionListModel(QAbstractItemModel):
    """
    Model for the session list that shows sessions.
    """
    
    def __init__(self, session_manager, parent=None):
        super().__init__(parent)
        self.session_manager = session_manager
        self.sessions = []
        self.current_folder_id = None
        
        # Connect signals from session manager
        self.session_manager.sessions_loaded.connect(self.reload_data)
        self.session_manager.session_saved.connect(self.reload_data)
        self.session_manager.session_deleted.connect(self.reload_data)
    
    def reload_data(self):
        """Reload data from session manager based on current folder"""
        self.beginResetModel()
        
        if self.current_folder_id == "favorites":
            # Load favorite sessions
            self.sessions = self.session_manager.get_favorite_sessions()
        elif self.current_folder_id == "recent":
            # Load recent sessions
            self.sessions = self.session_manager.get_recent_sessions()
        else:
            # Load all sessions (for now - folder support would be added)
            self.sessions = self.session_manager.model.get_all_sessions()
        
        # Sort by updated date (newest first)
        self.sessions.sort(key=lambda s: s.updated, reverse=True)
        
        self.endResetModel()
    
    def set_folder(self, folder_id):
        """Set the current folder to display"""
        self.current_folder_id = folder_id
        self.reload_data()
    
    def index(self, row, column, parent=QModelIndex()):
        """Create index for item"""
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        
        if row < len(self.sessions):
            return self.createIndex(row, column, self.sessions[row])
        
        return QModelIndex()
    
    def parent(self, index):
        """Get parent index (always invalid for list)"""
        return QModelIndex()
    
    def rowCount(self, parent=QModelIndex()):
        """Get number of rows"""
        if parent.isValid():
            return 0
        return len(self.sessions)
    
    def columnCount(self, parent=QModelIndex()):
        """Get number of columns"""
        return 1
    
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        """Get data for index"""
        if not index.isValid():
            return None
        
        item = index.internalPointer()
        
        if role == Qt.ItemDataRole.DisplayRole:
            return item.title
        elif role == Qt.ItemDataRole.UserRole:
            return item.id
        elif role == Qt.ItemDataRole.UserRole + 1:
            return item.created
        elif role == Qt.ItemDataRole.UserRole + 2:
            # Return a preview of the prompt
            return item.prompt[:100] + "..." if len(item.prompt) > 100 else item.prompt
        elif role == Qt.ItemDataRole.UserRole + 3:
            return item.favorite
        elif role == Qt.ItemDataRole.UserRole + 4:
            return item.tags
        
        return None
    
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        """Get header data"""
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return "Sessions"
        
        return None
    
    def get_session(self, index):
        """Get session from index"""
        if not index.isValid():
            return None
        
        return index.internalPointer()


class SessionSearchDialog(QDialog):
    """
    Dialog for searching sessions with advanced options.
    """
    
    def __init__(self, session_manager, parent=None):
        super().__init__(parent)
        self.session_manager = session_manager
        
        self.setWindowTitle("Search Sessions")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Search query
        self.query_layout = QHBoxLayout()
        self.query_label = QLabel("Search:")
        self.query_edit = QLineEdit()
        self.query_edit.setPlaceholderText("Enter search terms...")
        self.query_layout.addWidget(self.query_label)
        self.query_layout.addWidget(self.query_edit)
        layout.addLayout(self.query_layout)
        
        # Tags filter
        self.tags_layout = QHBoxLayout()
        self.tags_label = QLabel("Tags:")
        self.tags_combo = QComboBox()
        self.tags_combo.setEditable(True)
        
        # Add available tags
        self.tags_combo.addItem("")
        self.tags_combo.addItems(self.session_manager.get_all_tags())
        
        self.add_tag_button = QPushButton("Add")
        self.add_tag_button.clicked.connect(self.add_tag)
        
        self.tags_layout.addWidget(self.tags_label)
        self.tags_layout.addWidget(self.tags_combo)
        self.tags_layout.addWidget(self.add_tag_button)
        layout.addLayout(self.tags_layout)
        
        # Selected tags
        self.selected_tags_layout = QHBoxLayout()
        self.selected_tags_label = QLabel("Selected tags:")
        self.selected_tags_layout.addWidget(self.selected_tags_label)
        self.selected_tags = []
        self.selected_tags_widget = QWidget()
        self.selected_tags_widget_layout = QHBoxLayout(self.selected_tags_widget)
        self.selected_tags_widget_layout.setContentsMargins(0, 0, 0, 0)
        self.selected_tags_layout.addWidget(self.selected_tags_widget)
        layout.addLayout(self.selected_tags_layout)
        
        # Favorites only
        self.favorites_check = QCheckBox("Search in favorites only")
        layout.addWidget(self.favorites_check)
        
        # Buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
    
    def add_tag(self):
        """Add the current tag to the selected tags"""
        tag = self.tags_combo.currentText().strip()
        if tag and tag not in self.selected_tags:
            self.selected_tags.append(tag)
            self.update_selected_tags_display()
            self.tags_combo.setCurrentText("")
    
    def update_selected_tags_display(self):
        """Update the display of selected tags"""
        # Clear current widgets
        while self.selected_tags_widget_layout.count():
            item = self.selected_tags_widget_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add tag labels
        for tag in self.selected_tags:
            tag_layout = QHBoxLayout()
            tag_label = QLabel(tag)
            tag_label.setStyleSheet("background-color: #e0e0e0; padding: 2px 4px; border-radius: 4px;")
            remove_button = QPushButton("×")
            remove_button.setFixedSize(16, 16)
            remove_button.clicked.connect(lambda checked, t=tag: self.remove_tag(t))
            
            tag_layout.addWidget(tag_label)
            tag_layout.addWidget(remove_button)
            
            tag_widget = QWidget()
            tag_widget.setLayout(tag_layout)
            self.selected_tags_widget_layout.addWidget(tag_widget)
        
        self.selected_tags_widget_layout.addStretch()
    
    def remove_tag(self, tag):
        """Remove a tag from the selected tags"""
        if tag in self.selected_tags:
            self.selected_tags.remove(tag)
            self.update_selected_tags_display()
    
    def get_search_parameters(self):
        """Get the search parameters"""
        return {
            'query': self.query_edit.text(),
            'tags': self.selected_tags,
            'favorites_only': self.favorites_check.isChecked()
        }


class SessionBrowser(QWidget):
    """
    Browser component for viewing, searching, and managing sessions.
    """
    
    # Signal when a session is selected
    session_selected = pyqtSignal(object)
    
    def __init__(self, session_manager, theme_manager, parent=None):
        super().__init__(parent)
        self.session_manager = session_manager
        self.theme_manager = theme_manager
        
        self.setObjectName("sessionBrowser")
        
        # Create layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Create toolbar
        self.create_toolbar()
        
        # Create main content with splitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(1)
        self.splitter.setChildrenCollapsible(False)
        
        # Create folder tree
        self.create_folder_tree()
        
        # Create session list
        self.create_session_list()
        
        # Add to splitter
        self.splitter.addWidget(self.folder_frame)
        self.splitter.addWidget(self.session_frame)
        
        # Set initial sizes (30% folders, 70% sessions)
        self.splitter.setSizes([300, 700])
        
        self.layout.addWidget(self.splitter)
    
    def create_toolbar(self):
        """Create toolbar with actions"""
        self.toolbar = QWidget()
        self.toolbar_layout = QHBoxLayout(self.toolbar)
        self.toolbar_layout.setContentsMargins(10, 5, 10, 5)
        
        # New session button
        self.new_button = QPushButton("New Session")
        self.new_button.setObjectName("primaryButton")
        self.new_button.clicked.connect(self.new_session)
        self.toolbar_layout.addWidget(self.new_button)
        
        # Search button
        self.search_button = QPushButton("Search")
        self.search_button.setObjectName("secondaryButton")
        self.search_button.clicked.connect(self.search_sessions)
        self.toolbar_layout.addWidget(self.search_button)
        
        self.toolbar_layout.addStretch(1)
        
        # Import/Export buttons
        self.import_button = QPushButton("Import")
        self.import_button.setObjectName("toolButton")
        self.import_button.clicked.connect(self.import_sessions)
        self.toolbar_layout.addWidget(self.import_button)
        
        self.export_button = QPushButton("Export")
        self.export_button.setObjectName("toolButton")
        self.export_button.clicked.connect(self.export_sessions)
        self.toolbar_layout.addWidget(self.export_button)
        
        self.layout.addWidget(self.toolbar)
    
    def create_folder_tree(self):
        """Create the folder tree view"""
        self.folder_frame = QFrame()
        self.folder_frame.setObjectName("folderFrame")
        self.folder_frame.setFrameShape(QFrame.Shape.StyledPanel)
        
        folder_layout = QVBoxLayout(self.folder_frame)
        folder_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        folder_header = QWidget()
        folder_header_layout = QHBoxLayout(folder_header)
        folder_header_layout.setContentsMargins(10, 10, 10, 10)
        
        folder_title = QLabel("Folders")
        folder_title.setObjectName("sectionHeader")
        folder_header_layout.addWidget(folder_title)
        
        folder_header_layout.addStretch(1)
        
        # Add folder button
        self.add_folder_button = QPushButton("+")
        self.add_folder_button.setObjectName("smallButton")
        self.add_folder_button.setFixedSize(24, 24)
        self.add_folder_button.clicked.connect(self.add_folder)
        folder_header_layout.addWidget(self.add_folder_button)
        
        folder_layout.addWidget(folder_header)
        
        # Tree view
        self.folder_tree = QTreeView()
        self.folder_tree.setObjectName("folderTree")
        self.folder_tree.setHeaderHidden(True)
        self.folder_tree.setAnimated(True)
        self.folder_tree.setIndentation(20)
        self.folder_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.folder_tree.customContextMenuRequested.connect(self.show_folder_context_menu)
        
        # Connect to selection
        self.folder_tree.clicked.connect(self.on_folder_clicked)
        
        # Create model
        self.folder_model = FolderTreeModel(self.session_manager)
        self.folder_tree.setModel(self.folder_model)
        
        folder_layout.addWidget(self.folder_tree)
        
        # Smart folders section
        smart_folder_header = QWidget()
        smart_header_layout = QHBoxLayout(smart_folder_header)
        smart_header_layout.setContentsMargins(10, 10, 10, 5)
        
        smart_title = QLabel("Smart Folders")
        smart_title.setObjectName("sectionHeader")
        smart_header_layout.addWidget(smart_title)
        
        folder_layout.addWidget(smart_folder_header)
        
        # Smart folders list
        self.smart_folders = QWidget()
        smart_layout = QVBoxLayout(self.smart_folders)
        smart_layout.setContentsMargins(5, 0, 5, 10)
        smart_layout.setSpacing(2)
        
        # Favorites folder
        self.favorites_button = QPushButton("★ Favorites")
        self.favorites_button.setObjectName("smartFolderButton")
        self.favorites_button.clicked.connect(lambda: self.set_smart_folder("favorites"))
        smart_layout.addWidget(self.favorites_button)
        
        # Recent folder
        self.recent_button = QPushButton("⏱ Recent")
        self.recent_button.setObjectName("smartFolderButton")
        self.recent_button.clicked.connect(lambda: self.set_smart_folder("recent"))
        smart_layout.addWidget(self.recent_button)
        
        folder_layout.addWidget(self.smart_folders)
    
    def create_session_list(self):
        """Create the session list view"""
        self.session_frame = QFrame()
        self.session_frame.setObjectName("sessionFrame")
        self.session_frame.setFrameShape(QFrame.Shape.StyledPanel)
        
        session_layout = QVBoxLayout(self.session_frame)
        session_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        session_header = QWidget()
        session_header_layout = QHBoxLayout(session_header)
        session_header_layout.setContentsMargins(10, 10, 10, 10)
        
        self.session_title = QLabel("All Sessions")
        self.session_title.setObjectName("sectionHeader")
        session_header_layout.addWidget(self.session_title)
        
        session_header_layout.addStretch(1)
        
        # Delete button
        self.delete_button = QPushButton("Delete")
        self.delete_button.setObjectName("toolButton")
        self.delete_button.clicked.connect(self.delete_selected_session)
        self.delete_button.setEnabled(False)
        session_header_layout.addWidget(self.delete_button)
        
        session_layout.addWidget(session_header)
        
        # Session list view
        self.session_list = QListView()
        self.session_list.setObjectName("sessionList")
        self.session_list.setItemDelegate(SessionItemDelegate())
        self.session_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.session_list.customContextMenuRequested.connect(self.show_session_context_menu)
        
        # Connect to selection
        self.session_list.clicked.connect(self.on_session_clicked)
        self.session_list.doubleClicked.connect(self.on_session_double_clicked)
        
        # Create model
        self.session_model = SessionListModel(self.session_manager)
        self.session_list.setModel(self.session_model)
        
        session_layout.addWidget(self.session_list)
    
    def on_folder_clicked(self, index):
        """Handle folder click"""
        folder_id = self.folder_model.get_folder_id(index)
        if folder_id:
            self.session_model.set_folder(folder_id)
            
            # Update header
            folder_name = index.data(Qt.ItemDataRole.DisplayRole)
            self.session_title.setText(f"{folder_name} Sessions")
    
    def set_smart_folder(self, folder_id):
        """Set a smart folder as the current folder"""
        self.session_model.set_folder(folder_id)
        
        # Update header
        if folder_id == "favorites":
            self.session_title.setText("Favorite Sessions")
        elif folder_id == "recent":
            self.session_title.setText("Recent Sessions")
    
    def on_session_clicked(self, index):
        """Handle session click"""
        session = self.session_model.get_session(index)
        if session:
            # Enable delete button
            self.delete_button.setEnabled(True)
        else:
            self.delete_button.setEnabled(False)
    
    def on_session_double_clicked(self, index):
        """Handle session double click"""
        session = self.session_model.get_session(index)
        if session:
            # Emit signal to load this session
            self.session_selected.emit(session)
    
    def show_folder_context_menu(self, position):
        """Show context menu for folders"""
        index = self.folder_tree.indexAt(position)
        if not index.isValid():
            return
        
        # Get folder ID
        folder_id = self.folder_model.get_folder_id(index)
        folder_name = index.data(Qt.ItemDataRole.DisplayRole)
        
        # Create menu
        menu = QMenu(self)
        
        rename_action = menu.addAction("Rename Folder")
        rename_action.triggered.connect(lambda: self.rename_folder(folder_id))
        
        delete_action = menu.addAction("Delete Folder")
        delete_action.triggered.connect(lambda: self.delete_folder(folder_id))
        
        menu.exec(self.folder_tree.mapToGlobal(position))
    
    def show_session_context_menu(self, position):
        """Show context menu for sessions"""
        index = self.session_list.indexAt(position)
        if not index.isValid():
            return
        
        # Get session
        session = self.session_model.get_session(index)
        if not session:
            return
        
        # Create menu
        menu = QMenu(self)
        
        open_action = menu.addAction("Open Session")
        open_action.triggered.connect(lambda: self.session_selected.emit(session))
        
        rename_action = menu.addAction("Rename Session")
        rename_action.triggered.connect(lambda: self.rename_session(session))
        
        # Favorite option
        if session.favorite:
            favorite_action = menu.addAction("Remove from Favorites")
        else:
            favorite_action = menu.addAction("Add to Favorites")
        favorite_action.triggered.connect(lambda: self.toggle_favorite(session))
        
        # Tags submenu
        tags_menu = menu.addMenu("Tags")
        
        add_tag_action = tags_menu.addAction("Add Tag...")
        add_tag_action.triggered.connect(lambda: self.add_tag_to_session(session))
        
        if session.tags:
            tags_menu.addSeparator()
            for tag in session.tags:
                remove_tag_action = tags_menu.addAction(f"Remove '{tag}'")
                remove_tag_action.triggered.connect(
                    lambda checked, t=tag, s=session: self.remove_tag_from_session(s, t)
                )
        
        menu.addSeparator()
        
        delete_action = menu.addAction("Delete Session")
        delete_action.triggered.connect(lambda: self.delete_session(session.id))
        
        menu.exec(self.session_list.mapToGlobal(position))
    
    def new_session(self):
        """Create a new blank session"""
        # In practice, this would create a new session in the editor
        # and emit a signal to switch to the editor view
        pass
    
    def add_folder(self):
        """Add a new folder"""
        name, ok = QInputDialog.getText(self, "New Folder", "Folder name:")
        if ok and name:
            # Get current folder as parent
            indexes = self.folder_tree.selectedIndexes()
            parent_id = None
            if indexes:
                parent_id = self.folder_model.get_folder_id(indexes[0])
            
            # Create folder
            folder_id = self.session_manager.create_folder(name, parent_id)
            if folder_id:
                # Reload model
                self.folder_model.reload_data()
    
    def rename_folder(self, folder_id):
        """Rename a folder"""
        folder = self.session_manager.model.get_folder(folder_id)
        if folder:
            name, ok = QInputDialog.getText(
                self, "Rename Folder", "New folder name:", 
                text=folder.name
            )
            if ok and name:
                self.session_manager.rename_folder(folder_id, name)
                # Reload model
                self.folder_model.reload_data()
    
    def delete_folder(self, folder_id):
        """Delete a folder"""
        # Confirm deletion
        reply = QMessageBox.question(
            self, "Delete Folder",
            "Are you sure you want to delete this folder?\nThis will not delete the sessions inside.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.session_manager.delete_folder(folder_id)
            # Reload model
            self.folder_model.reload_data()
    
    def rename_session(self, session):
        """Rename a session"""
        name, ok = QInputDialog.getText(
            self, "Rename Session", "New session name:", 
            text=session.title
        )
        if ok and name:
            session.update_title(name)
            self.session_manager.save_session(session)
    
    def toggle_favorite(self, session):
        """Toggle favorite status for a session"""
        is_favorite = self.session_manager.toggle_favorite(session.id)
        # Reload model if in favorites view
        if self.session_model.current_folder_id == "favorites" and not is_favorite:
            self.session_model.reload_data()
    
    def add_tag_to_session(self, session):
        """Add a tag to a session"""
        # Get existing tags for autocomplete
        all_tags = self.session_manager.get_all_tags()
        
        tag, ok = QInputDialog.getItem(
            self, "Add Tag", "Select or enter a tag:",
            all_tags, 0, True
        )
        
        if ok and tag:
            self.session_manager.add_tag_to_session(session.id, tag)
    
    def remove_tag_from_session(self, session, tag):
        """Remove a tag from a session"""
        self.session_manager.remove_tag_from_session(session.id, tag)
    
    def delete_selected_session(self):
        """Delete the currently selected session"""
        indexes = self.session_list.selectedIndexes()
        if indexes:
            session = self.session_model.get_session(indexes[0])
            if session:
                self.delete_session(session.id)
    
    def delete_session(self, session_id):
        """Delete a session"""
        # Confirm deletion
        reply = QMessageBox.question(
            self, "Delete Session",
            "Are you sure you want to delete this session?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.session_manager.delete_session(session_id)
            # Disable delete button
            self.delete_button.setEnabled(False)
    
    def search_sessions(self):
        """Show search dialog and perform search"""
        dialog = SessionSearchDialog(self.session_manager, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            params = dialog.get_search_parameters()
            
            # Perform search
            if params['favorites_only']:
                results = [s for s in self.session_manager.get_favorite_sessions() 
                        if params['query'].lower() in s.title.lower() or 
                           params['query'].lower() in s.prompt.lower()]
            else:
                results = self.session_manager.search_sessions(params['query'], params['tags'])
            
            # Display results
            self.session_model.sessions = results
            self.session_model.current_folder_id = "search_results"
            self.session_title.setText(f"Search Results ({len(results)} sessions)")
            
            # Notify model
            self.session_model.beginResetModel()
            self.session_model.endResetModel()
    
    def import_sessions(self):
        """Import sessions from backup"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Sessions", "", "Zip Files (*.zip)"
        )
        
        if file_path:
            # Confirm import
            reply = QMessageBox.question(
                self, "Import Sessions",
                "Importing will replace your current sessions. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                success = self.session_manager.restore_sessions(file_path)
                if success:
                    QMessageBox.information(self, "Import Complete", "Sessions imported successfully.")
                    # Reload models
                    self.folder_model.reload_data()
                    self.session_model.reload_data()
                else:
                    QMessageBox.critical(self, "Import Failed", "Failed to import sessions.")
    
    def export_sessions(self):
        """Export sessions to backup"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Sessions", "", "Zip Files (*.zip)"
        )
        
        if file_path:
            success = self.session_manager.backup_sessions(file_path)
            if success:
                QMessageBox.information(self, "Export Complete", "Sessions exported successfully.")
            else:
                QMessageBox.critical(self, "Export Failed", "Failed to export sessions.")

# Missing imports to make the code work
from PyQt6.QtWidgets import QStyleOptionViewItem, QStackedWidget, QTabWidget, QApplication
