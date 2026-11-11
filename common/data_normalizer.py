"""Input validation and normalization for stock market JSON."""
from __future__ import annotations
from datetime import datetime, timezone
from datetime import date as _date
from typing import Any
import math

REQUIRED_BAR_FIELDS = ("date", "open", "high", "low", "close", "volume")
OPTIONAL_OBJECT_BLOCKS = ("market_context", "sector", "capital_flow", "chip", "metadata")
OPTIONAL_NUMERIC_FIELDS = (
    ("sector", "return_1d"),
    ("capital_flow", "net_inflow"),
    ("chip", "average_cost"),
    ("chip", "profit_ratio"),
)

def _num(value: Any, field: str, allow_none: bool = False):
    if value is None:
        if allow_none:
            return None
        raise ValueError(f"Field {field!r} must be numeric, got null")
    if isinstance(value, bool):
        raise ValueError(f"Field {field!r} must be numeric, got boolean")
    try:
        result = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"Field {field!r} must be numeric, got {value!r}")
    if not math.isfinite(result):
        raise ValueError(f"Field {field!r} must be finite")
    return result

def _text(payload: dict, key: str):
    """Return an optional non-empty string field or None."""
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Field {key!r} must be a non-empty string")
    return value.strip()

def _object_block(payload: dict, key: str) -> dict:
    value = payload.get(key)
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"Field {key!r} must be a JSON object, got {type(value).__name__}")
    return value

def _list_block(payload: dict, key: str) -> list:
    value = payload.get(key)
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"Field {key!r} must be a JSON array, got {type(value).__name__}")
    return value

def _iso_date(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Field {field!r} must be a date string in YYYY-MM-DD form")
    text = value.strip()[:10]
    try:
        _date.fromisoformat(text)
    except ValueError:
        raise ValueError(f"Field {field!r} must be a valid ISO date (YYYY-MM-DD), got {value!r}")
    return text

def normalize_market_data(payload: dict) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("Input JSON root must be an object")
    symbol = payload.get("symbol")
    if not isinstance(symbol, str) or not symbol.strip():
        raise ValueError("Field 'symbol' must be a non-empty string")
    symbol = symbol.strip()
    name = _text(payload, "name")
    raw_bars = payload.get("daily_bars")
    if not isinstance(raw_bars, list) or len(raw_bars) < 2:
        raise ValueError("daily_bars must contain at least 2 bars")
    bars = []
    seen = set()
    for i, raw in enumerate(raw_bars):
        if not isinstance(raw, dict):
            raise ValueError(f"daily_bars[{i}] must be an object")
        missing = [k for k in REQUIRED_BAR_FIELDS if k not in raw]
        if missing:
            raise ValueError(f"daily_bars[{i}] missing fields: {', '.join(missing)}")
        date = _iso_date(raw["date"], f"daily_bars[{i}].date")
        if date in seen:
            raise ValueError(f"Duplicate daily bar date: {date}")
        seen.add(date)
        bar = {"date": date}
        for key in ("open", "high", "low", "close", "volume"):
            bar[key] = _num(raw[key], f"daily_bars[{i}].{key}")
        for key in ("amount", "turnover_rate"):
            bar[key] = _num(raw.get(key), f"daily_bars[{i}].{key}", allow_none=True)
        if min(bar["open"], bar["high"], bar["low"], bar["close"]) <= 0:
            raise ValueError(f"daily_bars[{i}] prices must be > 0")
        if bar["high"] < max(bar["open"], bar["close"], bar["low"]):
            raise ValueError(f"daily_bars[{i}] high is inconsistent")
        if bar["low"] > min(bar["open"], bar["close"], bar["high"]):
            raise ValueError(f"daily_bars[{i}] low is inconsistent")
        if bar["volume"] < 0:
            raise ValueError(f"daily_bars[{i}] volume cannot be negative")
        bars.append(bar)
    bars.sort(key=lambda x: x["date"])
    as_of = _text(payload, "as_of") or bars[-1]["date"]
    try:
        datetime.fromisoformat(as_of.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError(f"Field 'as_of' must be an ISO date or date-time, got {as_of!r}")
    result = {
        "symbol": symbol,
        "name": name,
        "as_of": as_of,
        "daily_bars": bars,
        "intraday_bars": _list_block(payload, "intraday_bars"),
        "market_context": _object_block(payload, "market_context"),
        "sector": _object_block(payload, "sector"),
        "capital_flow": _object_block(payload, "capital_flow"),
        "chip": _object_block(payload, "chip"),
        "metadata": _object_block(payload, "metadata"),
    }
    regime = result["market_context"].get("market_regime")
    if regime is not None and not isinstance(regime, str):
        raise ValueError("Field 'market_context.market_regime' must be a string")
    for block, field in OPTIONAL_NUMERIC_FIELDS:
        value = result[block].get(field)
        if value is not None:
            result[block][field] = _num(value, f"{block}.{field}")
    return result

def load_market_data(path: str) -> dict:
    import json
    with open(path, "r", encoding="utf-8") as f:
        return normalize_market_data(json.load(f))

def generated_at() -> str:
    return datetime.now(timezone.utc).isoformat()