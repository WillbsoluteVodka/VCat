"""Menu UI module - simplified stub for minimal run.

The original `menu_bar.py` contained a full PyQt menu and dialogs.
For the current minimal run we replace it with a small stub that
provides the `MainMenuWindow` symbol so imports succeed.
"""

class MainMenuWindow:
    """Minimal stub used while other features are disabled."""
    def __init__(self, parent_app):
        self.parent_app = parent_app

    def show(self):
        return

    def hide(self):
        return

    def exec_(self):
        return

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
        self.setWindowTitle("Menu Window")
        self.parent_app = parent_app

        # Create the menu bar items
        menubar = self.menuBar()

        # Pet Setting Menu (first/leftmost)
        pet_setting_menu = menubar.addMenu("Setting")
        
        # Chat with Cat action (top priority)
        chat_action = QAction("Chat with Cat", self)
        chat_action.setShortcut("Ctrl+Shift+C")  # Cmd+Shift+C on macOS
        chat_action.triggered.connect(self.open_chat_dialog)
        pet_setting_menu.addAction(chat_action)
        
        pet_setting_menu.addSeparator()
        
        # Change Pet action
        pet_setting_action = QAction("Change Pet", self)
        pet_setting_action.triggered.connect(self.open_pet_setting_dialog)
        pet_setting_menu.addAction(pet_setting_action)
        
        # Pet Size submenu
        pet_size_menu = QMenu("Pet Size", self)
        
        # Increase Size action
        increase_size_action = QAction("Increase Size", self)
        increase_size_action.triggered.connect(self.increase_pet_size)
        pet_size_menu.addAction(increase_size_action)
        
        # Decrease Size action
        decrease_size_action = QAction("Decrease Size", self)
        decrease_size_action.triggered.connect(self.decrease_pet_size)
        pet_size_menu.addAction(decrease_size_action)
        
        pet_setting_menu.addMenu(pet_size_menu)
        
        # Move up action (move pet to menu bar)
        go_up_action = QAction("Go Up", self)
        go_up_action.triggered.connect(self.activate_toolbar_pet)
        pet_setting_menu.addAction(go_up_action)
        
        # Move down action (move pet to desktop)
        go_down_action = QAction("Go Down", self)
        go_down_action.triggered.connect(self.deactivate_toolbar_pet)
        pet_setting_menu.addAction(go_down_action)

        # Shop Menu
        shop_menu = menubar.addMenu("Shop")

        # Shop action
        shop_action = QAction("Open Shop", self)
        shop_action.triggered.connect(self.open_shop_window)
        shop_menu.addAction(shop_action)

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
        
    def open_shop_window(self):
        """Open the shop window with product categories."""
        dialog = ShopWindow(self.parent_app)
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


