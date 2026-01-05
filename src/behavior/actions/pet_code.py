import subprocess
import os
import time
import random
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QMovie
from pet_data_loader import load_pet_data
from src.ui.chat_dialog import ChatDialog


# Global reference to prevent garbage collection
_active_dialog = None


def run(self, parent, callback):
    """Extracted pet_code action - now shows Siri-style chat dialog."""
    global _active_dialog
    
    self.resize_pet_label(parent)

    if self.animation and self.animation.state() == getattr(self.animation, 'Running', None):
        try:
            self.animation.stop()
        except Exception:
            pass

    pet_movie = QMovie(self.resource_path(load_pet_data(self.pet_kind, self.pet_color, "code")))
    self.pet_label.setMovie(pet_movie)
    self.pet_label.setScaledContents(True)
    pet_movie.start()
    pet_movie.finished.connect(pet_movie.start)

    # Store callback for later use when dialog closes
    self._coding_callback = callback
    
    # Show chat dialog after a short delay
    coding_duration_timer = QTimer(parent)
    coding_duration_timer.setSingleShot(True)
    self.active_timers.append(coding_duration_timer)

    def show_chat_dialog():
        global _active_dialog
        
        # Check if dialog already exists
        if parent.is_chat_dialog_open:
            # Dialog already open, just call callback after delay
            QTimer.singleShot(5000, callback)
            return
            
        # Create and show chat dialog with pet_label reference for position tracking
        _active_dialog = ChatDialog(pet_label=self.pet_label)
        parent.is_chat_dialog_open = True
        parent.chat_dialog = _active_dialog
        
        # Get pet position and size
        pet_pos = self.pet_label.pos()
        pet_size = self.pet_label.size()
        
        # Connect dialog closed signal
        def on_dialog_closed():
            global _active_dialog
            parent.is_chat_dialog_open = False
            parent.chat_dialog = None
            _active_dialog = None
            # Call callback to continue state machine
            callback()
            
        _active_dialog.dialog_closed.connect(on_dialog_closed)
        
        # Show dialog near pet
        _active_dialog.show_dialog(
            pet_pos.x(),
            pet_pos.y(),
            pet_size.width(),
            pet_size.height()
        )

    coding_duration_timer.timeout.connect(show_chat_dialog)
    coding_duration_timer.start(1000)  # Show dialog after 1 second


def runterminal(self, command="echo Hello, Terminal!"):
    """Legacy terminal function - kept for compatibility."""
    try:
        script = f"""
        tell application \"Terminal\"
            activate
            do script \"{command}\"
        end tell
        """
        subprocess.Popen(["osascript", "-e", script])
    except Exception as e:
        print(f"Failed to run the terminal command: {e}")


def showtxt(self):
    """Legacy text function - kept for compatibility."""
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    file_path = os.path.join(desktop_path, "example.txt")
    txt_content = "Hello, what are you doing?"

    with open(file_path, "w") as file:
        file.write(txt_content)

    process = subprocess.Popen(["open", file_path])

    try:
        while True:
            ret_code = process.poll()
            if ret_code is not None:
                break
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    try:
        os.remove(file_path)
    except Exception:
        pass
