# desktop/utils/performance.py
import time
import functools
import logging
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread, QMutex, QWaitCondition

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """
    Utility for monitoring and logging performance metrics.
    """
    
    # Dictionary to store timing data
    _timings = {}
    
    @staticmethod
    def start_timer(name):
        """Start a timer with the given name"""
        PerformanceMonitor._timings[name] = {'start': time.time(), 'stop': None}
    
    @staticmethod
    def stop_timer(name):
        """Stop a timer and return the elapsed time"""
        if name in PerformanceMonitor._timings:
            PerformanceMonitor._timings[name]['stop'] = time.time()
            return PerformanceMonitor.get_elapsed(name)
        return None
    
    @staticmethod
    def get_elapsed(name):
        """Get the elapsed time for a timer"""
        if name in PerformanceMonitor._timings:
            timing = PerformanceMonitor._timings[name]
            if timing['start'] is not None:
                stop_time = timing['stop'] if timing['stop'] is not None else time.time()
                return stop_time - timing['start']
        return None
    
    @staticmethod
    def log_timer(name, level=logging.DEBUG):
        """Log the elapsed time for a timer"""
        elapsed = PerformanceMonitor.stop_timer(name)
        if elapsed is not None:
            logger.log(level, f"Performance: {name} took {elapsed:.4f} seconds")
            return elapsed
        return None
    
    @staticmethod
    def clear_timers():
        """Clear all timers"""
        PerformanceMonitor._timings.clear()
    
    @staticmethod
    def timed(name=None):
        """Decorator to time a function"""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                timer_name = name or f"{func.__module__}.{func.__name__}"
                PerformanceMonitor.start_timer(timer_name)
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    PerformanceMonitor.log_timer(timer_name)
            return wrapper
        return decorator


class LazyLoader(QObject):
    """
    Utility for lazy loading data to improve startup performance.
    """
    
    # Signal emitted when loading is complete
    loading_complete = pyqtSignal(object)
    
    def __init__(self, load_func, parent=None):
        """
        Initialize with a loading function.
        
        Args:
            load_func: Function to call for loading data
            parent: Parent QObject
        """
        super().__init__(parent)
        self.load_func = load_func
        self.loaded_data = None
        self.is_loaded = False
    
    def start_loading(self, delay=0):
        """
        Start loading data after an optional delay.
        
        Args:
            delay: Delay in milliseconds before starting load
        """
        if delay > 0:
            QTimer.singleShot(delay, self._perform_load)
        else:
            self._perform_load()
    
    def _perform_load(self):
        """Perform the actual loading operation"""
        try:
            self.loaded_data = self.load_func()
            self.is_loaded = True
            self.loading_complete.emit(self.loaded_data)
        except Exception as e:
            logger.error(f"Error in lazy loading: {e}")
            self.loading_complete.emit(None)
    
    def get_data(self):
        """
        Get the loaded data, waiting if not yet loaded.
        
        Returns:
            The loaded data
        """
        if not self.is_loaded:
            self._perform_load()
        return self.loaded_data


class WorkerThread(QThread):
    """
    Worker thread for performing background operations.
    """
    
    # Signal emitted when work is complete
    work_complete = pyqtSignal(object)
    
    # Signal emitted on error
    work_error = pyqtSignal(Exception)
    
    # Signal for progress updates
    progress_updated = pyqtSignal(int)
    
    def __init__(self, target_func, args=None, kwargs=None, parent=None):
        """
        Initialize with a target function.
        
        Args:
            target_func: Function to call in the thread
            args: Positional arguments for the function
            kwargs: Keyword arguments for the function
            parent: Parent QObject
        """
        super().__init__(parent)
        self.target_func = target_func
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.result = None
        
        # For thread control
        self.mutex = QMutex()
        self.condition = QWaitCondition()
        self.abort = False
    
    def run(self):
        """Run the worker thread"""
        try:
            # Execute the target function
            self.result = self.target_func(*self.args, **self.kwargs)
            
            # Check if we should abort
            self.mutex.lock()
            if self.abort:
                self.mutex.unlock()
                return
            self.mutex.unlock()
            
            # Emit result
            self.work_complete.emit(self.result)
        except Exception as e:
            logger.error(f"Error in worker thread: {e}")
            self.work_error.emit(e)
    
    def stop(self):
        """Stop the worker thread"""
        self.mutex.lock()
        self.abort = True
        self.mutex.unlock()
        self.condition.wakeOne()
        self.wait()


# Optimized implementations for core components

