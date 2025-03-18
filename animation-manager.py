# desktop/theme/animation_manager.py
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QSequentialAnimationGroup, QObject, pyqtProperty, QPoint, QSize
from PyQt6.QtWidgets import QWidget

class AnimatedWidget(QObject):
    """
    Base class for adding animation capabilities to Qt widgets.
    This allows for animating various properties of widgets.
    """
    
    def __init__(self, target_widget):
        super().__init__()
        self._target = target_widget
        self._opacity = 1.0
        
        # Apply the opacity to the widget's stylesheet
        self.update_style()
    
    def get_opacity(self):
        return self._opacity
    
    def set_opacity(self, opacity):
        self._opacity = opacity
        self.update_style()
    
    # Define the pyqtProperty for opacity
    opacity = pyqtProperty(float, get_opacity, set_opacity)
    
    def update_style(self):
        """Update the widget's style sheet to reflect the opacity"""
        current_style = self._target.styleSheet()
        
        # If opacity is already defined, replace it
        if "opacity: " in current_style:
            parts = current_style.split("opacity: ")
            prefix = parts[0]
            suffix = parts[1].split(";", 1)[1] if ";" in parts[1] else ""
            new_style = f"{prefix}opacity: {self._opacity};{suffix}"
        else:
            # Otherwise, add it to the beginning
            new_style = f"opacity: {self._opacity}; {current_style}"
        
        self._target.setStyleSheet(new_style)


