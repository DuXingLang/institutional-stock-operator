---
name: institutional-stock-operator
description: |
  分析单只A股个股的主力行为，给出T+1交易研判：依次调用三个本地脚本完成主力行为识别（9 类量价模式）、操盘情景模拟（5 种假设策略 × 3 种市场环境）、历史相似走势回测，输出带证据、分歧与失效条件的研判报告。
  当用户点名某只A股个股，询问主力/机构在做什么、该不该买/持有/减仓，要求一份交易研判或复盘报告，或希望做情景模拟、历史相似走势回测时使用。

  Use when the user names an A-share stock and asks what 主力/机构 is doing, whether to buy, hold or reduce, or wants 交易研判/复盘/情景模拟/相似走势回测 — e.g. 「分析一下 600000.SH」「主力在吸筹还是出货」「现在能不能买」「做个情景模拟」「从主力的角度分析一下这只股票」「预测一下这只股票」. Also use when asked to run institutional-behavior detection, Monte-Carlo scenario simulation, or historical analog backtesting on OHLCV daily bars.

  Scope: single stock on 沪深主板与创业板（不含科创板与 ST）。Requires a supplied daily-bar JSON (≥80 bars for detection, ~500 for backtesting); does not fetch quotes, scan or rank the market, or place orders — pair it with a market-data MCP/Skill upstream. Output is a research aid, not investment advice.
license: MIT
version: 1.1.0
metadata:
  author: DuXingLang
  language: zh-CN
  tags:
    - a-share
    - institutional-behavior
    - monte-carlo
    - backtesting
    - trading-assistant
  requires:
    python: ">=3.10"
    packages:
      - numpy
---

# 机构主力操盘分析 Skill

## 一、用途与定位

当用户提供A股股票名称或代码时，使用公开、带时间戳的市场数据进行分析。

**何时使用**：用户点名某只A股个股，询问主力/机构在做什么、该不该买/持有/减仓，要求一份交易研判或复盘报告，或希望做情景模拟、历史相似走势回测。

**何时不使用**：需要获取实时行情、全市场选股扫描、组合管理或下单执行，或要求保证收益、承诺具体买卖点位时，本 Skill 不适用；行情获取与候选池过滤应由上游行情 MCP/Skill 完成。

本 Skill 可以采用“假设自己已经持有该股票的机构主力”的分析视角，推演不同市场环境下可能采取的策略，但不得声称能够获取真实机构订单、机构私有持仓、内幕信息或真实操盘意图。

本 Skill 中的三个 Python 脚本属于量化研究与交易决策辅助工具，不构成自动交易系统，也不保证收益。

## 二、支持的股票范围

默认适用范围为沪市、深市主板及创业板股票。

构建股票候选池时，应排除科创板股票和 ST 股票。单只股票分析脚本本身不负责验证整个市场的股票范围，调用本 Skill 的 Agent 或行情数据服务应在候选池阶段完成这些过滤。

## 三、标准执行流程

1. 调用已安装的股票行情 MCP / Skill，获取最新可用行情和历史日 K 线数据。
2. 将行情数据转换为统一格式，符合 `schemas/market_data.schema.json`。
3. 主力行为识别建议至少提供 80 根日 K 线；历史相似走势回测建议尽可能提供 500 根或更多日 K 线。K 线数据应按时间升序排列，数据标准化模块会再次排序。
4. 调用 `scripts/detect_institutional_behavior.py`，识别当前行情对应的行为模式。
5. 将行为识别结果和行情数据传入 `scripts/simulate_institutional_scenarios.py`，进行不同市场环境及假设策略下的情景模拟。
6. 调用 `scripts/backtest_similar_patterns.py`，检索历史相似走势并统计后续表现。
7. 综合三个引擎的输出，形成分析结论。必须区分以下信息类型：
   - **客观事实**：输入的 OHLCV、换手率、成交额、大盘及板块数据。
   - **量化推断**：行为匹配评分、技术指标和量价信号。
   - **情景模拟**：基于假设参数生成的未来收益路径和条件分布。
   - **历史统计**：历史相似样本的后续表现，不代表未来收益保证。
8. 输出简明的交易研判报告，至少包括基准情景、乐观情景、悲观情景、判断失效条件、仓位与风险控制建议，以及明确的观望/不交易选项。

## 四、行情数据格式

输入为 UTF-8 编码的 JSON 文件，示例：

