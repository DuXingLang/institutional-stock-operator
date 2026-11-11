"""Robust descriptive statistics and Monte Carlo helpers."""
from __future__ import annotations
import numpy as np

def describe(values):
    a=np.asarray([x for x in values if x is not None and np.isfinite(x)],dtype=float)
    if len(a)==0:
        return {"n":0,"mean":None,"median":None,"std":None,"p10":None,"p25":None,"p75":None,"p90":None,"positive_rate":None}
    return {"n":int(len(a)),"mean":float(np.mean(a)),"median":float(np.median(a)),"std":float(np.std(a,ddof=1)) if len(a)>1 else 0.0,
            "p10":float(np.percentile(a,10)),"p25":float(np.percentile(a,25)),"p75":float(np.percentile(a,75)),"p90":float(np.percentile(a,90)),
            "positive_rate":float(np.mean(a>0))}

def monte_carlo_returns(mu, sigma, n_paths=10000, horizon=1, seed=17):
    rng=np.random.default_rng(seed)
    sigma=max(float(sigma),0.0001)
    daily=rng.normal(float(mu),sigma,size=(int(n_paths),int(horizon)))
    compounded=np.prod(1+daily/100,axis=1)-1
    return compounded*100
