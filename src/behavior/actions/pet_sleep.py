from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QMovie
from datetime import datetime
from pet_data_loader import load_pet_data


def run(self, parent, callback):
    """Extracted pet_sleep action."""
    self.resize_pet_label(parent)

    if self.animation and self.animation.state() == getattr(self.animation, 'Running', None):
        try:
            self.animation.stop()
        except Exception:
            pass

    pet_movie = QMovie(self.resource_path(load_pet_data(self.pet_kind, self.pet_color, "sleep")))
    self.pet_label.setMovie(pet_movie)
    self.pet_label.setScaledContents(True)
    pet_movie.start()
    pet_movie.finished.connect(pet_movie.start)

    duration = max(20000, datetime.now().hour * 1000 + datetime.now().minute * 60)

    sleep_duration_timer = QTimer(parent)
    sleep_duration_timer.setSingleShot(True)
    self.active_timers.append(sleep_duration_timer)
    sleep_duration_timer.timeout.connect(callback)
    sleep_duration_timer.start(duration)