```json
{
  "symbol": "600000.SH",
  "name": "示例股票",
  "as_of": "2026-11-10T14:25:00+08:00",
  "daily_bars": [
    {
      "date": "2026-11-10",
      "open": 10.0,
      "high": 10.3,
      "low": 9.9,
      "close": 10.2,
      "volume": 1200000,
      "amount": 12200000,
      "turnover_rate": 1.2
    }
  ],
  "intraday_bars": [],
  "market_context": {
    "index_return_1d": 0.3,
    "advance_decline_ratio": 1.1,
    "market_regime": "range"
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

字段说明：

- `symbol`：股票代码，非空字符串，建议包含交易所后缀，例如 `600000.SH`。
- `name`：股票名称，可选，提供时必须是字符串。
- `as_of`：行情数据截至时间，建议使用带时区的 ISO 8601 时间；仅作元数据，脚本不会据此截断 K 线。
- `daily_bars`：历史日 K 线，必填；每根 K 线的 `date` 必须是 `YYYY-MM-DD` 形式的 ISO 日期。
- `intraday_bars`：分钟 K 线数组，可选。
- `market_context`：大盘环境对象，可选。
- `sector`：所属板块对象，可选；引擎只读取 `return_1d`（板块当日收益）。
- `capital_flow`：资金流向对象，可选。
- `chip`：筹码分布对象，可选。
- `metadata`：其他元数据，可选。

收益率、换手率等百分比字段统一使用“百分数数值”，例如 `1.2` 表示 1.2%，而不是 `0.012`。成交量和成交额在同一数据集中必须使用一致的单位。可选字段缺失时应直接省略，不得伪造或填入未经证实的数据。

输入校验较为严格：`null` 只能用于可选字段，布尔值不会被当作数值，`NaN`/`Infinity` 会被拒绝，`market_context`、`sector`、`capital_flow`、`chip` 等可选对象字段必须是 JSON 对象；类型不符时脚本直接报错，而不是静默忽略。

`intraday_bars` 可以包含 `timestamp`、`open`、`high`、`low`、`close`、`volume`、`amount` 等字段。三个脚本均不强制要求分钟线。

## 五、脚本调用方式

在项目根目录下执行：

```bash
# 1. 主力行为识别
python scripts/detect_institutional_behavior.py \
  --input data/stock.json \
  --output results/behavior.json

# 2. 主力操盘情景模拟
python scripts/simulate_institutional_scenarios.py \
  --input data/stock.json \
  --behavior results/behavior.json \
  --output results/scenarios.json

# 3. 历史相似走势回测
python scripts/backtest_similar_patterns.py \
  --input data/stock.json \
  --output results/backtest.json