class ShopWindow(QDialog):
    """Window to display shop items categorized into food, toys, and magical products."""
    def __init__(self, parent_app):
        super().__init__()
        self.setWindowTitle("Pet Shop")
        self.parent_app = parent_app
        self.active_images = []  # Track active QLabel pixmaps for cleanup

        # Dialog layout
        layout = QVBoxLayout(self)

        # Tab widget for categories
        tabs = QTabWidget(self)
        layout.addWidget(tabs)

        # Define categories and their items
        categories = {
            "Food": ["Apple", "Fish", "Meat"],
            "Toys": ["Ball", "Feather"],
            "Magic": []
        }

        # Create tabs dynamically
        for category, items in categories.items():
            tab = QWidget()
            tab_layout = QGridLayout(tab)
            tab_layout.setSpacing(20)

            for idx, item in enumerate(items):
                card = self.create_item_card(item)
                row = idx // 3
                col = idx % 3
                tab_layout.addWidget(card, row, col)

            tabs.addTab(tab, category)

        # Close button
        close_button = QPushButton("Close", self)
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

    def create_item_card(self, item_name):
        """Create a visually appealing item card with an image and a clickable area."""
        card = QFrame(self)
        card.setFrameShape(QFrame.StyledPanel)
        card.setStyleSheet("""
            QFrame {
                background-color: #f9f9f9;
                border: 2px solid #ddd;
                border-radius: 10px;
                padding: 10px;
            }
            QFrame:hover {
                background-color: #e6f7ff;
                border: 2px solid #40a9ff;
            }
        """)

        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignCenter)

        # Item image
        screen_width = self.parent_app.width()
        button_width = int(screen_width * 0.08)

        item_image = QLabel(card)
        item_image.setFixedSize(button_width, button_width)
        item_image.setAlignment(Qt.AlignCenter)
        item_image.setScaledContents(True)

        # Load the item icon
        icon_path = f"src/icon/{item_name}.png"
        pixmap = QPixmap(icon_path)
        item_image.setPixmap(pixmap)
        self.active_images.append(item_image)

        # Item name
        item_label = QLabel(item_name)
        item_label.setAlignment(Qt.AlignCenter)
        item_label.setStyleSheet("font-weight: bold; color: #333;")

        # Add components to the card
        layout.addWidget(item_image)
        layout.addWidget(item_label)

        # Add click functionality
        card.mousePressEvent = lambda event: self.purchase_item(item_name)

        return card

    def purchase_item(self, item_name):
        """Handle item purchase logic."""
        print(f"You selected {item_name}!")
        self.parent_app.start_drag_food(item_name)
        self.close()

    def closeEvent(self, event):
        """Ensure all resources are released when the shop window is closed."""
        print("Shop window is closing. Cleaning up resources...")

        # Clear all active QLabel pixmaps to release memory
        for image_label in self.active_images:
            image_label.clear()

        self.active_images.clear()  # Clear the list of tracked images
        super().closeEvent(event)
    def __init__(self, parent_app):
        super().__init__()
        self.setWindowTitle("Shop")
        self.parent_app = parent_app
        self.active_images = []  # Track active QLabel pixmaps

        # Set background image for the shop
        self.setStyleSheet("""
            QDialog {
                background-image: url('icon/shop.png');
                background-repeat: no-repeat;
                background-position: center;
                background-size: cover;
            }
            QLabel {
                font-size: 14px;
                color: white;  /* Adjust text color to ensure readability over the background */
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                padding: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

        # Layout for the shop window
        main_layout = QVBoxLayout(self)

        # Add a tab widget for categories
        tab_widget = QTabWidget(self)
        tab_widget.setStyleSheet("""
            QTabBar::tab {
                background: rgba(0, 0, 0, 0.7); /* Semi-transparent background for tabs */
                padding: 8px;
                font-size: 14px;
                color: white;
            }
            QTabBar::tab:selected {
                background: #4CAF50;
                color: white;
            }
        """)

        categories = {
            "Food": ["Apple", "Fish", "Meat"],
            "Toys": ["Ball", "Stick", "Puzzle"],
            "Magical Items": ["Portal Key", "Time Crystal"]
        }

        # Add tabs for each category
        for category, items in categories.items():
            category_widget = QWidget()
            category_layout = QGridLayout(category_widget)
            category_layout.setSpacing(10)
            category_layout.setContentsMargins(10, 10, 10, 10)

            # Add items to the category
            for index, item in enumerate(items):
                item_card = self.create_item_card(item)
                category_layout.addWidget(item_card, index // 3, index % 3)

            tab_widget.addTab(category_widget, category)

        main_layout.addWidget(tab_widget)

        # Add close button
        close_button = QPushButton("Close", self)
        close_button.clicked.connect(self.close)
        main_layout.addWidget(close_button)

    def create_item_card(self, item_name):
        """Create a visually appealing item card with an image and a clickable area."""
        card = QFrame()
        card.setFixedSize(150, 200)
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.8); /* Semi-transparent white */
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 10px;
            }
            QFrame:hover {
                border: 2px solid #4CAF50;
            }
        """)

        layout = QVBoxLayout(card)

        # Item image
        item_image = QLabel()
        pixmap = QPixmap(f"icon/{item_name.lower()}.png").scaled(80, 80, Qt.KeepAspectRatio)
        item_image.setPixmap(pixmap)
        item_image.setAlignment(Qt.AlignCenter)
        self.active_images.append(item_image)  # Track the image for cleanup

        # Item name
        item_label = QLabel(item_name)
        item_label.setAlignment(Qt.AlignCenter)
        item_label.setStyleSheet("font-weight: bold; color: #333;")

        # Add components to the card
        layout.addWidget(item_image)
        layout.addWidget(item_label)

        # Add click functionality
        card.mousePressEvent = lambda event: self.purchase_item(item_name)

        return card

    def purchase_item(self, item_name):
        """Handle item purchase logic."""
        print(f"You selected {item_name}!")
        self.parent_app.start_drag_food(item_name)
        self.close()

    def closeEvent(self, event):
        """Ensure all resources are released when the shop window is closed."""
        print("Shop window is closing. Cleaning up resources...")

        # Clear all active QLabel pixmaps to release memory
        for image_label in self.active_images:
            image_label.clear()

        self.active_images.clear()  # Clear the list of tracked images
        super().closeEvent(event)





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
