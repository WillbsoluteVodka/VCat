# pet_actions.py (moved into behavior package)
import random
import math
from datetime import datetime
from PyQt5.QtCore import QPoint, QTimer, QEvent, QObject, QRect
from PyQt5.QtGui import QMovie, QCursor
from enum import Enum
from PyQt5.QtCore import QPropertyAnimation
import os
import subprocess
import time
from pet_data_loader import load_pet_data


class PetActions(Enum):
    STARTDEFAULT = "startdefault"
    WALKING = "walking"
    SITTING = "sitting"
    SLEEPING = "sleeping"
    CODING = "coding"
    PLAYING = "playing"
    GOINGTOPORTAL = "goingtoportal"
    REACHEDPORTAL = "reachedportal"



class PetBehavior(QObject):
    def __init__(self, pet_label, pet_kind, pet_color, resource_path):
        """
        Handles pet-specific behaviors.
        :param pet_label: QLabel representing the pet.
        :param resource_path: Function to retrieve resource file paths.
        """
        super().__init__()  # Initialize QObject
        self.pet_label = pet_label
        self.pet_kind = pet_kind
        self.pet_color = pet_color
        self.resource_path = resource_path
        self.animation = None
        self.current_state = PetActions.STARTDEFAULT
        self.lock_flag=False
        self.active_timers = []

    def set_state(self, new_state):
        self.current_state = new_state

    def get_state(self):
        return self.current_state

    def stop_all_timers(self):
        for t in self.active_timers:
            try:
                t.stop()
            except Exception:
                pass
        self.active_timers.clear()
        if self.animation and self.animation.state() == QPropertyAnimation.Running:
            self.animation.stop()

    def pause(self):
        self.stop_all_timers()

    def resume(self, parent, callback):
        self.stop_all_timers()
        self.perform_action(parent, callback)

    def perform_action(self, parent, callback,ID=None):
        """Perform an action based on the current state."""
        print(f"[Action] {self.current_state} ID={ID}")
        if self.current_state == PetActions.STARTDEFAULT:
            self.pet_startdefault(parent, callback)
        elif self.current_state == PetActions.WALKING:
            self.pet_random_walk(parent, callback)
        elif self.current_state == PetActions.SITTING:
            self.pet_sit(parent, callback)
        elif self.current_state == PetActions.PLAYING:
            self.pet_play(parent, callback)
        elif self.current_state == PetActions.SLEEPING:
            self.pet_sleep(parent, callback)
        elif self.current_state == PetActions.CODING:
            self.pet_code(parent, callback)
        elif self.current_state == PetActions.GOINGTOPORTAL:
            self.pet_move_to_portal(parent, callback)
        elif self.current_state == PetActions.REACHEDPORTAL:
            # Old networking code disabled - REACHEDPORTAL state unused
            pass

    def calculate_label_size(self, parent):
        """
        Dynamically calculate the label size based on the screen size while maintaining a 3:2 ratio.
        :param parent: The parent widget to get screen dimensions.
        :return: Tuple (width, height) for the label.
        """
        screen_width = parent.width()
        screen_height = parent.height()

        # Calculate dimensions as a percentage of screen size
        base_width = screen_width * 0.15
        base_height = base_width * 2 / 3  # Maintain 3:2 ratio

        # Ensure the label fits within the screen
        max_height = screen_height * 0.3  # Maximum height is 30% of the screen height
        if base_height > max_height:
            base_height = max_height
            base_width = base_height * 3 / 2  # Adjust width to maintain the ratio

        return int(base_width), int(base_height)

    def resize_pet_label(self, parent):
        """Resize the pet label dynamically based on screen size."""
        screen_width = parent.width()
        screen_height = parent.height()
        # Get the ratio from parent if available, otherwise use default
        ratio = getattr(parent, 'pet_size_ratio', 0.12)
        # Use PetWidget's resize_for_window if available
        if hasattr(self.pet_label, 'resize_for_window'):
            self.pet_label.resize_for_window(screen_width, screen_height, ratio)
        else:
            # Fallback to old method with 3:2 aspect ratio
            base_width = max(40, int(min(screen_width, screen_height) * ratio))
            base_height = int(base_width * 2 / 3)  # Height is 2/3 of width
            self.pet_label.resize(base_width, base_height)

    def pet_sit(self, parent, callback):
        # Delegates to extracted action implementation
        from .actions import pet_sit as _pet_sit
        return _pet_sit(self, parent, callback)

    def pet_play(self, parent, callback):
        from .actions import pet_play as _pet_play
        return _pet_play(self, parent, callback)

    def pet_random_walk(self, parent, callback):
        from .actions import pet_random_walk as _pet_random_walk
        return _pet_random_walk(self, parent, callback)

    def pet_code(self, parent, callback):
        from .actions import pet_code as _pet_code
        return _pet_code(self, parent, callback)

    def pet_code_runterminal(self, command="echo Hello, Terminal!"):
        from .actions import pet_code_runterminal as _runterminal
        return _runterminal(self, command)

    def pet_code_showtxt(self):
        from .actions import pet_code_showtxt as _showtxt
        return _showtxt(self)

    def pet_sleep(self, parent, callback):
        from .actions import pet_sleep as _pet_sleep
        return _pet_sleep(self, parent, callback)

    def pet_move_to_portal(self, parent, callback):
        from .actions import pet_move_to_portal as _pet_move_to_portal
        return _pet_move_to_portal(self, parent, callback)

    def pet_startdefault(self, parent, callback):
        from .actions import pet_startdefault as _pet_startdefault
        return _pet_startdefault(self, parent, callback)
