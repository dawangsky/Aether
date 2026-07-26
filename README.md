# 双色球 & 大乐透量化分析预测系统

本地 Python CLI：拉取历史开奖、量化走势（冷热/遗漏/形态）、约束加权生成推荐注，并做滚动回测对比随机基线。

**声明：开奖近似独立随机。本系统仅用于统计研究与娱乐，不承诺提高中奖率，不构成投注建议。**

## 功能

| 命令 | 说明 |
|------|------|
| `update` | 从福彩官网/体彩网关增量拉取历史数据到本地 CSV |
| `show` | 查看最近开奖 |
| `analyze` | 冷热、遗漏分层、奇偶/大小/三区/和值等报表 |
| `predict` | 按走势约束生成 N 注单式 |
| `backtest` | 滚动回测，对比纯随机基线 |

支持彩种：

- 双色球 `ssq`：红 6/33 + 蓝 1/16
- 大乐透 `dlt`：前区 5/35 + 后区 2/12

## 安装

```bash
cd lottery
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## 用法

```bash
# 拉取双色球 + 大乐透历史（默认各约 120 期）
python -m lottery update --game all

# 查看最近开奖
python -m lottery show --game ssq --limit 10
python -m lottery show --game dlt --limit 10

# 量化分析
python -m lottery analyze --game ssq --window 50
python -m lottery analyze --game dlt --window 50

# 生成推荐（默认 2 注）
python -m lottery predict --game ssq -n 2
python -m lottery predict --game dlt -n 2 --seed 7

# 回测
python -m lottery backtest --game ssq --window 30 -n 5 --periods 50
```

安装 editable 后也可直接用：

```bash
lottery predict --game ssq -n 2
```

## 数据

- 本地文件：`data/ssq.csv`、`data/dlt.csv`
- 双色球：中国福利彩票官网公开接口
- 大乐透：体育彩票网关历史接口

首次执行 `analyze` / `predict` / `show` 时，若本地数据不足会自动尝试拉取。

## 预测逻辑（简述）

1. 统计近窗频次与当前遗漏，热号加权，过冷号给予回补加权  
2. 根据上期形态偏斜设定约束（和值回中枢、空区回补、奇偶/大小、遗漏分层出号个数、连号组数）  
3. 在约束内加权采样生成单式；过严时自动放宽重试  
4. 回测将策略与同等注数的纯随机对比，避免过度解读

## 目录

```
lottery/
  cli.py
  config.py
  models.py
  data/        # CSV 读写 + 拉取
  analysis/    # 冷热遗漏形态报表
  predict/     # 约束与生成
  backtest/    # 滚动回测
data/          # 本地开奖库
```
