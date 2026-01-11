"""
Siri-style chat dialog for VCat.
Inspired by macOS Sequoia Siri design with glass morphism and gradient effects.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QScrollArea, QFrame,
    QGraphicsDropShadowEffect, QApplication, QDialog
)
import math

from PyQt5.QtCore import (
    Qt,
    pyqtSignal,
    QTimer,
    QRectF,
    QPointF,
    QPoint,
    QPropertyAnimation,
    QEasingCurve,
)
from PyQt5.QtGui import (
    QColor, QFont, QPainter, QBrush, QPen, QPainterPath, 
    QLinearGradient, QRadialGradient
)

from src.chat.handler import ChatHandler
from src.ui.llm_settings_panel import LLMSettingsPanel
from src.ui.setup_wizard import SetupWizard

# Whisper voice transcription
try:
    from src.chat.whisper_transcriber import WhisperTranscriber, is_whisper_available
    HAS_WHISPER = is_whisper_available()
except ImportError:
    HAS_WHISPER = False


class SiriGradientBubble(QWidget):
    """Siri-style gradient bubble for responses."""
    
    def __init__(self, text: str, parent=None, is_error: bool = False):
        super().__init__(parent)
        self.text = text
        self.is_error = is_error
        self.label = None
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(0)
        
        # Create gradient bubble container
        self.bubble = QWidget()
        self.bubble.setMinimumWidth(100)
        self.bubble.setMaximumWidth(280)
        
        bubble_layout = QVBoxLayout(self.bubble)
        bubble_layout.setContentsMargins(16, 12, 16, 12)
        
        self.label = QLabel(self.text)
        self.label.setWordWrap(True)
        self.label.setFont(QFont(".AppleSystemUIFont", 14))
        self.label.setStyleSheet("color: white; background: transparent;")
        self.label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        bubble_layout.addWidget(self.label)
        
        layout.addWidget(self.bubble)
        layout.addStretch()
        
        self.setStyleSheet("background: transparent;")
        self.bubble.setStyleSheet("background: transparent;")
        
    def paintEvent(self, event):
        if not self.bubble:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Get bubble geometry
        bubble_rect = self.bubble.geometry()
        
        # Create rounded path
        path = QPainterPath()
        path.addRoundedRect(QRectF(bubble_rect), 18, 18)
        
        # ChatGPT-style: clean dark gray background
        if self.is_error:
            painter.fillPath(path, QBrush(QColor(120, 40, 40, 230)))
        else:
            painter.fillPath(path, QBrush(QColor(55, 55, 60, 245)))
        
        # Subtle top highlight for depth
        highlight_path = QPainterPath()
        highlight_rect = QRectF(bubble_rect)
        highlight_rect.setHeight(min(30, bubble_rect.height() / 2))
        highlight_path.addRoundedRect(highlight_rect, 18, 18)
        
        highlight = QLinearGradient(
            bubble_rect.left(),
            bubble_rect.top(),
            bubble_rect.left(),
            bubble_rect.top() + 30,
        )
        highlight_alpha = 6 if self.is_error else 12
        highlight.setColorAt(0, QColor(255, 255, 255, highlight_alpha))
        highlight.setColorAt(1, QColor(255, 255, 255, 0))
        painter.fillPath(highlight_path, QBrush(highlight))
        
        painter.end()

    def append_text(self, chunk: str):
        if not chunk:
            return
        self.text += chunk
        self.label.setText(self.text)

    def set_text(self, text: str):
        self.text = text or ""
        self.label.setText(self.text)


class UserBubble(QWidget):
    """User message bubble."""
    
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self.text = text
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        
        layout.addStretch()
        
        self.label = QLabel(self.text)
        self.label.setWordWrap(True)
        self.label.setMaximumWidth(220)
        self.label.setFont(QFont(".AppleSystemUIFont", 14))
        self.label.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 255, 0.18);
                color: white;
                border-radius: 18px;
                padding: 10px 16px;
            }
        """)
        layout.addWidget(self.label)
        
        self.setStyleSheet("background: transparent;")


