## Context

仓库已有 Python CLI 量化系统（双色球/大乐透）：本地 CSV、官方源拉取、冷热/遗漏/形态分析、约束预测、滚动回测。用户需要桌面可视化，并选定 **FastAPI + Vue3 + TS + Electron**。当前无 Web/UI 层。

约束：单机本地使用；复用现有分析引擎；CLI 保持可用；中文界面与 OpenSpec 文档。

## Goals / Non-Goals

**Goals:**

- 本地 FastAPI 暴露结构化 JSON API（健康检查、更新、开奖列表、分析、预测、回测）
- Electron 应用启动时拉起 API，退出时尽量清理子进程
- Vue3 页面覆盖：开奖、分析、预测、回测
- 自动生成 OpenAPI（`/docs`）便于熟悉 FastAPI

**Non-Goals:**

- 云端部署、多用户鉴权、付费/投注下单
- 声称提高中奖率或实盘购彩对接
- 第一期不做复杂 ECharts 定制动画（可用简洁表格 + 基础图表）
- 不替换 CLI

## Decisions

1. **API 进程模型**  
   - 选择：Electron 主进程 `spawn` 本机 Python（优先 `.venv/bin/python -m lottery.api`），默认 `127.0.0.1:8765`。  
   - 备选：纯 CLI 每次 spawn → 否决（交互频繁）。  
   - 备选：打包进 Electron 二进制 → 第一期不做，开发期依赖本机 venv。

2. **FastAPI 模块布局**  
   - `lottery/api/app.py` 创建应用；`lottery/api/schemas.py` Pydantic 模型；`lottery/api/routes/*.py` 路由。  
   - 业务仍调用 `lottery.analysis` / `lottery.predict` / `lottery.backtest` / `lottery.data`，避免复制逻辑。

3. **前端工程位置**  
   - `desktop/`：Vite + Vue3 + TS + electron-vite（或 electron + vite 分离）。  
   - UI：轻量自研布局 + 少量组件，图表可用 ECharts；避免过重 UI 套件除非必要。

4. **CORS**  
   - 开发期允许 `localhost` 渲染源；生产加载 `file://` 或自定义协议时同源/本地回环即可。

5. **同步路由优先**  
   - 分析/回测为 CPU 密集，第一期用同步 `def` 即可；不强制全面 async。

## Risks / Trade-offs

- [Python 路径/venv 找不到] → 设置页或环境变量 `LOTTERY_PYTHON`；启动失败在 UI 明确报错  
- [端口占用] → 尝试 8765，失败则探测下一端口并写回 preload 配置  
- [策略与随机接近被误解为「无效系统」] → UI 固定免责声明 + 回测页强调基线对比含义  
- [Electron 安全] → `contextIsolation: true`，仅暴露有限 IPC；不开启 `nodeIntegration`

## Migration Plan

1. 安装 Python 新依赖并验证 `uvicorn lottery.api.app:app`  
2. 新建 `desktop/`，开发模式：先起 API，再起 Electron  
3. README 增加桌面端启动说明  
4. 回滚：删除/忽略 `desktop/` 与 `lottery/api` 不影响 CLI

## Open Questions

- 第一期图表库最终用 ECharts 还是 Chart.js（实现时默认 ECharts）  
- 是否需要「设置」页配置端口/Python 路径（实现时做最小设置：端口只读展示 + 重新连接）
