from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QMovie, QCursor
from PyQt5.QtCore import QPropertyAnimation, QPoint, Qt


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
        # Enable mouse tracking for hover events
        self.setMouseTracking(True)

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

    def enterEvent(self, event):
        """When mouse enters the pet widget, change cursor to pointing hand."""
        print("DEBUG: 鼠标进入小猫区域！")
        print(f"DEBUG: 小猫位置: {self.pos()}, 大小: {self.size()}")
        self.setCursor(QCursor(Qt.PointingHandCursor))
        super().enterEvent(event)

    def leaveEvent(self, event):
        """When mouse leaves the pet widget, restore default cursor."""
        print("DEBUG: 鼠标离开小猫区域！")
        self.setCursor(QCursor(Qt.ArrowCursor))
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        """When pet is clicked, log the event."""
        print("DEBUG: 检测到鼠标按下事件！")
        if event.button() == Qt.LeftButton:
            print("小猫被点击了！")
        super().mousePressEvent(event)
