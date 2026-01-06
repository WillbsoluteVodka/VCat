"""Behavior configuration management module.

Handles loading, saving, and validation of behavior probability settings.
"""

import json
import os
from typing import Dict, Tuple

DEFAULT_CONFIG = {
    "behavior_probabilities": {
        "walking_to_sitting": 0.5,
        "sitting_to_coding": 0.01,
        "sitting_to_sleeping": 0.3
    },
    "pet_size_ratio": 0.3,  # Default pet size (30%)
    "voice_wake_enabled": True,  # Voice wake-up feature enabled by default
    "version": "1.0"
}

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "behavior_config.json")


def load_behavior_config() -> Dict:
    """Load configuration from JSON file, return defaults if missing/invalid.

    Returns:
        Dict containing behavior configuration with probabilities
    """
    try:
        if not os.path.exists(CONFIG_PATH):
            print(f"[BehaviorConfig] File not found at {CONFIG_PATH}, using defaults")
            return DEFAULT_CONFIG.copy()

        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)

        is_valid, error = validate_config(config)
        if not is_valid:
            print(f"[BehaviorConfig] Invalid config: {error}. Using defaults")
            # Backup corrupt file
            backup_path = CONFIG_PATH + ".bak"
            if os.path.exists(CONFIG_PATH):
                import shutil
                shutil.copy(CONFIG_PATH, backup_path)
                print(f"[BehaviorConfig] Backed up corrupt file to {backup_path}")
            return DEFAULT_CONFIG.copy()

        print(f"[BehaviorConfig] Loaded: {config}")
        return config

    except json.JSONDecodeError as e:
        print(f"[BehaviorConfig] JSON decode error: {e}. Using defaults")
        return DEFAULT_CONFIG.copy()
    except Exception as e:
        print(f"[BehaviorConfig] Unexpected error: {e}. Using defaults")
        return DEFAULT_CONFIG.copy()


def save_behavior_config(config: Dict) -> Tuple[bool, str]:
    """Save configuration to JSON file.

    Args:
        config: Configuration dictionary to save

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        is_valid, error = validate_config(config)
        if not is_valid:
            return False, f"Invalid configuration: {error}"

        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        print(f"[BehaviorConfig] Saved to {CONFIG_PATH}")
        return True, "Settings saved successfully"

    except Exception as e:
        error_msg = f"Failed to save: {str(e)}"
        print(f"[BehaviorConfig] {error_msg}")
        return False, error_msg


def validate_config(config: Dict) -> Tuple[bool, str]:
    """Validate configuration structure and values.

    Args:
        config: Configuration dictionary to validate

    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    if not isinstance(config, dict):
        return False, "Config must be a dictionary"

    if "behavior_probabilities" not in config:
        return False, "Missing 'behavior_probabilities' key"

    probs = config["behavior_probabilities"]
    if not isinstance(probs, dict):
        return False, "'behavior_probabilities' must be a dictionary"

    required_keys = ["walking_to_sitting", "sitting_to_coding", "sitting_to_sleeping"]
    for key in required_keys:
        if key not in probs:
            return False, f"Missing required probability: {key}"

        value = probs[key]
        if not isinstance(value, (int, float)):
            return False, f"Probability '{key}' must be a number"

        if not 0 <= value <= 1:
            return False, f"Probability '{key}' out of range [0, 1]: {value}"

    return True, ""


def get_default_config() -> Dict:
    """Return a copy of the default configuration.

    Returns:
        Dict containing default behavior configuration
    """
    return DEFAULT_CONFIG.copy()
