"""Health module disabled for minimal run.

Provide a lightweight HealthBar stub so imports don't fail while
health/hunger mechanics are temporarily disabled.
"""

class HealthBar:
    def __init__(self, parent, initial_health=6):
        print("HealthBar stub initialized (disabled)")

    def heal_pet(self):
        print("HealthBar.heal_pet() called - disabled")

    def handle_lock_pet(self, flag, pet_kind, color):
        print("HealthBar.handle_lock_pet() called - disabled")
