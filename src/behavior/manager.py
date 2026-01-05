import random
from PyQt5.QtCore import QTimer
from .pet_actions import PetActions


class BehaviorManager:
    """Manage pet behaviors and state transitions.

    Responsibility:
    - register pet behaviors
    - advance state transitions using the same probabilities as the original
    - invoke behavior.perform_action(...) and handle callbacks
    """

    def __init__(self, parent_app):
        self.parent = parent_app
        self.pets = []  # list of dicts: {name, behavior, label}

    def register_pet(self, pet_name, behavior, label):
        entry = {"petname": pet_name, "behavior": behavior, "label": label}
        self.pets.append(entry)
        # start the behavior loop for this pet
        # schedule immediate start to allow UI to settle
        QTimer.singleShot(0, lambda: self._start_behavior(entry))

    def _start_behavior(self, entry):
        behavior = entry["behavior"]
        # perform initial action; callback advances the state
        behavior.perform_action(self.parent, lambda: self.advance_state(behavior))

    def perform_action(self, behavior, ID=None):
        """Call through to a behavior's perform_action, wiring callback to advance_state."""
        behavior.perform_action(self.parent, lambda: self.advance_state(behavior, ID), ID)

    def advance_state(self, behavior, ID=None):
        """Transition logic extracted from the original main_window.check_switch_state.

        This sets the next state on the behavior and triggers the behavior.perform_action
        again so the loop continues.
        """
        current_state = behavior.get_state()
        # replicates original probabilities and transitions
        if current_state == PetActions.STARTDEFAULT:
            behavior.set_state(PetActions.WALKING)
        elif current_state == PetActions.WALKING:
            if random.random() <= 0.95:
                behavior.set_state(PetActions.SITTING)
            else:
                behavior.set_state(PetActions.WALKING)
        elif current_state == PetActions.SITTING:
            if random.random() <= 0.99: # leave it 0.99 for all phases
                behavior.set_state(PetActions.CODING)
            elif random.random() <= 0.3:
                behavior.set_state(PetActions.SLEEPING)
            else:
                behavior.set_state(PetActions.WALKING)
        elif current_state == PetActions.PLAYING:
            behavior.set_state(PetActions.SITTING)
        elif current_state == PetActions.SLEEPING:
            behavior.set_state(PetActions.SITTING)
        elif current_state == PetActions.CODING:
            behavior.set_state(PetActions.SITTING)
        elif current_state == PetActions.GOINGTOPORTAL:
            behavior.set_state(PetActions.REACHEDPORTAL)

        # Trigger the next action
        QTimer.singleShot(0, lambda: self.perform_action(behavior, ID))
