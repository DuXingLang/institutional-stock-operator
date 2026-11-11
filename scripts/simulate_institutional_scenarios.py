#!/usr/bin/env python3
"""Monte Carlo scenario engine using ATR-scaled historical returns."""
import argparse,json,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from common.data_normalizer import load_market_data,generated_at
from common.config import int_option,require_object
from common.indicators import atr
from common.statistics import monte_carlo_returns,describe

VERSION="1.0.0"
PLAYBOOKS=["accumulation","shakeout","markup","high_level_turnover","distribution"]
REGIMES=["bullish","range","bearish"]

def simulate(data,behavior=None,config=None):
    cfg=require_object(config,"config")
    n_paths=int_option(cfg,"n_paths",10000,minimum=1)
    horizon=int_option(cfg,"horizon_sessions",1,minimum=1)
    seed=int_option(cfg,"seed",17,minimum=0)
    if behavior is not None and not isinstance(behavior,dict):
        raise ValueError("behavior must be a JSON object (the output of the detection engine)")
    bars=data["daily_bars"]
    close=np.array([b["close"] for b in bars]);high=np.array([b["high"] for b in bars]);low=np.array([b["low"] for b in bars])
    returns=(close[1:]/close[:-1]-1)*100
    recent=returns[-60:]
    mu=float(np.mean(recent)) if len(recent) else 0
    sigma=float(np.std(recent,ddof=1)) if len(recent)>1 else 1.5
    degenerate_vol=sigma<1e-6
    atrv=atr(high,low,close,14)[-1]
    atr_pct=float(atrv/close[-1]*100) if np.isfinite(atrv) else max(sigma,1)
    market=data.get("market_context")
    if market is None:
        market={}
    if not isinstance(market,dict):
        raise ValueError("market_context must be a JSON object")
    regime_value=market.get("market_regime","range")
    if not isinstance(regime_value,str):
        raise ValueError("market_context.market_regime must be a string")
    market=regime_value
    regime_map={"bull":"bullish","strong":"bullish","bullish":"bullish","bear":"bearish","weak":"bearish","bearish":"bearish","range":"range","震荡":"range","普涨":"bullish","普跌":"bearish","大跌修复":"range"}
    base_regime=regime_map.get(str(market).lower(),"range")
    # Small, explicit conditional shifts. These are model assumptions, not observed order flow.
    regime_shift={"bullish":0.35*atr_pct,"range":0.0,"bearish":-0.45*atr_pct}
    playbook_shift={"accumulation":0.05,"shakeout":-0.10,"markup":0.30,"high_level_turnover":-0.10,"distribution":-0.35}
    results=[]
    for regime in REGIMES:
      for playbook in PLAYBOOKS:
        adjusted_mu=mu+regime_shift[regime]+playbook_shift[playbook]*atr_pct
        # deterministic but distinct seeds for reproducibility
        samples=monte_carlo_returns(adjusted_mu,sigma,n_paths,horizon,seed+REGIMES.index(regime)*13+PLAYBOOKS.index(playbook))
        stats=describe(samples)
        p_loss=float(np.mean(samples<0))
        p_drawdown=float(np.mean(samples<=-atr_pct))
        results.append({"market_regime":regime,"hypothetical_playbook":playbook,
          "assumed_daily_mean_pct":round(adjusted_mu,4),"daily_volatility_pct":round(sigma,4),
          "atr_pct":round(atr_pct,4),"horizon_sessions":horizon,"return_distribution":stats,
          "probability_loss":p_loss,"probability_loss_exceeds_1_atr":p_drawdown,
          "risk_reward_proxy":round(stats["p90"]/abs(stats["p10"]),4) if stats["p10"] is not None and stats["p90"] is not None and stats["p10"]<0 else None})
    selected=[x for x in results if x["market_regime"]==base_regime]
    def _mean_key(item):
        mean=item["return_distribution"]["mean"]
        return mean if mean is not None else -999.0
    selected.sort(key=_mean_key,reverse=True)
    warnings=["情景结果依赖正态收益近似和人为设定的情景偏移，不能代表真实主力操盘计划。",
              "未模拟涨跌停排队、跳空、停牌、盘口冲击、交易费用及个股流动性约束。"]
    if len(bars)<60:warnings.append("历史日线少于60根，收益波动估计不稳定。")
    if degenerate_vol:warnings.append("近60日收益率波动接近零（价格几乎不变），模拟结果接近确定性，参考价值有限。")
    return {"symbol":data["symbol"],"name":data.get("name"),"as_of":data["as_of"],
      "generated_at":generated_at(),"algorithm_version":VERSION,"base_market_regime":base_regime,
      "historical_return_mean_pct":mu,"historical_return_volatility_pct":sigma,
      "selected_regime_ranking":selected,"all_scenarios":results,
      "behavior_context":(behavior or {}).get("leading_hypothesis"),
      "warnings":warnings}

def main():
    p=argparse.ArgumentParser();p.add_argument("--input",required=True);p.add_argument("--behavior")
    p.add_argument("--config");p.add_argument("--output");p.add_argument("--pretty",action="store_true");a=p.parse_args()
    behavior=json.loads(Path(a.behavior).read_text(encoding="utf-8")) if a.behavior else None
    cfg=json.loads(Path(a.config).read_text(encoding="utf-8")) if a.config else None
    result=simulate(load_market_data(a.input),behavior,cfg)
    out=json.dumps(result,ensure_ascii=False,indent=2 if a.pretty else None,allow_nan=False)
    if a.output:Path(a.output).parent.mkdir(parents=True,exist_ok=True);Path(a.output).write_text(out,encoding="utf-8")
    else:print(out)
if __name__=="__main__":main()