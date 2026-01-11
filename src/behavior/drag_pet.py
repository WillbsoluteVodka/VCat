"""Pet dragging handler for Command+Click drag functionality.

Allows dragging the pet to any position while holding Command key.
Pauses current behavior during drag and resumes after release.
"""
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor, QMovie


class DragHandler:
    """Handles Command+Click drag interaction for the pet."""
    
    def __init__(self, parent_app):
        """Initialize drag handler.
        
        Args:
            parent_app: Reference to PetApp main window
        """
        self.parent = parent_app
        self.is_dragging = False
        self.drag_start_pos = None
        self.saved_state = None
        self.saved_pet_pos = None
    
    def handle_press(self, event):
        """Handle mouse press event.
        
        Args:
            event: QMouseEvent from mousePressEvent
            
        Returns:
            True if drag started (event handled), False otherwise
        """
        # Check if Command key is pressed (Qt.ControlModifier on macOS is Command)
        if event.modifiers() & Qt.ControlModifier:
            # Check if cursor is within pet label bounds
            cursor_pos = QCursor.pos()
            pet_global_pos = self.parent.pet_label.mapToGlobal(self.parent.pet_label.rect().topLeft())
            pet_global_rect = self.parent.pet_label.rect()
            pet_global_rect.moveTopLeft(pet_global_pos)
            
            if pet_global_rect.contains(cursor_pos):
                # Start dragging
                self.is_dragging = True
                self.drag_start_pos = event.globalPos()
                self.saved_pet_pos = self.parent.pet_label.pos()
                
                # Save current state and pause behavior
                self.saved_state = self.parent.pet_behavior.current_state
                self.parent.behavior_manager.pause_all()
                
                # Play drag animation
                self._play_drag_animation()
                
                print(f"[VCat] Command+Drag started - paused at state: {self.saved_state}")
                return True
        
        return False
    
    def handle_move(self, event):
        """Handle mouse move event.
        
        Args:
            event: QMouseEvent from mouseMoveEvent
            
        Returns:
            True if drag in progress (event handled), False otherwise
        """
        if self.is_dragging and self.drag_start_pos:
            # Calculate the delta from drag start
            delta = event.globalPos() - self.drag_start_pos
            
            # Move the pet label
            new_pos = self.saved_pet_pos + delta
            self.parent.pet_label.move(new_pos)
            return True
        
        return False
    
    def handle_release(self, event):
        """Handle mouse release event.
        
        Args:
            event: QMouseEvent from mouseReleaseEvent
            
        Returns:
            True if drag ended (event handled), False otherwise
        """
        if self.is_dragging:
            self.is_dragging = False
            self.drag_start_pos = None
            self.saved_pet_pos = None
            
            # Resume behavior with saved state
            if self.saved_state is not None:
                print(f"[VCat] Command+Drag released - resuming state: {self.saved_state}")
                self.parent.behavior_manager.resume_with_state(
                    self.parent.pet_behavior, 
                    self.saved_state
                )
                self.saved_state = None
            
            return True
        
        return False
    
    def _play_drag_animation(self):
        """Play the drag animation GIF on the pet label."""
        from pet_data_loader import load_pet_data
        from main_window import resource_path
        
        drag_gif_path = resource_path(
            load_pet_data(self.parent.pet_kind, self.parent.pet_color, "drag")
        )
        drag_movie = QMovie(drag_gif_path)
        self.parent.pet_label.setMovie(drag_movie)
        self.parent.pet_label.setScaledContents(True)
        drag_movie.start()
