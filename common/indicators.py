"""Dependency-light technical indicators."""
from __future__ import annotations
import numpy as np

def sma(values, period):
    a = np.asarray(values, dtype=float)
    out = np.full(len(a), np.nan)
    if period <= 0: return out
    for i in range(period - 1, len(a)):
        out[i] = np.mean(a[i-period+1:i+1])
    return out

def true_range(high, low, close):
    h, l, c = map(lambda x: np.asarray(x, dtype=float), (high, low, close))
    prev = np.r_[c[0], c[:-1]]
    return np.maximum(h-l, np.maximum(np.abs(h-prev), np.abs(l-prev)))

def atr(high, low, close, period=14):
    tr = true_range(high, low, close)
    out = np.full(len(tr), np.nan)
    if len(tr) >= period:
        out[period-1] = np.mean(tr[:period])
        for i in range(period, len(tr)):
            out[i] = (out[i-1] * (period-1) + tr[i]) / period
    return out

def rsi(close, period=14):
    c = np.asarray(close, dtype=float)
    out = np.full(len(c), np.nan)
    if len(c) <= period: return out
    delta = np.diff(c)
    gain = np.maximum(delta, 0)
    loss = np.maximum(-delta, 0)
    avg_gain = np.mean(gain[:period])
    avg_loss = np.mean(loss[:period])
    def calc(g, l):
        return 100.0 if l == 0 and g > 0 else (50.0 if l == 0 else 100 - 100/(1+g/l))
    out[period] = calc(avg_gain, avg_loss)
    for i in range(period+1, len(c)):
        avg_gain = (avg_gain*(period-1) + gain[i-1])/period
        avg_loss = (avg_loss*(period-1) + loss[i-1])/period
        out[i] = calc(avg_gain, avg_loss)
    return out

def rolling_zscore(values, period=20):
    a = np.asarray(values, dtype=float)
    out = np.full(len(a), np.nan)
    for i in range(period-1, len(a)):
        w = a[i-period+1:i+1]
        w = w[np.isfinite(w)]
        if len(w) == 0 or not np.isfinite(a[i]):
            continue
        sd = np.std(w)
        out[i] = 0.0 if sd == 0 else (a[i]-np.mean(w))/sd
    return out

def pct_change(values, periods=1):
    a = np.asarray(values, dtype=float)
    out = np.full(len(a), np.nan)
    if periods < len(a):
        out[periods:] = (a[periods:] / a[:-periods] - 1.0) * 100
    return out
