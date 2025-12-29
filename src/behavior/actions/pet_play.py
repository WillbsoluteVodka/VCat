from PyQt5.QtCore import QTimer, QRect
from PyQt5.QtGui import QMovie, QCursor
from pet_data_loader import load_pet_data


def run(self, parent, callback):
    """Extracted pet_play (belly touch) action."""
    self.resize_pet_label(parent)

    if self.animation and self.animation.state() == getattr(self.animation, 'Running', None):
        try:
            self.animation.stop()
        except Exception:
            pass
    # Cancel any active sit monitoring so sit won't block play
    try:
        self.monitoring_active = False
    except Exception:
        pass
    try:
        self.stop_monitoring = True
    except Exception:
        pass
    # Stop and remove sit timers if they exist
    try:
        t = getattr(self, '_sit_cursor_timer', None)
        if t is not None:
            try:
                t.stop()
            except Exception:
                pass
            if t in self.active_timers:
                self.active_timers.remove(t)
            try:
                delattr(self, '_sit_cursor_timer')
            except Exception:
                try:
                    del self._sit_cursor_timer
                except Exception:
                    pass
    except Exception:
        pass
    try:
        f = getattr(self, '_sit_fallback_timer', None)
        if f is not None:
            try:
                f.stop()
            except Exception:
                pass
            if f in self.active_timers:
                self.active_timers.remove(f)
            try:
                delattr(self, '_sit_fallback_timer')
            except Exception:
                try:
                    del self._sit_fallback_timer
                except Exception:
                    pass
    except Exception:
        pass
    # Stop and remove sit poll timer if it exists
    try:
        p = getattr(self, '_sit_poll_timer', None)
        if p is not None:
            try:
                p.stop()
            except Exception:
                pass
            try:
                p.timeout.disconnect()
            except Exception:
                pass
            if p in self.active_timers:
                self.active_timers.remove(p)
            try:
                delattr(self, '_sit_poll_timer')
            except Exception:
                try:
                    del self._sit_poll_timer
                except Exception:
                    pass
    except Exception:
        pass

    pet_movie = QMovie(self.resource_path(load_pet_data(self.pet_kind, self.pet_color, "touch_belly")))
    self.pet_label.setMovie(pet_movie)
    self.pet_label.setScaledContents(True)
    pet_movie.start()
    pet_movie.finished.connect(pet_movie.start)  # Loop the animation

    absence_timer = QTimer()
    absence_timer.setSingleShot(True)
    self.active_timers.append(absence_timer)
    self.play_monitoring_active = True

    def monitor_cursor():
        if not self.play_monitoring_active:
            return

        cursor_pos = QCursor.pos()
        label_global_pos = self.pet_label.mapToGlobal(self.pet_label.rect().topLeft())
        label_global_rect = QRect(label_global_pos, self.pet_label.size())

        if label_global_rect.contains(cursor_pos):
            if absence_timer.isActive():
                absence_timer.stop()
        else:
            if not absence_timer.isActive():
                absence_timer.start(2000)

        if self.play_monitoring_active:
            QTimer.singleShot(100, monitor_cursor)

    def on_absence_timeout():
        self.play_monitoring_active = False
        absence_timer.stop()
        try:
            if absence_timer.isActive():
                absence_timer.timeout.disconnect()
        except Exception:
            pass
        if absence_timer in self.active_timers:
            self.active_timers.remove(absence_timer)

        callback()

    monitor_cursor()
    absence_timer.timeout.connect(on_absence_timeout)
