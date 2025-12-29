import math
import random
from PyQt5.QtCore import QPoint, QPropertyAnimation
from PyQt5.QtGui import QMovie
from pet_data_loader import load_pet_data


def run(self, parent, callback):
    """Extracted pet_random_walk action. Keeps the same signature and behavior.
    `self` is the PetBehavior instance.
    """
    self.resize_pet_label(parent)

    max_x = parent.width() - self.pet_label.width()
    max_y = parent.height() - self.pet_label.height()
    x = random.randint(0, max_x)
    y = random.randint(0, max_y)

    # Smooth movement animation
    self.animation = QPropertyAnimation(self.pet_label, b"pos")
    current_position = self.pet_label.pos()

    # Select animation direction
    if x > current_position.x():
        pet_movie = QMovie(self.resource_path(load_pet_data(self.pet_kind, self.pet_color, "walk_right")))
    else:
        pet_movie = QMovie(self.resource_path(load_pet_data(self.pet_kind, self.pet_color, "walk_left")))

    self.pet_label.setMovie(pet_movie)
    self.pet_label.setScaledContents(True)
    pet_movie.start()
    pet_movie.finished.connect(pet_movie.start)

    pet_width = parent.width() * 0.15

    distance = math.sqrt((current_position.x() - x) ** 2 + (current_position.y() - y) ** 2)
    speed = pet_width * 0.0005
    duration = int(distance / speed)

    self.animation.setDuration(duration)
    self.animation.setStartValue(current_position)
    self.animation.setEndValue(QPoint(x, y))

    self.animation.finished.connect(callback)
    self.animation.start()
