"""Adapter to wrap the legacy PetBehavior from `pet_actions.py`.

This allows the old implementation to be used under the new BehaviorManager
without editing the original `pet_actions.py`.
"""
from .pet_actions import PetBehavior


class LegacyBehaviorAdapter:
    """Wraps a PetBehavior instance and exposes a minimal API expected by the manager."""

    def __init__(self, pet_label, pet_kind, pet_color, resource_path):
        self._inner = PetBehavior(pet_label, pet_kind, pet_color, resource_path)

    # Expose commonly accessed attributes on the adapter so callers can read/write
    # them (e.g., `main_window.update_pet` assigns `pet_behavior.pet_kind`).
    @property
    def pet_kind(self):
        return getattr(self._inner, "pet_kind", None)

    @pet_kind.setter
    def pet_kind(self, value):
        setattr(self._inner, "pet_kind", value)

    @property
    def pet_color(self):
        return getattr(self._inner, "pet_color", None)

    @pet_color.setter
    def pet_color(self, value):
        setattr(self._inner, "pet_color", value)

    @property
    def pet_label(self):
        return getattr(self._inner, "pet_label", None)

    @pet_label.setter
    def pet_label(self, value):
        setattr(self._inner, "pet_label", value)

    @property
    def resource_path(self):
        return getattr(self._inner, "resource_path", None)

    @resource_path.setter
    def resource_path(self, value):
        setattr(self._inner, "resource_path", value)

    @property
    def current_state(self):
        return getattr(self._inner, "current_state", None)

    @current_state.setter
    def current_state(self, value):
        setattr(self._inner, "current_state", value)

    # Delegate commonly used methods
    def perform_action(self, parent, callback, ID=None):
        return self._inner.perform_action(parent, callback, ID)

    def set_state(self, state):
        return self._inner.set_state(state)

    def get_state(self):
        return self._inner.get_state()

    def resize_pet_label(self, parent):
        return self._inner.resize_pet_label(parent)

    def stop_all_timers(self):
        return self._inner.stop_all_timers()

    def pause(self):
        """Pause the pet's behavior (stop timers but keep state)."""
        return self._inner.pause()

    def resume(self, parent, callback):
        """Resume the pet's behavior from its current state."""
        return self._inner.resume(parent, callback)
    
    def pet_move_to_portal(self, parent, callback):
        """Move pet to portal (for teleportation)."""
        return self._inner.pet_move_to_portal(parent, callback)

    @property
    def animation(self):
        return getattr(self._inner, "animation", None)
