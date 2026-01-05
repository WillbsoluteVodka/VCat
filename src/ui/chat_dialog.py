"""
Siri-style chat dialog for VCat.
A floating dialog that appears above the cat for conversation.
Supports Whisper-based voice input.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QScrollArea, QFrame,
    QGraphicsDropShadowEffect, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QTimer
from PyQt5.QtGui import QColor, QFont, QPainter, QBrush, QPen, QPainterPath

from src.chat.handler import ChatHandler

# Whisper voice transcription
try:
    from src.chat.whisper_transcriber import WhisperTranscriber, is_whisper_available
    HAS_WHISPER = is_whisper_available()
except ImportError:
    HAS_WHISPER = False

# TODO: Native macOS blur effect (NSVisualEffectView) disabled due to 
# PyQt5/PyObjC compatibility issues causing crashes. Using semi-transparent
# background as fallback. Consider PySide6 or pure Cocoa window in future.
HAS_NATIVE_BLUR = False


class MessageBubble(QFrame):
    """A single message bubble in the chat."""
    
    def __init__(self, text: str, is_user: bool, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self.setup_ui(text)
        
    def setup_ui(self, text: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        
        label = QLabel(text)
        label.setWordWrap(True)
        label.setMaximumWidth(220)
        label.setFont(QFont("PingFang SC", 13))
        
        if self.is_user:
            # User message - right aligned, blue background
            label.setStyleSheet("""
                QLabel {
                    background-color: #007AFF;
                    color: white;
                    border-radius: 12px;
                    padding: 8px 12px;
                }
            """)
            layout.addStretch()
            layout.addWidget(label)
        else:
            # Cat message - left aligned, gray background
            label.setStyleSheet("""
                QLabel {
                    background-color: rgba(60, 60, 60, 0.9);
                    color: white;
                    border-radius: 12px;
                    padding: 8px 12px;
                }
            """)
            layout.addWidget(label)
            layout.addStretch()


class ChatDialog(QWidget):
    """
    Siri-style floating chat dialog.
    Appears above the cat and allows text-based conversation.
    Uses macOS native NSVisualEffectView for blur effect when available.
    """
    
    # Signal emitted when dialog is closed
    dialog_closed = pyqtSignal()
    
    def __init__(self, pet_label=None, parent=None):
        super().__init__(parent)
        self.chat_handler = ChatHandler()
        self.pet_label = pet_label  # Reference to pet widget for position tracking
        self.position_timer = None  # Timer for updating position
        self.visual_effect_view = None  # Native macOS blur view
        self.setup_window()
        self.setup_ui()
        self._setup_native_blur()
        
    def setup_window(self):
        """Configure window properties for floating dialog."""
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool  # Prevents showing in taskbar
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(320, 400)
        
    def _setup_native_blur(self):
        """Set up macOS native blur effect using NSVisualEffectView."""
        # TODO: Native blur disabled due to PyQt5/PyObjC compatibility issues
        # Using semi-transparent fallback for now
        print("[ChatDialog] Using semi-transparent background (native blur disabled)")
    
    def showEvent(self, event):
        """Handle show event."""
        super().showEvent(event)
    
    def _delayed_blur_setup(self):
        """Setup blur after window is visible - currently disabled."""
        pass
        
    def setup_ui(self):
        """Set up the dialog UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Container widget with rounded corners and semi-transparent background
        self.container = QFrame(self)
        self.container.setObjectName("chatContainer")
        
        # Dark semi-transparent background with subtle border
        self.container.setStyleSheet("""
            QFrame#chatContainer {
                background-color: rgba(25, 25, 25, 0.88);
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.08);
            }
        """)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(12, 12, 12, 12)
        container_layout.setSpacing(8)
        
        # Header with close button
        header_layout = QHBoxLayout()
        
        title_label = QLabel("🐱 VCat")
        title_label.setFont(QFont("PingFang SC", 14, QFont.Bold))
        title_label.setStyleSheet("color: white;")
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        close_btn.clicked.connect(self.close_dialog)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(close_btn)
        
        container_layout.addLayout(header_layout)
        
        # Chat history area (scrollable)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: transparent;
                width: 6px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(255, 255, 255, 0.3);
                border-radius: 3px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        self.messages_widget = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setAlignment(Qt.AlignTop)
        self.messages_layout.setSpacing(4)
        self.messages_layout.setContentsMargins(0, 0, 0, 0)
        
        self.scroll_area.setWidget(self.messages_widget)
        container_layout.addWidget(self.scroll_area)
        
        # Input area
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)
        
        # Voice input button
        self.voice_btn = QPushButton("🎤")
        self.voice_btn.setFixedSize(36, 36)
        self.voice_btn.setFont(QFont("Apple Color Emoji", 14))
        self.voice_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
                border: none;
                border-radius: 18px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
            QPushButton:pressed {
                background-color: #FF3B30;
            }
        """)
        self.voice_btn.setToolTip("点击开始/停止语音输入 (英文)")
        self.voice_btn.clicked.connect(self.toggle_voice_input)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("跟小猫说点什么喵～")
        self.input_field.setFont(QFont("PingFang SC", 13))
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
                border: none;
                border-radius: 16px;
                padding: 8px 16px;
            }
            QLineEdit:focus {
                background-color: rgba(255, 255, 255, 0.15);
            }
        """)
        self.input_field.returnPressed.connect(self.send_message)
        
        send_btn = QPushButton("发送")
        send_btn.setFont(QFont("PingFang SC", 12))
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 16px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #0056CC;
            }
        """)
        send_btn.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.voice_btn)
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(send_btn)
        
        container_layout.addLayout(input_layout)
        
        main_layout.addWidget(self.container)
        
        # Initialize Whisper voice transcriber (lazy load)
        self.whisper = None
        self.is_voice_active = False
        
        # Update voice button tooltip based on availability
        if HAS_WHISPER:
            self.voice_btn.setToolTip("点击开始/停止语音输入")
        else:
            self.voice_btn.setToolTip("语音功能不可用")
            self.voice_btn.setEnabled(False)
        
        # Show initial greeting
        self.add_cat_greeting()
        
    def add_cat_greeting(self):
        """Add initial greeting from the cat."""
        greeting = "主人好喵～有什么想跟我说的喵？"
        bubble = MessageBubble(greeting, is_user=False)
        self.messages_layout.addWidget(bubble)
    
    def toggle_voice_input(self):
        """Toggle voice input on/off with single click."""
        if not HAS_WHISPER:
            self.input_field.setPlaceholderText("语音功能不可用喵～")
            return
            
        # Initialize Whisper on first use
        if self.whisper is None:
            self.whisper = WhisperTranscriber(model_size='base')
            self.whisper.transcription_ready.connect(self._on_transcription_ready)
            self.whisper.status_changed.connect(self._on_voice_status_changed)
            self.whisper.error_occurred.connect(self._on_voice_error)
        
        if not self.is_voice_active:
            # Start recording
            self.is_voice_active = True
            self.voice_btn.setText("⏹")
            self.voice_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF3B30;
                    color: white;
                    border: none;
                    border-radius: 18px;
                }
                QPushButton:hover {
                    background-color: #FF6B60;
                }
            """)
            self.input_field.setPlaceholderText("正在录音...说完点击停止")
            self.whisper.start_recording()
        else:
            # Stop recording and transcribe
            self.is_voice_active = False
            self._reset_voice_button()
            self.input_field.setPlaceholderText("正在识别...")
            self.whisper.stop_recording()
    
    def _on_transcription_ready(self, text: str):
        """Handle transcription result from Whisper."""
        # Insert transcribed text into input field
        current_text = self.input_field.text()
        if current_text:
            self.input_field.setText(f"{current_text} {text}")
        else:
            self.input_field.setText(text)
        self.input_field.setPlaceholderText("跟小猫说点什么喵～")
        self.input_field.setFocus()
    
    def _on_voice_status_changed(self, status: str):
        """Handle voice status updates."""
        if status:
            self.input_field.setPlaceholderText(status)
        else:
            self.input_field.setPlaceholderText("跟小猫说点什么喵～")
    
    def _on_voice_error(self, error: str):
        """Handle voice recognition error."""
        self.is_voice_active = False
        self._reset_voice_button()
        self.input_field.setPlaceholderText(f"❌ {error}")
        # Reset placeholder after 2 seconds
        QTimer.singleShot(2000, lambda: self.input_field.setPlaceholderText("跟小猫说点什么喵～"))
        
    def _reset_voice_button(self):
        """Reset voice button to default state."""
        self.voice_btn.setText("🎤")
        self.voice_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
                border: none;
                border-radius: 18px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
            
    def stop_voice_input(self):
        """Stop voice recording if active."""
        if not self.is_voice_active:
            return
            
        try:
            if self.whisper:
                self.whisper.cancel()
            
            # Reset button style
            self._reset_voice_button()
            
            self.is_voice_active = False
            self.input_field.setPlaceholderText("跟小猫说点什么喵～")
            
        except Exception as e:
            print(f"Failed to stop voice input: {e}")
        
    def send_message(self):
        """Handle sending a message."""
        text = self.input_field.text().strip()
        if not text:
            return
            
        # Add user message bubble
        user_bubble = MessageBubble(text, is_user=True)
        self.messages_layout.addWidget(user_bubble)
        
        # Clear input
        self.input_field.clear()
        
        # Get response from handler
        response = self.chat_handler.send_message(text)
        
        # Add response with slight delay for natural feeling
        QTimer.singleShot(300, lambda: self.add_response(response))
        
    def add_response(self, response: str):
        """Add cat's response to the chat."""
        cat_bubble = MessageBubble(response, is_user=False)
        self.messages_layout.addWidget(cat_bubble)
        
        # Scroll to bottom
        QTimer.singleShot(50, self.scroll_to_bottom)
        
    def scroll_to_bottom(self):
        """Scroll the chat to the bottom."""
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def close_dialog(self):
        """Close the dialog and emit signal."""
        # Stop position tracking timer
        if self.position_timer:
            self.position_timer.stop()
            self.position_timer = None
        # Stop whisper if recording
        if self.whisper:
            self.whisper.cancel()
            self.whisper = None
        self.chat_handler.clear_history()
        self.dialog_closed.emit()
        self.close()
        
    def position_near_pet(self, pet_x: int, pet_y: int, pet_width: int, pet_height: int):
        """
        Position the dialog above the pet.
        
        Args:
            pet_x, pet_y: Pet's current position
            pet_width, pet_height: Pet's dimensions
        """
        # Position dialog above the pet, centered horizontally
        dialog_x = pet_x + (pet_width // 2) - (self.width() // 2)
        dialog_y = pet_y - self.height() - 10  # 10px gap above pet
        
        # Make sure dialog stays on screen
        from PyQt5.QtWidgets import QApplication
        screen = QApplication.primaryScreen().availableGeometry()
        
        # Horizontal bounds
        if dialog_x < 10:
            dialog_x = 10
        elif dialog_x + self.width() > screen.width() - 10:
            dialog_x = screen.width() - self.width() - 10
            
        # Vertical bounds - if not enough space above, show below
        if dialog_y < 10:
            dialog_y = pet_y + pet_height + 10
            
        self.move(dialog_x, dialog_y)
        
    def show_dialog(self, pet_x: int, pet_y: int, pet_width: int, pet_height: int):
        """Show the dialog positioned near the pet."""
        self.position_near_pet(pet_x, pet_y, pet_width, pet_height)
        self.show()
        self.input_field.setFocus()
        self.raise_()
        self.activateWindow()
        
        # Start position tracking if pet_label is available
        self.start_position_tracking()
        
    def start_position_tracking(self):
        """Start timer to update dialog position following the pet."""
        if self.pet_label and not self.position_timer:
            self.position_timer = QTimer(self)
            self.position_timer.timeout.connect(self.update_position)
            self.position_timer.start(50)  # Update every 50ms for smooth following
            
    def update_position(self):
        """Update dialog position to follow the pet."""
        if not self.pet_label:
            return
            
        try:
            pet_pos = self.pet_label.pos()
            pet_size = self.pet_label.size()
            self.position_near_pet(
                pet_pos.x(),
                pet_pos.y(),
                pet_size.width(),
                pet_size.height()
            )
        except Exception:
            # Pet label might be deleted
            pass