class SiriInputBar(QWidget):
    """Siri-style input bar with gradient border."""
    
    textSubmitted = pyqtSignal(str)
    voiceClicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.input_field = None
        self.setup_ui()
        
    def setup_ui(self):
        self.setFixedHeight(56)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(0)
        
        # Input field
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("跟小猫说点什么喵～")
        self.input_field.setFont(QFont(".AppleSystemUIFont", 15))
        self.input_field.setStyleSheet("""
            QLineEdit {
                background: transparent;
                color: white;
                border: none;
                padding: 0 16px;
            }
            QLineEdit::placeholder {
                color: rgba(255, 255, 255, 0.45);
            }
        """)
        self.input_field.returnPressed.connect(self._on_submit)
        
        # Voice button
        self.voice_btn = QPushButton()
        self.voice_btn.setFixedSize(36, 36)
        self.voice_btn.setCursor(Qt.PointingHandCursor)
        self.voice_btn.clicked.connect(self.voiceClicked.emit)
        self.voice_btn.setStyleSheet("background: transparent; border: none;")
        
        layout.addWidget(self.input_field, 1)
        layout.addWidget(self.voice_btn)
        
    def _on_submit(self):
        text = self.input_field.text().strip()
        if text:
            self.textSubmitted.emit(text)
            self.input_field.clear()
            
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect()
        
        # Create pill shape path
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect).adjusted(1, 1, -1, -1), 24, 24)
        
        # Dark glass background
        painter.fillPath(path, QBrush(QColor(30, 30, 35, 200)))
        
        # Gradient border (Siri style - subtle rainbow)
        gradient = QLinearGradient(0, 0, rect.width(), 0)
        gradient.setColorAt(0, QColor(255, 100, 150, 80))     # Pink
        gradient.setColorAt(0.3, QColor(150, 100, 200, 80))   # Purple  
        gradient.setColorAt(0.6, QColor(100, 150, 255, 80))   # Blue
        gradient.setColorAt(1, QColor(100, 200, 200, 80))     # Cyan
        
        painter.setPen(QPen(QBrush(gradient), 1.5))
        painter.drawPath(path)
        
        # Draw mic icon
        mic_center = QPointF(self.voice_btn.geometry().center())
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 255, 255, 150))
        
        # Mic body
        mic_path = QPainterPath()
        mic_path.addRoundedRect(mic_center.x() - 3, mic_center.y() - 8, 6, 11, 3, 3)
        painter.drawPath(mic_path)
        
        # Mic arc
        painter.setPen(QPen(QColor(255, 255, 255, 150), 1.5))
        painter.setBrush(Qt.NoBrush)
        painter.drawArc(
            int(mic_center.x()) - 6, int(mic_center.y()) - 3,
            12, 10, 0, -180 * 16
        )
        # Mic stand
        painter.drawLine(
            int(mic_center.x()), int(mic_center.y()) + 5,
            int(mic_center.x()), int(mic_center.y()) + 9
        )
        
        painter.end()
        
    def set_placeholder(self, text: str):
        self.input_field.setPlaceholderText(text)
        
    def text(self):
        return self.input_field.text()
        
    def clear(self):
        self.input_field.clear()
        
    def setFocus(self):
        self.input_field.setFocus()


