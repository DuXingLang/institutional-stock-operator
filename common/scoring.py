"""Transparent rule-based behavior scoring."""
from __future__ import annotations
import json
import math
import sys
from pathlib import Path

DEFAULT_WEIGHTS = {
 "bottom_accumulation":{"low_volatility":0.18,"range_bound":0.20,"volume_dryup":0.18,"turnover_stable":0.12,"support_holding":0.18,"rsi_recovery":0.14},
 "range_accumulation":{"range_bound":0.22,"volume_dryup":0.16,"up_day_volume":0.18,"support_holding":0.18,"ma20_flat":0.12,"turnover_stable":0.14},
 "test_breakout":{"near_resistance":0.22,"volume_expansion":0.22,"strong_close":0.18,"positive_return":0.14,"sector_strength":0.12,"rsi_strength":0.12},
 "shakeout":{"intraday_recovery":0.20,"support_holding":0.20,"volume_spike":0.15,"prior_uptrend":0.18,"close_strong":0.17,"rsi_reset":0.10},
 "breakout_start":{"breakout":0.25,"volume_expansion":0.22,"strong_close":0.16,"ma_alignment":0.15,"sector_strength":0.12,"capital_inflow":0.10},
 "main_uptrend":{"ma_alignment":0.25,"positive_momentum":0.22,"higher_highs":0.18,"volume_confirmation":0.15,"sector_strength":0.10,"rsi_strength":0.10},
 "high_level_turnover":{"high_range_position":0.20,"high_volume":0.20,"wide_range":0.15,"weak_close":0.20,"turnover_spike":0.15,"momentum_fade":0.10},
 "distribution":{"weak_close":0.22,"volume_spike":0.18,"negative_momentum":0.18,"failed_breakout":0.16,"turnover_spike":0.14,"sector_weakness":0.12},
 "neutral":{"default":1.0}
}

# Every signal the detection engine can emit. Custom weight files may only
# reference these keys, so a typo fails fast instead of silently scoring zero.
SIGNAL_NAMES = frozenset("""
low_volatility range_bound volume_dryup turnover_stable support_holding rsi_recovery
up_day_volume ma20_flat near_resistance volume_expansion strong_close positive_return
sector_strength rsi_strength intraday_recovery volume_spike prior_uptrend close_strong
rsi_reset breakout ma_alignment capital_inflow positive_momentum higher_highs
volume_confirmation high_range_position high_volume wide_range weak_close turnover_spike
momentum_fade negative_momentum failed_breakout sector_weakness default
""".split())

def _warn(message: str) -> None:
    print(f"[scoring] {message}", file=sys.stderr)

def _validate_weights(raw, source: str = "weights") -> dict:
    if not isinstance(raw, dict) or not raw:
        raise ValueError(f"{source}: weights must be a non-empty JSON object")
    unknown_labels = [k for k in raw if k not in DEFAULT_WEIGHTS]
    if unknown_labels:
        raise ValueError(
            f"{source}: unknown behavior label(s) {unknown_labels}; "
            f"expected one of {sorted(DEFAULT_WEIGHTS)}"
        )
    merged = {}
    for label, default_parts in DEFAULT_WEIGHTS.items():
        parts = raw.get(label, default_parts)
        if not isinstance(parts, dict) or not parts:
            raise ValueError(f"{source}: behavior {label!r} must map to a non-empty object of signal weights")
        unknown = [k for k in parts if k not in SIGNAL_NAMES]
        if unknown:
            raise ValueError(
                f"{source}: behavior {label!r} references unknown signal(s) {unknown}; "
                "see SIGNAL_NAMES in common/scoring.py"
            )
        clean = {}
        for key, weight in parts.items():
            if isinstance(weight, bool):
                raise ValueError(f"{source}: weight for {label}.{key} must be numeric, got boolean")
            try:
                number = float(weight)
            except (TypeError, ValueError):
                raise ValueError(f"{source}: weight for {label}.{key} must be numeric, got {weight!r}")
            if not math.isfinite(number) or number < 0:
                raise ValueError(f"{source}: weight for {label}.{key} must be a finite non-negative number")
            clean[key] = number
        total = sum(clean.values())
        if abs(total - 1.0) > 1e-6:
            _warn(f"{source}: behavior {label!r} weights sum to {total:.4f}, not 1.0; scores will be rescaled.")
        merged[label] = clean
    missing = [k for k in DEFAULT_WEIGHTS if k not in raw]
    if missing:
        _warn(f"{source}: behavior(s) {missing} missing from the file; built-in defaults were used.")
    return merged

def load_weights(path=None):
    if not path:
        return DEFAULT_WEIGHTS
    if not Path(path).exists():
        _warn(f"weights file {path!r} not found; falling back to built-in defaults.")
        return DEFAULT_WEIGHTS
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    return _validate_weights(raw, source=str(path))

def score_behaviors(signals, weights):
    if not isinstance(weights, dict) or not weights:
        raise ValueError("weights must be a non-empty object")
    scores = {}
    for behavior, parts in weights.items():
        total = 0.0
        for key, weight in parts.items():
            value = signals.get(key, 0.0)
            try:
                number = float(value)
            except (TypeError, ValueError):
                number = 0.0
            if not math.isfinite(number):
                number = 0.0
            total += float(weight) * number
        if not math.isfinite(total):
            total = 0.0
        scores[behavior] = round(max(0.0, min(100.0, total * 100)), 2)
    if "neutral" in scores:
        non_neutral = max((v for k, v in scores.items() if k != "neutral"), default=0)
        scores["neutral"] = round(max(scores["neutral"], 100 - non_neutral), 2)
    return dict(sorted(scores.items(), key=lambda x: x[1], reverse=True))