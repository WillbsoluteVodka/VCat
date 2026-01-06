import gc
import json
import sys
import threading
import time

from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow
from PyQt5.QtCore import QTimer, Qt, QPoint, QElapsedTimer, QPropertyAnimation, QMetaObject, Q_ARG, pyqtSlot
from PyQt5.QtGui import QPixmap, QMovie, QPainter, QCursor

import os
import random
# NOTE: Non-essential modules (menus, networking, toolbar, health) are commented out
# while we keep only the pet and pet_actions for a minimal runnable state.
from menu_bar import MainMenuWindow

# Use PetActions from legacy behavior package (keep one import path to avoid duplicate enums)
from behavior.pet_actions import PetActions
from behavior import LegacyBehaviorAdapter
from src.ui.pet_widget import PetWidget
from behavior import BehaviorManager
from src.pet_data_loader import load_pet_data, get_current_pet  # keep data loader for resources
from src.toolbar_pet import MacOSToolbarIcon
from src.teleport.teleport_cat import TeleportManager


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
        self.pet_size_ratio = 0.3

        self.pet_kind, self.pet_color = get_current_pet()
        self.pet_behavior, self.pet_label = self.add_pet("Cat1", self.pet_kind, self.pet_color)
        self.pet_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.toolbar_icon = None

        # Chat dialog state management
        self.is_chat_dialog_open = False
        self.chat_dialog = None
        
        # Voice wake-up recognizer (listens for "Hey Kitty" etc.)
        self.voice_wake_recognizer = None
        
        # Global hotkey for chat (Cmd+Shift+C)
        self._init_global_hotkey()
        
        # Check for first-time onboarding (will request mic permission)
        # Note: _init_voice_wake_up is called after onboarding or directly if not first launch
        if not self._check_onboarding():
            # Not first launch, initialize voice wake-up directly
            self._init_voice_wake_up()

        # Teleport and room connection management
        self.teleport_manager = TeleportManager(self)

        # Set up window
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowTransparentForInput)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAutoFillBackground(False)
        self._screen_hooked = False
        self._sync_window_to_screen()

    def _get_target_screen(self):
        handle = self.windowHandle()
        if handle and handle.screen():
            return handle.screen()
        screen = QApplication.screenAt(QCursor.pos())
        if screen:
            return screen
        return QApplication.primaryScreen()

    def _sync_window_to_screen(self):
        screen = self._get_target_screen()
        if not screen:
            return
        screen_geometry = screen.availableGeometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()
        self.resize(max(200, screen_width - 100), max(200, screen_height - 100))
        self.move(screen_geometry.topLeft())
        self.update()

    def _on_screen_changed(self, screen):
        self._sync_window_to_screen()

    def showEvent(self, event):
        super().showEvent(event)
        self._sync_window_to_screen()
        handle = self.windowHandle()
        if handle and not self._screen_hooked:
            handle.screenChanged.connect(self._on_screen_changed)
            self._screen_hooked = True

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.fillRect(event.rect(), Qt.transparent)
        painter.end()

    def _init_global_hotkey(self):
        """Initialize global hotkey (Cmd+Shift+C) for opening chat."""
        try:
            from AppKit import NSEvent, NSApplication
            from Quartz import (
                CGEventMaskBit, kCGEventKeyDown, 
                kCGKeyboardEventKeycode, CGEventGetIntegerValueField
            )
            import Quartz
            
            # Key code for 'C' is 8, Cmd=0x100000, Shift=0x20000
            def hotkey_callback(proxy, event_type, event, refcon):
                try:
                    # Get flags and keycode
                    flags = Quartz.CGEventGetFlags(event)
                    keycode = Quartz.CGEventGetIntegerValueField(event, kCGKeyboardEventKeycode)
                    
                    # Check for Cmd+Shift+C (keycode 8 = 'C')
                    cmd_pressed = (flags & 0x100000) != 0
                    shift_pressed = (flags & 0x20000) != 0
                    
                    if keycode == 8 and cmd_pressed and shift_pressed:
                        print("[VCat] Global hotkey Cmd+Shift+C pressed!")
                        # Use QTimer to call from main thread
                        QTimer.singleShot(0, self._on_voice_wake)
                        return None  # Consume the event
                except Exception as e:
                    print(f"[Hotkey] Error: {e}")
                return event
            
            # Create event tap
            mask = CGEventMaskBit(kCGEventKeyDown)
            tap = Quartz.CGEventTapCreate(
                Quartz.kCGSessionEventTap,
                Quartz.kCGHeadInsertEventTap,
                Quartz.kCGEventTapOptionDefault,
                mask,
                hotkey_callback,
                None
            )
            
            if tap:
                # Create run loop source
                run_loop_source = Quartz.CFMachPortCreateRunLoopSource(None, tap, 0)
                Quartz.CFRunLoopAddSource(
                    Quartz.CFRunLoopGetCurrent(),
                    run_loop_source,
                    Quartz.kCFRunLoopCommonModes
                )
                Quartz.CGEventTapEnable(tap, True)
                print("[VCat] Global hotkey (Cmd+Shift+C) registered")
            else:
                print("[VCat] Failed to create event tap - need Accessibility permission")
                
        except Exception as e:
            print(f"[VCat] Global hotkey not available: {e}")

    def _init_voice_wake_up(self):
        """Initialize voice wake-up listener using macOS NSSpeechRecognizer."""
        try:
            from src.chat.voice import VoiceRecognizer
            
            self.voice_wake_recognizer = VoiceRecognizer(self)
            self.voice_wake_recognizer.wake_word_detected.connect(self._on_voice_wake)
            self.voice_wake_recognizer.start()
            print("[VCat] Voice wake-up enabled (NSSpeechRecognizer). Say 'Hey Cat' to start.")
        except Exception as e:
            print(f"[VCat] Voice wake-up not available: {e}")
            self.voice_wake_recognizer = None
    
    def _on_voice_wake(self):
        """Handle voice wake word detection - trigger chat dialog."""
        print("[VCat] Wake word detected! Opening chat dialog...")
        # Trigger CODING state which opens the chat dialog
        if not self.is_chat_dialog_open and self.pet_behavior:
            # Stop current behavior and force immediate CODING state
            self.pet_behavior.stop_all_timers()
            self.pet_behavior.set_state(PetActions.CODING)
            # Immediately perform the CODING action
            self.pet_behavior.perform_action(
                self, 
                lambda: self.behavior_manager.advance_state(self.pet_behavior)
            )
    
    def _check_onboarding(self) -> bool:
        """Show onboarding dialog on first launch.
        
        Returns:
            True if onboarding was shown, False otherwise.
        """
        try:
            from src.ui.onboarding_dialog import OnboardingDialog, should_show_onboarding
            
            if should_show_onboarding():
                dialog = OnboardingDialog(self)
                dialog.completed.connect(self._on_onboarding_complete)
                dialog.exec_()
                return True
        except Exception as e:
            print(f"[VCat] Onboarding check failed: {e}")
        return False
    
    def _on_onboarding_complete(self, mic_granted: bool):
        """Handle onboarding completion."""
        print(f"[VCat] Onboarding complete. Mic permission: {mic_granted}")
        if mic_granted and not self.voice_wake_recognizer:
            # Permission was just granted, initialize voice wake-up
            self._init_voice_wake_up()
    
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
        
        # Save to current_pet.json
        current_pet_path = os.path.join(os.path.dirname(__file__), "current_pet.json")
        with open(current_pet_path, 'w') as f:
            json.dump({
                "Current_Pet_Kind": new_kind,
                "Current_Pet_Color": new_color
            }, f, indent=2)
        
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
        # Center within the parent window
        pet_label.move(
            max(0, (self.width() - pet_label.width()) // 2),
            max(0, (self.height() - pet_label.height()) // 2)
        )
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

    def teleport_pet_to_portal(self):
        """Teleport pet to portal and freeze actions (for non-holder users)"""
        self.teleport_manager.teleport_pet_to_portal()
    
    @pyqtSlot()
    def recall_pet_from_portal(self):
        """Recall pet from portal (when leaving room or room closed)"""
        self.teleport_manager.recall_pet_from_portal()
    
    @pyqtSlot(int, str, str)
    def spawn_remote_pet(self, user_id, pet_kind, pet_color):
        """Spawn a remote user's pet through portal animation (holder side)"""
        self.teleport_manager.spawn_remote_pet(user_id, pet_kind, pet_color)
    
    @pyqtSlot(int)
    def despawn_remote_pet(self, user_id):
        """Remove a remote user's pet with portal animation (holder side)"""
        self.teleport_manager.despawn_remote_pet(user_id)
    
    def connect_to_room(self, room_id, user_id):
        """Connect to a room (called from menu)"""
        self.teleport_manager.connect_to_room(room_id, user_id)
    
    def leave_room(self):
        """Leave current room (wrapper for disconnect_from_room)"""
        self.teleport_manager.leave_room()
    
    def disconnect_from_room(self):
        """Disconnect from current room"""
        self.teleport_manager.disconnect_from_room()
    
    # Property accessors for backward compatibility with menu_bar.py
    @property
    def room_worker(self):
        """Get room worker thread reference from teleport manager"""
        return self.teleport_manager.room_worker
    
    @property
    def room_thread(self):
        """Get room thread reference from teleport manager"""
        return self.teleport_manager.room_thread
    
    @property
    def room_stop_event(self):
        """Get room stop event reference from teleport manager"""
        return self.teleport_manager.room_stop_event
    
    def closeEvent(self, event):
        """Handle application shutdown"""
        # Stop voice wake recognizer
        if self.voice_wake_recognizer:
            self.voice_wake_recognizer.stop()
            self.voice_wake_recognizer = None
        
        # Disconnect from room if connected
        if self.teleport_manager.room_thread and self.teleport_manager.room_thread.is_alive():
            print("[TELEPORT] Cleaning up room connection...")
            self.teleport_manager.room_stop_event.set()
            self.teleport_manager.room_thread.join(timeout=3)
        
        # Call parent close handler
        super().closeEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    pet_app = PetApp()
    
    # Create and show menu window
    main_menu_window = MainMenuWindow(pet_app)
    main_menu_window.show()
    main_menu_window.hide()  # Hide initially but keep in memory
    
    pet_app.show()
    sys.exit(app.exec_())
