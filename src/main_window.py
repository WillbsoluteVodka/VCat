import gc
import json
import sys
import threading
import time

from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow
from PyQt5.QtCore import QTimer, Qt, QPoint, QElapsedTimer, QPropertyAnimation, QMetaObject, Q_ARG, pyqtSlot
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
from src.pet_data_loader import load_pet_data, get_current_pet  # keep data loader for resources
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

        # Pet size ratio - load from config or use default
        self.load_pet_size_from_config()

        self.pet_kind, self.pet_color = get_current_pet()
        self.pet_behavior, self.pet_label = self.add_pet("超级大恐龙", self.pet_kind, self.pet_color)
        self.pet_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.toolbar_icon = None

        # Chat dialog state management
        self.is_chat_dialog_open = False
        self.chat_dialog = None
        
        # Voice wake-up recognizer (listens for "Hey Kitty" etc.)
        self.voice_wake_recognizer = None
        
        # Global hotkey for chat (Cmd+Shift+C)
        self._init_global_hotkey()
        
        # Initialize voice wake-up in background thread for faster startup
        threading.Thread(target=self._background_voice_init, daemon=True).start()

        # Room connection management
        self.room_thread = None
        self.room_stop_event = None
        self.current_room_id = None
        self.is_room_holder = False
        self.room_worker = None  # For compatibility with menu_bar.py checks
        self.remote_pets = {}  # Track remote pets by user_id

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
        self.move(screen_geometry.topLeft())

    def _background_voice_init(self):
        """Initialize voice recognition in background thread for faster startup."""
        import time
        time.sleep(0.5)  # Let UI settle first
        
        # Check if this is first launch (onboarding needed)
        if not self._check_onboarding():
            # Not first launch - initialize voice wake-up
            # Use QTimer.singleShot to call from main thread for thread safety
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(0, self._init_voice_wake_up)

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
        # Check if voice wake is enabled in config
        from src.behavior.config import load_behavior_config
        config = load_behavior_config()
        if not config.get("voice_wake_enabled", True):
            print("[VCat] Voice wake-up is disabled in settings.")
            self.voice_wake_recognizer = None
            return
        
        try:
            from src.chat.voice import VoiceRecognizer
            
            self.voice_wake_recognizer = VoiceRecognizer(self)
            self.voice_wake_recognizer.wake_word_detected.connect(self._on_voice_wake)
            self.voice_wake_recognizer.start()
            print("[VCat] Voice wake-up enabled (NSSpeechRecognizer). Say 'Hey Cat' to start.")
        except Exception as e:
            print(f"[VCat] Voice wake-up not available: {e}")
            self.voice_wake_recognizer = None
    
    def set_voice_wake_enabled(self, enabled: bool):
        """Enable or disable voice wake-up feature."""
        if enabled:
            if not self.voice_wake_recognizer:
                # Initialize voice wake-up
                try:
                    from src.chat.voice import VoiceRecognizer
                    self.voice_wake_recognizer = VoiceRecognizer(self)
                    self.voice_wake_recognizer.wake_word_detected.connect(self._on_voice_wake)
                    self.voice_wake_recognizer.start()
                    print("[VCat] Voice wake-up enabled.")
                except Exception as e:
                    print(f"[VCat] Failed to enable voice wake-up: {e}")
        else:
            if self.voice_wake_recognizer:
                self.voice_wake_recognizer.stop()
                self.voice_wake_recognizer = None
                print("[VCat] Voice wake-up disabled.")
    
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
        
        # Create name label as child of pet label
        pet_label.create_name_label(pet_name)
        
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

    def load_pet_size_from_config(self):
        """Load pet size from behavior config file."""
        from src.behavior.config import load_behavior_config
        config = load_behavior_config()
        if "pet_size_ratio" in config:
            self.pet_size_ratio = config["pet_size_ratio"]
            print(f"[PetApp] Loaded pet size from config: {self.pet_size_ratio}")
        else:
            # Use default if not in config
            self.pet_size_ratio = 0.3
            print(f"[PetApp] Using default pet size: {self.pet_size_ratio}")

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
            # TODO: health_bar.feed() - pet_health module missing
            self.food_label.hide()
            self.dragging_food = False
            self.selected_food = None
    
    def teleport_pet_to_portal(self):
        """Teleport pet to portal and freeze actions (for non-holder users)"""
        # Stop current behavior
        self.pet_behavior.pause()
        
        # Mark pet as teleported
        self.pet_teleported = True
        
        # Execute portal teleportation animation
        def on_portal_complete():
            """After portal animation, keep pet hidden and frozen"""
            self.pet_label.hide()
            print("[TELEPORT] Pet has been teleported to the host and actions are frozen")
        
        # Use the pet_move_to_portal action
        self.pet_behavior.pet_move_to_portal(self, on_portal_complete)
    
    @pyqtSlot()
    def recall_pet_from_portal(self):
        """Recall pet from portal (when leaving room or room closed)"""
        if not hasattr(self, 'pet_teleported') or not self.pet_teleported:
            return
        
        print("[TELEPORT] Retrieving pet from portal...")
        
        # Create portal at screen center
        screen = QApplication.primaryScreen().availableGeometry()
        portal_center_x = screen.width() // 2
        portal_center_y = screen.height() // 2
        
        portal = QLabel(self)
        portal.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        portal.setAttribute(Qt.WA_TranslucentBackground)
        portal_pixmap = QPixmap(resource_path("src/icon/portal.png"))
        portal.setPixmap(portal_pixmap)
        portal.setScaledContents(True)
        
        portal_size = int(screen.width() * 0.1)
        portal.resize(portal_size, portal_size)
        portal.move(portal_center_x - portal_size // 2, portal_center_y - portal_size // 2)
        portal.lower()
        portal.show()
        
        # Position pet at center (initially hidden)
        center_x = (screen.width() - self.pet_label.width()) // 2
        center_y = (screen.height() - self.pet_label.height()) // 2
        self.pet_label.move(center_x, center_y)
        
        # After portal shows for a moment, play end_move_portal animation (pet emerging)
        def show_pet_emerging():
            end_movie = QMovie(resource_path(load_pet_data(self.pet_kind, self.pet_color, "end_move_portal")))
            self.pet_label.setMovie(end_movie)
            self.pet_label.setScaledContents(True)
            self.pet_label.show()
            end_movie.start()
            
            def finish_recall():
                try:
                    end_movie.stop()
                except Exception:
                    pass
                
                # Hide portal
                portal.hide()
                portal.deleteLater()
                
                # Resume normal behavior
                self.pet_behavior.resume(self, lambda: self.check_switch_state(self.pet_behavior))
                self.pet_teleported = False
                print("[TELEPORT] Pet has been recalled and resumed")
            
            finish_timer = QTimer(self)
            finish_timer.setSingleShot(True)
            finish_timer.timeout.connect(finish_recall)
            finish_timer.start(1000)
        
        emerge_timer = QTimer(self)
        emerge_timer.setSingleShot(True)
        emerge_timer.timeout.connect(show_pet_emerging)
        emerge_timer.start(500)  # Show portal for 500ms before pet emerges
    
    @pyqtSlot(int, str, str)
    def spawn_remote_pet(self, user_id, pet_kind, pet_color):
        """Spawn a remote user's pet through portal animation (holder side)"""
        if user_id in self.remote_pets:
            print(f"[TELEPORT] Warning: User {user_id}'s pet already exists")
            return
        
        # Create portal at screen center
        screen = QApplication.primaryScreen().availableGeometry()
        portal_center_x = screen.width() // 2
        portal_center_y = screen.height() // 2
        
        portal = QLabel(self)
        portal.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        portal.setAttribute(Qt.WA_TranslucentBackground)
        portal_pixmap = QPixmap(resource_path("src/icon/portal.png"))
        portal.setPixmap(portal_pixmap)
        portal.setScaledContents(True)
        
        portal_size = int(screen.width() * 0.1)
        portal.resize(portal_size, portal_size)
        portal.move(portal_center_x - portal_size // 2, portal_center_y - portal_size // 2)
        portal.lower()
        portal.show()
        
        print(f"[TELEPORT] Portal established, summoning User {user_id}'s pet...")
        
        # Add the remote pet (initially hidden, will appear from portal)
        remote_pet_behavior, remote_pet_label = self.add_pet(
            f"RemotePet_{user_id}",
            pet_kind,
            pet_color
        )
        
        # Position pet at portal center initially (hidden)
        remote_pet_label.move(
            portal_center_x - remote_pet_label.width() // 2,
            portal_center_y - remote_pet_label.height() // 2
        )
        remote_pet_label.hide()
        
        # Store remote pet info
        self.remote_pets[user_id] = {
            'behavior': remote_pet_behavior,
            'label': remote_pet_label,
            'pet_kind': pet_kind,
            'pet_color': pet_color
        }
        
        # Pause the remote pet's behavior initially
        remote_pet_behavior.pause()
        
        # Animate pet coming out of portal
        def show_pet_from_portal():
            # Play end_move_portal animation (pet emerging)
            end_movie = QMovie(resource_path(load_pet_data(pet_kind, pet_color, "end_move_portal")))
            remote_pet_label.setMovie(end_movie)
            remote_pet_label.setScaledContents(True)
            remote_pet_label.show()
            end_movie.start()
            
            def finish_spawn():
                try:
                    end_movie.stop()
                except Exception:
                    pass
                
                # Hide portal
                portal.hide()
                portal.deleteLater()
                
                # Resume pet behavior
                remote_pet_behavior.resume(self, lambda: self.check_switch_state(remote_pet_behavior, user_id))
                print(f"[TELEPORT] User {user_id}'s pet has been spawned")
            
            finish_timer = QTimer(self)
            finish_timer.setSingleShot(True)
            finish_timer.timeout.connect(finish_spawn)
            finish_timer.start(1000)
        
        # Delay before showing pet (portal display time)
        spawn_timer = QTimer(self)
        spawn_timer.setSingleShot(True)
        spawn_timer.timeout.connect(show_pet_from_portal)
        spawn_timer.start(500)  # Show portal for 500ms before pet emerges
    
    @pyqtSlot(int)
    def despawn_remote_pet(self, user_id):
        """Remove a remote user's pet with portal animation (holder side)"""
        if user_id not in self.remote_pets:
            print(f"[TELEPORT] Warning: User {user_id}'s pet does not exist")
            return
        
        remote_pet_info = self.remote_pets[user_id]
        remote_pet_behavior = remote_pet_info['behavior']
        remote_pet_label = remote_pet_info['label']
        pet_kind = remote_pet_info['pet_kind']
        pet_color = remote_pet_info['pet_color']
        
        # Pause pet behavior
        remote_pet_behavior.pause()
        
        # Get current pet position for portal
        pet_x = remote_pet_label.x() + remote_pet_label.width() // 2
        pet_y = remote_pet_label.y() + remote_pet_label.height() // 2
        
        # Create portal at pet's position
        screen = QApplication.primaryScreen().availableGeometry()
        portal = QLabel(self)
        portal.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        portal.setAttribute(Qt.WA_TranslucentBackground)
        portal_pixmap = QPixmap(resource_path("src/icon/portal.png"))
        portal.setPixmap(portal_pixmap)
        portal.setScaledContents(True)
        
        portal_size = int(screen.width() * 0.1)
        portal.resize(portal_size, portal_size)
        portal.move(pet_x - portal_size // 2, pet_y - portal_size // 2)
        portal.lower()
        portal.show()
        
        print(f"[TELEPORT] User {user_id}'s pet is returning...")
        
        # Play start_move_portal animation (pet entering portal)
        start_movie = QMovie(resource_path(load_pet_data(pet_kind, pet_color, "start_move_portal")))
        remote_pet_label.setMovie(start_movie)
        remote_pet_label.setScaledContents(True)
        start_movie.start()
        
        def hide_pet_and_portal():
            # Hide pet
            remote_pet_label.hide()
            
            def cleanup():
                try:
                    start_movie.stop()
                except Exception:
                    pass
                
                # Hide portal
                portal.hide()
                portal.deleteLater()
                
                # Remove pet from behavior manager and cleanup
                if hasattr(self.behavior_manager, 'pets') and f"RemotePet_{user_id}" in self.behavior_manager.pets:
                    del self.behavior_manager.pets[f"RemotePet_{user_id}"]
                
                remote_pet_label.deleteLater()
                del self.remote_pets[user_id]
                print(f"[TELEPORT] User {user_id}'s pet has been removed")
            
            cleanup_timer = QTimer(self)
            cleanup_timer.setSingleShot(True)
            cleanup_timer.timeout.connect(cleanup)
            cleanup_timer.start(500)  # Wait for portal visibility
        
        # Wait for animation to finish before hiding
        hide_timer = QTimer(self)
        hide_timer.setSingleShot(True)
        hide_timer.timeout.connect(hide_pet_and_portal)
        hide_timer.start(1000)  # 1 second for start_move_portal animation
    
    def connect_to_room(self, room_id, user_id):
        """Connect to a room (called from menu)"""
        # Stop existing connection if any
        if self.room_thread and self.room_thread.is_alive():
            print("Stopping existing room connection...")
            self.room_stop_event.set()
            self.room_thread.join(timeout=3)
        
        # Get credentials
        supabase_url = os.environ.get('SUPABASE_URL', 'https://qamgefqejxydheqabdxo.supabase.co')
        supabase_key = os.environ.get('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFhbWdlZnFlanh5ZGhlcWFiZHhvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY0NTE5NjAsImV4cCI6MjA4MjAyNzk2MH0.g2t5nlqUuOzu0z3adJFkvqNLwztljL3d3fE6SHOtx7I')
        
        # Check if room exists first to determine if user will be holder
        from supabase import create_client
        supabase_sync = create_client(supabase_url, supabase_key)
        
        # Update user's current pet in database before joining
        user_pet_data = {
            'user_num': user_id,
            'pet_kind': self.pet_kind,
            'pet_color': self.pet_color
        }
        supabase_sync.table('user_cur_pet').upsert(user_pet_data).execute()
        print(f"[TELEPORT] Updated user {user_id}'s pet info: {self.pet_kind} - {self.pet_color}")
        
        room_check = supabase_sync.table("pet_rooms").select("*").eq("room_id", room_id).execute()
        
        will_be_holder = not room_check.data  # If room doesn't exist, user will be holder
        
        # Create stop event
        self.room_stop_event = threading.Event()
        
        # Import connection module
        from connection import start_room_connection
        
        # Define callback for room events
        def on_room_event(event_type, data):
            """Handle room events"""
            if event_type == 'connected':
                self.current_room_id = data['room_id']
                self.is_room_holder = data['is_holder']
                role = "房主" if data['is_holder'] else "成员"
                print(f"[TELEPORT] Connected to room {data['room_id']} AS {role}")
            
            elif event_type == 'members_list':
                members = data['members']
                print(f"\n[ROOM] Room has {len(members)} members:")
                for member in members:
                    marker = "👑" if member['is_holder'] else "👤"
                    print(f"    {marker} User {member['user_id']}: {member['pet_kind']} - {member['pet_color']}")
                
                # If holder, spawn pets for new members
                if self.is_room_holder:
                    for member in members:
                        user_id = member['user_id']
                        if not member['is_holder'] and user_id not in self.remote_pets:
                            # New member - spawn their pet (must call from main thread)
                            print(f"[TELEPORT] Spawning pet for new member User {user_id}...")
                            QMetaObject.invokeMethod(
                                self,
                                "spawn_remote_pet",
                                Qt.QueuedConnection,
                                Q_ARG(int, user_id),
                                Q_ARG(str, member['pet_kind']),
                                Q_ARG(str, member['pet_color'])
                            )
            
            elif event_type == 'member_joined':
                print(f"[ROOM] New member joined: User {data['user_id']}")
                # Spawn remote pet if holder
                if self.is_room_holder:
                    # Get member info from the updated members_list that follows
                    # We'll handle spawning in the members_list event to get full pet info
                    pass
            
            elif event_type == 'member_left':
                print(f"[ROOM] Member left: User {data['user_id']}")
                # Remove remote pet if holder
                if self.is_room_holder:
                    user_id = data['user_id']
                    if user_id in self.remote_pets:
                        QMetaObject.invokeMethod(
                            self,
                            "despawn_remote_pet",
                            Qt.QueuedConnection,
                            Q_ARG(int, user_id)
                        )
            
            elif event_type == 'room_closed':
                print(f"[TELEPORT] Room closed: {data.get('message', 'Unknown reason')}")
                self.current_room_id = None
                self.is_room_holder = False
                
                # Recall pet if it was teleported
                if hasattr(self, 'pet_teleported') and self.pet_teleported:
                    print("[TELEPORT] Recalling pet...")
                    QMetaObject.invokeMethod(
                        self,
                        "recall_pet_from_portal",
                        Qt.QueuedConnection
                    )
            
            elif event_type == 'error':
                print(f"[TELEPORT] Error: {data['message']}")
        
        # Start connection in background thread
        self.room_thread = threading.Thread(
            target=start_room_connection,
            args=(supabase_url, supabase_key, room_id, user_id, on_room_event, self.room_stop_event),
            daemon=True
        )
        self.room_thread.start()
        self.room_worker = self.room_thread  # Set for menu_bar compatibility
        print(f"[TELEPORT] Connecting to room {room_id}...")
        
        # If not holder, teleport pet immediately (in main thread)
        if not will_be_holder:
            print("[TELEPORT] Create portal and teleport pet...")
            self.teleport_pet_to_portal()
    
    def leave_room(self):
        """Leave current room (wrapper for disconnect_from_room)"""
        self.disconnect_from_room()
    
    def disconnect_from_room(self):
        """Disconnect from current room"""
        if self.room_thread and self.room_thread.is_alive():
            print("正在断开房间连接...")
            
            # Clean up remote pets if holder is leaving
            if self.is_room_holder:
                print(f"[TELEPORT] Room holder leaving, cleaning up {len(self.remote_pets)} remote pets...")
                for user_id in list(self.remote_pets.keys()):
                    print(f"    [TELEPORT]Cleaning up User {user_id}'s pet")
                    remote_pet_info = self.remote_pets[user_id]
                    remote_pet_label = remote_pet_info['label']
                    remote_pet_behavior = remote_pet_info['behavior']
                    
                    # Stop behavior and cleanup
                    remote_pet_behavior.pause()
                    remote_pet_label.hide()
                    remote_pet_label.deleteLater()
                    
                    # Remove from behavior manager
                    if hasattr(self.behavior_manager, 'pets') and f"RemotePet_{user_id}" in self.behavior_manager.pets:
                        del self.behavior_manager.pets[f"RemotePet_{user_id}"]
                
                self.remote_pets.clear()
                print("[TELEPORT] Remote pets cleaned up.")
            
            self.room_stop_event.set()
            self.room_thread.join(timeout=3)
            
            self.current_room_id = None
            self.is_room_holder = False
            self.room_worker = None  # Clear compatibility flag
            
            # Recall pet if it was teleported
            if hasattr(self, 'pet_teleported') and self.pet_teleported:
                print("[TELEPORT] Recalling pet...")
                self.recall_pet_from_portal()
            
            print("[TELEPORT] Disconnected successfully.")
        else:
            print("[TELEPORT] Not currently connected to any room.")
    
    def closeEvent(self, event):
        """Handle application shutdown"""
        # Stop voice wake recognizer
        if self.voice_wake_recognizer:
            self.voice_wake_recognizer.stop()
            self.voice_wake_recognizer = None
        
        # Disconnect from room if connected
        if self.room_thread and self.room_thread.is_alive():
            print("[TELEPORT] Cleaning up room connection...")
            self.room_stop_event.set()
            self.room_thread.join(timeout=3)
        
        # Call parent close handler
        super().closeEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Set application name for macOS menu bar
    app.setApplicationName("VCat")
    app.setApplicationDisplayName("VCat")
    app.setOrganizationName("VCat")

    # For macOS: Set the application name in the menu bar using PyObjC
    try:
        from Foundation import NSBundle
        bundle = NSBundle.mainBundle()
        if bundle:
            info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
            if info:
                info['CFBundleName'] = 'VCat'
                info['CFBundleDisplayName'] = 'VCat'
    except ImportError:
        print("[VCat] PyObjC not available, using default app name")

    pet_app = PetApp()

    # Create and show menu window
    main_menu_window = MainMenuWindow(pet_app)
    pet_app.menu_window = main_menu_window  # Store reference for settings window
    main_menu_window.show()
    main_menu_window.hide()  # Hide initially but keep in memory

    pet_app.show()
    sys.exit(app.exec_())