class OptimizedSessionManager:
    """
    Performance optimizations for the SessionManager class.
    These methods should be applied to improve session management performance.
    """
    
    @staticmethod
    @PerformanceMonitor.timed("session_index_load")
    def load_index_optimized(session_manager):
        """
        Optimized method to load the session index.
        This replaces the direct loading of all session files on startup.
        
        Args:
            session_manager: The SessionManager instance
        """
        # Load index first if it exists
        index_path = session_manager.get_index_path()
        if os.path.exists(index_path):
            with open(index_path, 'r', encoding='utf-8') as f:
                index = json.load(f)
            
            # Load folders
            for folder_data in index.get('folders', []):
                folder = SessionFolder.from_dict(folder_data)
                session_manager.model.folders[folder.id] = folder
            
            # Only load session metadata, not full content
            sessions_metadata = index.get('sessions', {})
            for session_id, metadata in sessions_metadata.items():
                # Create a placeholder session with metadata only
                session = SessionItem(
                    title=metadata.get('title', ''),
                    session_id=session_id,
                    tags=metadata.get('tags', []),
                    favorite=metadata.get('favorite', False),
                    created=metadata.get('created'),
                    updated=metadata.get('updated')
                )
                # Note: prompt and response are left empty and loaded on demand
                session_manager.model.sessions[session_id] = session
            
            # Emit signal that sessions were loaded
            session_manager.sessions_loaded.emit()
            return True
        
        return False
    
    @staticmethod
    @PerformanceMonitor.timed("session_load")
    def load_session_content(session_manager, session_id):
        """
        Load session content on demand.
        This loads the full session file only when needed.
        
        Args:
            session_manager: The SessionManager instance
            session_id: The ID of the session to load
            
        Returns:
            The loaded session with full content, or None if not found
        """
        try:
            session = session_manager.model.get_session(session_id)
            
            # If session exists but has no content, load it
            if session and not session.prompt and not session.response:
                session_path = os.path.join(session_manager.get_sessions_path(), f"{session_id}.json")
                if os.path.exists(session_path):
                    with open(session_path, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                        # Update the content fields only
                        session.prompt = session_data.get('prompt', '')
                        session.response = session_data.get('response', '')
                        session.flow_type = session_data.get('flow_type', '')
            
            return session
        except Exception as e:
            logger.error(f"Error loading session content {session_id}: {e}")
            return None

    @staticmethod
    def apply_optimizations(session_manager):
        """
        Apply all optimizations to a SessionManager instance.
        
        Args:
            session_manager: The SessionManager instance to optimize
        """
        # Replace the load_sessions method with optimized version
        session_manager.load_sessions = lambda: OptimizedSessionManager.load_index_optimized(session_manager)
        
        # Add the load_session_content method
        session_manager.load_session_content = lambda session_id: OptimizedSessionManager.load_session_content(session_manager, session_id)
        
        # Modify the load_session method to use the content loading
        original_load_session = session_manager.load_session
        
        def optimized_load_session(session_id):
            # First try to load from memory with content
            session = session_manager.load_session_content(session_id)
            if session:
                return session
            # Fall back to original method if needed
            return original_load_session(session_id)
        
        session_manager.load_session = optimized_load_session


class OptimizedUIComponents:
    """
    Performance optimizations for UI components.
    These methods should be applied to improve UI responsiveness.
    """
    
    @staticmethod
    def optimize_text_rendering(text_edit):
        """
        Optimize a QTextEdit for better performance with large text.
        
        Args:
            text_edit: The QTextEdit instance to optimize
        """
        # Disable expensive real-time operations
        text_edit.setUndoRedoEnabled(False)
        
        # Enable line wrap at word boundaries for better performance
        text_edit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        text_edit.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        
        # Disable automatic spell checking if available
        try:
            text_edit.document().setDefaultTextOption(QTextOption(QTextOption.Flag.SuppressAdditionalTextOutput))
        except AttributeError:
            pass
        
        # Set document size limit
        text_edit.document().setMaximumBlockCount(100000)  # Limit to 100K blocks
    
    @staticmethod
    def optimize_list_view(list_view):
        """
        Optimize a QListView for better performance with many items.
        
        Args:
            list_view: The QListView instance to optimize
        """
        # Enable viewport update optimization
        list_view.setUniformItemSizes(True)
        
        # Reduce repaint events
        list_view.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        
        # Improve scrolling performance
        list_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Batch item loading
        list_view.setBatchSize(30)
    
    @staticmethod
    def optimize_tree_view(tree_view):
        """
        Optimize a QTreeView for better performance.
        
        Args:
            tree_view: The QTreeView instance to optimize
        """
        # Reduce repaint events
        tree_view.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        
        # Optimize for speed
        tree_view.setUniformRowHeights(True)
        
        # Batch item loading
        tree_view.setBatchSize(20)


# Import necessary modules to make the code work
import os
import json
from PyQt6.QtWidgets import QTextEdit, QAbstractItemView, QDialog
from PyQt6.QtGui import QTextOption
from desktop.models.session_model import SessionFolder, SessionItem
