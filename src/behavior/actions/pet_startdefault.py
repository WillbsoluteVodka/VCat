from PyQt5.QtCore import QTimer


def run(self, parent, callback):
    self.pet_label.clear()
    sleep_duration_timer = QTimer(parent)
    sleep_duration_timer.setSingleShot(True)
    self.active_timers.append(sleep_duration_timer)
    sleep_duration_timer.timeout.connect(callback)
    sleep_duration_timer.start(500)
