"""
Onboarding dialog for first-time users.
Claude-inspired clean, minimal design.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QWidget, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QColor, QPainter, QBrush, QPen, QLinearGradient

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.permissions import (
    check_microphone_permission,
    request_microphone_permission,
    is_first_launch,
    mark_onboarding_complete
)


class WakeMethodItem(QFrame):
    """A single wake method item with icon and description."""
    
    def __init__(self, icon: str, title: str, subtitle: str, parent=None):
        super().__init__(parent)
        self.setFixedHeight(64)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(14)
        
        # Icon circle
        icon_container = QFrame()
        icon_container.setFixedSize(40, 40)
        icon_container.setStyleSheet("""
            QFrame {
                background-color: #F5F5F4;
                border-radius: 20px;
            }
        """)
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("", 18))
        icon_label.setAlignment(Qt.AlignCenter)
        icon_layout.addWidget(icon_label)
        layout.addWidget(icon_container)
        
        # Text
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        title_label = QLabel(title)
        title_label.setFont(QFont(".AppleSystemUIFont", 14, QFont.Medium))
        title_label.setStyleSheet("color: #1A1A1A;")
        text_layout.addWidget(title_label)
        
        subtitle_label = QLabel(subtitle)
        subtitle_label.setFont(QFont(".AppleSystemUIFont", 12))
        subtitle_label.setStyleSheet("color: #666666;")
        text_layout.addWidget(subtitle_label)
        
        layout.addLayout(text_layout, 1)


class OnboardingDialog(QDialog):
    """
    First-launch onboarding dialog with Claude-inspired design.
    Clean, minimal, warm aesthetic.
    """
    
    completed = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("VCat")
        self.setFixedSize(420, 520)
        self.setModal(True)
        
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self._setup_ui()
        
    def _setup_ui(self):
        # Main container
        container = QFrame(self)
        container.setObjectName("container")
        container.setStyleSheet("""
            #container {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: 1px solid #E5E5E5;
            }
        """)
        
        # Add shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 8)
        container.setGraphicsEffect(shadow)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(32, 36, 32, 28)
        layout.setSpacing(0)
        
        # Cat emoji
        cat_label = QLabel("🐱")
        cat_label.setFont(QFont("", 52))
        cat_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(cat_label)
        
        layout.addSpacing(16)
        
        # Welcome text
        welcome_label = QLabel("Welcome to VCat")
        welcome_label.setFont(QFont(".AppleSystemUIFont", 24, QFont.DemiBold))
        welcome_label.setStyleSheet("color: #1A1A1A;")
        welcome_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(welcome_label)
        
        layout.addSpacing(8)
        
        # Subtitle
        subtitle_label = QLabel("Your AI companion on the desktop")
        subtitle_label.setFont(QFont(".AppleSystemUIFont", 14))
        subtitle_label.setStyleSheet("color: #666666;")
        subtitle_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle_label)
        
        layout.addSpacing(28)
        
        # Divider
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet("background-color: #E5E5E5;")
        layout.addWidget(divider)
        
        layout.addSpacing(20)
        
        # Section title
        section_label = QLabel("Three ways to start a conversation")
        section_label.setFont(QFont(".AppleSystemUIFont", 12, QFont.Medium))
        section_label.setStyleSheet("color: #999999;")
        layout.addWidget(section_label)
        
        layout.addSpacing(12)
        
        # Wake methods
        layout.addWidget(WakeMethodItem(
            "🎤", 
            'Say "Hey Cat"', 
            "Voice activation"
        ))
        
        layout.addWidget(WakeMethodItem(
            "⌨️", 
            "Press ⌘ + Shift + C", 
            "Global keyboard shortcut"
        ))
        
        layout.addWidget(WakeMethodItem(
            "🖱", 
            "Click Setting menu", 
            "Chat with Cat option"
        ))
        
        layout.addStretch()
        
        # Permission status
        self.status_label = QLabel()
        self.status_label.setFont(QFont(".AppleSystemUIFont", 12))
        self.status_label.setAlignment(Qt.AlignCenter)
        self._update_permission_status()
        layout.addWidget(self.status_label)
        
        layout.addSpacing(16)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        # Skip button
        self.skip_btn = QPushButton("Skip")
        self.skip_btn.setFont(QFont(".AppleSystemUIFont", 14))
        self.skip_btn.setFixedHeight(44)
        self.skip_btn.setCursor(Qt.PointingHandCursor)
        self.skip_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666666;
                border: 1px solid #E5E5E5;
                border-radius: 10px;
                padding: 0 20px;
            }
            QPushButton:hover {
                background-color: #F5F5F4;
                border-color: #D5D5D5;
            }
            QPushButton:pressed {
                background-color: #EBEBEA;
            }
        """)
        self.skip_btn.clicked.connect(self._on_skip)
        button_layout.addWidget(self.skip_btn)
        
        # Primary button - Claude's terracotta/coral color
        self.primary_btn = QPushButton("Enable Voice")
        self.primary_btn.setFont(QFont(".AppleSystemUIFont", 14, QFont.Medium))
        self.primary_btn.setFixedHeight(44)
        self.primary_btn.setCursor(Qt.PointingHandCursor)
        self.primary_btn.setStyleSheet("""
            QPushButton {
                background-color: #D97757;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 0 24px;
            }
            QPushButton:hover {
                background-color: #C4684A;
            }
            QPushButton:pressed {
                background-color: #B55D42;
            }
        """)
        self.primary_btn.clicked.connect(self._on_enable_voice)
        button_layout.addWidget(self.primary_btn, 1)
        
        layout.addLayout(button_layout)
        
        self._check_permission_and_update_ui()
    
    def _update_permission_status(self):
        status = check_microphone_permission()
        
        if status == 'authorized':
            self.status_label.setText("✓ Microphone access enabled")
            self.status_label.setStyleSheet("color: #16A34A;")
        elif status == 'denied':
            self.status_label.setText("Microphone access needed for voice wake")
            self.status_label.setStyleSheet("color: #D97757;")
        elif status == 'restricted':
            self.status_label.setText("Microphone restricted by system")
            self.status_label.setStyleSheet("color: #999999;")
        else:
            self.status_label.setText("Microphone access needed for voice wake")
            self.status_label.setStyleSheet("color: #666666;")
    
    def _check_permission_and_update_ui(self):
        status = check_microphone_permission()
        
        if status == 'authorized':
            self.primary_btn.setText("Get Started")
            try:
                self.primary_btn.clicked.disconnect()
            except:
                pass
            self.primary_btn.clicked.connect(self._on_complete)
            self.skip_btn.hide()
        elif status == 'denied':
            self.primary_btn.setText("Open Settings")
            try:
                self.primary_btn.clicked.disconnect()
            except:
                pass
            self.primary_btn.clicked.connect(self._on_open_preferences)
    
    def _on_enable_voice(self):
        def callback(granted):
            QTimer.singleShot(0, lambda: self._on_permission_result(granted))
        request_microphone_permission(callback)
    
    def _on_permission_result(self, granted: bool):
        self._update_permission_status()
        self._check_permission_and_update_ui()
        if granted:
            QTimer.singleShot(300, self._on_complete)
    
    def _on_open_preferences(self):
        import subprocess
        subprocess.run([
            'open', 
            'x-apple.systempreferences:com.apple.preference.security?Privacy_Microphone'
        ])
    
    def _on_skip(self):
        self._finish(mic_granted=False)
    
    def _on_complete(self):
        status = check_microphone_permission()
        self._finish(mic_granted=(status == 'authorized'))
    
    def _finish(self, mic_granted: bool):
        mark_onboarding_complete()
        self.completed.emit(mic_granted)
        self.accept()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and hasattr(self, '_drag_pos'):
            self.move(event.globalPos() - self._drag_pos)
            event.accept()


def should_show_onboarding() -> bool:
    return is_first_launch()


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    dialog = OnboardingDialog()
    dialog.completed.connect(lambda granted: print(f"Completed, mic granted: {granted}"))
    dialog.show()
    sys.exit(app.exec_())
