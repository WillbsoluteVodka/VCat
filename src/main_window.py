import gc
import json
import sys
import threading
import time

from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow
from PyQt5.QtCore import QTimer, Qt, QPoint, QElapsedTimer, QPropertyAnimation
from PyQt5.QtGui import QPixmap, QMovie

import os
import random
# NOTE: Non-essential modules (menus, networking, toolbar, health) are commented out
# while we keep only the pet and pet_actions for a minimal runnable state.
from menu_bar import MainMenuWindow
from PyQt5.QtGui import QCursor


# Use PetActions from legacy behavior package (keep one import path to avoid duplicate enums)
from behavior.pet_actions import PetActions
from behavior import LegacyBehaviorAdapter
from src.ui.pet_widget import PetWidget
from behavior import BehaviorManager
from src.communication import PortalClient, PortalServer
from src.pet_data_loader import load_pet_data, get_current_pet  # keep data loader for resources
from src.pet_health import HealthBar
from src.toolbar_pet import MacOSToolbarIcon


def resource_path(relative_path):
    """专门打包用的"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)



class PetApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # behavior manager centralizes state transitions and behavior loops
        self.behavior_manager = BehaviorManager(self)
        self.pets = []
        self.setMouseTracking(True)
        self.pet_movie = None
        
        # Pet size ratio - must be set BEFORE add_pet is called
        self.pet_size_ratio = 0.12

        self.pet_kind, self.pet_color = get_current_pet()
        self.pet_behavior, self.pet_label = self.add_pet("Cat1", self.pet_kind, self.pet_color)
        self.pet_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.toolbar_icon = None

        # Health and hunger mechanics
        self.health_bar = HealthBar(self)

        # Food dragging
        self.food_label = QLabel(self)
        self.food_label.hide()  # Initially hidden
        self.food_label.setScaledContents(True)

        self.dragging_food = False  # Track if food is being dragged
        self.selected_food = None  # Currently selected food

        # Set up window
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowTransparentForInput)
        self.setAttribute(Qt.WA_TranslucentBackground)
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()
        self.resize(screen_width - 100, screen_height - 100)

    def activate_toolbar_pet(self):
        """Create the moving pet icon in the toolbar and hide the desktop pet."""
        if not self.toolbar_icon:
            # Create and activate the toolbar pet
            self.toolbar_icon = MacOSToolbarIcon(self)

            # Hide the desktop pet if it exists and pause its behavior
            if self.pet_label.isVisible():
                self.pet_behavior.pause()
                self.pet_label.hide()
                print("Desktop pet hidden. Toolbar pet activated.")
        else:
            print("Pet is already active in the toolbar.")
    
    def deactivate_toolbar_pet(self):
        """Deactivate the pet in the macOS toolbar and return to desktop."""
        if self.toolbar_icon:
            # Stop the toolbar icon's timer and remove it from the status bar
            if self.toolbar_icon.timer:
                self.toolbar_icon.timer.invalidate()
            self.toolbar_icon.status_bar.removeStatusItem_(self.toolbar_icon.status_item)
            self.toolbar_icon = None
            
            # Resume the desktop pet
            self.pet_behavior.resume(self, lambda: self.check_switch_state(self.pet_behavior))
            self.pet_label.show()
            print("Toolbar pet closed. Desktop pet resumed.")
        else:
            print("Toolbar icon not activated.")
    
    def end_toolbar_pet(self):
        
        """Return the pet from toolbar to desktop."""
        if self.toolbar_icon:
            self.pet_behavior.resume(self, lambda: self.check_switch_state(self.pet_behavior))
            self.pet_label.show()
            self.toolbar_icon = None
            print("Toolbar pet closed. Desktop pet resumed.")
        else:
            print("Toolbar icon not activated.")
    def update_pet(self, new_kind, new_color):
        """Update pet kind and color, then reload the current behavior."""
        # Stop all timers and animations
        self.pet_behavior.stop_all_timers()
        
        # Update pet kind and color
        self.pet_kind = new_kind
        self.pet_color = new_color
        self.pet_behavior.pet_kind = new_kind
        self.pet_behavior.pet_color = new_color
        
        # Get current state and reload the GIF for that state
        current_state = self.pet_behavior.get_state()
        if current_state:
            # Load the appropriate GIF for the new pet with current state
            state_name = current_state.value  # Get the enum value name
            gif_path = load_pet_data(new_kind, new_color, state_name)
            
            if gif_path:
                # Update the pet label with new GIF
                pet_movie = QMovie(gif_path)
                self.pet_label.setMovie(pet_movie)
                self.pet_label.setScaledContents(True)
                pet_movie.start()
                pet_movie.finished.connect(pet_movie.start)  # Loop the animation
            
            # Resume behavior from current state
            self.pet_behavior.resume(self, lambda: self.check_switch_state(self.pet_behavior))

    def add_pet(self, pet_name, pet_kind, pet_color):
        """Add a new pet to the screen."""
        # Use PetWidget (QLabel subclass) for better encapsulation
        pet_label = PetWidget(self)
        # Use the legacy PetBehavior (wrapped by LegacyBehaviorAdapter) so all
        # actions are available while still routing through the BehaviorManager.
        pet_behavior = LegacyBehaviorAdapter(pet_label, pet_kind, pet_color, resource_path)

        # Set up the initial position of the pet
        pet_behavior.resize_pet_label(self)
        # Calculate screen center
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        pet_label.move(screen_geometry.width() // 2,
                       screen_geometry.height() // 2)
        pet_label.show()

        # Store the pet's behavior and name
        self.pets.append({
            "petname": pet_name,
            "petkind": pet_kind,
            "petcolor": pet_color,
            "label": pet_label,
            "behavior": pet_behavior
        })
        # Register pet with the behavior manager which will start the loop
        self.behavior_manager.register_pet(pet_name, pet_behavior, pet_label)

        return pet_behavior, pet_label

    def perform_action(self, pet_behavior,ID=None):
        """Perform an action for the given pet."""
        # Delegate to behavior manager to keep behavior control centralized
        self.behavior_manager.perform_action(pet_behavior, ID)

    def check_switch_state(self, pet_behavior,ID=None):
        """Delegate state transition handling to the BehaviorManager."""
        return self.behavior_manager.advance_state(pet_behavior, ID)
    
    def increase_pet_size(self):
        """Increase pet size by 0.02."""
        self.pet_size_ratio = min(1.0, self.pet_size_ratio + 0.02)
        screen_width = self.width()
        screen_height = self.height()
        self.pet_label.resize_for_window(screen_width, screen_height, self.pet_size_ratio)
        print(f"Pet size increased. New ratio: {self.pet_size_ratio}")
    
    def decrease_pet_size(self):
        """Decrease pet size by 0.02."""
        self.pet_size_ratio = max(0.02, self.pet_size_ratio - 0.02)
        screen_width = self.width()
        screen_height = self.height()
        self.pet_label.resize_for_window(screen_width, screen_height, self.pet_size_ratio)
        print(f"Pet size decreased. New ratio: {self.pet_size_ratio}")

    def handle_parameters(self, param1, param2):
        # Networking/portal disabled in minimal mode.
        print("handle_parameters: networking disabled in minimal mode")

    def recall_pet(self):
        # Disabled: networking
        print("recall_pet: networking disabled")

    def receive_cat(self, message):
        # Networking disabled; ignore messages
        print("receive_cat: networking disabled")

    def show_pet_on_client(self,message):
        # Disabled: networking
        print("show_pet_on_client: networking disabled")

    def create_portal(self):
        # Portals disabled in minimal mode.
        print("create_portal: disabled in minimal mode")

    def teleport_cat(self,id, pet=None):
        # Networking disabled
        print("teleport_cat: networking disabled")

    def mouseMoveEvent(self, event):
        """Move the food icon with the mouse."""
        if self.dragging_food:  # Only move the food icon if dragging is active
            # Update the position of the food icon to follow the mouse
            cursor_x = event.globalX() - self.food_label.width() // 2
            cursor_y = event.globalY() - self.food_label.height() // 2
            self.food_label.move(cursor_x, cursor_y)
            self.check_food_collision()  # Check if the food overlaps with the pet

    def start_drag_food(self, food_name):
        """Start dragging the selected food."""
        self.selected_food = food_name
        self.dragging_food = True

        # Load and display the food icon
        food_icon_path = resource_path(f"src/icon/{food_name}.png")
        food_pixmap = QPixmap(food_icon_path)
        self.food_label.setPixmap(food_pixmap)

        # Resize food icon proportional to screen size
        screen_width = self.width()
        food_size = int(screen_width * 0.05)
        self.food_label.resize(food_size, food_size)
        self.food_label.show()
        print(f"Dragging {food_name}...")

    def check_food_collision(self):
        """Check if the food overlaps with the pet."""
        if not self.dragging_food:
            return

        food_rect = self.food_label.geometry()
        pet_rect = self.pet_label.geometry()

        if food_rect.intersects(pet_rect):
            print(f"Pet ate {self.selected_food}!")
            self.health_bar.feed(self.selected_food)
            self.food_label.hide()
            self.dragging_food = False
            self.selected_food = None


if __name__ == '__main__':
    app = QApplication(sys.argv)
    pet_app = PetApp()
    
    # Create and show menu window
    main_menu_window = MainMenuWindow(pet_app)
    main_menu_window.show()
    main_menu_window.hide()  # Hide initially but keep in memory
    
    pet_app.show()
    sys.exit(app.exec_())