class GearButton(QPushButton):
    """Minimal gear icon button drawn with QPainter."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(28, 28)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("background: transparent; border: none;")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        color = QColor(255, 255, 255, 200 if self.underMouse() else 140)
        center = self.rect().center()
        radius = 7

        painter.setPen(Qt.NoPen)
        painter.setBrush(color)

        for i in range(6):
            angle = math.radians(i * 60)
            x = center.x() + math.cos(angle) * (radius + 4) - 2
            y = center.y() + math.sin(angle) * (radius + 4) - 2
            painter.drawRoundedRect(int(x), int(y), 4, 4, 1.5, 1.5)

        painter.drawEllipse(center, radius, radius)

        painter.setBrush(QColor(20, 20, 25, 255))
        painter.drawEllipse(center, 3, 3)

        painter.end()


class ChatDialog(QWidget):
    """
    Siri-inspired floating chat dialog.
    Clean, minimal design with gradient effects.
    """
    
    dialog_closed = pyqtSignal()
    
    def __init__(self, pet_label=None, parent=None):
        super().__init__(parent)
        self.chat_handler = ChatHandler()
        self.pet_label = pet_label
        self.position_timer = None
        self.whisper = None
        self.is_voice_active = False
        self.active_response_bubble = None
        self.settings_panel = None
        self.panel_animation = None
        self.panel_visible = False
        self.setup_wizard = None
        
        # Drag support
        self._drag_pos = None
        self._is_dragging = False
        
        self.setup_window()
        self.setup_ui()

        self.chat_handler.response_chunk.connect(self._on_response_chunk)
        self.chat_handler.response_complete.connect(self._on_response_complete)
        self.chat_handler.response_error.connect(self._on_response_error)
        
    def setup_window(self):
        """Configure window."""
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(360, 460)
        
    def setup_ui(self):
        """Build the UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(0)
        
        # Main container
        self.container = QWidget()
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(12)
        
        # Header
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 10, 12, 8)
        
        # Close button (minimal, transparent)
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setFont(QFont(".AppleSystemUIFont", 15))
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: rgba(255, 255, 255, 0.4);
                border: none;
            }
            QPushButton:hover {
                color: rgba(255, 255, 255, 0.8);
            }
        """)
        close_btn.clicked.connect(self.close_dialog)

        # Title
        cat_title = QLabel("VCat")
        cat_title.setFont(QFont(".AppleSystemUIFont", 15, QFont.Medium))
        cat_title.setStyleSheet("color: white; background: transparent;")

        # Settings button
        settings_btn = GearButton()
        settings_btn.clicked.connect(self.toggle_settings_panel)

        header_layout.addWidget(close_btn)
        header_layout.addStretch()
        header_layout.addWidget(cat_title)
        header_layout.addStretch()
        header_layout.addWidget(settings_btn)
        
        header.setStyleSheet("background: transparent;")
        container_layout.addWidget(header)
        
        # Chat area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 4px;
                margin: 8px 2px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.25);
                border-radius: 2px;
                min-height: 30px;
            }
            QScrollBar::add-line:vertical, 
            QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: transparent;
                height: 0px;
            }
        """)
        
        self.messages_widget = QWidget()
        self.messages_widget.setStyleSheet("background: transparent;")
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setAlignment(Qt.AlignTop)
        self.messages_layout.setSpacing(8)
        self.messages_layout.setContentsMargins(16, 8, 16, 8)
        
        self.scroll_area.setWidget(self.messages_widget)
        container_layout.addWidget(self.scroll_area, 1)
        
        # Input bar
        self.input_bar = SiriInputBar()
        self.input_bar.textSubmitted.connect(self.send_message)
        self.input_bar.voiceClicked.connect(self.toggle_voice_input)
        
        if not HAS_WHISPER:
            self.input_bar.voice_btn.setEnabled(False)

        self.input_bar.set_placeholder(self._default_placeholder())
            
        container_layout.addWidget(self.input_bar)
        
        main_layout.addWidget(self.container)

        # Settings panel (slide-in)
        self.settings_panel = LLMSettingsPanel(self.container)
        self.settings_panel.saved.connect(self._on_settings_saved)
        self.settings_panel.closed.connect(self.hide_settings_panel)
        self.settings_panel.hide()
        QTimer.singleShot(0, self._update_settings_panel_geometry)
        
        # Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(50)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 8)
        self.container.setGraphicsEffect(shadow)
        
        # Add greeting
        self.add_greeting()

        QTimer.singleShot(0, self.ensure_llm_setup)
        
    def paintEvent(self, event):
        """Draw the glass background."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Container rect (accounting for margins)
        rect = self.container.geometry()
        
        # Main glass background
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), 28, 28)
        
        # Dark translucent background
        painter.fillPath(path, QBrush(QColor(20, 20, 25, 235)))
        
        # Subtle gradient overlay for depth
        overlay = QLinearGradient(rect.left(), rect.top(), rect.left(), rect.bottom())
        overlay.setColorAt(0, QColor(255, 255, 255, 8))
        overlay.setColorAt(0.1, QColor(255, 255, 255, 0))
        overlay.setColorAt(1, QColor(0, 0, 0, 20))
        painter.fillPath(path, QBrush(overlay))
        
        # Very subtle border
        painter.setPen(QPen(QColor(255, 255, 255, 15), 0.5))
        painter.drawPath(path)
        
        painter.end()
        
    def add_greeting(self):
        """Show initial greeting."""
        language = self.chat_handler.config.get("language", "zh")
        if language == "en":
            greeting = "Hi! I'm VCat. What would you like to chat about? 喵～"
        else:
            greeting = "主人好喵～有什么想跟我说的喵？"
        bubble = SiriGradientBubble(greeting)
        self.messages_layout.addWidget(bubble)

    def _default_placeholder(self) -> str:
        language = self.chat_handler.config.get("language", "zh")
        if language == "en":
            return "Say something to VCat..."
        return "跟小猫说点什么喵～"

    def _setup_required_text(self, include_meow: bool = False) -> str:
        language = self.chat_handler.config.get("language", "zh")
        if language == "en":
            base = "Please complete LLM setup"
        else:
            base = "请先完成 LLM 配置"
        if include_meow:
            return f"{base}喵～"
        return base

    def _streaming_placeholder(self) -> str:
        language = self.chat_handler.config.get("language", "zh")
        if language == "en":
            return "Replying..."
        return "正在回复..."
        
    def toggle_voice_input(self):
        """Toggle voice."""
        if not HAS_WHISPER:
            return
            
        if self.whisper is None:
            self.whisper = WhisperTranscriber(model_size='base')
            self.whisper.transcription_ready.connect(self._on_transcription)
            self.whisper.status_changed.connect(self._on_voice_status)
            self.whisper.error_occurred.connect(self._on_voice_error)
        
        if not self.is_voice_active:
            self.is_voice_active = True
            self.input_bar.set_placeholder("语音输入中...")
            self.whisper.start_recording()
        else:
            self.is_voice_active = False
            self.input_bar.set_placeholder("正在识别...")
            self.whisper.stop_recording()
            
    def _on_transcription(self, text: str):
        self.is_voice_active = False
        current = self.input_bar.text()
        if current:
            self.input_bar.input_field.setText(f"{current} {text}")
        else:
            self.input_bar.input_field.setText(text)
        self.input_bar.set_placeholder(self._default_placeholder())
        self.input_bar.setFocus()
        
    def _on_voice_status(self, status: str):
        if status:
            self.input_bar.set_placeholder(status)
            
    def _on_voice_error(self, error: str):
        self.is_voice_active = False
        self.input_bar.set_placeholder(f"错误: {error}")
        QTimer.singleShot(2000, lambda: self.input_bar.set_placeholder(self._default_placeholder()))
        
    def send_message(self, text: str = None):
        """Send message."""
        if text is None:
            text = self.input_bar.text().strip()
        if not text:
            return

        if not self.input_bar.input_field.isEnabled():
            return
            
        # User bubble
        user_bubble = UserBubble(text)
        self.messages_layout.addWidget(user_bubble)
        self.input_bar.clear()
        self.scroll_to_bottom()

        result = self.chat_handler.send_message(text)
        if result.kind == "command":
            if result.action == "new_session":
                self.clear_messages()
            if result.action == "open_settings":
                self.show_settings_panel()
            if result.response:
                QTimer.singleShot(200, lambda: self.add_response(result.response))
            return

        if result.kind == "error":
            self.add_response(result.response, is_error=True)
            if result.action == "open_setup":
                self.open_setup_wizard()
            return

        if result.kind == "stream":
            self._start_streaming_response()
        
    def add_response(self, response: str, is_error: bool = False):
        """Add cat response."""
        bubble = SiriGradientBubble(response, is_error=is_error)
        self.messages_layout.addWidget(bubble)
        QTimer.singleShot(50, self.scroll_to_bottom)
        
    def scroll_to_bottom(self):
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear_messages(self):
        while self.messages_layout.count():
            item = self.messages_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.add_greeting()

    def set_input_enabled(self, enabled: bool, placeholder: str = None):
        self.input_bar.input_field.setEnabled(enabled)
        self.input_bar.voice_btn.setEnabled(enabled and HAS_WHISPER)
        if placeholder is not None:
            self.input_bar.set_placeholder(placeholder)
        elif enabled:
            self.input_bar.set_placeholder(self._default_placeholder())

    def ensure_llm_setup(self):
        if self.chat_handler.is_configured():
            self.set_input_enabled(True)
            return
        self.set_input_enabled(False, self._setup_required_text())
        self.open_setup_wizard()

    def open_setup_wizard(self):
        if self.setup_wizard and self.setup_wizard.isVisible():
            return
        wizard = SetupWizard(self)
        self.setup_wizard = wizard
        wizard.configured.connect(self._on_settings_saved)
        result = wizard.exec_()
        if result != QDialog.Accepted:
            self.add_response(self._setup_required_text(include_meow=True), is_error=True)

    def _on_settings_saved(self):
        self.chat_handler.reload_config()
        if self.chat_handler.is_configured():
            self.set_input_enabled(True)
        else:
            self.set_input_enabled(False, self._setup_required_text())

    def _start_streaming_response(self):
        self.active_response_bubble = SiriGradientBubble("")
        self.messages_layout.addWidget(self.active_response_bubble)
        self.scroll_to_bottom()
        self.set_input_enabled(False, self._streaming_placeholder())

    def _on_response_chunk(self, chunk: str):
        if not self.active_response_bubble:
            self.active_response_bubble = SiriGradientBubble("")
            self.messages_layout.addWidget(self.active_response_bubble)
        self.active_response_bubble.append_text(chunk)
        self.scroll_to_bottom()

    def _on_response_complete(self, response: str):
        if not self.active_response_bubble:
            self.add_response(response)
        else:
            if not self.active_response_bubble.text:
                self.active_response_bubble.set_text(response)
        self.active_response_bubble = None
        if self.chat_handler.is_configured():
            self.set_input_enabled(True)
        self.scroll_to_bottom()

    def _on_response_error(self, message: str):
        if self.active_response_bubble:
            self.active_response_bubble.is_error = True
            self.active_response_bubble.set_text(message)
            self.active_response_bubble.update()
            self.active_response_bubble = None
        else:
            self.add_response(message, is_error=True)
        if self.chat_handler.is_configured():
            self.set_input_enabled(True)
        self.scroll_to_bottom()

    def _update_settings_panel_geometry(self):
        if not self.settings_panel:
            return
        panel_width = 280
        self.settings_panel.setFixedWidth(panel_width)
        self.settings_panel.setFixedHeight(self.container.height())
        base_x = self.container.geometry().x()
        base_y = self.container.geometry().y()
        hidden_x = base_x + self.container.width()
        visible_x = hidden_x - panel_width
        x = visible_x if self.panel_visible else hidden_x
        self.settings_panel.move(x, base_y)

    def toggle_settings_panel(self):
        if self.panel_visible:
            self.hide_settings_panel()
        else:
            self.show_settings_panel()

    def show_settings_panel(self):
        if not self.settings_panel:
            return
        self.panel_visible = True
        self.settings_panel.show()
        self.settings_panel.raise_()
        self._animate_settings_panel(True)

    def hide_settings_panel(self):
        if not self.settings_panel:
            return
        self.panel_visible = False
        self._animate_settings_panel(False)

    def _animate_settings_panel(self, show: bool):
        self._update_settings_panel_geometry()
        start_pos = self.settings_panel.pos()
        base_x = self.container.geometry().x()
        base_y = self.container.geometry().y()
        hidden_x = base_x + self.container.width()
        visible_x = hidden_x - self.settings_panel.width()
        end_x = visible_x if show else hidden_x
        end_pos = QPoint(end_x, base_y)

        self.panel_animation = QPropertyAnimation(self.settings_panel, b"pos", self)
        self.panel_animation.setDuration(220)
        self.panel_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.panel_animation.setStartValue(start_pos)
        self.panel_animation.setEndValue(end_pos)
        if not show:
            self.panel_animation.finished.connect(self.settings_panel.hide)
        self.panel_animation.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_settings_panel_geometry()
    
    # ===== Drag support =====
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            self._is_dragging = True
            # Stop following pet when user starts dragging
            if self.position_timer:
                self.position_timer.stop()
                self.position_timer = None
            event.accept()
    
    def mouseMoveEvent(self, event):
        if self._is_dragging and self._drag_pos is not None:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._is_dragging = False
            self._drag_pos = None
            event.accept()
        
    def close_dialog(self):
        if self.position_timer:
            self.position_timer.stop()
            self.position_timer = None
        if self.whisper:
            self.whisper.cancel()
            self.whisper = None
        self.chat_handler.clear_history()
        self.dialog_closed.emit()
        self.close()
        
    def position_near_pet(self, pet_x: int, pet_y: int, pet_width: int, pet_height: int):
        margin = 10
        dialog_width = self.width()
        dialog_height = self.height()
        center_x = pet_x + (pet_width // 2) - (dialog_width // 2)
        above_y = pet_y - dialog_height - margin
        below_y = pet_y + pet_height + margin
        screen = self.pet_label.screen() if self.pet_label else None
        if not screen:
            screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        screen_left = screen_geometry.left()
        screen_top = screen_geometry.top()
        screen_right = screen_left + screen_geometry.width()
        screen_bottom = screen_top + screen_geometry.height()

        def clamp_position(x, y):
            x = max(screen_left + margin, min(x, screen_right - dialog_width - margin))
            y = max(screen_top + margin, min(y, screen_bottom - dialog_height - margin))
            return x, y

        if above_y >= screen_top + margin:
            dialog_x, dialog_y = clamp_position(center_x, above_y)
        elif below_y + dialog_height <= screen_bottom - margin:
            dialog_x, dialog_y = clamp_position(center_x, below_y)
        else:
            left_x = pet_x - dialog_width - margin
            right_x = pet_x + pet_width + margin
            if right_x + dialog_width <= screen_right - margin:
                dialog_x, dialog_y = clamp_position(
                    right_x,
                    pet_y + (pet_height // 2) - (dialog_height // 2)
                )
            elif left_x >= screen_left + margin:
                dialog_x, dialog_y = clamp_position(
                    left_x,
                    pet_y + (pet_height // 2) - (dialog_height // 2)
                )
            else:
                dialog_x, dialog_y = clamp_position(center_x, above_y)

        self.move(dialog_x, dialog_y)
        
    def show_dialog(self, pet_x: int, pet_y: int, pet_width: int, pet_height: int):
        if self.pet_label:
            pet_pos = self.pet_label.mapToGlobal(QPoint(0, 0))
            pet_x = pet_pos.x()
            pet_y = pet_pos.y()
            pet_width = self.pet_label.width()
            pet_height = self.pet_label.height()
        self.position_near_pet(pet_x, pet_y, pet_width, pet_height)
        self.show()
        self.input_bar.setFocus()
        self.raise_()
        self.activateWindow()
        self.start_position_tracking()
        
    def start_position_tracking(self):
        if self.pet_label and not self.position_timer:
            self.position_timer = QTimer(self)
            self.position_timer.timeout.connect(self.update_position)
            self.position_timer.start(50)
            
    def update_position(self):
        if not self.pet_label:
            return
        try:
            pos = self.pet_label.mapToGlobal(QPoint(0, 0))
            size = self.pet_label.size()
            self.position_near_pet(pos.x(), pos.y(), size.width(), size.height())
        except Exception:
            pass
