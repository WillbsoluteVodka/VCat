"""
VCat Settings Window - Apple Design Style
Comprehensive settings management with behavior probability controls.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QSpinBox, QRadioButton, QButtonGroup, QFrame,
    QMessageBox, QGraphicsDropShadowEffect, QWidget, QScrollArea,
    QCheckBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPainter, QBrush

from src.behavior.config import load_behavior_config, save_behavior_config, get_default_config


class ToggleSwitch(QWidget):
    """Apple-style toggle switch widget."""
    
    toggled = pyqtSignal(bool)
    
    def __init__(self, checked=True, parent=None):
        super().__init__(parent)
        self._checked = checked
        self.setFixedSize(51, 31)
        self.setCursor(Qt.PointingHandCursor)
    
    def isChecked(self):
        return self._checked
    
    def setChecked(self, checked):
        if self._checked != checked:
            self._checked = checked
            self.update()
            self.toggled.emit(self._checked)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._checked = not self._checked
            self.update()
            self.toggled.emit(self._checked)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background
        if self._checked:
            painter.setBrush(QBrush(QColor("#D97757")))  # Active color (coral)
        else:
            painter.setBrush(QBrush(QColor("#E5E5E5")))  # Inactive color (gray)
        
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, 51, 31, 15.5, 15.5)
        
        # Thumb (white circle)
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        thumb_x = 22 if self._checked else 2
        painter.drawEllipse(thumb_x, 2, 27, 27)


class ProbabilityControl(QWidget):
    """Slider + SpinBox combo for probability (0-100%)."""

    valueChanged = pyqtSignal(int)

    def __init__(self, label_text, default_value=50):
        super().__init__()
        self.setup_ui(label_text, default_value)

    def setup_ui(self, label_text, default_value):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Label
        label = QLabel(label_text)
        label.setFont(QFont(".AppleSystemUIFont", 13))
        label.setStyleSheet("color: #666666;")
        layout.addWidget(label)

        # Slider and spinbox row
        control_layout = QHBoxLayout()
        control_layout.setSpacing(12)

        # Slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(default_value)
        self.slider.setFixedHeight(24)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 4px;
                background: #E5E5E5;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: white;
                border: 1px solid #D5D5D5;
                width: 18px;
                height: 18px;
                margin: -7px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                border: 1px solid #B5B5B5;
            }
            QSlider::sub-page:horizontal {
                background: #D97757;
                border-radius: 2px;
            }
        """)
        self.slider.valueChanged.connect(self._on_slider_changed)
        control_layout.addWidget(self.slider, 1)

        # SpinBox
        self.spinbox = QSpinBox()
        self.spinbox.setRange(0, 100)
        self.spinbox.setSuffix("%")
        self.spinbox.setValue(default_value)
        self.spinbox.setFixedWidth(70)
        self.spinbox.setFixedHeight(28)
        self.spinbox.setAlignment(Qt.AlignCenter)
        self.spinbox.setFont(QFont(".AppleSystemUIFont", 13))
        self.spinbox.setStyleSheet("""
            QSpinBox {
                background-color: #F5F5F4;
                border: 1px solid #E5E5E5;
                border-radius: 6px;
                padding: 4px 8px;
                color: #1A1A1A;
            }
            QSpinBox:focus {
                border: 1px solid #D97757;
                background-color: #FFFFFF;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 0px;
                border: none;
            }
        """)
        self.spinbox.valueChanged.connect(self._on_spinbox_changed)
        control_layout.addWidget(self.spinbox)

        layout.addLayout(control_layout)

    def _on_slider_changed(self, value):
        self.spinbox.blockSignals(True)
        self.spinbox.setValue(value)
        self.spinbox.blockSignals(False)
        self.valueChanged.emit(value)

    def _on_spinbox_changed(self, value):
        self.slider.blockSignals(True)
        self.slider.setValue(value)
        self.slider.blockSignals(False)
        self.valueChanged.emit(value)

    def value(self):
        return self.slider.value()

    def setValue(self, value):
        self.slider.setValue(value)


