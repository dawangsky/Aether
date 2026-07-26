## ADDED Requirements

### Requirement: 预测页可生成推荐注
桌面端 SHALL 允许用户选择彩种、注数与可选 seed，调用预测 API 并展示结果。

#### Scenario: 生成两注双色球
- **WHEN** 用户选择 ssq、n=2 并点击生成
- **THEN** 展示 2 注号码及形态摘要（和值、奇偶、三区、遗漏层等）

### Requirement: 预测免责声明
预测结果区域 SHALL 明确提示开奖随机、不构成投注建议。

#### Scenario: 结果区声明
- **WHEN** 预测结果返回成功
- **THEN** 结果区域同时显示免责声明
