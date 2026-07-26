## ADDED Requirements

### Requirement: Electron 桌面壳
系统 SHALL 提供基于 Electron + Vue3 + TypeScript 的桌面应用工程，可在开发模式启动窗口加载前端。

#### Scenario: 开发模式启动
- **WHEN** 开发者按 README 启动桌面端
- **THEN** 出现应用窗口且能加载主界面路由

### Requirement: 本地 API 生命周期
Electron 主进程 SHALL 在应用启动时尝试拉起本地 FastAPI，并在应用退出时终止该子进程。

#### Scenario: API 就绪后前端可用
- **WHEN** FastAPI 健康检查变为成功
- **THEN** 前端解除「服务未就绪」阻塞并允许发起业务请求

#### Scenario: 启动失败可见
- **WHEN** Python/API 启动失败
- **THEN** UI 展示明确错误信息（含可能的 Python 路径问题提示）

### Requirement: 安全默认
渲染进程 SHALL 启用 contextIsolation，且不得直接开启 nodeIntegration；与主进程通信仅通过预加载暴露的有限 API。

#### Scenario: 预加载桥接
- **WHEN** 渲染进程需要获知 API Base URL
- **THEN** 通过 preload 暴露的方法读取，而非直接访问 Node API
