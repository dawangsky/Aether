## 1. FastAPI 后端

- [x] 1.1 添加 fastapi/uvicorn 依赖到 requirements.txt 与 pyproject.toml
- [x] 1.2 实现 Pydantic schemas 与 `lottery/api` 应用工厂
- [x] 1.3 实现路由：health、draws、update、analyze、predict、backtest
- [x] 1.4 增加 `python -m lottery.api` 启动入口并本地冒烟验证 `/docs`

## 2. Electron + Vue3 桌面壳

- [x] 2.1 初始化 `desktop/`（Vite + Vue3 + TS + Electron）
- [x] 2.2 主进程 spawn/守护 FastAPI，preload 暴露 API baseURL
- [x] 2.3 路由与布局：开奖 / 分析 / 预测 / 回测

## 3. 业务页面

- [x] 3.1 开奖列表页对接 `GET /draws`，支持 ssq/dlt 切换
- [x] 3.2 分析页对接 `GET /analyze`，展示冷热/遗漏/分层与免责声明
- [x] 3.3 预测页对接 `POST /predict`，展示推荐注与形态摘要
- [x] 3.4 回测页对接 `POST /backtest`，展示策略 vs 随机对比

## 4. 文档与验收

- [x] 4.1 更新根 README：API 与桌面端启动说明
- [x] 4.2 端到端冒烟：API + 桌面开发模式关键流程可跑通
