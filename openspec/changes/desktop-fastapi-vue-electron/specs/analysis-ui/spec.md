## ADDED Requirements

### Requirement: 开奖列表页
桌面端 SHALL 提供开奖列表视图，支持切换双色球与大乐透，并展示最近 N 期号码。

#### Scenario: 切换彩种刷新列表
- **WHEN** 用户选择 `dlt`
- **THEN** 列表展示大乐透最近开奖且号码格式为前区+后区

### Requirement: 量化分析页
桌面端 SHALL 展示上期形态摘要、冷热 Top、当前遗漏与遗漏分层。

#### Scenario: 调整窗口期重算
- **WHEN** 用户将 window 设为 30 并刷新
- **THEN** 分析数据按近 30 期重新展示

### Requirement: 免责声明可见
分析相关页面 SHALL 展示「仅供研究娱乐，不构成投注建议」类声明。

#### Scenario: 页面底部声明
- **WHEN** 用户打开分析页
- **THEN** 可见免责声明文本
