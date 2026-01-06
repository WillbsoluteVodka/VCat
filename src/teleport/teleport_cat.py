"""
TeleportManager - Handles all room connection and pet teleportation functionality
"""
import os
import threading
from PyQt5.QtCore import QTimer, Qt, pyqtSlot, QMetaObject, Q_ARG
from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QPixmap, QMovie
from supabase import create_client


class TeleportManager:
    """Manages room connections and pet teleportation between users"""
    
    def __init__(self, parent_app):
        """
        Initialize the teleport manager
        
        Args:
            parent_app: Reference to the main PetApp instance
        """
        self.app = parent_app
        
        # Room connection state
        self.room_thread = None
        self.room_stop_event = None
        self.current_room_id = None
        self.is_room_holder = False
        self.room_worker = None  # For compatibility with menu_bar.py checks
        self.remote_pets = {}  # Track remote pets by user_id
        self.pet_teleported = False  # Track if local pet is teleported
    
    def teleport_pet_to_portal(self):
        """Teleport pet to portal and freeze actions (for non-holder users)"""
        # Stop current behavior
        self.app.pet_behavior.pause()
        
        # Mark pet as teleported
        self.pet_teleported = True
        
        # Execute portal teleportation animation
        def on_portal_complete():
            """After portal animation, keep pet hidden and frozen"""
            self.app.pet_label.hide()
            print("[TELEPORT] Pet has been teleported to the host and actions are frozen")
        
        # Use the pet_move_to_portal action
        self.app.pet_behavior.pet_move_to_portal(self.app, on_portal_complete)
    
    @pyqtSlot()
    def recall_pet_from_portal(self):
        """Recall pet from portal (when leaving room or room closed)"""
        if not self.pet_teleported:
            return
        
        print("[TELEPORT] Retrieving pet from portal...")
        
        # Import resource_path and load_pet_data locally to avoid circular imports
        from src.main_window import resource_path
        from src.pet_data_loader import load_pet_data
        
        # Create portal at window center
        portal_center_x = self.app.width() // 2
        portal_center_y = self.app.height() // 2
        
        portal = QLabel(self.app)
        portal.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        portal.setAttribute(Qt.WA_TranslucentBackground)
        portal_pixmap = QPixmap(resource_path("src/icon/portal.png"))
        portal.setPixmap(portal_pixmap)
        portal.setScaledContents(True)
        
        portal_size = int(self.app.width() * 0.1)
        portal.resize(portal_size, portal_size)
        portal.move(portal_center_x - portal_size // 2, portal_center_y - portal_size // 2)
        portal.lower()
        portal.show()
        
        # Position pet at center (initially hidden)
        center_x = (self.app.width() - self.app.pet_label.width()) // 2
        center_y = (self.app.height() - self.app.pet_label.height()) // 2
        self.app.pet_label.move(center_x, center_y)
        
        # After portal shows for a moment, play end_move_portal animation (pet emerging)
        def show_pet_emerging():
            end_movie = QMovie(resource_path(load_pet_data(self.app.pet_kind, self.app.pet_color, "end_move_portal")))
            self.app.pet_label.setMovie(end_movie)
            self.app.pet_label.setScaledContents(True)
            self.app.pet_label.show()
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
                self.app.pet_behavior.resume(self.app, lambda: self.app.check_switch_state(self.app.pet_behavior))
                self.pet_teleported = False
                print("[TELEPORT] Pet has been recalled and resumed")
            
            finish_timer = QTimer(self.app)
            finish_timer.setSingleShot(True)
            finish_timer.timeout.connect(finish_recall)
            finish_timer.start(1000)
        
        emerge_timer = QTimer(self.app)
        emerge_timer.setSingleShot(True)
        emerge_timer.timeout.connect(show_pet_emerging)
        emerge_timer.start(500)  # Show portal for 500ms before pet emerges
    
    @pyqtSlot(int, str, str)
    def spawn_remote_pet(self, user_id, pet_kind, pet_color):
        """Spawn a remote user's pet through portal animation (holder side)"""
        if user_id in self.remote_pets:
            print(f"[TELEPORT] Warning: User {user_id}'s pet already exists")
            return
        
        # Import resource_path and load_pet_data locally
        from src.main_window import resource_path
        from src.pet_data_loader import load_pet_data
        
        # Create portal at window center
        portal_center_x = self.app.width() // 2
        portal_center_y = self.app.height() // 2
        
        portal = QLabel(self.app)
        portal.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        portal.setAttribute(Qt.WA_TranslucentBackground)
        portal_pixmap = QPixmap(resource_path("src/icon/portal.png"))
        portal.setPixmap(portal_pixmap)
        portal.setScaledContents(True)
        
        portal_size = int(self.app.width() * 0.1)
        portal.resize(portal_size, portal_size)
        portal.move(portal_center_x - portal_size // 2, portal_center_y - portal_size // 2)
        portal.lower()
        portal.show()
        
        print(f"[TELEPORT] Portal established, summoning User {user_id}'s pet...")
        
        # Add the remote pet (initially hidden, will appear from portal)
        remote_pet_behavior, remote_pet_label = self.app.add_pet(
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
                remote_pet_behavior.resume(self.app, lambda: self.app.check_switch_state(remote_pet_behavior, user_id))
                print(f"[TELEPORT] User {user_id}'s pet has been spawned")
            
            finish_timer = QTimer(self.app)
            finish_timer.setSingleShot(True)
            finish_timer.timeout.connect(finish_spawn)
            finish_timer.start(1000)
        
        # Delay before showing pet (portal display time)
        spawn_timer = QTimer(self.app)
        spawn_timer.setSingleShot(True)
        spawn_timer.timeout.connect(show_pet_from_portal)
        spawn_timer.start(500)  # Show portal for 500ms before pet emerges
    
    @pyqtSlot(int)
    def despawn_remote_pet(self, user_id):
        """Remove a remote user's pet with portal animation (holder side)"""
        if user_id not in self.remote_pets:
            print(f"[TELEPORT] Warning: User {user_id}'s pet does not exist")
            return
        
        # Import resource_path and load_pet_data locally
        from src.main_window import resource_path
        from src.pet_data_loader import load_pet_data
        
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
        portal = QLabel(self.app)
        portal.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        portal.setAttribute(Qt.WA_TranslucentBackground)
        portal_pixmap = QPixmap(resource_path("src/icon/portal.png"))
        portal.setPixmap(portal_pixmap)
        portal.setScaledContents(True)
        
        portal_size = int(self.app.width() * 0.1)
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
                if hasattr(self.app.behavior_manager, 'pets') and f"RemotePet_{user_id}" in self.app.behavior_manager.pets:
                    del self.app.behavior_manager.pets[f"RemotePet_{user_id}"]
                
                remote_pet_label.deleteLater()
                del self.remote_pets[user_id]
                print(f"[TELEPORT] User {user_id}'s pet has been removed")
            
            cleanup_timer = QTimer(self.app)
            cleanup_timer.setSingleShot(True)
            cleanup_timer.timeout.connect(cleanup)
            cleanup_timer.start(500)  # Wait for portal visibility
        
        # Wait for animation to finish before hiding
        hide_timer = QTimer(self.app)
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
        supabase_sync = create_client(supabase_url, supabase_key)
        
        # Update user's current pet in database before joining
        user_pet_data = {
            'user_num': user_id,
            'pet_kind': self.app.pet_kind,
            'pet_color': self.app.pet_color
        }
        supabase_sync.table('user_cur_pet').upsert(user_pet_data).execute()
        print(f"[TELEPORT] Updated user {user_id}'s pet info: {self.app.pet_kind} - {self.app.pet_color}")
        
        room_check = supabase_sync.table("pet_rooms").select("*").eq("room_id", room_id).execute()
        
        will_be_holder = not room_check.data  # If room doesn't exist, user will be holder
        
        # Create stop event
        self.room_stop_event = threading.Event()
        
        # Import db_connection module from teleport package
        from teleport.db_connection import start_room_connection
        
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
                        user_id_m = member['user_id']
                        if not member['is_holder'] and user_id_m not in self.remote_pets:
                            # New member - spawn their pet (must call from main thread)
                            print(f"[TELEPORT] Spawning pet for new member User {user_id_m}...")
                            QMetaObject.invokeMethod(
                                self,
                                "spawn_remote_pet",
                                Qt.QueuedConnection,
                                Q_ARG(int, user_id_m),
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
                    user_id_m = data['user_id']
                    if user_id_m in self.remote_pets:
                        QMetaObject.invokeMethod(
                            self,
                            "despawn_remote_pet",
                            Qt.QueuedConnection,
                            Q_ARG(int, user_id_m)
                        )
            
            elif event_type == 'room_closed':
                print(f"[TELEPORT] Room closed: {data.get('message', 'Unknown reason')}")
                self.current_room_id = None
                self.is_room_holder = False
                
                # Recall pet if it was teleported
                if self.pet_teleported:
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
                    print(f"    [TELEPORT] Cleaning up User {user_id}'s pet")
                    remote_pet_info = self.remote_pets[user_id]
                    remote_pet_label = remote_pet_info['label']
                    remote_pet_behavior = remote_pet_info['behavior']
                    
                    # Stop behavior and cleanup
                    remote_pet_behavior.pause()
                    remote_pet_label.hide()
                    remote_pet_label.deleteLater()
                    
                    # Remove from behavior manager
                    if hasattr(self.app.behavior_manager, 'pets') and f"RemotePet_{user_id}" in self.app.behavior_manager.pets:
                        del self.app.behavior_manager.pets[f"RemotePet_{user_id}"]
                
                self.remote_pets.clear()
                print("[TELEPORT] Remote pets cleaned up.")
            
            self.room_stop_event.set()
            self.room_thread.join(timeout=3)
            
            self.current_room_id = None
            self.is_room_holder = False
            self.room_worker = None  # Clear compatibility flag
            
            # Recall pet if it was teleported
            if self.pet_teleported:
                print("[TELEPORT] Recalling pet...")
                self.recall_pet_from_portal()
            
            print("[TELEPORT] Disconnected successfully.")
        else:
            print("[TELEPORT] Not currently connected to any room.")
