## ADDED Requirements

### Requirement: 回测对比页
桌面端 SHALL 展示量化策略与随机基线的对比指标，以及最近若干期明细。

#### Scenario: 运行回测
- **WHEN** 用户设置 window/n/periods 并运行回测
- **THEN** 展示主号最佳命中均值、平均命中、特码命中及 ≥3 期数等对比

### Requirement: 结果解读提示
回测页 SHALL 提示「接近随机不代表系统故障，说明缺少显著预测边缘」。

#### Scenario: 基线说明可见
- **WHEN** 回测结果展示完成
- **THEN** 页面包含基线对比含义说明
