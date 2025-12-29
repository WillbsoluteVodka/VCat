import subprocess
import os
import time
import random
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QMovie
from pet_data_loader import load_pet_data


def run(self, parent, callback):
    """Extracted pet_code action."""
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

    coding_duration_timer = QTimer(parent)
    coding_duration_timer.setSingleShot(True)
    self.active_timers.append(coding_duration_timer)

    def after_initial_timer():
        prob = random.random()
        if prob < 0.99:
            # show text via helper
            showtxt(self)
        else:
            path = self.resource_path("behavior/actions/pet_code_sea_terminal.py")
            runterminal(self, "python " + path)

        sleep_duration_timer = QTimer(parent)
        sleep_duration_timer.setSingleShot(True)
        self.active_timers.append(sleep_duration_timer)
        sleep_duration_timer.timeout.connect(callback)
        sleep_duration_timer.start(5000)

    coding_duration_timer.timeout.connect(after_initial_timer)
    coding_duration_timer.start(6000)


def runterminal(self, command="echo Hello, Terminal!"):
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
