"""LLM configuration management."""

import json
import os
from copy import deepcopy
from typing import Dict, List, Tuple

DEFAULT_CONFIG: Dict = {
    "language": "zh",
    "custom_personality": "",
    "temperature": 0.7,
    "max_tokens": 1024,
    "timeout_seconds": 30,
    "providers": [],
}

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "llm_config.json")


def _normalize_provider(provider: Dict) -> Dict:
    return {
        "name": (provider.get("name") or "").strip(),
        "endpoint_url": (provider.get("endpoint_url") or "").strip(),
        "encrypted_api_key": provider.get("encrypted_api_key") or "",
        "model_name": (provider.get("model_name") or "").strip(),
        "is_default": bool(provider.get("is_default", False)),
        "available_models": provider.get("available_models") or [],
    }


def validate_llm_config(config: Dict) -> Tuple[bool, str]:
    if not isinstance(config, dict):
        return False, "Config must be a dictionary"

    for key in ["language", "custom_personality", "temperature", "max_tokens", "timeout_seconds"]:
        if key not in config:
            return False, f"Missing key: {key}"

    if not isinstance(config.get("providers"), list):
        return False, "Providers must be a list"

    return True, ""


def load_llm_config() -> Dict:
    if not os.path.exists(CONFIG_PATH):
        return deepcopy(DEFAULT_CONFIG)

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as handle:
            config = json.load(handle)
    except Exception:
        return deepcopy(DEFAULT_CONFIG)

    is_valid, _ = validate_llm_config(config)
    if not is_valid:
        return deepcopy(DEFAULT_CONFIG)

    return config


def save_llm_config(config: Dict) -> Tuple[bool, str]:
    is_valid, error = validate_llm_config(config)
    if not is_valid:
        return False, error

    normalized = deepcopy(config)
    normalized["providers"] = [_normalize_provider(p) for p in config.get("providers", [])]

    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as handle:
            json.dump(normalized, handle, indent=2, ensure_ascii=False)
    except Exception as exc:
        return False, str(exc)

    return True, ""


def get_default_provider(config: Dict) -> Dict:
    providers = config.get("providers", [])
    if not providers:
        return {}
    for provider in providers:
        if provider.get("is_default"):
            return provider
    return providers[0]


def set_default_provider(config: Dict, name: str) -> Dict:
    for provider in config.get("providers", []):
        provider["is_default"] = provider.get("name") == name
    return config


def upsert_provider(config: Dict, provider: Dict) -> Dict:
    providers: List[Dict] = config.get("providers", [])
    incoming = _normalize_provider(provider)
    for idx, existing in enumerate(providers):
        if existing.get("name") == incoming["name"]:
            providers[idx] = incoming
            break
    else:
        providers.append(incoming)
    config["providers"] = providers
    return config


def remove_provider(config: Dict, name: str) -> Dict:
    providers = [p for p in config.get("providers", []) if p.get("name") != name]
    config["providers"] = providers
    return config
