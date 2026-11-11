#!/usr/bin/env python3
"""Detect observable price/volume patterns; never infer actual private intent."""
import argparse, json, math, sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from common.data_normalizer import load_market_data, generated_at
from common.indicators import sma, atr, rsi, rolling_zscore
from common.scoring import load_weights, score_behaviors

VERSION="1.0.0"

def _block(data,key):
    value=data.get(key)
    if value is None:
        return {}
    if not isinstance(value,dict):
        raise ValueError(f"{key} must be a JSON object, got {type(value).__name__}")
    return value

def _finite_float(value,default=0.0):
    try: number=float(value)
    except (TypeError,ValueError): return default
    if isinstance(value,bool): return default
    return number if math.isfinite(number) else default

def analyze(data, weights=None):
    bars=data["daily_bars"]; n=len(bars)
    c=np.array([b["close"] for b in bars]); o=np.array([b["open"] for b in bars])
    h=np.array([b["high"] for b in bars]); l=np.array([b["low"] for b in bars])
    v=np.array([b["volume"] for b in bars])
    t=np.array([b["turnover_rate"] if b["turnover_rate"] is not None else np.nan for b in bars])
    ma5,ma20,ma60=sma(c,5),sma(c,20),sma(c,60)
    a=atr(h,l,c,14); rr=rsi(c,14)
    avgv20=np.mean(v[-20:]) if n>=20 else np.mean(v)
    vol_ratio=float(v[-1]/avgv20) if avgv20>0 else 1
    ret1=float((c[-1]/c[-2]-1)*100)
    ret5=float((c[-1]/c[-6]-1)*100) if n>=6 else ret1
    ret20=float((c[-1]/c[-21]-1)*100) if n>=21 else ret5
    range20=(float(np.max(h[-20:])),float(np.min(l[-20:]))) if n>=20 else (float(np.max(h)),float(np.min(l)))
    width=(range20[0]-range20[1])/max(range20[1],1e-9)*100
    pos=(c[-1]-range20[1])/max(range20[0]-range20[1],1e-9)
    close_loc=(c[-1]-l[-1])/max(h[-1]-l[-1],1e-9)
    body=(c[-1]-o[-1])/o[-1]*100
    # Turnover can be missing for the most recent bars while older bars carry
    # it. The recent-20 median would then be NaN, so fall back to the full
    # history median and never leave NaNs inside the z-score series.
    finite_t=np.isfinite(t)
    if finite_t.any():
        tmed=(float(np.nanmedian(t[-20:])) if np.isfinite(t[-20:]).any()
              else float(np.nanmedian(t)))
    else:
        tmed=None
    tlast=float(t[-1]) if finite_t[-1] else None
    tz=0.0
    if n>=20:
        filled=np.nan_to_num(t,nan=(tmed if tmed is not None else 0.0))
        raw_tz=float(rolling_zscore(filled,min(20,n))[-1])
        tz=raw_tz if math.isfinite(raw_tz) else 0.0
    near_high=(range20[0]-c[-1])/max(c[-1],1e-9)*100
    prior_ret5=float((c[-2]/c[-7]-1)*100) if n>=7 else 0
    sector=_block(data,"sector")
    flow=_block(data,"capital_flow")
    chip=_block(data,"chip")
    sector_ret=_finite_float(sector.get("return_1d"),0.0)
    inflow=_finite_float(flow.get("net_inflow"),0.0)
    signals={
      "low_volatility":float(np.clip(1-vol_ratio/1.5,0,1)),
      "range_bound":float(np.clip(1-width/18,0,1)),
      "volume_dryup":float(np.clip(1-vol_ratio,0,1)),
      "turnover_stable":float(np.clip(1-abs(tz)/3,0,1)),
      "support_holding":float(np.clip((c[-1]-range20[1])/max(range20[0]-range20[1],1e-9),0,1)),
      "rsi_recovery":float(np.clip((rr[-1]-35)/25,0,1)) if np.isfinite(rr[-1]) else 0.5,
      "up_day_volume":float(np.clip((vol_ratio-0.8)/1.5,0,1)) if ret1>0 else 0,
      "ma20_flat":float(np.clip(1-abs((ma20[-1]/ma20[-6]-1)*100)/5,0,1)) if n>=25 and np.isfinite(ma20[-6]) else 0.5,
      "near_resistance":float(np.clip(1-abs(near_high)/5,0,1)),
      "volume_expansion":float(np.clip((vol_ratio-1)/1.5,0,1)),
      "strong_close":float(np.clip((close_loc-0.45)/0.55,0,1)),
      "positive_return":float(np.clip((ret1+1)/4,0,1)),
      "sector_strength":float(np.clip((sector_ret+1)/3,0,1)),
      "rsi_strength":float(np.clip((rr[-1]-45)/30,0,1)) if np.isfinite(rr[-1]) else 0.5,
      "intraday_recovery":float(np.clip((close_loc-0.3)/0.7,0,1)),
      "volume_spike":float(np.clip((vol_ratio-1)/2,0,1)),
      "prior_uptrend":float(np.clip((prior_ret5+2)/8,0,1)),
      "close_strong":float(np.clip((close_loc-0.35)/0.65,0,1)),
      "rsi_reset":float(np.clip(1-abs((rr[-1] if np.isfinite(rr[-1]) else 50)-50)/50,0,1)),
      "breakout":1.0 if c[-1]>range20[0] * 0.995 and ret1>0 else float(np.clip((c[-1]/range20[0]-0.94)/0.06,0,1)),
      "ma_alignment":float(np.mean([c[-1]>ma5[-1], c[-1]>ma20[-1], np.isfinite(ma60[-1]) and c[-1]>ma60[-1]])),
      "capital_inflow":float(np.clip(inflow/(abs(inflow)+1e7),0,1)) if inflow>0 else 0,
      "positive_momentum":float(np.clip((ret20+5)/20,0,1)),
      "higher_highs":float(np.clip((c[-1]/np.max(h[-10:-1])-0.97)/0.05,0,1)) if n>=10 else 0.5,
      "volume_confirmation":float(np.clip(vol_ratio/2,0,1)) if ret1>0 else 0,
      "high_range_position":float(np.clip((pos-0.65)/0.35,0,1)),
      "high_volume":float(np.clip((vol_ratio-1)/1.5,0,1)),
      "wide_range":float(np.clip(width/15,0,1)),
      "weak_close":float(np.clip((0.55-close_loc)/0.55,0,1)),
      "turnover_spike":float(np.clip(tz/3,0,1)),
      "momentum_fade":float(np.clip((ret5-ret1)/5,0,1)),
      "negative_momentum":float(np.clip((-ret5+2)/8,0,1)),
      "failed_breakout":float(np.clip((near_high+max(ret1,0))/5,0,1)),
      "sector_weakness":float(np.clip((1-sector_ret)/3,0,1)),
      "default":0.35
    }
    # A non-finite signal used to slip into the score as 100 because
    # min(100, nan) == 100. Normalize every signal to a finite number first.
    signals={k:(float(v) if math.isfinite(float(v)) else 0.0) for k,v in signals.items()}
    scores=score_behaviors(signals,weights or load_weights())
    best=max(scores,key=scores.get)
    evidence=[
      f"最新单日涨跌幅 {ret1:.2f}%",
      f"最新成交量/近20日均量 {vol_ratio:.2f} 倍",
      f"收盘在近20日区间的位置 {pos:.2f}",
      f"近20日区间宽度 {width:.2f}%",
      f"收盘位置指标 {close_loc:.2f}"
    ]
    if tlast is not None:evidence.append(f"最新换手率 {tlast:.2f}%")
    warnings=[]
    if n<60:warnings.append("日线样本少于60根，长周期均线与行为判断可靠性有限")
    if not finite_t.any():
        warnings.append("缺少换手率，换手相关信号已弱化")
    elif not np.isfinite(t[-20:]).any():
        warnings.append("最近20根日K缺少换手率，换手率突变信号按中性处理")
    if not data.get("intraday_bars"):warnings.append("缺少分钟线，无法识别真实分时承接/冲高回落结构")
    if not chip:warnings.append("缺少筹码分布数据，未使用筹码成本/集中度判断")
    if not flow:warnings.append("缺少资金流数据，资金流相关信号按中性或零处理")
    if best=="neutral":warnings.append("各行为特征区分度不足，neutral 得分最高，宜按中性/观望处理")
    return {
      "symbol":data["symbol"],"name":data.get("name"),"as_of":data["as_of"],
      "generated_at":generated_at(),"algorithm_version":VERSION,
      "leading_hypothesis":best,"leading_score":scores[best],
      "scores":scores,"signals":{k:round(float(v),4) for k,v in signals.items()},
      "key_metrics":{"close":float(c[-1]),"return_1d_pct":ret1,"return_5d_pct":ret5,"return_20d_pct":ret20,
        "volume_ratio_20d":vol_ratio,"atr14":float(a[-1]) if np.isfinite(a[-1]) else None,
        "rsi14":float(rr[-1]) if np.isfinite(rr[-1]) else None,"turnover_rate":tlast,
        "chip_average_cost":chip.get("average_cost"),"chip_profit_ratio":chip.get("profit_ratio")},
      "evidence":evidence,
      "interpretation":"以上为公开行情特征与预设规则的匹配程度，不代表真实机构持仓、真实主力意图或内幕信息。",
      "warnings":warnings
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True);p.add_argument("--output");p.add_argument("--weights")
    p.add_argument("--pretty",action="store_true");args=p.parse_args()
    result=analyze(load_market_data(args.input),load_weights(args.weights))
    out=json.dumps(result,ensure_ascii=False,indent=2 if args.pretty else None,allow_nan=False)
    if args.output:Path(args.output).parent.mkdir(parents=True,exist_ok=True);Path(args.output).write_text(out,encoding="utf-8")
    else:print(out)
if __name__=="__main__":main()