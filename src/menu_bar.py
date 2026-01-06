"""Menu UI module - VCat menu bar and dialogs."""

from PyQt5.QtGui import QMovie, QPixmap
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QAction, QMenu, QDialog, QVBoxLayout, QLineEdit, QLabel, QPushButton, QMessageBox,
    QScrollArea, QWidget, QGridLayout, QHBoxLayout, QTabWidget, QFrame
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal

from pet_data_loader import get_all_pet_kinds_and_colors, load_pet_data



class MainMenuWindow(QMainWindow):
    """Window to hold the native menu bar."""
    def __init__(self, parent_app):
        super().__init__()
        self.setWindowTitle("VCat")
        self.parent_app = parent_app

        # Create the menu bar items
        menubar = self.menuBar()
        menubar.setNativeMenuBar(True)  # Use native macOS menu bar

        # 🐱 Menu (避免 macOS 自动将 Settings/Preferences 归类到应用菜单)
        cat_menu = menubar.addMenu("🐱")

        # 设置窗口 action - 设置 NoRole 防止 macOS 自动归类
        settings_action = QAction("Settings", self)
        settings_action.setMenuRole(QAction.NoRole)  # 关键：阻止 macOS 自动移动到应用菜单
        settings_action.triggered.connect(self.open_settings_window)
        cat_menu.addAction(settings_action)

    # 测试测试测试测试测试
        # Test Menu
        test_menu = menubar.addMenu("Test")
        test_action = QAction("Test Room", self)
        test_action.triggered.connect(self.open_test_dialog)
        test_menu.addAction(test_action)
        
        # Leave Room action
        leave_room_action = QAction("Leave Room", self)
        leave_room_action.triggered.connect(self.leave_room)
        test_menu.addAction(leave_room_action)

    def open_chat_dialog(self):
        """Open the chat dialog with the cat."""
        if self.parent_app.is_chat_dialog_open:
            print("[Menu] Chat dialog already open")
            return
        print("[Menu] Opening chat dialog...")
        self.parent_app._on_voice_wake()

    def activate_toolbar_pet(self):
        """Activate the pet to move in the macOS toolbar."""
        # Check if chat dialog is open
        if self.parent_app.is_chat_dialog_open:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, "提示", "请先结束对话喵～")
            return
        print("Activating pet in the toolbar...")
        self.parent_app.activate_toolbar_pet()

    def deactivate_toolbar_pet(self):
        """Deactivate the pet to move in the macOS toolbar."""
        print("Deactivating pet in the toolbar...")
        self.parent_app.deactivate_toolbar_pet()
    
    def increase_pet_size(self):
        """Increase the pet size by 0.02."""
        self.parent_app.increase_pet_size()
    
    def decrease_pet_size(self):
        """Decrease the pet size by 0.02."""
        self.parent_app.decrease_pet_size()
        
    def open_settings_window(self):
        """Open the settings window."""
        from src.ui.settings_window import SettingsWindow
        dialog = SettingsWindow(self.parent_app)
        dialog.exec_()

    # 测试测试测试测试测试
    def open_test_dialog(self):
        """Open a dialog to input Room Number and User ID for testing."""
        # Check if chat dialog is open
        if self.parent_app.is_chat_dialog_open:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, "提示", "请先结束对话喵～")
            return
            
        dialog = QDialog(self)
        dialog.setWindowTitle("Test Room")

        layout = QVBoxLayout(dialog)

        # Room Number input
        room_label = QLabel("Room Number:", dialog)
        layout.addWidget(room_label)
        room_input = QLineEdit(dialog)
        layout.addWidget(room_input)

        # User ID input
        user_label = QLabel("User ID:", dialog)
        layout.addWidget(user_label)
        user_input = QLineEdit(dialog)
        layout.addWidget(user_input)

        # OK button
        ok_button = QPushButton("OK", dialog)
        layout.addWidget(ok_button)

        # Handle the OK button click
        def on_ok():
            room_num = room_input.text()
            user_id = user_input.text()
            if room_num and user_id:
                dialog.accept()
                self.handle_test_room(room_num, user_id)
            else:
                QMessageBox.warning(dialog, "Invalid Input", "Both Room Number and User ID are required.")

        ok_button.clicked.connect(on_ok)
        dialog.exec_()
    
    # 测试测试测试测试测试
    def handle_test_room(self, room_num, user_id):
        """Start room connection when user submits the dialog"""
        print(f"Test Room - Room Number: {room_num}, User ID: {user_id}")
        
        # Call the main app's connect_to_room method
        try:
            self.parent_app.connect_to_room(int(room_num), int(user_id))
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Failed to connect: {str(e)}")
            print(f"❌ Connection error: {e}")
    
    def leave_room(self):
        """Leave the current room without re-entering."""
        if hasattr(self.parent_app, 'room_worker') and self.parent_app.room_worker:
            reply = QMessageBox.question(
                self, 
                'Leave Room', 
                'Are you sure you want to leave the room?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.parent_app.leave_room()
                QMessageBox.information(self, "Left Room", "You have left the room.")
        else:
            QMessageBox.information(self, "Not in Room", "You are not currently in a room.")

    def open_pet_setting_dialog(self):
        """Open the Pet Setting dialog."""
        dialog = PetSettingDialog(self.parent_app)
        dialog.exec_()


class PetSettingDialog(QDialog):
    """Dialog for selecting pet kind and color."""
    def __init__(self, parent_app):
        super().__init__()
        self.setWindowTitle("Pet Settings")
        self.parent_app = parent_app
        self.active_movies = []  # Track all active QMovie objects

        # Dialog layout
        layout = QVBoxLayout(self)

        # Scrollable area for buttons
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # Retrieve all pet kinds and colors
        pet_kinds_and_colors = get_all_pet_kinds_and_colors()
        print("*"*20)
        print(pet_kinds_and_colors)

        screen_width = self.parent_app.width()  # Use the parent app's width as screen width reference
        button_width = int(screen_width * 0.1)  # Set button width to 10% of screen width

        # Dynamically create buttons for each pair of pet kind and color
        for pet_kind, colors in pet_kinds_and_colors.items():

            kind_label = QLabel(f"Pet Kind: {pet_kind}", self)
            kind_label.setAlignment(Qt.AlignCenter)
            kind_label.setStyleSheet("""
                                      font-size: 18px;
                                      font-weight: bold;
                                      font-family: 'Segoe UI Semibold', 'Noto Sans', 'Helvetica Neue', Arial, sans-serif;
                                    """)
            scroll_layout.addWidget(kind_label)

            button_layout = QHBoxLayout()
            button_layout.setSpacing(16)  # Keep consistent gaps between buttons
            button_layout.setAlignment(Qt.AlignLeft)
            for color in colors.keys():
                # Load the image for this pet kind and color (lock functionality commented out)
                gif_path = load_pet_data(pet_kind, color, "demo")
                # if lock_flag==False:
                #     gif_path = load_pet_data(pet_kind, color, "demo")
                # else:
                #     gif_path = load_pet_data(pet_kind, color, "lock")

                # Create a QPushButton
                button = QPushButton(self)
                button.setFixedSize(button_width, button_width)  # Set dynamic size
                button.setStyleSheet("""
                                    background-color: #c0c0c0;  /* silver base */
                                    border: 3px solid #1b8f6a;   /* gem-like green border */
                                    border-radius: 6px;        /* inwardly curved corners */
                                    padding: 6px;               /* keep border tucked inside */
                                """)
                button_layout.addWidget(button)

                # Add a QLabel to display the image inside the button
                gif_label = QLabel(button)
                gif_label.setFixedSize(button_width, button_width)  # Same size as button
                gif_label.setAlignment(Qt.AlignCenter)
                gif_label.setStyleSheet("background: transparent;")

                # Load and play the GIF
                movie = QMovie(gif_path)
                movie.setScaledSize(QSize(button_width, button_width))  # Resize the GIF to match the button size
                gif_label.setMovie(movie)
                movie.start()  # Start the GIF playback

                # Keep track of the active movies for cleanup later
                self.active_movies.append(movie)

                # Connect the button to save_settings (unlock functionality commented out)
                button.clicked.connect(
                    lambda _, k=pet_kind, c=color: self.save_settings(k, c)
                )
                # if lock_flag==True:
                #     button.clicked.connect(
                #         lambda _, k=pet_kind, c=color: self.unlock_pet(k, c)
                #     )
                # else:
                #     button.clicked.connect(
                #         lambda _, k=pet_kind, c=color: self.save_settings(k, c)
                #     )


            scroll_layout.addLayout(button_layout)

        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

        # Close button
        close_button = QPushButton("Close", self)
        close_button.clicked.connect(self.handle_close)
        layout.addWidget(close_button)

    def handle_close(self):
        """Ensure the dialog is properly closed."""
        self.close()

    def closeEvent(self, event):
        """Stop all active movies when the dialog is closed."""
        for movie in self.active_movies:
            movie.stop()
        self.active_movies.clear()
        super().closeEvent(event)

    def save_settings(self, kind, color):
        """Save the selected settings and update the pet."""
        self.parent_app.update_pet(kind, color)
        self.accept()
        self.close()

    def unlock_pet(self, kind, color):
        """Unlock the selected pet."""
        print(f"Unlocking pet: {kind} - {color}")
        self.parent_app.health_bar.handle_lock_pet(False, kind, color)  # Call a method
        self.parent_app.pet_label.show()
        self.close()
