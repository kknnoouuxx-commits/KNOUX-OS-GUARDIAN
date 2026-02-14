"""
Serialization helpers for runtime telemetry, Flask responses, and persistence.
"""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, time
from enum import Enum
from pathlib import Path
from typing import Any


def to_serializable(value: Any) -> Any:
    """Convert arbitrary runtime objects into JSON-safe structures."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, (datetime, date, time)):
        return value.isoformat()

    if isinstance(value, Path):
        return str(value)

    if isinstance(value, bytes):
        try:
            return value.decode("utf-8")
        except UnicodeDecodeError:
            return value.decode("utf-8", errors="replace")

    if is_dataclass(value):
        return to_serializable(asdict(value))

    if isinstance(value, dict):
        return {str(to_serializable(k)): to_serializable(v) for k, v in value.items()}

    if isinstance(value, (list, tuple, set)):
        return [to_serializable(item) for item in value]

    if hasattr(value, "__dict__"):
        attrs = {}
        for key, attr_value in vars(value).items():
            if key.startswith("_") or callable(attr_value):
                continue
            attrs[key] = to_serializable(attr_value)
        if attrs:
            return attrs

    if hasattr(value, "__slots__"):
        attrs = {}
        for slot in value.__slots__:
            if slot.startswith("_"):
                continue
            try:
                attrs[slot] = to_serializable(getattr(value, slot))
            except Exception:
                continue
        if attrs:
            return attrs

    return str(value)


def make_json_safe(payload: Any) -> Any:
    return to_serializable(payload)


def safe_json_dumps(payload: Any, **kwargs: Any) -> str:
    kwargs.setdefault("ensure_ascii", False)
    return json.dumps(make_json_safe(payload), **kwargs)
