from PyQt5.QtWidgets import QLabel, QGraphicsOpacityEffect
from PyQt5.QtGui import QMovie, QCursor
from PyQt5.QtCore import QPropertyAnimation, QPoint, Qt, QTimer, QRect


class PetWidget(QLabel):
    """Thin QLabel wrapper for the desktop pet.

    - Keeps references to QMovie and QPropertyAnimation to avoid GC issues.
    - Provides small helper API for future refactors: `set_movie`, `move_to`, `resize_for_window`.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background-color: transparent;")
        self.setScaledContents(True)
        self._movie = None
        self._animation = None
        self._name_label = None
        self._parent_window = parent
        self._hover_timer = None
        self._hover_poll_timer = None
        self._is_hovering = False
        self._name_opacity_effect = None
        self._name_fade_animation = None
        self._name_fade_delay_timer = None

    def set_movie(self, path):
        """Set and start a QMovie from path. If path is None, does nothing."""
        if not path:
            return
        try:
            if self._movie:
                self._movie.stop()
        except Exception:
            pass
        self._movie = QMovie(path)
        self.setMovie(self._movie)
        self._movie.start()

    def move_to(self, x, y, duration_ms=1000, finished_callback=None):
        """Animate the widget's position to (x, y) over `duration_ms` milliseconds.

        Keeps a reference to the animation to avoid garbage collection.
        """
        try:
            if self._animation:
                self._animation.stop()
        except Exception:
            pass
        self._animation = QPropertyAnimation(self, b"pos")
        self._animation.setDuration(int(duration_ms))
        self._animation.setStartValue(self.pos())
        self._animation.setEndValue(QPoint(int(x), int(y)))
        if finished_callback:
            self._animation.finished.connect(finished_callback)
        self._animation.start()

    def resize_for_window(self, width, height, ratio=0.12):
        """Resize pet to a sensible fraction of available space."""
        base_width = max(40, int(min(width, height) * ratio))
        base_height = int(base_width * 2 / 3)  # Height is 2/3 of width
        self.resize(base_width, base_height)
        # Update name position when pet resizes
        if self._name_label:
            self.update_name_position()
    
    def create_name_label(self, pet_name):
        """Create a name label that hovers above the pet as a separate window."""
        self._name_label = QLabel(pet_name, self._parent_window)
        self._name_label.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.WindowTransparentForInput |
            Qt.WindowDoesNotAcceptFocus
        )
        self._name_label.setAttribute(Qt.WA_TranslucentBackground)
        self._name_label.setAttribute(Qt.WA_ShowWithoutActivating)
        self._name_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._name_label.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 150);
                color: white;
                padding: 3px 8px;
                border-radius: 5px;
                font-family: "Noto Sans CJK SC";
                font-size: 20px;
                font-weight: bold;
            }
        """)
        
        # Set up opacity effect for fade animation
        self._name_opacity_effect = QGraphicsOpacityEffect()
        self._name_opacity_effect.setOpacity(0.0)  # Start hidden
        self._name_label.setGraphicsEffect(self._name_opacity_effect)
        
        self._name_label.adjustSize()
        self.update_name_position()
        self._name_label.show()
        
        # Start cursor polling to detect hover
        self._start_hover_polling()
        
        # Start cursor polling to detect hover
        self._start_hover_polling()
    
    def update_name_position(self):
        """Position the name label at the top-center of the pet."""
        if not self._name_label:
            return
        # Get pet's global position
        pet_global_pos = self.mapToGlobal(QPoint(0, 0))
        # Center horizontally, position above pet (with small offset)
        name_x = pet_global_pos.x() + (self.width() - self._name_label.width()) // 2
        name_y = pet_global_pos.y() - self._name_label.height()  # right above the pet
        self._name_label.move(name_x, name_y)
    
    def moveEvent(self, event):
        """Update name position when pet moves."""
        super().moveEvent(event)
        if self._name_label:
            self.update_name_position()
    
    def _start_hover_polling(self):
        """Start polling cursor position to detect hover."""
        if not self._hover_poll_timer:
            self._hover_poll_timer = QTimer()
            self._hover_poll_timer.setInterval(100)  # Check every 100ms
            self._hover_poll_timer.timeout.connect(self._check_hover)
            self._hover_poll_timer.start()
    
    def _check_hover(self):
        """Check if cursor is over the pet widget."""
        cursor_pos = QCursor.pos()
        label_global_pos = self.mapToGlobal(self.rect().topLeft())
        label_global_rect = QRect(label_global_pos, self.size())
        
        is_over = label_global_rect.contains(cursor_pos)
        
        if is_over and not self._is_hovering:
            # Just entered
            self._is_hovering = True
            self._on_hover_start()
        elif not is_over and self._is_hovering:
            # Just left
            self._is_hovering = False
            self._on_hover_end()
    
    def _on_hover_start(self):
        """Called when cursor enters pet area."""
        # Cancel any ongoing fade animation or delay timer
        if self._name_fade_animation:
            self._name_fade_animation.stop()
        if self._name_fade_delay_timer:
            self._name_fade_delay_timer.stop()
        
        # Show name with full opacity
        if self._name_opacity_effect:
            self._name_opacity_effect.setOpacity(1.0)
        
        # Start timer to print every 1 second (for debugging)
        if not self._hover_timer:
            self._hover_timer = QTimer()
            # self._hover_timer.timeout.connect(lambda: print("in area"))
        self._hover_timer.start(1000)  # Print every 1000ms (1 second)
    
    def _on_hover_end(self):
        """Called when cursor leaves pet area."""
        # Stop the debug print timer
        if self._hover_timer:
            self._hover_timer.stop()
        
        # Start 5 second delay timer before fading
        if not self._name_fade_delay_timer:
            self._name_fade_delay_timer = QTimer()
            self._name_fade_delay_timer.setSingleShot(True)
            self._name_fade_delay_timer.timeout.connect(self._start_fade_out)
        self._name_fade_delay_timer.start(5000)  # 5 seconds
    
    def _start_fade_out(self):
        """Start gradually fading out the name label."""
        if not self._name_opacity_effect:
            return
        
        # Create fade out animation
        self._name_fade_animation = QPropertyAnimation(self._name_opacity_effect, b"opacity")
        self._name_fade_animation.setDuration(1000)  # 1 second fade
        self._name_fade_animation.setStartValue(1.0)
        self._name_fade_animation.setEndValue(0.0)
        self._name_fade_animation.start()
