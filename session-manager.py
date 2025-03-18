# desktop/controllers/session_manager.py
import os
import json
import shutil
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal, QSettings

from desktop.models.session_model import SessionsModel, SessionItem, SessionFolder


class SessionManager(QObject):
    """
    Manages saving, loading, and organizing user sessions.
    Handles persistence of session data to the file system.
    """
    
    # Signals
    sessions_loaded = pyqtSignal()  # Emitted when sessions are loaded
    session_saved = pyqtSignal(str)  # Emitted when a session is saved, with ID
    session_deleted = pyqtSignal(str)  # Emitted when a session is deleted, with ID
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize model
        self.model = SessionsModel()
        
        # Set up paths
        self.settings = QSettings("OpenManus", "OpenManusRedo")
        self.base_dir = self.settings.value(
            "sessions/directory", 
            os.path.join(os.path.expanduser("~"), ".openmanus", "sessions")
        )
        
        # Create directories if they don't exist
        self._ensure_directories()
        
        # Load existing sessions
        self.load_sessions()
    
    def _ensure_directories(self):
        """Create necessary directories if they don't exist"""
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir, exist_ok=True)
        
        # Create subdirectories
        sessions_dir = os.path.join(self.base_dir, "sessions")
        folders_dir = os.path.join(self.base_dir, "folders")
        
        os.makedirs(sessions_dir, exist_ok=True)
        os.makedirs(folders_dir, exist_ok=True)
    
    def get_sessions_path(self):
        """Get the path to the sessions directory"""
        return os.path.join(self.base_dir, "sessions")
    
    def get_folders_path(self):
        """Get the path to the folders directory"""
        return os.path.join(self.base_dir, "folders")
    
    def get_index_path(self):
        """Get the path to the index file"""
        return os.path.join(self.base_dir, "index.json")
    
    def load_sessions(self):
        """Load all sessions and folders from disk"""
        # Reset model
        self.model = SessionsModel()
        
        try:
            # Load index first if it exists
            index_path = self.get_index_path()
            if os.path.exists(index_path):
                with open(index_path, 'r', encoding='utf-8') as f:
                    index = json.load(f)
                
                # Load folders
                for folder_data in index.get('folders', []):
                    folder = SessionFolder.from_dict(folder_data)
                    self.model.folders[folder.id] = folder
            
            # Load individual session files
            sessions_dir = self.get_sessions_path()
            if os.path.exists(sessions_dir):
                for filename in os.listdir(sessions_dir):
                    if filename.endswith('.json'):
                        session_path = os.path.join(sessions_dir, filename)
                        try:
                            with open(session_path, 'r', encoding='utf-8') as f:
                                session_data = json.load(f)
                                session = SessionItem.from_dict(session_data)
                                self.model.sessions[session.id] = session
                        except Exception as e:
                            print(f"Error loading session {filename}: {e}")
            
            # Emit signal that sessions were loaded
            self.sessions_loaded.emit()
            
            return True
        except Exception as e:
            print(f"Error loading sessions: {e}")
            return False
    
    def save_sessions_index(self):
        """Save index of folders and session metadata"""
        try:
            index = {
                'folders': [folder.to_dict() for folder in self.model.folders.values()],
                'sessions': {
                    session_id: {
                        'id': session.id,
                        'title': session.title,
                        'tags': session.tags,
                        'favorite': session.favorite,
                        'created': session.created,
                        'updated': session.updated
                    } for session_id, session in self.model.sessions.items()
                }
            }
            
            with open(self.get_index_path(), 'w', encoding='utf-8') as f:
                json.dump(index, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving sessions index: {e}")
            return False
    
    def save_session(self, session):
        """Save a session to disk"""
        try:
            # Update session if it exists, otherwise add it
            if session.id in self.model.sessions:
                # Update the timestamp
                session.updated = datetime.now().isoformat()
                self.model.sessions[session.id] = session
            else:
                # Add new session
                self.model.add_session(session)
            
            # Save to file
            session_path = os.path.join(self.get_sessions_path(), f"{session.id}.json")
            with open(session_path, 'w', encoding='utf-8') as f:
                json.dump(session.to_dict(), f, indent=2)
            
            # Update index
            self.save_sessions_index()
            
            # Emit signal
            self.session_saved.emit(session.id)
            
            return session.id
        except Exception as e:
            print(f"Error saving session: {e}")
            return None
    
    def load_session(self, session_id):
        """Load a specific session from disk"""
        try:
            session_path = os.path.join(self.get_sessions_path(), f"{session_id}.json")
            if os.path.exists(session_path):
                with open(session_path, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                    session = SessionItem.from_dict(session_data)
                    self.model.sessions[session.id] = session
                    return session
            return None
        except Exception as e:
            print(f"Error loading session {session_id}: {e}")
            return None
    
    def delete_session(self, session_id):
        """Delete a session from disk and model"""
        try:
            # Remove from model
            if session_id in self.model.sessions:
                self.model.delete_session(session_id)
            
            # Remove file
            session_path = os.path.join(self.get_sessions_path(), f"{session_id}.json")
            if os.path.exists(session_path):
                os.remove(session_path)
            
            # Update index
            self.save_sessions_index()
            
            # Emit signal
            self.session_deleted.emit(session_id)
            
            return True
        except Exception as e:
            print(f"Error deleting session {session_id}: {e}")
            return False
    
    def create_session_from_current(self, title, prompt, response, flow_type, tags=None):
        """Create and save a new session from current input/output"""
        try:
            # Generate a title if none provided
            if not title:
                # Extract first line or first few words as title
                title = prompt.split('\n')[0][:30].strip()
                if len(title) < 3:  # If title is too short
                    title = f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            # Create session
            session = SessionItem(
                title=title,
                prompt=prompt,
                response=response,
                flow_type=flow_type,
                tags=tags or []
            )
            
            # Save it
            return self.save_session(session)
        except Exception as e:
            print(f"Error creating session: {e}")
            return None
    
    def create_folder(self, name, parent_id=None):
        """Create a new folder"""
        try:
            folder = SessionFolder(name=name, parent_id=parent_id)
            self.model.add_folder(folder)
            self.save_sessions_index()
            return folder.id
        except Exception as e:
            print(f"Error creating folder: {e}")
            return None
    
    def rename_folder(self, folder_id, new_name):
        """Rename an existing folder"""
        try:
            if self.model.update_folder(folder_id, new_name):
                self.save_sessions_index()
                return True
            return False
        except Exception as e:
            print(f"Error renaming folder: {e}")
            return False
    
    def delete_folder(self, folder_id):
        """Delete a folder"""
        try:
            if self.model.delete_folder(folder_id):
                self.save_sessions_index()
                return True
            return False
        except Exception as e:
            print(f"Error deleting folder: {e}")
            return False
    
    def search_sessions(self, query, tags=None):
        """Search for sessions by query text and optional tags"""
        return self.model.search_sessions(query, tags)
    
    def get_recent_sessions(self, limit=10):
        """Get the most recently updated sessions"""
        return self.model.get_recent_sessions(limit)
    
    def get_favorite_sessions(self):
        """Get all favorite sessions"""
        return self.model.get_favorite_sessions()
    
    def toggle_favorite(self, session_id):
        """Toggle favorite status for a session"""
        session = self.model.get_session(session_id)
        if session:
            is_favorite = session.toggle_favorite()
            self.save_session(session)
            return is_favorite
        return False
    
    def add_tag_to_session(self, session_id, tag):
        """Add a tag to a session"""
        session = self.model.get_session(session_id)
        if session and session.add_tag(tag):
            self.save_session(session)
            return True
        return False
    
    def remove_tag_from_session(self, session_id, tag):
        """Remove a tag from a session"""
        session = self.model.get_session(session_id)
        if session and session.remove_tag(tag):
            self.save_session(session)
            return True
        return False
    
    def get_all_tags(self):
        """Get all unique tags used across sessions"""
        return self.model.get_all_tags()
    
    def backup_sessions(self, backup_path):
        """Create a backup of all sessions"""
        try:
            # Create backup directory if it doesn't exist
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # Create zip archive
            shutil.make_archive(
                backup_path, 'zip', self.base_dir
            )
            
            return True
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False
    
    def restore_sessions(self, backup_path):
        """Restore sessions from backup"""
        try:
            # Create temporary directory
            import tempfile
            with tempfile.TemporaryDirectory() as temp_dir:
                # Extract backup
                shutil.unpack_archive(backup_path, temp_dir, 'zip')
                
                # Verify backup structure
                if not os.path.exists(os.path.join(temp_dir, "index.json")):
                    return False
                
                # Clear current sessions
                shutil.rmtree(self.base_dir)
                self._ensure_directories()
                
                # Copy backup files
                for item in os.listdir(temp_dir):
                    src = os.path.join(temp_dir, item)
                    dst = os.path.join(self.base_dir, item)
                    if os.path.isdir(src):
                        shutil.copytree(src, dst)
                    else:
                        shutil.copy2(src, dst)
                
                # Reload sessions
                self.load_sessions()
                
                return True
        except Exception as e:
            print(f"Error restoring backup: {e}")
            return False
