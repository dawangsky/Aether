## Why

当前双色球/大乐透量化系统只有 CLI 终端输出，不方便查看走势、冷热遗漏与回测对比。需要一套本地桌面可视化，并借此引入 FastAPI 作为结构化 API，便于前后端联调与后续扩展。

## What Changes

- 新增本地 **FastAPI** 服务，将现有 `analyze` / `predict` / `backtest` / `update` / `show` 能力以 JSON API 暴露
- 新增 **Vue3 + TypeScript + Electron** 桌面端，提供开奖列表、走势分析、推荐预测、回测对比页面
- Electron 主进程负责拉起/守护本地 FastAPI，渲染进程通过 HTTP 调用
- 保留现有 CLI 不变，API 复用同一套 Python 分析/预测/回测模块
- 页面与文档中持续标明：开奖随机，仅供研究娱乐，不构成投注建议

## Capabilities

### New Capabilities

- `lottery-api`：本地 FastAPI 服务端点、请求/响应契约、健康检查与错误模型
- `desktop-shell`：Electron + Vue3 + TS 桌面壳、窗口启动、本地 API 生命周期
- `analysis-ui`：开奖列表与量化分析可视化（冷热、遗漏、形态摘要）
- `predict-ui`：推荐注生成与形态摘要展示
- `backtest-ui`：滚动回测结果与随机基线对比展示

### Modified Capabilities

- （无；仓库尚无既有 `openspec/specs/`）

## Impact

- Python：新增 `fastapi`/`uvicorn` 依赖与 `lottery/api` 包；`requirements.txt` / `pyproject.toml` 更新
- 前端：新建 `desktop/`（或 `apps/desktop`）Electron + Vite + Vue3 + TS 工程
- 数据：继续使用本地 `data/ssq.csv`、`data/dlt.csv`，API 可触发增量更新
- 不改变 CLI 对外命令语义；不引入账号体系与云端部署
