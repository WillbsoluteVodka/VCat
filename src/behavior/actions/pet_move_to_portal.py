from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QMovie
from pet_data_loader import load_pet_data


def run(self, parent, callback):
    """Extracted pet_move_to_portal action.
    `self` should be PetBehavior instance.
    """
    if self.animation and self.animation.state() == QTimer().__class__.QPropertyAnimation if False else getattr(self, 'animation', None) and getattr(self.animation, 'state', lambda: None)() == None:
        # defensive: stop if running
        try:
            if self.animation and self.animation.state() == self.animation.Running:
                self.animation.stop()
        except Exception:
            pass

    self.resize_pet_label(parent)

    start_movie = QMovie(self.resource_path(load_pet_data(self.pet_kind, self.pet_color, "start_move_portal")))
    self.pet_label.setMovie(start_movie)
    self.pet_label.setScaledContents(True)
    self.resize_pet_label(parent)
    start_movie.start()

    def after_startmove():
        self.pet_label.clear()
        self.pet_label.hide()
        end_timer = QTimer(parent)
        end_timer.setSingleShot(True)
        self.active_timers.append(end_timer)
        end_timer.timeout.connect(play_endmove_gif)
        end_timer.start(1000)

    start_timer = QTimer(parent)
    start_timer.setSingleShot(True)
    self.active_timers.append(start_timer)
    start_timer.timeout.connect(after_startmove)
    start_timer.start(1000)

    def play_endmove_gif():
        screen_width = parent.width()
        screen_height = parent.height()
        center_x = (screen_width - self.pet_label.width()) // 2
        center_y = (screen_height - self.pet_label.height()) // 2

        self.pet_label.move(center_x, center_y)
        self.pet_label.show()

        end_movie = QMovie(self.resource_path(load_pet_data(self.pet_kind, self.pet_color, "end_move_portal")))
        self.pet_label.setMovie(end_movie)
        self.pet_label.setScaledContents(True)
        self.resize_pet_label(parent)
        end_movie.start()

        def stop_end_movie_and_callback():
            try:
                end_movie.stop()
            except Exception:
                pass
            self.pet_label.hide()
            callback()

        finish_timer = QTimer(parent)
        finish_timer.setSingleShot(True)
        self.active_timers.append(finish_timer)
        finish_timer.timeout.connect(stop_end_movie_and_callback)
        finish_timer.start(1000)
