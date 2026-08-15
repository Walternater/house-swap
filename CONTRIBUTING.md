# 贡献指南

## 本项目的铁律

1. **决策引擎 spec.md 是唯一契约**：web/engine.js 与 skills/house-analyze 的 Python 实现都从 spec 生成，改公式必须三处同步（spec + JS + Python）+ 跑 tests/ 对照测试
2. **policy 改动的格式**：必须带 updated_at + 官方来源链接，CI 拒绝无日期的 PR
3. **示例数据必须脱敏**：禁止提交真实房源/真实财务（结构保留+数值扰动）

## 模块认领

| 模块 | 文件 | 说明 |
|---|---|---|
| 决策引擎 JS | web/engine.js | 评分/缺口/月供计算（与 spec 对齐） |
| 决策引擎 Python | skills/house-analyze/scripts/ | 同上，CLI 版 |
| 看板 UI | web/app.js + index.html | 6步向导/结论卡/报告 |
| 政策 | config/policy.json | 按城市，带日期 |
| 测试 | tests/ | 对照测试（双引擎一致性） |

## 提交流程

1. 跑 tests/ 对照测试（20组用例：JS vs Python 输出一致）
2. 改 policy 附来源链接
3. 新功能带示例（脱敏）
4. PR 说明改动+影响

## 路线图（v2 候选）

- LLM 自然语言顾问小结（BYO key）
- 本地服务版（桥接 house-scrape 采集）
- 更多城市 policy