```

每个脚本均支持 `--pretty` 参数，用于格式化输出 JSON。

配置文件不会自动加载，需要显式传入：行为识别用 `--weights config/behavior_weights.json`，情景模拟与回测用 `--config config/scenario_config.json`、`--config config/backtest_config.json`；不传时使用内置默认值。权重文件不存在时脚本会在标准错误输出提示并回退默认权重，但权重文件内的未知标签、未知信号键或非数值权重会直接报错；配置文件中的 `n_paths`、`horizon_sessions`、`top_k`、`min_history`、`horizons` 等参数会校验类型与取值范围，非法时直接报错。

脚本发生输入校验错误或运行错误时会返回非零退出码。输出结果包含 `symbol`、`as_of`、`generated_at`、`algorithm_version`、`warnings` 等基础字段，以及各引擎自己的分析结果。`leading_hypothesis` 始终等于 `scores` 中排第一的标签。

## 六、三个核心引擎的说明

### 6.1 主力行为识别引擎

脚本：`scripts/detect_institutional_behavior.py`

识别以下九类可观察行情模式：

- `bottom_accumulation`：底部吸筹特征
- `range_accumulation`：区间吸筹特征
- `test_breakout`：试盘/测试突破特征
- `shakeout`：洗盘/震仓特征
- `breakout_start`：启动突破特征
- `main_uptrend`：主升趋势特征
- `high_level_turnover`：高位换手特征
- `distribution`：派发/出货风险特征
- `neutral`：中性或特征不明显

引擎根据量价关系、成交量变化、换手率、趋势结构、收盘位置及可用的板块当日收益、资金数据、筹码数据进行规则评分。`leading_hypothesis` 始终等于 `scores` 中排第一的标签；当所有非中性分数都低于 50 时，`neutral` 可能成为领先假设。换手率仅部分缺失时会用截至当日的历史中位数回填并给出警告，最近 20 根全缺失时换手率相关信号按中性处理。

输出分数代表当前行情与某类模式的匹配程度，不是该行为真实发生的概率，更不能证明某个机构正在执行对应操作。分析报告应结合证据、反向证据和数据缺失情况进行解释。

### 6.2 主力操盘情景模拟引擎

脚本：`scripts/simulate_institutional_scenarios.py`

对以下五类假设策略进行模拟：

- `accumulation`：吸筹
- `shakeout`：洗盘
- `markup`：拉升
- `high_level_turnover`：高位换手
- `distribution`：派发

同时考虑三种市场环境：

- `bullish`：上涨/强势环境
- `range`：震荡环境
- `bearish`：下跌/弱势环境

引擎使用历史收益率、波动率、ATR 等数据，结合可配置的情景偏移参数进行 Monte Carlo 随机模拟。输出收益分布、亏损比例、超过一个 ATR 的不利波动比例及风险收益参考指标。

这些情景偏移属于模型假设，不是实际机构操盘计划。当前模型不是盘口级撮合模拟器，无法预知未来新闻、跳空、涨跌停排队、停牌或真实市场冲击。

### 6.3 历史相似走势回测引擎

脚本：`scripts/backtest_similar_patterns.py`

主要步骤：

1. 从日 K 线构建价格、成交量、均线偏离、波动率、RSI、区间位置等特征。
2. 对历史候选样本的特征进行标准化。
3. 使用标准化欧氏距离计算当前形态与历史形态的相似度。
4. 选取相似度较高的历史样本。
5. 统计历史样本之后 1、3、5、10 个交易日的收益率、正收益比例、最大有利波动（MFE）和最大不利波动（MAE）。

历史候选样本必须位于当前观察日期之前，候选索引不早于 60（特征预热）且不早于 `min_history`（默认 120），特征计算不得使用该历史样本之后的数据；换手率缺失时按截至该日、最多 60 个交易日的中位数回填，避免未来信息进入特征。历史前视收益只作为回测统计标签使用。

历史相似样本统计仅用于描述历史条件分布。相邻样本可能存在重叠，市场环境也可能发生变化，因此统计结果仍可能存在偏差。

## 七、三个引擎的联合决策

建议初始综合权重如下，可在后续通过样本外验证调整：

| 分析模块         | 初始权重 |
| ---------------- | --------:|
| 主力行为识别证据 | 30%      |
| 情景模拟稳健性   | 25%      |
| 历史相似走势统计 | 30%      |
| 大盘及板块环境   | 15%      |

综合评分不等于上涨概率。除非使用独立、足量的样本外数据完成概率校准，否则不得将综合评分直接表述为“上涨概率”。

如果三个引擎的结论相互冲突，应分析冲突来源、降低结论置信度，并在报告中明确说明。

## 八、交易研判报告建议结构

每次分析建议按以下结构输出：

1. **股票与行情概况**：股票代码、名称、数据截至时间、最新价格、涨跌幅、成交额、换手率。
2. **主力行为识别**：最高匹配模式、各模式分数、关键证据、反向证据、数据缺失情况。
3. **情景模拟结果**：当前市场环境、不同假设策略下的收益分布、主要风险。
4. **历史相似走势回测**：相似样本数量、相似度、未来 1/3/5/10 日统计。
5. **联合研判**：多引擎是否一致、核心驱动因素、置信度及其依据。
6. **今日操作计划**：持仓情况下的持有、减仓、止盈、止损或观望条件。
7. **明日操作计划**：高开、平开、低开等情景下的应对策略，以及关键价位和失效条件。
8. **最终交易决策**：买入/持有/减仓/卖出/观望，并说明理由及风险。

不要为了给出明确动作而强行生成买卖信号。当预期优势不足、数据质量较差或风险收益比不合理时，应优先给出观望建议。

## 九、A股 T+1 交易约束

分析时必须考虑：

- A 股 T+1 卖出限制；
- 不同板块适用的涨跌幅限制；
- 停牌、临时停牌及交易时段；
- 个股流动性、成交容量、滑点和交易费用；
- 涨停/跌停时可能无法按预期成交的风险。

如果策略在交易日 14:25 左右运行，只能使用该时点真实可获得的数据。不得将尚未发生的收盘价或收盘后数据用于盘中决策。调用方必须保证行情快照具有正确的时间边界，避免未来数据泄漏。

## 十、风险控制与使用边界

- 不得伪造行情、资金流向、筹码分布、回测样本或模型置信度。
- 不得把模式匹配分数描述为对“主力”真实意图的确认。
- 必须标注行情数据时间、缺失字段、历史样本数量和模型局限。
- 必须提供判断失效条件；预期优势不足时允许且应当建议不交易。
- 不得使用保证收益、稳赚、必涨等表述，也不得鼓励使用杠杆。
- 所有分析仅用于研究和决策辅助，不构成个性化投资建议。
