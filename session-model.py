# desktop/models/session_model.py
import json
import uuid
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal

class SessionItem:
    """
    Represents a saved session with prompt, response, and metadata.
    """
    
    def __init__(self, title="", prompt="", response="", flow_type="", 
                 tags=None, favorite=False, session_id=None, created=None, updated=None):
        # Generate new ID if none provided
        self.id = session_id if session_id else str(uuid.uuid4())
        
        # Content
        self.title = title
        self.prompt = prompt
        self.response = response
        self.flow_type = flow_type
        
        # Metadata
        self.tags = tags or []
        self.favorite = favorite
        self.created = created or datetime.now().isoformat()
        self.updated = updated or datetime.now().isoformat()
    
    def to_dict(self):
        """Convert session to dictionary for serialization"""
        return {
            "id": self.id,
            "title": self.title,
            "prompt": self.prompt,
            "response": self.response,
            "flow_type": self.flow_type,
            "tags": self.tags,
            "favorite": self.favorite,
            "created": self.created,
            "updated": self.updated
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create session from dictionary"""
        return cls(
            title=data.get("title", ""),
            prompt=data.get("prompt", ""),
            response=data.get("response", ""),
            flow_type=data.get("flow_type", ""),
            tags=data.get("tags", []),
            favorite=data.get("favorite", False),
            session_id=data.get("id"),
            created=data.get("created"),
            updated=data.get("updated")
        )
    
    def update_title(self, title):
        """Update the session title"""
        self.title = title
        self.updated = datetime.now().isoformat()
    
    def update_content(self, prompt, response, flow_type):
        """Update session content"""
        self.prompt = prompt
        self.response = response
        self.flow_type = flow_type
        self.updated = datetime.now().isoformat()
    
    def toggle_favorite(self):
        """Toggle favorite status"""
        self.favorite = not self.favorite
        self.updated = datetime.now().isoformat()
        return self.favorite
    
    def add_tag(self, tag):
        """Add a tag if it doesn't exist"""
        if tag and tag not in self.tags:
            self.tags.append(tag)
            self.updated = datetime.now().isoformat()
            return True
        return False
    
    def remove_tag(self, tag):
        """Remove a tag if it exists"""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated = datetime.now().isoformat()
            return True
        return False
    
    def get_age(self):
        """Get session age in days"""
        created_date = datetime.fromisoformat(self.created)
        now = datetime.now()
        return (now - created_date).days


class SessionFolder:
    """
    Represents a folder for organizing sessions.
    """
    
    def __init__(self, name="", folder_id=None, parent_id=None, created=None):
        # Generate new ID if none provided
        self.id = folder_id if folder_id else str(uuid.uuid4())
        
        # Properties
        self.name = name
        self.parent_id = parent_id  # Parent folder ID or None for root
        self.created = created or datetime.now().isoformat()
    
    def to_dict(self):
        """Convert folder to dictionary for serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "parent_id": self.parent_id,
            "created": self.created
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create folder from dictionary"""
        return cls(
            name=data.get("name", ""),
            folder_id=data.get("id"),
            parent_id=data.get("parent_id"),
            created=data.get("created")
        )


class SessionsModel(QObject):
    """
    Model for managing sessions and folders in memory.
    Emits signals when data changes for UI updates.
    """
    
    # Signals
    sessions_changed = pyqtSignal()  # Emitted when sessions list changes
    folders_changed = pyqtSignal()   # Emitted when folders list changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sessions = {}  # Dictionary of sessions by ID
        self.folders = {}   # Dictionary of folders by ID
        
        # Initialize with default folders
        self._initialize_defaults()
    
    def _initialize_defaults(self):
        """Initialize model with default folders"""
        # Create root folder if it doesn't exist
        if not self.folders:
            root_folder = SessionFolder(name="Root")
            self.folders[root_folder.id] = root_folder
            
            # Create default folders
            favorites_folder = SessionFolder(name="Favorites", parent_id=root_folder.id)
            recent_folder = SessionFolder(name="Recent", parent_id=root_folder.id)
            
            self.folders[favorites_folder.id] = favorites_folder
            self.folders[recent_folder.id] = recent_folder
            
            # Signal that folders have changed
            self.folders_changed.emit()
    
    def add_session(self, session):
        """Add a new session to the model"""
        self.sessions[session.id] = session
        self.sessions_changed.emit()
        return session.id
    
    def update_session(self, session_id, **kwargs):
        """Update an existing session"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            
            # Update fields
            if "title" in kwargs:
                session.update_title(kwargs["title"])
            
            if all(k in kwargs for k in ["prompt", "response", "flow_type"]):
                session.update_content(
                    kwargs["prompt"], kwargs["response"], kwargs["flow_type"]
                )
            
            if "favorite" in kwargs:
                session.favorite = kwargs["favorite"]
            
            if "tags" in kwargs:
                session.tags = kwargs["tags"].copy()
            
            session.updated = datetime.now().isoformat()
            self.sessions_changed.emit()
            return True
        
        return False
    
    def delete_session(self, session_id):
        """Delete a session from the model"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            self.sessions_changed.emit()
            return True
        
        return False
    
    def get_session(self, session_id):
        """Get a session by ID"""
        return self.sessions.get(session_id)
    
    def get_all_sessions(self):
        """Get all sessions as a list"""
        return list(self.sessions.values())
    
    def add_folder(self, folder):
        """Add a new folder to the model"""
        self.folders[folder.id] = folder
        self.folders_changed.emit()
        return folder.id
    
    def update_folder(self, folder_id, name):
        """Update an existing folder"""
        if folder_id in self.folders:
            self.folders[folder_id].name = name
            self.folders_changed.emit()
            return True
        
        return False
    
    def delete_folder(self, folder_id):
        """Delete a folder and move its sessions to parent"""
        if folder_id in self.folders:
            # Get parent folder
            parent_id = self.folders[folder_id].parent_id
            
            # Remove folder
            del self.folders[folder_id]
            self.folders_changed.emit()
            return True
        
        return False
    
    def get_folder(self, folder_id):
        """Get a folder by ID"""
        return self.folders.get(folder_id)
    
    def get_all_folders(self):
        """Get all folders as a list"""
        return list(self.folders.values())
    
    def get_child_folders(self, parent_id=None):
        """Get folders that are children of the specified parent"""
        return [f for f in self.folders.values() if f.parent_id == parent_id]
    
    def search_sessions(self, query, tags=None):
        """Search sessions by query text and optional tags"""
        results = []
        query = query.lower()
        
        for session in self.sessions.values():
            # Check if query matches title or content
            if (query in session.title.lower() or 
                query in session.prompt.lower() or 
                query in session.response.lower()):
                
                # If tags specified, check if session has all required tags
                if tags:
                    if all(tag in session.tags for tag in tags):
                        results.append(session)
                else:
                    results.append(session)
        
        return results
    
    def get_favorite_sessions(self):
        """Get all favorite sessions"""
        return [s for s in self.sessions.values() if s.favorite]
    
    def get_recent_sessions(self, limit=10):
        """Get most recently updated sessions"""
        sessions = list(self.sessions.values())
        sessions.sort(key=lambda s: s.updated, reverse=True)
        return sessions[:limit]
    
    def get_sessions_with_tag(self, tag):
        """Get all sessions with the specified tag"""
        return [s for s in self.sessions.values() if tag in s.tags]
    
    def get_all_tags(self):
        """Get all unique tags used across sessions"""
        tags = set()
        for session in self.sessions.values():
            tags.update(session.tags)
        return sorted(list(tags))
