# 双色球 & 大乐透量化分析预测系统

本地 Python CLI + FastAPI + Electron 桌面端：拉取历史开奖、量化走势、约束预测、滚动回测。

**声明：开奖近似独立随机。本系统仅用于统计研究与娱乐，不承诺提高中奖率，不构成投注建议。**

## 功能

| 能力 | 说明 |
|------|------|
| CLI | `update` / `show` / `analyze` / `predict` / `backtest` |
| FastAPI | 本地 JSON API + Swagger `/docs` |
| Desktop | Vue3 + TS + Electron 可视化工作台 |

彩种：双色球 `ssq`（6+1）、大乐透 `dlt`（5+2）。

## 安装

```bash
cd lottery
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .

cd desktop
npm install
```

## CLI

```bash
python -m lottery update --game all
python -m lottery analyze --game ssq --window 50
python -m lottery predict --game ssq -n 2
python -m lottery backtest --game ssq --window 30 -n 5 --periods 50
```

## FastAPI

```bash
source .venv/bin/activate
python -m lottery.api --host 127.0.0.1 --port 8765
# 浏览器打开 http://127.0.0.1:8765/docs
```

主要接口：`GET /health`、`GET /draws`、`POST /update`、`GET /analyze`、`POST /predict`、`POST /backtest`。

## 桌面端

若 Electron 二进制下载较慢，可使用镜像：

```bash
cd desktop
ELECTRON_MIRROR="https://npmmirror.com/mirrors/electron/" npm install --registry=https://registry.npmmirror.com
npm run dev
```

打包并安装到「应用程序」：

```bash
cd desktop
npm run install:local
# 产物：release/mac-arm64/LQ Terminal.app
# 同时安装到：/Applications/LQ Terminal.app
# 也可打开：release/*.dmg
```

Electron 启动时会检测 `127.0.0.1:8765`；若未运行则尝试用仓库 `.venv` 拉起 API。  
打包后可通过环境变量指定仓库：`LOTTERY_ROOT`、`LOTTERY_PYTHON`。

## OpenSpec

本仓库使用 OpenSpec 做变更管理，当前变更：`openspec/changes/desktop-fastapi-vue-electron/`。

## 目录

```
lottery/           # Python 包（CLI / analysis / api）
desktop/           # Electron + Vue3 + TS
data/              # 本地开奖 CSV
openspec/          # 规格与变更
```
