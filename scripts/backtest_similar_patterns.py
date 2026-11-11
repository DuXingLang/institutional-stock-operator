#!/usr/bin/env python3
"""Historical analog search with strictly prior forward outcomes."""
import argparse,json,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from common.data_normalizer import load_market_data,generated_at
from common.config import int_option,int_list_option,require_object
from common.feature_engineering import build_feature_rows,FEATURE_NAMES
from common.statistics import describe

VERSION="1.0.0"
COMMON_WARNINGS=["相似样本统计为历史条件分布，不是未来收益承诺。",
  "候选样本的特征只使用其当时及以前数据；其前视收益用于统计标签。相邻历史样本可能重叠，统计置信度会因此偏乐观。",
  "未进行跨股票横截面验证、幸存者偏差校正或交易成本扣除。"]

def _vector(features):
    return np.array([features.get(k,np.nan) if features.get(k) is not None else np.nan for k in FEATURE_NAMES],dtype=float)

def _prepare_matrix(rows):
    """Scale candidate rows with statistics computed on candidates only.

    Returns the scaled matrix, the median/scale used, and per-feature coverage
    (share of finite values) so callers can warn when a feature is unusable.
    """
    mat=np.vstack([_vector(r["features"]) for r in rows])
    coverage=np.mean(np.isfinite(mat),axis=0)
    med=np.zeros(mat.shape[1])
    scale=np.ones(mat.shape[1])
    for j in range(mat.shape[1]):
        column=mat[:,j]
        finite=column[np.isfinite(column)]
        if len(finite):
            med[j]=float(np.median(finite))
    filled=np.where(np.isfinite(mat),mat,med)
    for j in range(mat.shape[1]):
        sd=float(np.std(filled[:,j]))
        scale[j]=sd if sd>=1e-8 else 1.0
    return (filled-med)/scale,med,scale,coverage

def _similarity(query,candidate):
    # Robust normalized Euclidean distance converted to [0,1] similarity.
    dist=float(np.sqrt(np.mean((query-candidate)**2)))
    return 1.0/(1.0+dist)

def _empty_statistics(horizons):
    return {str(h):{metric:describe([]) for metric in ("forward_returns_pct","mfe_pct","mae_pct")} for h in horizons}

def backtest(data,config=None):
    cfg=require_object(config,"config")
    top_k=int_option(cfg,"top_k",30,minimum=1)
    min_history=int_option(cfg,"min_history",120,minimum=0)
    horizons=int_list_option(cfg,"horizons",[1,3,5,10],minimum=1)
    rows=build_feature_rows(data); n=len(rows)
    start=max(60,min_history)
    required=start+max(horizons)+1
    warnings=[]
    if n<required:
        warnings.append(f"样本不足：当前{n}根日K，建议至少{required}根（候选起点={start}，最长前视={max(horizons)}）；仍尝试输出可用统计。")
    # Query is the latest feature row. Historical candidates must have enough
    # look-ahead bars and cannot overlap the query date or its future.
    query_idx=n-1
    train_end=max(0,query_idx-max(horizons))
    candidate_indices=list(range(start,train_end))
    if not candidate_indices:
        warnings.append(f"没有满足条件的候选样本：候选索引需 >= {start} 且 <= {train_end-1}，即至少需要 {start+max(horizons)+1} 根日K。")
        warnings.extend(COMMON_WARNINGS)
        return {"symbol":data["symbol"],"name":data.get("name"),"as_of":data["as_of"],
          "generated_at":generated_at(),"algorithm_version":VERSION,
          "feature_names":FEATURE_NAMES,"analog_count":0,
          "similarity_method":"historical-candidate-only z-score + normalized Euclidean similarity",
          "horizon_statistics":_empty_statistics(horizons),"analogs":[],"warnings":warnings}
    # Fit scaler only on historical candidates, avoiding query/future leakage.
    hist_rows=[rows[i] for i in candidate_indices]
    hist_scaled,med,scale,coverage=_prepare_matrix(hist_rows)
    for name,cov in zip(FEATURE_NAMES,coverage):
        if cov==0:
            warnings.append(f"特征 {name} 在历史候选中全部缺失，已从相似度计算中失效；结果主要由其余特征决定。")
        elif cov<0.5:
            warnings.append(f"特征 {name} 在历史候选中仅 {cov:.0%} 可用，相似度稳定性下降。")
    qv=_vector(rows[query_idx]["features"])
    qv=np.where(np.isfinite(qv),qv,med)
    qscaled=(qv-med)/scale
    sims=[(_similarity(qscaled,hist_scaled[j]),idx) for j,idx in enumerate(candidate_indices)]
    sims.sort(reverse=True)
    selected=sims[:top_k]
    closes=np.array([b["close"] for b in data["daily_bars"]],dtype=float)
    highs=np.array([b["high"] for b in data["daily_bars"]],dtype=float)
    lows=np.array([b["low"] for b in data["daily_bars"]],dtype=float)
    analogs=[]
    for sim,idx in selected:
        item={"date":rows[idx]["date"],"similarity":round(float(sim),5),"forward_returns_pct":{},"mfe_pct":{},"mae_pct":{}}
        for h in horizons:
            if idx+h>=n: continue
            base=closes[idx]
            item["forward_returns_pct"][str(h)]=float((closes[idx+h]/base-1)*100)
            item["mfe_pct"][str(h)]=float((np.max(highs[idx+1:idx+h+1])/base-1)*100)
            item["mae_pct"][str(h)]=float((np.min(lows[idx+1:idx+h+1])/base-1)*100)
        analogs.append(item)
    stats={}
    for h in horizons:
        key=str(h)
        stats[key]={}
        for metric in ("forward_returns_pct","mfe_pct","mae_pct"):
            vals=[x[metric][key] for x in analogs if key in x[metric]]
            stats[key][metric]=describe(vals)
    warnings.extend(COMMON_WARNINGS)
    return {"symbol":data["symbol"],"name":data.get("name"),"as_of":data["as_of"],
      "generated_at":generated_at(),"algorithm_version":VERSION,
      "feature_names":FEATURE_NAMES,"analog_count":len(analogs),
      "similarity_method":"historical-candidate-only z-score + normalized Euclidean similarity",
      "horizon_statistics":stats,"analogs":analogs,"warnings":warnings}

def main():
    p=argparse.ArgumentParser();p.add_argument("--input",required=True);p.add_argument("--config")
    p.add_argument("--output");p.add_argument("--pretty",action="store_true");a=p.parse_args()
    cfg=json.loads(Path(a.config).read_text(encoding="utf-8")) if a.config else None
    result=backtest(load_market_data(a.input),cfg)
    out=json.dumps(result,ensure_ascii=False,indent=2 if a.pretty else None,allow_nan=False)
    if a.output:Path(a.output).parent.mkdir(parents=True,exist_ok=True);Path(a.output).write_text(out,encoding="utf-8")
    else:print(out)
if __name__=="__main__":main()