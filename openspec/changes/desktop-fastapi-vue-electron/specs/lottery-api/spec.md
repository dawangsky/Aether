## ADDED Requirements

### Requirement: 本地 FastAPI 服务可启动
系统 SHALL 提供可通过 `python -m lottery.api` 或 uvicorn 启动的本地 HTTP 服务，默认监听 `127.0.0.1:8765`。

#### Scenario: 健康检查成功
- **WHEN** 客户端请求 `GET /health`
- **THEN** 返回 200 且 JSON 包含 `status=ok` 与版本信息

### Requirement: 开奖数据查询与更新 API
系统 SHALL 提供开奖列表查询与增量更新接口，彩种参数支持 `ssq` 与 `dlt`。

#### Scenario: 查询最近开奖
- **WHEN** 客户端请求 `GET /draws?game=ssq&limit=10`
- **THEN** 返回按期号升序或约定顺序的开奖数组，每项含 `issue`、`date`、`main`、`special`

#### Scenario: 触发数据更新
- **WHEN** 客户端请求 `POST /update` 且 body 含 `game`（或 `all`）
- **THEN** 系统拉取并合并本地 CSV，返回总期数与新增期数

### Requirement: 分析、预测、回测 API
系统 SHALL 将既有量化能力以 JSON API 暴露。

#### Scenario: 分析接口
- **WHEN** 客户端请求 `GET /analyze?game=ssq&window=50`
- **THEN** 返回冷热、遗漏、遗漏分层与上期形态摘要等结构化字段

#### Scenario: 预测接口
- **WHEN** 客户端请求 `POST /predict` 含 `game`、`n`、可选 `window`/`seed`
- **THEN** 返回 N 注号码及形态摘要；响应含免责声明字段

#### Scenario: 回测接口
- **WHEN** 客户端请求 `POST /backtest` 含窗口与注数等参数
- **THEN** 返回策略与随机基线的对比指标及明细列表

### Requirement: 错误模型一致
系统在参数非法或数据不足时 SHALL 返回 4xx，并在 body 中提供可读的 `detail` 说明。

#### Scenario: 未知彩种
- **WHEN** 请求使用不支持的 `game` 值
- **THEN** 返回 422 或 400，并说明可选值为 `ssq`/`dlt`