class SettingsWindow(QDialog):
    """VCat Settings Window - Apple Design Style."""

    def __init__(self, parent_app):
        super().__init__()
        self.parent_app = parent_app
        self.config = load_behavior_config()

        # Store probability controls
        self.walking_sitting_control = None
        self.sitting_coding_control = None
        self.sitting_sleeping_control = None

        # Store size slider
        self.size_slider = None

        # Store position radio buttons
        self.toolbar_radio = None
        self.desktop_radio = None
        
        # Store voice wake toggle
        self.voice_wake_toggle = None

        # For dragging
        self._drag_pos = None

        self.setup_window()
        self.setup_ui()
        self.load_current_values()

    def setup_window(self):
        self.setWindowTitle("VCat Settings")
        self.setFixedSize(500, 680)
        self.setModal(True)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def setup_ui(self):
        # Main container
        container = QFrame(self)
        container.setObjectName("mainContainer")
        container.setStyleSheet("""
            #mainContainer {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: 1px solid #E5E5E5;
            }
        """)

        # Shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 8)
        container.setGraphicsEffect(shadow)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)

        # Container layout
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Title bar
        container_layout.addWidget(self._create_title_bar())

        # Scrollable content area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                width: 8px;
                background: transparent;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #D5D5D5;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #B5B5B5;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(32, 24, 32, 32)
        content_layout.setSpacing(20)

        # Pet Settings section
        content_layout.addWidget(self._section_header("Pet Settings"))
        content_layout.addSpacing(4)
        content_layout.addWidget(self._create_voice_wake_card())
        content_layout.addWidget(self._create_chat_card())
        content_layout.addWidget(self._create_pet_card())
        content_layout.addWidget(self._create_size_card())
        content_layout.addWidget(self._create_position_card())

        # Divider
        content_layout.addSpacing(8)
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet("background-color: #E5E5E5;")
        content_layout.addWidget(divider)
        content_layout.addSpacing(8)

        # Behavior Probabilities section
        content_layout.addWidget(self._section_header("Behavior Probabilities"))
        content_layout.addSpacing(4)

        walking_sitting_card, self.walking_sitting_control = self._create_probability_card(
            "Walking → Sitting", "walking_to_sitting"
        )
        sitting_coding_card, self.sitting_coding_control = self._create_probability_card(
            "Sitting → Coding", "sitting_to_coding"
        )
        sitting_sleeping_card, self.sitting_sleeping_control = self._create_probability_card(
            "Sitting → Sleeping", "sitting_to_sleeping"
        )

        content_layout.addWidget(walking_sitting_card)
        content_layout.addWidget(sitting_coding_card)
        content_layout.addWidget(sitting_sleeping_card)

        content_layout.addStretch()

        scroll.setWidget(content_widget)
        container_layout.addWidget(scroll, 1)

        # Action buttons (fixed at bottom)
        container_layout.addWidget(self._create_action_buttons())

    def _create_title_bar(self):
        """Title bar with draggable area and close button."""
        bar = QFrame()
        bar.setFixedHeight(56)
        bar.setStyleSheet("background-color: #FFFFFF; border-top-left-radius: 16px; border-top-right-radius: 16px;")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(24, 16, 20, 16)

        title = QLabel("🐱 VCat Settings")
        title.setFont(QFont(".AppleSystemUIFont", 16, QFont.Medium))
        title.setStyleSheet("color: #1A1A1A;")
        layout.addWidget(title)

        layout.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setFont(QFont(".AppleSystemUIFont", 16))
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #999999;
                border: none;
                border-radius: 14px;
            }
            QPushButton:hover {
                color: #666666;
                background: #F5F5F4;
            }
        """)
        close_btn.clicked.connect(self.reject)
        layout.addWidget(close_btn)

        return bar

    def _section_header(self, text):
        label = QLabel(text)
        label.setFont(QFont(".AppleSystemUIFont", 18, QFont.DemiBold))
        label.setStyleSheet("color: #1A1A1A;")
        return label

    def _create_card(self):
        """Create a base card frame."""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #F5F5F4;
                border-radius: 12px;
                border: 1px solid #E5E5E5;
            }
        """)
        return card

    def _create_voice_wake_card(self):
        """Voice Wake-up toggle card with description below."""
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(6)
        
        # Card with rounder corners
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #F5F5F4;
                border-radius: 16px;
                border: 1px solid #E5E5E5;
            }
        """)
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(16, 14, 16, 14)

        label = QLabel("🎤 Voice Wake-up")
        label.setFont(QFont(".AppleSystemUIFont", 14))
        label.setStyleSheet("color: #1A1A1A;")
        card_layout.addWidget(label)
        card_layout.addStretch()

        # Toggle switch
        self.voice_wake_toggle = ToggleSwitch(checked=self.config.get("voice_wake_enabled", True))
        self.voice_wake_toggle.toggled.connect(self._on_voice_wake_toggled)
        card_layout.addWidget(self.voice_wake_toggle)
        
        container_layout.addWidget(card)
        
        # Description below the card (no background)
        desc_label = QLabel("Say \"Hey Cat\" to open chat dialog")
        desc_label.setFont(QFont(".AppleSystemUIFont", 11))
        desc_label.setStyleSheet("color: #999999;")
        desc_label.setContentsMargins(4, 0, 0, 0)
        container_layout.addWidget(desc_label)

        return container

    def _create_chat_card(self):
        """Chat with Cat card."""
        card = self._create_card()
        layout = QHBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)

        label = QLabel("💬 Chat with Cat")
        label.setFont(QFont(".AppleSystemUIFont", 14))
        label.setStyleSheet("color: #1A1A1A;")
        layout.addWidget(label)
        layout.addStretch()

        btn = QPushButton("Open")
        btn.setFixedHeight(32)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(self._secondary_button_style())
        btn.clicked.connect(self._open_chat)
        layout.addWidget(btn)

        return card

    def _create_pet_card(self):
        """Change Pet card."""
        card = self._create_card()
        layout = QHBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)

        label = QLabel("🎨 Change Pet")
        label.setFont(QFont(".AppleSystemUIFont", 14))
        label.setStyleSheet("color: #1A1A1A;")
        layout.addWidget(label)
        layout.addStretch()

        btn = QPushButton("Open")
        btn.setFixedHeight(32)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(self._secondary_button_style())
        btn.clicked.connect(self._open_pet_selection)
        layout.addWidget(btn)

        return card

    def _create_size_card(self):
        """Pet Size control without card background."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Header
        header_layout = QHBoxLayout()
        label = QLabel("📏 Pet Size")
        label.setFont(QFont(".AppleSystemUIFont", 14))
        label.setStyleSheet("color: #1A1A1A;")
        header_layout.addWidget(label)
        header_layout.addStretch()

        self.size_value_label = QLabel("30%")
        self.size_value_label.setFont(QFont(".AppleSystemUIFont", 14, QFont.Medium))
        self.size_value_label.setStyleSheet("color: #666666;")
        header_layout.addWidget(self.size_value_label)

        layout.addLayout(header_layout)

        # Slider
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setRange(2, 100)
        self.size_slider.setValue(30)
        self.size_slider.setFixedHeight(24)
        self.size_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 4px;
                background: #E5E5E5;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: white;
                border: 1px solid #D5D5D5;
                width: 18px;
                height: 18px;
                margin: -7px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                border: 1px solid #B5B5B5;
            }
            QSlider::sub-page:horizontal {
                background: #D97757;
                border-radius: 2px;
            }
        """)
        self.size_slider.valueChanged.connect(self._on_size_changed)
        layout.addWidget(self.size_slider)

        return container

    def _create_position_card(self):
        """Position control without card background."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        label = QLabel("📍 Position")
        label.setFont(QFont(".AppleSystemUIFont", 14))
        label.setStyleSheet("color: #1A1A1A;")
        layout.addWidget(label)

        radio_layout = QHBoxLayout()
        radio_layout.setSpacing(24)

        self.toolbar_radio = QRadioButton("Toolbar")
        self.desktop_radio = QRadioButton("Desktop")

        for radio in [self.toolbar_radio, self.desktop_radio]:
            radio.setFont(QFont(".AppleSystemUIFont", 13))
            radio.setCursor(Qt.PointingHandCursor)
            radio.setStyleSheet("""
                QRadioButton {
                    color: #666666;
                    spacing: 8px;
                }
                QRadioButton::indicator {
                    width: 18px;
                    height: 18px;
                }
                QRadioButton::indicator:unchecked {
                    border: 2px solid #D5D5D5;
                    border-radius: 9px;
                    background: white;
                }
                QRadioButton::indicator:checked {
                    border: 2px solid #D97757;
                    border-radius: 9px;
                    background: white;
                }
                QRadioButton::indicator:checked:after {
                    width: 10px;
                    height: 10px;
                    border-radius: 5px;
                    background: #D97757;
                    top: 2px;
                    left: 2px;
                }
            """)
            radio_layout.addWidget(radio)

        self.toolbar_radio.toggled.connect(self._on_position_changed)

        radio_layout.addStretch()
        layout.addLayout(radio_layout)

        return container

    def _create_probability_card(self, label_text, config_key):
        """Probability control without card background.

        Returns:
            Tuple[QWidget, ProbabilityControl]: The container and the control widget
        """
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        default_value = int(self.config["behavior_probabilities"][config_key] * 100)
        control = ProbabilityControl(label_text, default_value)
        control.valueChanged.connect(lambda v: self._on_probability_changed(config_key, v))
        layout.addWidget(control)

        return container, control

    def _create_action_buttons(self):
        """Reset and Save buttons."""
        container = QFrame()
        container.setStyleSheet("background-color: #FFFFFF; border-bottom-left-radius: 16px; border-bottom-right-radius: 16px;")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(32, 16, 32, 20)

        reset_btn = QPushButton("Reset to Default")
        reset_btn.setFixedHeight(40)
        reset_btn.setCursor(Qt.PointingHandCursor)
        reset_btn.setStyleSheet(self._secondary_button_style())
        reset_btn.clicked.connect(self._reset_defaults)
        layout.addWidget(reset_btn)

        layout.addStretch()

        save_btn = QPushButton("Save")
        save_btn.setFixedHeight(40)
        save_btn.setFixedWidth(100)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet(self._primary_button_style())
        save_btn.clicked.connect(self._save_settings)
        layout.addWidget(save_btn)

        return container

    def _on_size_changed(self, value):
        """Handle pet size slider change."""
        self.size_value_label.setText(f"{value}%")
        self.parent_app.pet_size_ratio = value / 100.0
        # Update pet size immediately
        if hasattr(self.parent_app, 'pet_label'):
            screen_width = self.parent_app.width()
            screen_height = self.parent_app.height()
            self.parent_app.pet_label.resize_for_window(screen_width, screen_height, self.parent_app.pet_size_ratio)

    def _on_position_changed(self, checked):
        """Handle position radio button change."""
        if not checked:
            return

        if self.toolbar_radio.isChecked():
            # Move to toolbar
            if self.parent_app.toolbar_icon is None:
                from src.menu_bar import MainMenuWindow
                # Get menu window instance
                if hasattr(self.parent_app, 'menu_window'):
                    self.parent_app.menu_window.activate_toolbar_pet()
        else:
            # Move to desktop
            if self.parent_app.toolbar_icon is not None:
                from src.menu_bar import MainMenuWindow
                if hasattr(self.parent_app, 'menu_window'):
                    self.parent_app.menu_window.deactivate_toolbar_pet()

    def _on_probability_changed(self, config_key, value):
        """Update config dict when slider changes."""
        self.config["behavior_probabilities"][config_key] = value / 100.0

    def _on_voice_wake_toggled(self, checked):
        """Handle voice wake toggle change."""
        self.config["voice_wake_enabled"] = checked
        # Apply immediately to the app
        if hasattr(self.parent_app, 'set_voice_wake_enabled'):
            self.parent_app.set_voice_wake_enabled(checked)

    def _open_chat(self):
        """Open chat dialog."""
        if self.parent_app.is_chat_dialog_open:
            QMessageBox.information(self, "提示", "Chat dialog is already open")
        else:
            self.parent_app._on_voice_wake()

    def _open_pet_selection(self):
        """Open pet selection dialog."""
        from src.menu_bar import PetSettingDialog
        dialog = PetSettingDialog(self.parent_app)
        dialog.exec_()

    def _save_settings(self):
        """Save config to file and reload manager."""
        # Update pet size in config before saving
        self.config["pet_size_ratio"] = self.parent_app.pet_size_ratio

        success, message = save_behavior_config(self.config)
        if success:
            self.parent_app.behavior_manager.reload_config()
            # Also reload pet size from config
            self.parent_app.load_pet_size_from_config()
            QMessageBox.information(self, "Success", message)
            self.accept()
        else:
            QMessageBox.critical(self, "Error", message)

    def _reset_defaults(self):
        """Reset all values to defaults."""
        reply = QMessageBox.question(
            self, "Reset Settings",
            "Reset all behavior settings to defaults?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.config = get_default_config()
            self.load_current_values()

    def load_current_values(self):
        """Load current values into UI."""
        # Load voice wake setting
        voice_wake_enabled = self.config.get("voice_wake_enabled", True)
        self.voice_wake_toggle.setChecked(voice_wake_enabled)
        
        # Load pet size from config if available, otherwise use current app value
        if "pet_size_ratio" in self.config:
            current_size = int(self.config["pet_size_ratio"] * 100)
        else:
            current_size = int(self.parent_app.pet_size_ratio * 100)
        self.size_slider.setValue(current_size)
        self.size_value_label.setText(f"{current_size}%")

        # Load position
        is_toolbar = self.parent_app.toolbar_icon is not None
        self.toolbar_radio.setChecked(is_toolbar)
        self.desktop_radio.setChecked(not is_toolbar)

        # Load probabilities
        probs = self.config["behavior_probabilities"]
        self.walking_sitting_control.setValue(int(probs["walking_to_sitting"] * 100))
        self.sitting_coding_control.setValue(int(probs["sitting_to_coding"] * 100))
        self.sitting_sleeping_control.setValue(int(probs["sitting_to_sleeping"] * 100))

    def _secondary_button_style(self):
        return """
            QPushButton {
                background-color: transparent;
                color: #666666;
                border: 1px solid #E5E5E5;
                border-radius: 8px;
                padding: 6px 20px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #F5F5F4;
                border-color: #D5D5D5;
            }
            QPushButton:pressed {
                background-color: #EBEBEA;
            }
        """

    def _primary_button_style(self):
        return """
            QPushButton {
                background-color: #D97757;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #C4684A;
            }
            QPushButton:pressed {
                background-color: #B55D42;
            }
        """

    def mousePressEvent(self, event):
        """Handle mouse press for dragging."""
        if event.button() == Qt.LeftButton:
            # Only allow dragging from title bar area (top 56px)
            if event.pos().y() <= 56:
                self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging."""
        if self._drag_pos is not None and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        """Handle mouse release."""
        self._drag_pos = None
