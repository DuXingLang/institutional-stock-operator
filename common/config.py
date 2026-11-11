"""Validation helpers shared by the engine scripts' configuration objects."""
from __future__ import annotations

from typing import Any


def require_object(config: Any, name: str = "config") -> dict:
    """Return ``config`` as a dict; reject anything else with a clear message."""
    if config is None:
        return {}
    if not isinstance(config, dict):
        raise ValueError(f"{name} must be a JSON object, got {type(config).__name__}")
    return config


def int_option(config: dict, key: str, default: int, minimum: int = 1, name: str = "config") -> int:
    """Read a strictly positive (or ``>= minimum``) integer option."""
    config = require_object(config, name)
    if key not in config or config[key] is None:
        return default
    value = config[key]
    if isinstance(value, bool):
        raise ValueError(f"{name}.{key} must be an integer, got boolean")
    if isinstance(value, float):
        if not value.is_integer():
            raise ValueError(f"{name}.{key} must be an integer, got {value!r}")
        value = int(value)
    if isinstance(value, str):
        raise ValueError(f"{name}.{key} must be an integer, got string {value!r}")
    if not isinstance(value, int):
        raise ValueError(f"{name}.{key} must be an integer, got {type(value).__name__}")
    if value < minimum:
        raise ValueError(f"{name}.{key} must be >= {minimum}, got {value}")
    return value


def int_list_option(config: dict, key: str, default: list[int], minimum: int = 1, name: str = "config") -> list[int]:
    """Read a non-empty list of integers, deduplicated and sorted ascending."""
    config = require_object(config, name)
    if key not in config or config[key] is None:
        return list(default)
    value = config[key]
    if not isinstance(value, list) or not value:
        raise ValueError(f"{name}.{key} must be a non-empty list of integers")
    cleaned: list[int] = []
    for item in value:
        if isinstance(item, bool):
            raise ValueError(f"{name}.{key} must contain integers, got boolean")
        if isinstance(item, float):
            if not item.is_integer():
                raise ValueError(f"{name}.{key} must contain integers, got {item!r}")
            item = int(item)
        if isinstance(item, str):
            raise ValueError(f"{name}.{key} must contain integers, got string {item!r}")
        if not isinstance(item, int):
            raise ValueError(f"{name}.{key} must contain integers, got {type(item).__name__}")
        if item < minimum:
            raise ValueError(f"{name}.{key} entries must be >= {minimum}, got {item}")
        cleaned.append(item)
    return sorted(set(cleaned))