class AnimationManager:
    """
    Manages animations for UI elements throughout the application.
    Provides standard animations for common transitions.
    """
    
    @staticmethod
    def create_fade_animation(widget, start_value=0.0, end_value=1.0, duration=300):
        """
        Create a fade animation (opacity transition)
        
        Args:
            widget: The widget to animate
            start_value: Starting opacity (0.0 = fully transparent)
            end_value: Ending opacity (1.0 = fully opaque)
            duration: Animation duration in milliseconds
            
        Returns:
            QPropertyAnimation: The configured animation object
        """
        # Create an animated widget wrapper if not already animatable
        if not hasattr(widget, "_animated_wrapper"):
            widget._animated_wrapper = AnimatedWidget(widget)
        
        # Create the animation
        animation = QPropertyAnimation(widget._animated_wrapper, b"opacity")
        animation.setStartValue(start_value)
        animation.setEndValue(end_value)
        animation.setDuration(duration)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        return animation
    
    @staticmethod
    def create_slide_animation(widget, start_pos, end_pos, duration=300):
        """
        Create a slide animation (position transition)
        
        Args:
            widget: The widget to animate
            start_pos: Starting position (QPoint)
            end_pos: Ending position (QPoint)
            duration: Animation duration in milliseconds
            
        Returns:
            QPropertyAnimation: The configured animation object
        """
        animation = QPropertyAnimation(widget, b"pos")
        animation.setStartValue(start_pos)
        animation.setEndValue(end_pos)
        animation.setDuration(duration)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        return animation
    
    @staticmethod
    def create_resize_animation(widget, start_size, end_size, duration=300):
        """
        Create a resize animation (size transition)
        
        Args:
            widget: The widget to animate
            start_size: Starting size (QSize)
            end_size: Ending size (QSize)
            duration: Animation duration in milliseconds
            
        Returns:
            QPropertyAnimation: The configured animation object
        """
        animation = QPropertyAnimation(widget, b"size")
        animation.setStartValue(start_size)
        animation.setEndValue(end_size)
        animation.setDuration(duration)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        return animation
    
    @staticmethod
    def create_appear_animation(widget, direction="right", distance=50, duration=300):
        """
        Create an appear animation combining fade and slide
        
        Args:
            widget: The widget to animate
            direction: The direction to appear from ("left", "right", "up", "down")
            distance: The distance to slide in pixels
            duration: Animation duration in milliseconds
            
        Returns:
            QParallelAnimationGroup: The combined animation
        """
        # Determine the start position based on direction
        current_pos = widget.pos()
        if direction == "right":
            start_pos = current_pos - QPoint(distance, 0)
        elif direction == "left":
            start_pos = current_pos + QPoint(distance, 0)
        elif direction == "down":
            start_pos = current_pos - QPoint(0, distance)
        elif direction == "up":
            start_pos = current_pos + QPoint(0, distance)
        else:
            start_pos = current_pos
        
        # Create the fade and slide animations
        fade_anim = AnimationManager.create_fade_animation(widget, 0.0, 1.0, duration)
        slide_anim = AnimationManager.create_slide_animation(widget, start_pos, current_pos, duration)
        
        # Combine them into a parallel animation group
        group = QParallelAnimationGroup()
        group.addAnimation(fade_anim)
        group.addAnimation(slide_anim)
        
        return group
    
    @staticmethod
    def create_disappear_animation(widget, direction="right", distance=50, duration=300):
        """
        Create a disappear animation combining fade and slide
        
        Args:
            widget: The widget to animate
            direction: The direction to disappear to ("left", "right", "up", "down")
            distance: The distance to slide in pixels
            duration: Animation duration in milliseconds
            
        Returns:
            QParallelAnimationGroup: The combined animation
        """
        # Determine the end position based on direction
        current_pos = widget.pos()
        if direction == "right":
            end_pos = current_pos + QPoint(distance, 0)
        elif direction == "left":
            end_pos = current_pos - QPoint(distance, 0)
        elif direction == "down":
            end_pos = current_pos + QPoint(0, distance)
        elif direction == "up":
            end_pos = current_pos - QPoint(0, distance)
        else:
            end_pos = current_pos
        
        # Create the fade and slide animations
        fade_anim = AnimationManager.create_fade_animation(widget, 1.0, 0.0, duration)
        slide_anim = AnimationManager.create_slide_animation(widget, current_pos, end_pos, duration)
        
        # Combine them into a parallel animation group
        group = QParallelAnimationGroup()
        group.addAnimation(fade_anim)
        group.addAnimation(slide_anim)
        
        return group
    
    @staticmethod
    def pulse_widget(widget, scale_factor=1.05, duration=300):
        """
        Create a pulse animation to draw attention to a widget
        
        Args:
            widget: The widget to animate
            scale_factor: How much to scale the widget during the pulse
            duration: Animation duration in milliseconds
            
        Returns:
            QSequentialAnimationGroup: The pulse animation sequence
        """
        # Get original size
        original_size = widget.size()
        
        # Calculate the expanded size
        expanded_width = int(original_size.width() * scale_factor)
        expanded_height = int(original_size.height() * scale_factor)
        expanded_size = QSize(expanded_width, expanded_height)
        
        # Create grow and shrink animations
        grow_anim = AnimationManager.create_resize_animation(
            widget, original_size, expanded_size, duration // 2
        )
        shrink_anim = AnimationManager.create_resize_animation(
            widget, expanded_size, original_size, duration // 2
        )
        
        # Combine into a sequential animation
        sequence = QSequentialAnimationGroup()
        sequence.addAnimation(grow_anim)
        sequence.addAnimation(shrink_anim)
        
        return sequence
    
    @staticmethod
    def crossfade_widget(old_widget, new_widget, duration=300):
        """
        Create a crossfade transition between two widgets
        
        Args:
            old_widget: The widget to fade out
            new_widget: The widget to fade in
            duration: Animation duration in milliseconds
            
        Returns:
            QParallelAnimationGroup: The crossfade animation
        """
        # Ensure the new widget is initially invisible
        if not hasattr(new_widget, "_animated_wrapper"):
            new_widget._animated_wrapper = AnimatedWidget(new_widget)
        new_widget._animated_wrapper.set_opacity(0.0)
        
        # Create fade animations
        fade_out = AnimationManager.create_fade_animation(old_widget, 1.0, 0.0, duration)
        fade_in = AnimationManager.create_fade_animation(new_widget, 0.0, 1.0, duration)
        
        # Combine into a parallel animation
        parallel = QParallelAnimationGroup()
        parallel.addAnimation(fade_out)
        parallel.addAnimation(fade_in)
        
        return parallel
