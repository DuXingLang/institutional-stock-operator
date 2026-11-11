<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white">
  <img alt="NumPy" src="https://img.shields.io/badge/NumPy-1.24%2B-013243?logo=numpy&logoColor=white">
  <img alt="License" src="https://img.shields.io/badge/License-MIT-green">
  <img alt="Skill" src="https://img.shields.io/badge/Skill-v1.1.0-blue">
</p>

<!-- Language navigation -->

<p align="center">
  <a href="#中文">中文</a> | <a href="#english">English</a>
</p>

<a id="中文"></a>

# 机构主力操盘分析 Skill

> 基于公开、带时间戳的行情数据，以假设的机构操盘视角分析 A 股个股；调用主力行为识别、操盘情景模拟和历史相似走势回测三个引擎，输出有证据支撑的 T+1 交易研判辅助。

**一句话定位**：它不预言“主力想做什么”，而是把量价证据、情景假设和历史类比分别摊开，让使用者看清结论从哪里来、又可能在哪里失效。

> **重要提示**：本项目是研究与决策辅助工具，不是自动交易系统。规则评分不等于真实机构意图，情景模拟不等于预测，历史统计不代表未来收益。

## 目录

- [项目简介](#项目简介)
- [核心能力](#核心能力)
- [快速开始](#快速开始)
- [工作流程](#工作流程)
- [输入数据](#输入数据)
- [输出结果](#输出结果)
- [三个分析引擎](#三个分析引擎)
- [配置项](#配置项)
- [推荐使用流程](#推荐使用流程)
- [联合研判与报告结构](#联合研判与报告结构)
- [A股交易约束](#a股交易约束)
- [结果解读](#结果解读)
- [限制与风险](#限制与风险)
- [项目结构](#项目结构)
- [常见问题](#常见问题)
- [许可证](#许可证)
- [免责声明](#免责声明)

## 项目简介

本 Skill 面向 A 股个股研究与短线交易决策辅助。用户提供股票名称或代码后，上层 Agent 获取公开、带时间戳的行情数据，并依次运行三个 Python 引擎：

1. **主力行为识别**：把当前量价结构映射到 9 个可观察标签，给出匹配分数、信号与证据。
2. **操盘情景模拟**：在 3 种市场环境 × 5 类假设策略下进行 Monte Carlo 模拟，展示不同假设下的收益分布与风险。
3. **历史相似走势回测**：在特征计算不使用未来价格数据的前提下，检索历史上相似形态，并统计其后 1、3、5、10 个交易日的表现。

三个引擎的输出由上层 Agent 综合成一份报告，至少包含基准、乐观、悲观情景，判断失效条件，仓位与风险控制建议，以及明确的观望/不交易选项。

**设计原则**

- **证据优先**：明确区分客观事实、量化推断、情景模拟和历史统计。
- **时点严格**：只使用决策时点已经可获得的数据，避免未来数据泄漏。
- **不确定性显式化**：每个输出都带 `warnings`，并保留模型假设说明。
- **允许不交易**：预期优势不足时，观望是合法且应当被优先考虑的结论。

**它不是什么**

- 不是自动交易系统，不连接券商、不生成或执行订单。
- 不获取真实机构订单、持仓、席位或内幕信息。
- 不保证收益，不构成个性化投资建议。
- 不是盘口级撮合器或实盘执行模拟器。

## 核心能力

| 能力             | 说明                                                | 主要输出                           |
| ---------------- | --------------------------------------------------- | ---------------------------------- |
| 数据校验与标准化 | 校验 JSON、按日期排序、补默认值                     | 统一格式的行情数据                 |
| 指标与特征工程   | SMA、EMA、ATR、RSI、滚动 z-score 等                 | 14 维形态特征                      |
| 主力行为识别     | 9 个行为标签的透明规则评分                          | 主导假设、分数、信号、证据、警告   |
| 操盘情景模拟     | 3 种市场环境 × 5 类假设策略，默认每组 10,000 条路径 | 收益分布、亏损概率、风险收益参考   |
| 历史相似走势回测 | 历史候选标准化后计算相似度，默认保留 30 个样本      | 1/3/5/10 日收益、MFE/MAE、正收益率 |
| 结构化输出       | 统一信封字段与 `warnings`，便于上层 Agent 消费      | JSON 结果文件                      |

## 快速开始

这是一个 Agent Skill，没有构建、打包步骤，也不需要单独配置环境。

**安装**

把本仓库地址（或本地目录）交给 Agent，说一句「安装这个 skill」即可。手动安装也只有两步：把整个目录放进 Agent 的 skills 目录（DeepSeek Harness 为 `~/.dsh/skills/`），确认 `SKILL.md` 位于该目录根下、目录名与 frontmatter 的 `name` 一致。

安装完就能用：技能自带示例数据，运行时只依赖 NumPy（Agent 环境缺少时执行 `python -m pip install -r requirements.txt`）。

**使用**

用自然语言给出标的和问题，Agent 会自行调用本技能。常用示例指令：

| 场景 | 示例指令 |
|---|---|
| 主力行为判断 | 用 institutional-stock-operator 分析 600000.SH，最近是主力吸筹还是出货？ |
| 交易决策 | 600000.SH 现在能不能买？给我未来 5 个交易日的上涨概率和回撤风险 |
| 情景推演 | 假设主力明天继续拉升，做一下未来 5 个交易日的情景模拟 |
| 形态回测 | 回测当前形态，历史上相似走势之后 1/3/5/10 日的表现如何？ |
| 复盘报告 | 按技能的报告结构，整理一份 600000.SH 的交易复盘 |

也可以只点名其中一个引擎，例如「只做行为识别，不用情景模拟」。

**数据怎么给**

技能不联网抓行情，需要你提供日 K 数据，以下方式任选一种：

- 直接粘贴 JSON（字段见[输入数据](#输入数据)）；
- 给出本地文件路径，例如 `data/stock.json`；
- 说明先用仓库自带的 `sample_market_data.json`（180 根模拟日 K）试跑。

行为识别建议至少 80 根日 K，回测建议 500 根以上。数据请自行截断到决策时点——脚本不会按 `as_of` 截断 K 线。

**进阶：直接运行脚本**

需要自己跑或接入其他流程时，三个脚本就是全部入口：

```bash
python -m pip install -r requirements.txt

python scripts/detect_institutional_behavior.py --input sample_market_data.json --output results/behavior.json --pretty
python scripts/simulate_institutional_scenarios.py --input sample_market_data.json --behavior results/behavior.json --output results/scenarios.json --pretty
python scripts/backtest_similar_patterns.py --input sample_market_data.json --output results/backtest.json --pretty
```

`--input` 必填，省略 `--output` 时结果打印到标准输出，`results/` 会自动创建。全部参数见 `--help`，引擎细节见[三个分析引擎](#三个分析引擎)。

## 工作流程

```text
行情数据（JSON）
        │
        ▼
校验与标准化（common/data_normalizer.py）
        │
        ├── ① 主力行为识别 ──────────► behavior.json
        │        └── 行为上下文
        ├── ② 操盘情景模拟 ──────────► scenarios.json
        ├── ③ 历史相似走势回测 ──────► backtest.json
        │
        ▼
上层 Agent 综合研判 ─────────────► 交易研判报告
```

## 输入数据

三个脚本接收 UTF-8 编码的 JSON 文件。最小示例如下：

```json
{
  "symbol": "600000.SH",
  "name": "示例股票",
  "as_of": "2026-06-29T14:25:00+08:00",
  "daily_bars": [
    {
      "date": "2026-11-07",
      "open": 10.0,
      "high": 10.3,
      "low": 9.9,
      "close": 10.2,
      "volume": 1200000,
      "amount": 12200000,
      "turnover_rate": 1.2
    },
    {
      "date": "2026-11-10",
      "open": 10.2,
      "high": 10.45,
      "low": 10.1,
      "close": 10.38,
      "volume": 1500000,
      "amount": 15500000,
      "turnover_rate": 1.5
    }
  ],
  "market_context": {
    "market_regime": "range",
    "index_return_1d": 0.3
  },
  "sector": {
    "name": "银行",
    "return_1d": 0.5
  },
  "capital_flow": {
    "net_inflow": 1000000
  },
  "chip": {
    "average_cost": 9.8,
    "profit_ratio": 0.65,
    "concentration_90": 0.18
  }
}
```

**顶层字段**

| 字段             | 必填 | 说明                                                                                                 |
| ---------------- | ---- | ---------------------------------------------------------------------------------------------------- |
| `symbol`         | 是   | 非空字符串，建议带交易所后缀，如 `600000.SH`                                                         |
| `daily_bars`     | 是   | 历史日 K 线，至少 2 根；脚本会按日期升序重新排序                                                     |
| `as_of`          | 否   | 数据截至时间，ISO 日期或日期时间；省略时取最后一根 K 线的日期。仅作元数据记录，脚本不会据此截断 K 线 |
| `name`           | 否   | 股票名称，非空字符串                                                                                 |
| `intraday_bars`  | 否   | 分钟 K 线数组；三个脚本均不强制，缺失时行为引擎会给出警告                                            |
| `market_context` | 否   | 大盘环境（对象）；`market_regime` 支持 `bullish`、`range`、`bearish` 及常见别名                      |
| `sector`         | 否   | 板块对象，如名称与当日收益（`return_1d`）                                                            |
| `capital_flow`   | 否   | 资金流对象，如 `net_inflow`                                                                          |
| `chip`           | 否   | 筹码分布对象，如 `average_cost`、`profit_ratio`、`concentration_90`                                  |
| `metadata`       | 否   | 其他数据源或数据质量信息（对象）                                                                     |

`market_regime` 的常见别名会被映射：`bull`、`strong`、`普涨` 视为 `bullish`；`bear`、`weak`、`普跌` 视为 `bearish`；`震荡`、`大跌修复` 视为 `range`；无法识别的取值按 `range` 处理。

**日 K 线字段**

| 字段                           | 必填 | 约束                                                          |
| ------------------------------ | ---- | ------------------------------------------------------------- |
| `date`                         | 是   | `YYYY-MM-DD` 形式的 ISO 日期字符串；非 ISO 或重复日期会被拒绝 |
| `open`、`high`、`low`、`close` | 是   | 数值且大于 0；最高价/最低价必须与开盘价、收盘价自洽           |
| `volume`                       | 是   | 数值且不小于 0                                                |
| `amount`                       | 否   | 数值或 `null`                                                 |
| `turnover_rate`                | 否   | 数值或 `null`；使用百分数数值                                 |

**数据约定**

- 百分比字段使用百分数数值：`1.2` 表示 `1.2%`，不是 `0.012`。
- 同一数据集中的成交量与成交额必须保持单位一致；示例按“价格 × 成交量”的口径构造成交额。
- 所有数值必须有限；价格必须为正；`high >= max(open, close)`，`low <= min(open, close)`。布尔值不被当作数值，`null` 只能用于可选字段。
- 可选对象字段（`market_context`、`sector`、`capital_flow`、`chip`、`metadata`）必须是 JSON 对象，`intraday_bars` 必须是数组；类型不符会直接报错而不是被静默忽略。
- 可选字段缺失时应直接省略或设为 `null`，不得伪造或填入未经证实的数据。
- `as_of` 仅作元数据记录，脚本不会按它截断 K 线；若数据晚于决策时点，调用方必须在传入前自行截断。
- 完整结构见 `schemas/market_data.schema.json`，可直接参考 `sample_market_data.json`。

## 输出结果

三个脚本都输出一个统一信封，并在其中附带各自的分析结果：

| 字段                | 说明                                                                            |
| ------------------- | ------------------------------------------------------------------------------- |
| `symbol`            | 股票代码                                                                        |
| `name`              | 股票名称；输入未提供时为 `null`，其余情况在包括提前返回在内的所有结果中都会保留 |
| `as_of`             | 数据截至时间；仅作元数据，不触发 K 线截断                                       |
| `generated_at`      | 结果生成时间，UTC ISO 8601                                                      |
| `algorithm_version` | 算法版本，当前为 `1.0.0`                                                        |
| `warnings`          | 数据质量、样本量、模型假设等提示                                                |

`--output` 会写入 JSON 文件，否则输出到标准输出。各引擎的专有字段见下一节；`schemas/engine_output.schema.json` 定义五个必填信封字段（`symbol`、`as_of`、`generated_at`、`algorithm_version`、`warnings`），`name` 是可选附加字段。

## 三个分析引擎

### 1. 主力行为识别

脚本：`scripts/detect_institutional_behavior.py`

根据量价关系、成交量变化、换手率、趋势结构、收盘位置及可选的板块当日收益/资金数据，对 9 个标签进行透明规则评分：

| 标签                  | 含义              | 典型观察                                      |
| --------------------- | ----------------- | --------------------------------------------- |
| `bottom_accumulation` | 底部吸筹特征      | 低位、缩量、波动收窄、换手稳定、守住支撑      |
| `range_accumulation`  | 区间吸筹特征      | 箱体震荡、缩量、阳线放量、20 日线走平         |
| `test_breakout`       | 试盘/测试突破特征 | 接近压力位、放量、收盘偏强、板块配合          |
| `shakeout`            | 洗盘/震仓特征     | 前期上涨后放量急跌、盘中收回、守住支撑        |
| `breakout_start`      | 启动突破特征      | 放量突破 20 日高点、均线转多、资金流入        |
| `main_uptrend`        | 主升趋势特征      | 均线多头排列、20 日动量为正、创新高、量价配合 |
| `high_level_turnover` | 高位换手特征      | 高位、巨量、宽振幅、收盘偏弱、动量衰减        |
| `distribution`        | 派发/出货风险特征 | 收盘弱、放量、负动量、突破失败、板块走弱      |
| `neutral`             | 中性或特征不明显  | 各项信号相互抵消，或数据不足                  |

评分是“0–1 信号值 × 权重”的加权和再乘以 100，范围 0–100；`neutral` 取默认分与“100 − 最高非中性分”中的较大值。`leading_hypothesis` 始终等于 `scores` 中排第一的标签，因此当所有非中性分数都低于 50 时，`neutral` 可能成为领先假设。分数表示当前行情与某类规则的匹配程度，**不是该行为真实发生的概率**，更不能证明某个机构正在执行对应操作。

**关键输出**

- `leading_hypothesis` / `leading_score`：匹配度最高的标签及其分数。
- `scores`：全部标签的分数，按降序排列。
- `signals`：底层信号值（0–1），便于复核评分来源。
- `key_metrics`：最新收盘价、1/5/20 日收益、量比、ATR14、RSI14、换手率及可选筹码指标。
- `evidence`、`interpretation`：关键证据与解释边界。
- `warnings`：样本不足、缺少换手率/分钟线/筹码/资金流等提示。

### 2. 操盘情景模拟

脚本：`scripts/simulate_institutional_scenarios.py`

对 5 类假设策略与 3 种市场环境的所有组合进行模拟，共 15 组；默认每组 10,000 条路径，因此单次运行生成 150,000 条模拟收益路径。

| 假设策略              | 含义     |
| --------------------- | -------- |
| `accumulation`        | 吸筹     |
| `shakeout`            | 洗盘     |
| `markup`              | 拉升     |
| `high_level_turnover` | 高位换手 |
| `distribution`        | 派发     |

| 市场环境  | 含义          |
| --------- | ------------- |
| `bullish` | 上涨/强势环境 |
| `range`   | 震荡环境      |
| `bearish` | 下跌/弱势环境 |

模型先用最近 60 个交易日收益估计日均收益与波动率（不足 60 个时使用全部可用样本），再叠加以下**显式假设偏移**（以 ATR% 为单位）：

**市场环境偏移**

| 市场环境  | 收益偏移     |
| --------- | ------------:|
| `bullish` | +0.35 × ATR% |
| `range`   | 0            |
| `bearish` | −0.45 × ATR% |

**假设策略偏移**

| 假设策略              | 收益偏移     |
| --------------------- | ------------:|
| `accumulation`        | +0.05 × ATR% |
| `shakeout`            | −0.10 × ATR% |
| `markup`              | +0.30 × ATR% |
| `high_level_turnover` | −0.10 × ATR% |
| `distribution`        | −0.35 × ATR% |

两组偏移相互独立并按加法叠加：情景日均收益 = 历史日均收益 + 环境偏移 + 策略偏移；波动率沿用历史估计，不随情景改变。这些偏移是硬编码的模型假设，不是实际机构操盘计划；配置文件中仅暴露路径数、持有期和随机种子三个参数（见[配置项](#配置项)）。模拟使用正态收益近似，未模拟涨跌停排队、跳空、停牌、盘口冲击、交易费用及个股流动性约束。

**关键输出**

- `base_market_regime`：从 `market_context` 推断出的基准环境。
- `historical_return_mean_pct` / `historical_return_volatility_pct`：历史日均收益与波动率估计。
- `selected_regime_ranking`：基准环境下 5 类策略的排序结果（按模拟平均收益降序）。
- `all_scenarios`：全部 15 组情景。
- `behavior_context`：传入的行为识别主导标签（可选；仅作为报告上下文，不改变模拟分布）。
- 每组情景包含 `assumed_daily_mean_pct`、`daily_volatility_pct`、`atr_pct`、`horizon_sessions`、`return_distribution`、`probability_loss`、`probability_loss_exceeds_1_atr`、`risk_reward_proxy`。
- `return_distribution` 含样本数、均值、中位数、标准差、10/25/75/90 分位和正收益率；`probability_loss`、`probability_loss_exceeds_1_atr` 与正收益率均为 0–1 比例，不是百分数。
- `risk_reward_proxy` 为 `p90 / |p10|`（仅当 `p10 < 0` 时给出，否则为 `null`），只是分布不对称性的粗略参考，不是胜率或期望收益。

### 3. 历史相似走势回测

脚本：`scripts/backtest_similar_patterns.py`

主要步骤：

1. 从日 K 线构建 14 维形态特征：`ret_1`、`ret_5`、`ret_20`、`ma5_gap`、`ma20_gap`、`ma60_gap`、`vol_ratio_5_20`、`amount_ratio_5_20`、`turnover_z20`、`atr_pct`、`rsi14`、`range_pos20`、`body_pct`、`close_location`。
2. 只使用历史候选样本拟合中位数与标准差，避免把当前样本或未来信息带入标准化。
3. 用标准化欧氏距离衡量形态相似度，并转换为 `1 / (1 + RMSE)` 的 0–1 相似度。
4. 默认保留相似度最高的 30 个历史样本。
5. 统计每个样本之后 1、3、5、10 个交易日的收益率、最大有利波动（MFE）、最大不利波动（MAE），并汇总分位数与正收益率。

历史候选样本必须满足：候选索引 ≥ `max(60, min_history)`（60 根用于特征预热，`min_history` 默认 120）；特征只使用该样本当时及以前的行情数据（换手率缺失时按截至当日、最多 60 个交易日的中位数回填，见[限制与风险](#限制与风险)）；其后必须有足够的前视窗口。默认 `min_history=120`、最长前视 10 日，因此少于 131 根日 K 时会给出样本不足警告；建议尽可能提供 500 根以上以增加候选样本。

**关键输出**

- `feature_names`：14 个特征名。
- `analog_count`：实际采用的相似样本数。
- `similarity_method`：相似度方法说明。
- `horizon_statistics`：按 `1`、`3`、`5`、`10` 分组，每组含 `forward_returns_pct`、`mfe_pct`、`mae_pct` 的统计量。
- `analogs`：每个历史样本的日期、相似度、前视收益、MFE、MAE。
- `warnings`：样本不足、样本重叠、未做横截面验证/幸存者偏差校正/交易成本扣除等提示。

> 如果没有候选样本（数据长度不足以覆盖 `max(60, min_history) + 最长前视 + 1`），回测会提前返回 `analog_count: 0` 的结果；`feature_names`、`similarity_method`、`name` 与完整的 `horizon_statistics` 仍会保留，便于下游按同一结构解析。

## 配置项

| 文件                           | 作用                   | 可配置项                                                                       |
| ------------------------------ | ---------------------- | ------------------------------------------------------------------------------ |
| `config/behavior_weights.json` | 行为模式的信号权重模板 | 各标签下信号权重、`neutral` 的 `default`                                       |
| `config/scenario_config.json`  | 情景模拟参数           | `n_paths`（默认 10,000）、`horizon_sessions`（默认 1）、`seed`（默认 17）      |
| `config/backtest_config.json`  | 相似走势回测参数       | `top_k`（默认 30）、`min_history`（默认 120）、`horizons`（默认 `[1,3,5,10]`） |

**注意**：脚本不会自动读取 `config/` 下的文件，需要使用 `--weights` 或 `--config` 显式传入；不传时使用代码内置默认值。

```bash
python scripts/detect_institutional_behavior.py \
  --input data/stock.json \
  --weights config/behavior_weights.json \
  --output results/behavior.json

python scripts/simulate_institutional_scenarios.py \
  --input data/stock.json \
  --config config/scenario_config.json \
  --output results/scenarios.json

python scripts/backtest_similar_patterns.py \
  --input data/stock.json \
  --config config/backtest_config.json \
  --output results/backtest.json
```

> `--weights` 指向的文件不存在时，会在标准错误输出一条提示并回退到内置默认权重；权重文件里的未知标签、未知信号键或非数值权重会直接报错，避免拼写错误被静默当成 0 分。`--config` 路径不存在、JSON 无效或参数类型/取值非法时同样会直接报错。

## 推荐使用流程

1. **获取数据**：从行情 MCP、数据服务或其他可信来源获取带时间戳的行情数据。
2. **转换格式**：整理为 `schemas/market_data.schema.json` 定义的 JSON。
3. **检查质量**：按日期升序、日期不重复；行为识别建议至少 80 根日 K；回测建议至少 131 根，尽可能 500 根以上；确认成交量与成交额单位一致。
4. **运行行为识别**：得到主导标签、分数、信号与证据。
5. **运行情景模拟**：传入行为结果作为上下文，查看不同环境与策略下的收益分布。
6. **运行相似走势回测**：查看历史条件分布及样本数量。
7. **综合研判**：由上层 Agent 汇总三个引擎，输出基准、乐观、悲观情景，判断失效条件和风险控制建议。

报告中必须明确区分四类信息：

- **客观事实**：输入的 OHLCV、换手率、成交额、大盘及板块数据。
- **量化推断**：技术指标、量价信号和行为匹配评分。
- **情景模拟**：基于假设参数生成的可能路径和收益分布。
- **历史统计**：历史相似样本的后续表现，不代表未来收益保证。

## 联合研判与报告结构

上层 Agent 可参考以下初始权重进行综合研判；脚本本身不自动计算综合分，权重也应通过样本外验证调整：

| 分析模块         | 初始权重 |
| ---------------- | --------:|
| 主力行为识别证据 | 30%      |
| 情景模拟稳健性   | 25%      |
| 历史相似走势统计 | 30%      |
| 大盘及板块环境   | 15%      |

综合评分不等于上涨概率。除非使用独立、足量的样本外数据完成概率校准，否则不得把综合评分直接表述为“上涨概率”。如果三个引擎结论冲突，应分析冲突来源、降低置信度，并在报告中明确说明。

**建议报告结构**

1. **股票与行情概况**：代码、名称、数据截至时间、最新价格、涨跌幅、成交额、换手率。
2. **主力行为识别**：最高匹配标签、各标签分数、关键证据、反向证据、数据缺失情况。
3. **情景模拟结果**：当前市场环境、不同假设策略下的收益分布、主要风险。
4. **历史相似走势回测**：相似样本数量、相似度、未来 1/3/5/10 日统计。
5. **联合研判**：多引擎是否一致、核心驱动因素、置信度及其依据。
6. **今日操作计划**：持仓情况下的持有、减仓、止盈、止损或观望条件。
7. **明日操作计划**：高开、平开、低开等情景下的应对策略，以及关键价位和失效条件。
8. **最终交易决策**：买入/持有/减仓/卖出/观望，并说明理由及风险。

不要为了给出明确动作而强行生成买卖信号。预期优势不足、数据质量较差或风险收益比不合理时，应优先给出观望建议。

## A股交易约束

分析时必须考虑：

- **T+1 卖出限制**：当日买入的股票最早下一交易日才能卖出。
- **涨跌幅限制**：不同板块限制不同（主板 10%，创业板 20%；ST 股票通常 5%，但本 Skill 默认排除 ST）。
- **停牌与交易时段**：停牌、临时停牌、集合竞价和连续竞价时段都会影响可执行性。
- **流动性与成本**：个股流动性、成交容量、滑点、佣金、印花税和过户费。
- **涨跌停成交风险**：涨停或跌停时可能无法按预期价格成交。
- **时点边界**：若在交易日 14:25 左右运行，只能使用该时点真实可获得的数据；不得把尚未发生的收盘价或收盘后数据用于盘中决策。

调用方必须保证行情快照具有正确的时间边界，避免未来数据泄漏。

## 结果解读

| 可以这样理解                                         | 不要这样理解                       |
| ---------------------------------------------------- | ---------------------------------- |
| “当前量价特征与主升趋势规则的匹配度最高（65/100）。” | “主力在拉升，上涨概率是 65%。”     |
| “在震荡环境、拉升假设下，模拟收益中位数为 X%。”      | “未来一定会涨 X%。”                |
| “历史上 30 个相似样本之后 5 日的正收益比例为 60%。”  | “这次有 60% 的概率上涨。”          |
| “缺少筹码与资金流数据，相关判断已被弱化。”           | “没有这些数据也能给出确定结论。”   |
| “三个引擎结论冲突，因此降低置信度。”                 | “挑一个最乐观的结论作为最终判断。” |

## 限制与风险

- “主力行为”是对公开行情特征的规则化命名，不代表识别到了真实机构账户、订单、持仓或交易意图。
- 行为匹配分数是规则匹配程度，不应直接解释为上涨概率。
- Monte Carlo 结果依赖正态收益近似、历史波动估计和人为设定的情景偏移，不构成确定性预测。
- 历史相似样本统计不保证未来表现；应关注样本数量、市场阶段差异、相邻样本重叠和幸存者偏差。
- 回测和实盘分析必须严格使用决策时点已经可获得的数据；数据快照的时间边界由调用方负责。
- 若 `turnover_rate` 仅部分缺失，`turnover_z20` 会用截至当日、最多 60 个交易日的中位数回填后再计算滚动 z-score，不使用未来数据；但缺失比例过高时该特征区分度会下降，回测会给出覆盖率警告。
- `amount` 缺失不会被当作 0：相关滚动窗口的特征会留空，回测会提示该特征在历史候选中不可用，而不是用失真的成交额比例参与相似度。
- 当前脚本不是完整的盘口撮合或实盘交易模拟器，未覆盖涨跌停排队、跳空、停牌、交易费用和流动性冲击。
- 股票池过滤（沪深主板、创业板，排除科创板与 ST）应由上游 Agent 或行情服务完成，单股脚本不扫描全市场。
- 不得伪造行情、资金流向、筹码分布、回测样本或模型置信度；不得使用保证收益、稳赚、必涨等表述，也不得鼓励使用杠杆。
- 所有分析仅用于研究和决策辅助，不构成个性化投资建议。

## 项目结构

```text
institutional-stock-operator/
├── README.md
├── SKILL.md                     # Agent Skill 说明（中文）
├── LICENSE                      # MIT
├── requirements.txt             # numpy>=1.24,<3.0
├── sample_market_data.json      # 180 根模拟日 K
├── scripts/
│   ├── detect_institutional_behavior.py
│   ├── simulate_institutional_scenarios.py
│   └── backtest_similar_patterns.py
├── common/
│   ├── data_normalizer.py       # 校验、排序、默认值
│   ├── indicators.py            # SMA/EMA/ATR/RSI/z-score
│   ├── feature_engineering.py   # 14 维形态特征
│   ├── scoring.py               # 行为规则评分
│   └── statistics.py            # 描述统计 + Monte Carlo
├── config/
│   ├── behavior_weights.json
│   ├── scenario_config.json
│   └── backtest_config.json
└── schemas/
    ├── market_data.schema.json
    └── engine_output.schema.json
```

## 常见问题

**支持哪些股票？**

默认面向沪市、深市主板及创业板，排除科创板与 ST 股票。脚本本身不校验全市场范围，股票池过滤应由上游完成。

**行情数据从哪里来？**

项目不内置行情接口。可使用已安装的行情 MCP、数据服务或手工整理的 JSON，只要符合输入 Schema 并带有明确时间戳即可。

**为什么三个引擎的结论可能不一致？**

三者分别刻画当前形态、假设情景和历史条件分布，对不同市场阶段与数据缺失的敏感度不同。冲突本身是有用信息，应解释来源并降低置信度，而不是强行统一。

**可以直接用于实盘吗？**

不能。本项目仅用于研究与决策辅助，不执行交易，也不替代独立风控与合规判断。使用者应自行复核数据、仓位和交易约束。

**如何增加历史相似样本？**

调整 `config/backtest_config.json` 中的 `top_k`（控制保留的相似样本数），并提供更长的日 K 历史。`min_history` 决定候选样本至少要有的前置 K 线数（最低 60 根），调大它会缩小候选池；`horizons` 决定前视窗口。同时注意样本重叠会令统计置信度偏乐观。

## 许可证

本项目采用 [MIT License](LICENSE)。Copyright (c) 2026 DuXingLang.

## 免责声明

本项目及其输出仅用于研究与决策辅助，不构成投资建议、要约或收益承诺。市场有风险，使用者应自行核实数据、独立判断并承担交易结果。

<p align="right"><a href="#中文">↑ 返回顶部</a></p>

---

<a id="english"></a>

# Institutional Stock Operator Skill

> An Agent Skill for A-share single-stock research and T+1 decision support. It combines institutional-behavior detection, trading-scenario simulation, and historical-analog backtesting on public, timestamped market data to produce evidence-backed assessments.

**In one sentence**: it does not claim to know what “the main force” intends. It separates price-volume evidence, scenario assumptions, and historical analogs so you can see where a conclusion comes from and where it may fail.

> **Important**: This is a research and decision-support tool, not an automated trading system. A rule-based score is not institutional intent, a simulation is not a forecast, and historical statistics do not guarantee future returns.

## Contents

- [Overview](#overview)
- [Key capabilities](#key-capabilities)
- [Quick start](#quick-start)
- [How it works](#how-it-works)
- [Input data](#input-data)
- [Outputs](#outputs)
- [The three engines](#the-three-engines)
- [Configuration](#configuration)
- [Recommended workflow](#recommended-workflow)
- [Combined assessment and report structure](#combined-assessment-and-report-structure)
- [A-share trading constraints](#a-share-trading-constraints)
- [Reading the results](#reading-the-results)
- [Limitations and risks](#limitations-and-risks)
- [Project structure](#project-structure)
- [FAQ](#faq)
- [License](#license)
- [Disclaimer](#disclaimer)

## Overview

This Skill supports A-share single-stock research and short-term trading decisions. Given a ticker or company name, an upstream Agent obtains public, timestamped market data and runs three Python engines in sequence:

1. **Institutional-behavior detection**: maps the current price-volume structure to 9 observable labels and reports match scores, signals, and evidence.
2. **Trading-scenario simulation**: runs Monte Carlo simulations across 3 market regimes × 5 hypothetical playbooks, showing return distributions and risks under explicit assumptions.
3. **Historical-analog backtesting**: searches for similar historical patterns without using future price data in feature construction, then summarizes their performance over the next 1, 3, 5, and 10 trading days.

The upstream Agent combines the three outputs into a report covering base, bullish, and bearish scenarios, invalidation conditions, position sizing and risk controls, and an explicit wait/no-trade option.

**Design principles**

- **Evidence first**: keep observed facts, quantitative inferences, simulations, and historical statistics separate.
- **Point-in-time discipline**: use only information available at the decision timestamp to prevent look-ahead bias.
- **Explicit uncertainty**: every output carries `warnings` and documents its assumptions.
- **No-trade is valid**: when the expected edge is weak, waiting is a legitimate and often preferred conclusion.

**What it is not**

- Not an automated trading system; it does not connect to a broker or place orders.
- It does not access real institutional orders, holdings, seats, or inside information.
- It does not guarantee returns and is not personalized investment advice.
- It is not an order-book matching engine or a live-execution simulator.

## Key capabilities

| Capability                        | Description                                           | Main outputs                                                |
| --------------------------------- | ----------------------------------------------------- | ----------------------------------------------------------- |
| Data validation and normalization | Validates JSON, sorts by date, fills defaults         | Standardized market data                                    |
| Indicators and features           | SMA, EMA, ATR, RSI, rolling z-score, and more         | 14-dimensional pattern features                             |
| Institutional-behavior detection  | Transparent rule scoring across 9 behavior labels     | Leading hypothesis, scores, signals, evidence, warnings     |
| Trading-scenario simulation       | 3 regimes × 5 playbooks, 10,000 paths each by default | Return distributions, loss probabilities, risk-reward proxy |
| Historical-analog backtesting     | Standardized similarity search, 30 analogs by default | 1/3/5/10-day returns, MFE/MAE, positive rate                |
| Structured output                 | Common envelope plus `warnings` for Agent consumption | JSON result files                                           |

## Quick start

This is an Agent Skill: there is nothing to build or package, and no environment to configure.

**Install**

Hand your Agent the repository URL (or a local path) and say "install this skill". Manual installation takes two steps: copy the whole directory into your Agent's skills directory (`~/.dsh/skills/` for DeepSeek Harness), and make sure `SKILL.md` sits at its root and the directory name matches the `name` in the frontmatter.

That is all: the skill ships with sample data, and its only runtime dependency is NumPy (`python -m pip install -r requirements.txt` if the Agent environment lacks it).

**Use**

State the symbol and the question in natural language; the Agent picks the skill and runs it. Typical prompts:

| Goal | Example prompt |
|---|---|
| Read institutional behavior | Use institutional-stock-operator to analyze 600000.SH — is this accumulation or distribution? |
| Make a trading decision | Can I buy 600000.SH now? Give me the 5-day upside probability and drawdown risk. |
| Run scenarios | Assume the main force keeps marking it up tomorrow; simulate the next 5 sessions. |
| Backtest a pattern | Backtest the current pattern — how did similar setups perform over the next 1/3/5/10 days? |
| Write a review | Write a 600000.SH trading review using the skill's report structure. |

You can also name one engine only, for example "detection only, skip the scenario simulation".

**Providing the data**

The skill does not fetch quotes. Supply daily bars in any of these ways:

- Paste the JSON directly (fields in [Input data](#input-data));
- Give a local file path such as `data/stock.json`;
- Or say you want to try the bundled `sample_market_data.json` (180 simulated daily bars) first.

Detection wants at least 80 daily bars; backtesting wants 500 or more. Truncate the data to your decision time yourself — the scripts do not cut bars at `as_of`.

**Advanced: run the scripts directly**

To run them yourself or wire them into a pipeline, the three scripts are the whole entry point:

```bash
python -m pip install -r requirements.txt

python scripts/detect_institutional_behavior.py --input sample_market_data.json --output results/behavior.json --pretty
python scripts/simulate_institutional_scenarios.py --input sample_market_data.json --behavior results/behavior.json --output results/scenarios.json --pretty
python scripts/backtest_similar_patterns.py --input sample_market_data.json --output results/backtest.json --pretty
```

`--input` is required, omitting `--output` prints to standard output, and `results/` is created automatically. See `--help` for every flag and [The three engines](#the-three-engines) for engine details.

## How it works

```text
market data (JSON)
        │
        ▼
normalize + validate  (common/data_normalizer.py)
        │
        ├── ① behavior detection ──────► behavior.json
        │        └── behavior context
        ├── ② scenario simulation ─────► scenarios.json
        ├── ③ analog backtest ─────────► backtest.json
        │
        ▼
upstream Agent: combined assessment ─► research report
```

## Input data

The scripts accept UTF-8 JSON files. Minimal example:

```json
{
  "symbol": "600000.SH",
  "name": "Example Stock",
  "as_of": "2026-06-29T14:25:00+08:00",
  "daily_bars": [
    {
      "date": "2026-11-07",
      "open": 10.0,
      "high": 10.3,
      "low": 9.9,
      "close": 10.2,
      "volume": 1200000,
      "amount": 12200000,
      "turnover_rate": 1.2
    },
    {
      "date": "2026-11-10",
      "open": 10.2,
      "high": 10.45,
      "low": 10.1,
      "close": 10.38,
      "volume": 1500000,
      "amount": 15500000,
      "turnover_rate": 1.5
    }
  ],
  "market_context": {
    "market_regime": "range",
    "index_return_1d": 0.3
  },
  "sector": {
    "name": "Banks",
    "return_1d": 0.5
  },
  "capital_flow": {
    "net_inflow": 1000000
  },
  "chip": {
    "average_cost": 9.8,
    "profit_ratio": 0.65,
    "concentration_90": 0.18
  }
}
```

**Top-level fields**

| Field            | Required | Description                                                                                                                                            |
| ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `symbol`         | Yes      | Non-empty string; an exchange suffix is recommended, e.g. `600000.SH`                                                                                  |
| `daily_bars`     | Yes      | Daily bars, at least 2; the loader re-sorts them by date                                                                                               |
| `as_of`          | No       | Data cutoff as an ISO date or date-time. Defaults to the last bar date. Recorded as metadata only; the loader does not truncate bars to this timestamp |
| `name`           | No       | Stock name; non-empty string                                                                                                                           |
| `intraday_bars`  | No       | Intraday bar array; not required by any script, but missing data triggers a behavior warning                                                           |
| `market_context` | No       | Broad-market conditions (object); `market_regime` accepts `bullish`, `range`, `bearish`, and common aliases                                            |
| `sector`         | No       | Sector object, e.g. name and daily return (`return_1d`)                                                                                                |
| `capital_flow`   | No       | Capital-flow object such as `net_inflow`                                                                                                               |
| `chip`           | No       | Chip-distribution object such as `average_cost`, `profit_ratio`, `concentration_90`                                                                    |
| `metadata`       | No       | Additional source or data-quality metadata (object)                                                                                                    |

Common `market_regime` aliases are mapped as follows: `bull`, `strong`, and `普涨` mean `bullish`; `bear`, `weak`, and `普跌` mean `bearish`; `震荡` and `大跌修复` mean `range`; unrecognized values fall back to `range`.

**Daily-bar fields**

| Field                          | Required | Constraint                                                                    |
| ------------------------------ | -------- | ----------------------------------------------------------------------------- |
| `date`                         | Yes      | ISO date string in `YYYY-MM-DD` form; non-ISO or duplicate dates are rejected |
| `open`, `high`, `low`, `close` | Yes      | Numeric and greater than 0; high/low must be consistent with open/close       |
| `volume`                       | Yes      | Numeric and non-negative                                                      |
| `amount`                       | No       | Numeric or `null`                                                             |
| `turnover_rate`                | No       | Numeric or `null`; percentage-point value                                     |

**Data conventions**

- Percentage fields use percentage-point values: `1.2` means `1.2%`, not `0.012`.
- Volume and turnover amount must use consistent units within a dataset; the sample constructs amount as price × volume.
- All numbers must be finite; prices must be positive; `high >= max(open, close)` and `low <= min(open, close)`. Booleans are not accepted as numbers, and `null` is allowed only for optional fields.
- Optional object fields (`market_context`, `sector`, `capital_flow`, `chip`, `metadata`) must be JSON objects, and `intraday_bars` must be an array; a type mismatch raises an error instead of being silently ignored.
- Omit unavailable optional fields or set them to `null`; never fabricate or fill them with unverified values.
- `as_of` is metadata only; the scripts do not truncate bars to it. If the series extends past the decision time, truncate it before calling the scripts.
- See `schemas/market_data.schema.json` for the full structure and `sample_market_data.json` for a working example.

## Outputs

All three scripts emit a common envelope around their engine-specific results:

| Field               | Description                                                                                              |
| ------------------- | -------------------------------------------------------------------------------------------------------- |
| `symbol`            | Ticker                                                                                                   |
| `name`              | Stock name; `null` when the input has none, otherwise preserved in every result, including early returns |
| `as_of`             | Data cutoff timestamp; metadata only, does not truncate bars                                             |
| `generated_at`      | Generation time in UTC ISO 8601                                                                          |
| `algorithm_version` | Algorithm version, currently `1.0.0`                                                                     |
| `warnings`          | Data-quality, sample-size, and model-assumption notices                                                  |

`--output` writes a JSON file; otherwise the result goes to standard output. Engine-specific fields are described in the next section; `schemas/engine_output.schema.json` defines the five required envelope fields (`symbol`, `as_of`, `generated_at`, `algorithm_version`, `warnings`), and `name` is an optional extra field.

## The three engines

### 1. Institutional-behavior detection

Script: `scripts/detect_institutional_behavior.py`

The engine scores 9 labels using price-volume relationships, volume changes, turnover, trend structure, close location, and optional sector daily return/capital-flow data:

| Label                 | Meaning             | Typical observations                                                              |
| --------------------- | ------------------- | --------------------------------------------------------------------------------- |
| `bottom_accumulation` | Bottom accumulation | Low price zone, shrinking volume, narrow range, stable turnover, support holding  |
| `range_accumulation`  | Range accumulation  | Box range, low volume, up-day volume expansion, flat 20-day MA                    |
| `test_breakout`       | Breakout test       | Near resistance, volume expansion, strong close, sector support                   |
| `shakeout`            | Shakeout            | Volume spike and sharp drop after an advance, intraday recovery, support held     |
| `breakout_start`      | Breakout start      | Volume breakout above the 20-day high, bullish MA alignment, capital inflow       |
| `main_uptrend`        | Main uptrend        | Bullish MA alignment, positive 20-day momentum, higher highs, volume confirmation |
| `high_level_turnover` | High-level turnover | High range position, heavy volume, wide range, weak close, fading momentum        |
| `distribution`        | Distribution risk   | Weak close, volume spike, negative momentum, failed breakout, sector weakness     |
| `neutral`             | Neutral or unclear  | Signals cancel out or data is insufficient                                        |

Scores are the weighted sum of 0–1 signal values multiplied by 100, bounded to 0–100. `neutral` is the larger of its default score and “100 minus the best non-neutral score.” `leading_hypothesis` always equals the top-ranked label in `scores`, so `neutral` can be the leading hypothesis whenever every non-neutral score stays below 50. A score measures rule similarity, **not the probability that the behavior is actually occurring**, and it cannot prove that any institution is executing a particular playbook.

**Key outputs**

- `leading_hypothesis` / `leading_score`: the best-matching label and its score.
- `scores`: all label scores in descending order.
- `signals`: underlying 0–1 signal values for auditing the score.
- `key_metrics`: latest close, 1/5/20-day returns, volume ratio, ATR14, RSI14, turnover, and optional chip metrics.
- `evidence`, `interpretation`: supporting evidence and interpretation boundaries.
- `warnings`: insufficient samples, missing turnover/intraday/chip/capital-flow data, and similar notices.

### 2. Trading-scenario simulation

Script: `scripts/simulate_institutional_scenarios.py`

The engine simulates every combination of 5 hypothetical playbooks and 3 market regimes—15 groups in total. With the default 10,000 paths per group, one run produces 150,000 simulated return paths.

| Hypothetical playbook | Meaning             |
| --------------------- | ------------------- |
| `accumulation`        | Accumulation        |
| `shakeout`            | Shakeout            |
| `markup`              | Markup              |
| `high_level_turnover` | High-level turnover |
| `distribution`        | Distribution        |

| Market regime | Meaning                      |
| ------------- | ---------------------------- |
| `bullish`     | Advancing/strong environment |
| `range`       | Sideways environment         |
| `bearish`     | Declining/weak environment   |

The model estimates mean return and volatility from up to the latest 60 daily returns (all available returns when there are fewer than 60), then applies the following **explicit assumption shifts** (in ATR% units):

**Market-regime shifts**

| Market regime | Return shift |
| ------------- | ------------:|
| `bullish`     | +0.35 × ATR% |
| `range`       | 0            |
| `bearish`     | −0.45 × ATR% |

**Playbook shifts**

| Hypothetical playbook | Return shift |
| --------------------- | ------------:|
| `accumulation`        | +0.05 × ATR% |
| `shakeout`            | −0.10 × ATR% |
| `markup`              | +0.30 × ATR% |
| `high_level_turnover` | −0.10 × ATR% |
| `distribution`        | −0.35 × ATR% |

The two sets are independent and additive: scenario mean = historical mean + regime shift + playbook shift. Volatility stays at the historical estimate and is not shifted by regime or playbook. These shifts are hard-coded model assumptions, not actual institutional plans. The config file exposes only the path count, holding horizon, and random seed (see [Configuration](#configuration)). The engine uses a normal-return approximation and does not model limit-up/limit-down queues, gaps, suspensions, order-book impact, transaction costs, or stock-specific liquidity constraints.

**Key outputs**

- `base_market_regime`: the regime inferred from `market_context`.
- `historical_return_mean_pct` / `historical_return_volatility_pct`: historical daily mean and volatility estimates.
- `selected_regime_ranking`: the 5 playbooks ranked under the base regime (by simulated mean return, descending).
- `all_scenarios`: all 15 scenarios.
- `behavior_context`: the behavior label passed in, if any (report context only; it does not change the simulated distributions).
- Each scenario includes `assumed_daily_mean_pct`, `daily_volatility_pct`, `atr_pct`, `horizon_sessions`, `return_distribution`, `probability_loss`, `probability_loss_exceeds_1_atr`, and `risk_reward_proxy`.
- `return_distribution` reports sample count, mean, median, standard deviation, 10/25/75/90 percentiles, and positive rate. `probability_loss`, `probability_loss_exceeds_1_atr`, and the positive rate are fractions in 0–1, not percentages.
- `risk_reward_proxy` is `p90 / |p10|` (only when `p10 < 0`, otherwise `null`); it is a rough asymmetry reference, not a win rate or expected return.

### 3. Historical-analog backtesting

Script: `scripts/backtest_similar_patterns.py`

Main steps:

1. Build 14 pattern features from daily bars: `ret_1`, `ret_5`, `ret_20`, `ma5_gap`, `ma20_gap`, `ma60_gap`, `vol_ratio_5_20`, `amount_ratio_5_20`, `turnover_z20`, `atr_pct`, `rsi14`, `range_pos20`, `body_pct`, `close_location`.
2. Fit the median and standard deviation only on historical candidates, so neither the query nor future information leaks into normalization.
3. Measure similarity with normalized Euclidean distance, converted to a 0–1 score as `1 / (1 + RMSE)`.
4. Keep the 30 most similar historical observations by default.
5. Summarize forward returns, maximum favorable excursion (MFE), and maximum adverse excursion (MAE) over the next 1, 3, 5, and 10 trading days, including percentiles and positive rate.

A historical candidate must sit at index ≥ `max(60, min_history)` (60 bars of feature warm-up, and the default `min_history=120`); its features use only price data available at that time (missing turnover is filled from the median of at most 60 trading days up to that date, so no future information leaks in; see [Limitations and risks](#limitations-and-risks)); and it must have a complete forward window. With the defaults `min_history=120` and a 10-day maximum horizon, fewer than 131 daily bars triggers an insufficient-sample warning; 500 or more bars are preferable to enlarge the candidate pool.

**Key outputs**

- `feature_names`: the 14 feature names.
- `analog_count`: number of analogs actually used.
- `similarity_method`: description of the similarity method.
- `horizon_statistics`: grouped by `1`, `3`, `5`, and `10`, each with statistics for `forward_returns_pct`, `mfe_pct`, and `mae_pct`.
- `analogs`: date, similarity, forward returns, MFE, and MAE for each historical analog.
- `warnings`: insufficient samples, overlapping analogs, and missing cross-sectional validation, survivorship-bias correction, or transaction-cost deduction.

> If no candidate is available (the series cannot cover `max(60, min_history) + longest horizon + 1`), the backtest returns an early result with `analog_count: 0`; `feature_names`, `similarity_method`, `name`, and the full `horizon_statistics` are still present, so downstream code can parse the same structure.

## Configuration

| File                           | Purpose                                      | Configurable fields                                                                  |
| ------------------------------ | -------------------------------------------- | ------------------------------------------------------------------------------------ |
| `config/behavior_weights.json` | Signal-weight template for behavior patterns | Signal weights per label; `neutral.default`                                          |
| `config/scenario_config.json`  | Scenario-simulation parameters               | `n_paths` (default 10,000), `horizon_sessions` (default 1), `seed` (default 17)      |
| `config/backtest_config.json`  | Analog-backtest parameters                   | `top_k` (default 30), `min_history` (default 120), `horizons` (default `[1,3,5,10]`) |

**Note**: the scripts do not read files under `config/` automatically. Pass them explicitly with `--weights` or `--config`; otherwise built-in defaults are used.

```bash
python scripts/detect_institutional_behavior.py \
  --input data/stock.json \
  --weights config/behavior_weights.json \
  --output results/behavior.json

python scripts/simulate_institutional_scenarios.py \
  --input data/stock.json \
  --config config/scenario_config.json \
  --output results/scenarios.json

python scripts/backtest_similar_patterns.py \
  --input data/stock.json \
  --config config/backtest_config.json \
  --output results/backtest.json
```

> If the file passed to `--weights` does not exist, the script prints a notice to standard error and falls back to the built-in default weights. Unknown labels, unknown signal keys, or non-numeric weights in a weights file raise an error, so a typo is never silently scored as zero. A missing or invalid `--config` file, or a config value of the wrong type or range, also raises an error.

## Recommended workflow

1. **Retrieve data**: obtain timestamped market data from a market-data MCP, data service, or another trusted source.
2. **Convert**: format it as `schemas/market_data.schema.json`.
3. **Check quality**: ascending, unique dates; at least 80 daily bars for behavior detection, at least 131 for backtesting, and preferably 500+; verify consistent volume/amount units.
4. **Run behavior detection**: obtain the leading label, scores, signals, and evidence.
5. **Run scenario simulation**: pass the behavior output as context and review return distributions across regimes and playbooks.
6. **Run analog backtesting**: review the historical conditional distribution and sample size.
7. **Synthesize**: let the upstream Agent combine the three engines into base, bullish, and bearish scenarios, invalidation conditions, and risk controls.

Reports must clearly distinguish four information types:

- **Observed facts**: supplied OHLCV, turnover, amount, market, and sector data.
- **Quantitative inferences**: technical indicators, price-volume signals, and behavior-match scores.
- **Simulations**: possible paths and return distributions under explicit assumptions.
- **Historical statistics**: subsequent performance of similar historical observations; not a promise of future returns.

## Combined assessment and report structure

An upstream Agent may use the following initial weights for its combined assessment. The scripts do not compute a composite score automatically, and the weights should be tuned through out-of-sample validation:

| Module                         | Initial weight |
| ------------------------------ | --------------:|
| Behavior-detection evidence    | 30%            |
| Scenario-simulation robustness | 25%            |
| Historical-analog statistics   | 30%            |
| Market and sector environment  | 15%            |

A composite score is not an upside probability. Unless it has been calibrated on an independent, sufficiently large out-of-sample dataset, do not present it as a “probability of rising.” If the three engines disagree, analyze the source of the conflict, lower confidence, and state the disagreement explicitly.

**Suggested report structure**

1. **Stock and market snapshot**: ticker, name, data cutoff, latest price, change, amount, turnover.
2. **Behavior detection**: best-matching label, all scores, supporting evidence, counter-evidence, missing data.
3. **Scenario simulation**: current regime, return distributions under each hypothetical playbook, main risks.
4. **Analog backtest**: number of analogs, similarity, 1/3/5/10-day statistics.
5. **Combined assessment**: whether the engines agree, key drivers, confidence and its basis.
6. **Today's plan**: hold, trim, take profit, stop loss, or wait conditions for an existing position.
7. **Tomorrow's plan**: responses to gap-up, flat, and gap-down opens, plus key levels and invalidation conditions.
8. **Final decision**: buy/hold/trim/sell/wait, with rationale and risks.

Do not force a buy or sell signal just to provide an action. When the expected edge is weak, data quality is poor, or risk-reward is unattractive, a wait recommendation should take priority.

## A-share trading constraints

Analysis must account for:

- **T+1 selling restriction**: shares bought today cannot be sold until the next trading day.
- **Price limits**: limits vary by board (10% on the main boards, 20% on ChiNext; ST stocks are typically 5%, but this Skill excludes ST by default).
- **Suspensions and sessions**: suspensions, temporary halts, call auctions, and continuous trading all affect executability.
- **Liquidity and costs**: stock-specific liquidity, capacity, slippage, commissions, stamp duty, and transfer fees.
- **Limit-up/limit-down fill risk**: orders may not fill at the expected price when the stock is locked at a limit.
- **Timestamp boundary**: if the analysis runs around 14:25 on a trading day, use only data genuinely available at that time. Never use close or post-close data for intraday decisions.

The caller must guarantee correct timestamp boundaries in the market-data snapshot to prevent look-ahead leakage.

## Reading the results

| Reasonable interpretation                                                          | Incorrect interpretation                                            |
| ---------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| “Current price-volume features best match the main-uptrend rules (65/100).”        | “Institutions are marking it up; the probability of rising is 65%.” |
| “Under the range regime and markup assumption, the simulated median return is X%.” | “It will definitely rise X%.”                                       |
| “60% of 30 similar historical analogs had positive 5-day forward returns.”         | “There is a 60% chance it rises this time.”                         |
| “Chip and capital-flow data are missing, so related signals are weakened.”         | “A definitive conclusion is possible without that data.”            |
| “The engines disagree, so confidence is reduced.”                                  | “Pick the most optimistic conclusion as the final call.”            |

## Limitations and risks

- “Institutional behavior” is a rule-based label for public-market patterns. It does not identify actual institutional accounts, orders, holdings, or intent.
- Behavior-match scores measure rule similarity and must not be presented as probabilities of a price increase.
- Monte Carlo results depend on a normal-return approximation, historical volatility estimates, and human-set scenario shifts; they are not deterministic forecasts.
- Historical analogs do not guarantee future performance. Consider sample size, regime changes, overlapping observations, and survivorship bias.
- Backtests and live analysis must use only information available at the decision timestamp; the caller owns the snapshot's time boundary.
- If `turnover_rate` is only partially missing, `turnover_z20` fills the gaps with the median of at most 60 trading days up to that date before the rolling z-score, so no future information is used; a high missing ratio still reduces the feature's discriminative power, and the backtest reports a coverage warning.
- Missing `amount` is never treated as zero: features over the affected rolling windows stay empty, and the backtest reports that the feature is unavailable across historical candidates instead of using a distorted amount ratio.
- These scripts are not a full order-book matching engine or live-execution simulator. They do not model limit queues, gaps, suspensions, transaction costs, or liquidity impact.
- Universe filtering (Shanghai/Shenzhen main boards and ChiNext, excluding STAR Market and ST stocks) belongs to the upstream Agent or data service; the single-stock scripts do not scan the market.
- Never fabricate market data, capital flows, chip distributions, backtest samples, or model confidence. Do not use guaranteed-return language or encourage leverage.
- All analysis is for research and decision support only and is not personalized investment advice.

## Project structure

```text
institutional-stock-operator/
├── README.md
├── SKILL.md                     # Agent Skill documentation (Chinese)
├── LICENSE                      # MIT
├── requirements.txt             # numpy>=1.24,<3.0
├── sample_market_data.json      # 180 simulated daily bars
├── scripts/
│   ├── detect_institutional_behavior.py
│   ├── simulate_institutional_scenarios.py
│   └── backtest_similar_patterns.py
├── common/
│   ├── data_normalizer.py       # validation, sorting, defaults
│   ├── indicators.py            # SMA/EMA/ATR/RSI/z-score
│   ├── feature_engineering.py   # 14 pattern features
│   ├── scoring.py               # behavior rule scoring
│   └── statistics.py            # descriptive statistics + Monte Carlo
├── config/
│   ├── behavior_weights.json
│   ├── scenario_config.json
│   └── backtest_config.json
└── schemas/
    ├── market_data.schema.json
    └── engine_output.schema.json
```

## FAQ

**Which stocks are supported?**

By default: Shanghai and Shenzhen main boards plus ChiNext, excluding STAR Market and ST stocks. The scripts do not validate the universe; upstream filtering is required.

**Where does the market data come from?**

The project ships no market-data feed. Use an installed market-data MCP, a data service, or manually prepared JSON that matches the input schema and carries explicit timestamps.

**Why might the three engines disagree?**

They describe current structure, hypothetical scenarios, and historical conditional distributions respectively, and they react differently to regime changes and missing data. Disagreement is useful information: explain it and lower confidence rather than forcing agreement.

**Can this be used for live trading?**

No. It is for research and decision support only. It does not execute trades and does not replace independent risk management or compliance review. Verify data, position sizing, and trading constraints yourself.

**How can I get more historical analogs?**

Increase `top_k` in `config/backtest_config.json` (it controls how many analogs are kept) and provide a longer daily history. `min_history` sets the minimum number of preceding bars a candidate must have (at least 60); raising it shrinks the candidate pool, while `horizons` controls the forward windows. Remember that overlapping analogs make the statistics look more confident than they are.

## License

Released under the [MIT License](LICENSE). Copyright (c) 2026 DuXingLang.

## Disclaimer

This project and its outputs are for research and decision support only. They are not investment advice, an offer, or a guarantee of returns. Markets carry risk; users must verify data, make independent judgments, and bear the consequences of their trades.

<p align="right"><a href="#english">↑ Back to top</a></p>