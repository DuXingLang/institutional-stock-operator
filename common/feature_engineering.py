"""Build point-in-time features from normalized daily bars."""
from __future__ import annotations
import numpy as np
from .indicators import sma, atr, rsi, rolling_zscore, pct_change

FEATURE_NAMES = [
    "ret_1", "ret_5", "ret_20", "ma5_gap", "ma20_gap", "ma60_gap",
    "vol_ratio_5_20", "amount_ratio_5_20", "turnover_z20",
    "atr_pct", "rsi14", "range_pos20", "body_pct", "close_location"
]

TURNOVER_FILL_WINDOW = 60

def causal_median_fill(values, window=TURNOVER_FILL_WINDOW):
    """Fill missing points with the median of at most ``window`` prior samples.

    Each filled value uses only bars up to and including its own index, so a
    candidate row never sees future data. If no observation exists yet the
    point stays NaN instead of being replaced by an arbitrary constant.
    """
    a = np.asarray(values, dtype=float)
    out = np.array(a, copy=True)
    filled = np.full(len(a), np.nan)
    for i in range(len(a)):
        window_values = a[max(0, i - window + 1):i + 1]
        window_values = window_values[np.isfinite(window_values)]
        if len(window_values):
            filled[i] = float(np.median(window_values))
    missing = ~np.isfinite(out)
    out[missing] = filled[missing]
    return out

def build_feature_rows(data: dict):
    bars = data["daily_bars"]
    close = np.array([b["close"] for b in bars], dtype=float)
    high = np.array([b["high"] for b in bars], dtype=float)
    low = np.array([b["low"] for b in bars], dtype=float)
    op = np.array([b["open"] for b in bars], dtype=float)
    vol = np.array([b["volume"] for b in bars], dtype=float)
    amount = np.array([b["amount"] if b["amount"] is not None else np.nan for b in bars], dtype=float)
    turnover = np.array([b["turnover_rate"] if b["turnover_rate"] is not None else np.nan for b in bars], dtype=float)
    ma5, ma20, ma60 = sma(close,5), sma(close,20), sma(close,60)
    a = atr(high, low, close, 14)
    r = rsi(close,14)
    v5, v20 = sma(vol,5), sma(vol,20)
    # Missing amount must not be treated as zero turnover of money: that
    # silently shrinks the 5/20 ratio. sma propagates NaN, so rows whose window
    # contains a gap stay empty and are dropped/handled by the caller.
    am5, am20 = sma(amount,5), sma(amount,20)
    turnover_filled = causal_median_fill(turnover)
    tz = rolling_zscore(turnover_filled, 20)
    hi20, lo20 = np.full(len(close),np.nan), np.full(len(close),np.nan)
    for i in range(19,len(close)):
        hi20[i], lo20[i] = np.max(high[i-19:i+1]), np.min(low[i-19:i+1])
    rows=[]
    for i,b in enumerate(bars):
        def safe(x):
            return None if not np.isfinite(x) else float(x)
        f = {
            "ret_1": safe(pct_change(close,1)[i]),
            "ret_5": safe(pct_change(close,5)[i]),
            "ret_20": safe(pct_change(close,20)[i]),
            "ma5_gap": safe((close[i]/ma5[i]-1)*100) if np.isfinite(ma5[i]) else None,
            "ma20_gap": safe((close[i]/ma20[i]-1)*100) if np.isfinite(ma20[i]) else None,
            "ma60_gap": safe((close[i]/ma60[i]-1)*100) if np.isfinite(ma60[i]) else None,
            "vol_ratio_5_20": safe(v5[i]/v20[i]) if np.isfinite(v5[i]) and v20[i] and v20[i]>0 else None,
            "amount_ratio_5_20": safe(am5[i]/am20[i]) if np.isfinite(am5[i]) and np.isfinite(am20[i]) and am20[i]>0 else None,
            "turnover_z20": safe(tz[i]),
            "atr_pct": safe(a[i]/close[i]*100) if np.isfinite(a[i]) else None,
            "rsi14": safe(r[i]),
            "range_pos20": safe((close[i]-lo20[i])/(hi20[i]-lo20[i])) if np.isfinite(hi20[i]) and hi20[i]>lo20[i] else None,
            "body_pct": safe((close[i]-op[i])/op[i]*100),
            "close_location": safe((close[i]-low[i])/(high[i]-low[i])) if high[i]>low[i] else 0.5,
        }
        rows.append({"date":b["date"], "close":float(close[i]), "high":float(high[i]), "low":float(low[i]), "volume":float(vol[i]), "features":f})
    return rows

def latest_feature_vector(data):
    return build_feature_rows(data)[-1]["features"]