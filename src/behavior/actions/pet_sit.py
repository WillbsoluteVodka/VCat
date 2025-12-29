import time
from PyQt5.QtCore import QTimer, QRect
from PyQt5.QtGui import QMovie, QCursor
from PyQt5.QtCore import QPropertyAnimation
from pet_data_loader import load_pet_data
from ..pet_actions import PetActions


def run(self, parent, callback):
    """Extracted pet_sit action. Expects the original PetBehavior instance as `self`."""
    self.resize_pet_label(parent)

    if self.animation and self.animation.state() == QPropertyAnimation.Running:
        self.animation.stop()

    pet_movie = QMovie(self.resource_path(load_pet_data(self.pet_kind, self.pet_color, "sit")))
    self.pet_label.setMovie(pet_movie)
    self.pet_label.setScaledContents(True)
    pet_movie.start()

    cursor_timer = QTimer(parent)
    cursor_timer.setSingleShot(True)
    self.active_timers.append(cursor_timer)
    self._sit_cursor_timer = cursor_timer
    # print(f"[pet_sit] created cursor_timer={id(cursor_timer)} for behavior={id(self)}")

    fallback_timer = QTimer(parent)
    fallback_timer.setSingleShot(True)
    self.active_timers.append(fallback_timer)
    fallback_timer.start(6000)
    self._sit_fallback_timer = fallback_timer
    # print(f"[pet_sit] created fallback_timer={id(fallback_timer)} (started 6000ms) for behavior={id(self)}")

    poll_timer = QTimer(parent)
    poll_timer.setInterval(100)
    self.active_timers.append(poll_timer)
    self._sit_poll_timer = poll_timer
    # print(f"[pet_sit] created poll_timer={id(poll_timer)} for behavior={id(self)}")

    self.monitoring_active = True
    self.stop_monitoring = False
    # print(f"[pet_sit] monitoring_active={self.monitoring_active} stop_monitoring={self.stop_monitoring} active_timers={list(map(id,self.active_timers))}")

    def monitor_cursor():
        if not self.monitoring_active or self.stop_monitoring:
            # print("SIT MMONITOR HALT.")
            # print(f"[pet_sit.monitor_cursor] aborting: monitoring_active={self.monitoring_active} stop_monitoring={self.stop_monitoring} active_timers={list(map(id,self.active_timers))}")
            return

        cursor_pos = QCursor.pos()
        label_global_pos = self.pet_label.mapToGlobal(self.pet_label.rect().topLeft())
        label_global_rect = QRect(label_global_pos, self.pet_label.size())

        contains = label_global_rect.contains(cursor_pos)
        # print(f"[pet_sit.monitor_cursor] cursor_pos={cursor_pos} label_rect={label_global_rect} contains={contains}")
        if contains:
            if not cursor_timer.isActive():
                print(f"[pet_sit.monitor_cursor] starting cursor_timer={id(cursor_timer)}")
                cursor_timer.start(3000)
        else:
            if cursor_timer.isActive():
                print(f"[pet_sit.monitor_cursor] stopping cursor_timer={id(cursor_timer)}")
                cursor_timer.stop()

    def on_timer_finished():
        # print(f"[pet_sit.on_timer_finished] cursor_timer fired for behavior={id(self)}")
        # print(f"[pet_sit.on_timer_finished] monitoring_active={self.monitoring_active} stop_monitoring={self.stop_monitoring} active_timers={list(map(id,self.active_timers))}")
        stop_monitoring()
        # print(f"[pet_sit.on_timer_finished] setting state to PLAYING and invoking perform_action")
        self.set_state(PetActions.PLAYING)
        QTimer.singleShot(0, lambda: self.perform_action(parent, callback))

    def on_fallback_timer_finished():
        # print(f"[pet_sit.on_fallback_timer_finished] fallback timer fired for behavior={id(self)}")
        stop_monitoring()
        try:
            callback()
        except Exception as e:
            print(f"[pet_sit.on_fallback_timer_finished] callback raised: {e}")

    def stop_monitoring():
        # print(f"[pet_sit.stop_monitoring] entering stop_monitoring for behavior={id(self)}")
        self.monitoring_active = False
        self.stop_monitoring = True
        # print(f"[pet_sit.stop_monitoring] flags set: monitoring_active={self.monitoring_active} stop_monitoring={self.stop_monitoring}")
        try:
            # print(f"[pet_sit.stop_monitoring] attempting cursor_timer.stop() id={id(cursor_timer)}")
            cursor_timer.stop()
        except Exception as e:
            print(f"[pet_sit.stop_monitoring] cursor_timer.stop() raised: {e}")
        try:
            # print(f"[pet_sit.stop_monitoring] attempting fallback_timer.stop() id={id(fallback_timer)}")
            fallback_timer.stop()
        except Exception as e:
            print(f"[pet_sit.stop_monitoring] fallback_timer.stop() raised: {e}")
        try:
            # print(f"[pet_sit.stop_monitoring] attempting poll_timer.stop() id={id(poll_timer)}")
            poll_timer.stop()
        except Exception as e:
            print(f"[pet_sit.stop_monitoring] poll_timer.stop() raised: {e}")
        try:
            cursor_timer.timeout.disconnect()
            # print(f"[pet_sit.stop_monitoring] disconnected cursor_timer timeout")
        except Exception as e:
            print(f"[pet_sit.stop_monitoring] cursor_timer.timeout.disconnect() raised: {e}")
        try:
            fallback_timer.timeout.disconnect()
            # print(f"[pet_sit.stop_monitoring] disconnected fallback_timer timeout")
        except Exception as e:
            print(f"[pet_sit.stop_monitoring] fallback_timer.timeout.disconnect() raised: {e}")
        try:
            poll_timer.timeout.disconnect()
            # print(f"[pet_sit.stop_monitoring] disconnected poll_timer timeout")
        except Exception as e:
            print(f"[pet_sit.stop_monitoring] poll_timer.timeout.disconnect() raised: {e}")
        # print(f"[pet_sit.stop_monitoring] active_timers before removal: {list(map(id,self.active_timers))}")
        if cursor_timer in self.active_timers:
            self.active_timers.remove(cursor_timer)
            # print(f"[pet_sit.stop_monitoring] removed cursor_timer from active_timers")
        if fallback_timer in self.active_timers:
            self.active_timers.remove(fallback_timer)
            # print(f"[pet_sit.stop_monitoring] removed fallback_timer from active_timers")
        if poll_timer in self.active_timers:
            self.active_timers.remove(poll_timer)
            # print(f"[pet_sit.stop_monitoring] removed poll_timer from active_timers")
        if hasattr(self, '_sit_cursor_timer'):
            try:
                del self._sit_cursor_timer
                # print("[pet_sit.stop_monitoring] deleted attribute _sit_cursor_timer")
            except Exception as e:
                print(f"[pet_sit.stop_monitoring] deleting _sit_cursor_timer raised: {e}")
        else:
            print("[pet_sit.stop_monitoring] no _sit_cursor_timer attribute present")
        if hasattr(self, '_sit_fallback_timer'):
            try:
                del self._sit_fallback_timer
                # print("[pet_sit.stop_monitoring] deleted attribute _sit_fallback_timer")
            except Exception as e:
                print(f"[pet_sit.stop_monitoring] deleting _sit_fallback_timer raised: {e}")
        else:
            print("[pet_sit.stop_monitoring] no _sit_fallback_timer attribute present")
        if hasattr(self, '_sit_poll_timer'):
            try:
                del self._sit_poll_timer
                # print("[pet_sit.stop_monitoring] deleted attribute _sit_poll_timer")
            except Exception as e:
                print(f"[pet_sit.stop_monitoring] deleting _sit_poll_timer raised: {e}")
        else:
            print("[pet_sit.stop_monitoring] no _sit_poll_timer attribute present")

    monitor_cursor()
    poll_timer.timeout.connect(monitor_cursor)
    poll_timer.start()
    cursor_timer.timeout.connect(on_timer_finished)
    fallback_timer.timeout.connect(on_fallback_timer_finished)
