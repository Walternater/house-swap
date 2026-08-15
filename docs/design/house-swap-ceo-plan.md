---
status: ACTIVE
---
# CEO Plan: house-swap 开源包（技能+看板）

> 由 /plan-ceo-review 生成 2026-08-15 ｜ Mode: EXPANSION

## Vision

### 10x Check
普通人打开网页 10 分钟回答 6 个问题 → 得到"和资深顾问聊完一样"的置换决策书（该不该换/换什么价位/哪些小区/现金流/风险/90天清单），数据全本地。

### Platonic Ideal
输入卖房+负债+收入+目标 → 输出三方案对比+综合可行性指数+报告导出。成为"置换决策"场景默认开源工具。

## Scope Decisions

| # | 提案 | Effort | Decision |
|---|------|--------|----------|
| E1 | 反向计算器（目标月供→可买总价） | S | ✅ ACCEPTED |
| E2 | 综合可行性指数+结论卡 | S | ✅ ACCEPTED |
| E3 | 报告导出（打印/PDF） | S | ✅ ACCEPTED |
| E4 | 三方案一键切换（稳健/平衡/激进） | S | ✅ ACCEPTED |
| E5 | 多城市政策配置（北京+示例上海） | M | ✅ ACCEPTED |
| E6 | 社区脱敏样本库+贡献流程 | M | ✅ ACCEPTED |

## Accepted Scope
- 看板：手动输入 + E1反向计算 + E2指数结论卡 + E4三方案 + E3报告导出 + E5城市切换 + E6示例数据
- house-analyze 技能：六模块 + 与看板共享"决策引擎 spec"
- 数据契约：user_profile.json / schema.md / policy.md(多城市,带updated_at)

## Deferred to TODOS
- LLM 自然语言顾问小结（BYO key）—— v2
- 本地服务版（桥接 house-scrape 采集）—— v2

## 11 章审查结论（plan-ceo-review）

### 关键决策（用户已确认）
1. **双引擎一致性**：决策引擎 spec.md（公式/权重/边界）+ JS/Python 双实现 + 20组对照测试
2. **政策维护**：policy 条目强制 updated_at + 官方来源链接；CI 拒绝无日期 PR；看板显示"政策更新日期"
3. **脱敏**：结构保留 + 数值扰动（假ID/假小区/价格±15%扰动/删真实链接）

### 审查发现汇总
| 章节 | 级别 | 结论 |
|---|---|---|
| S1 架构 | 🔴 | 双实现一致性 → spec+对照测试（已定） |
| S2 错误 | 🔴 | 输入校验/除零/NaN/政策过期警告/无静默失败 |
| S3 安全 | 🟠 | 纯本地✅；localStorage 一键清除；真实44套彻底脱敏 |
| S4 数据流 | 🟠 | 空表单→示例数据引导；多城市数据按城市命名空间 |
| S5 质量 | ✅ | 决策公式集中 engine.js，DRY |
| S6 测试 | 🔴 | 对照测试20组+边界+E1逆运算精度±1万 |
| S7 性能 | ✅ | 无问题 |
| S8 可观测 | 🟠 | 导出诊断日志（匿名可提交） |
| S9 部署 | ✅ | GitHub Pages + CI（对照测试+policy校验） |
| S10 长期 | 🟠 | 可逆4/5；政策靠社区PR（CONTRIBUTING模板） |
| S11 设计 | ✅ | 6步向导+结论先行（指数卡→细节→行动清单） |

### 完成状态
- Mode: EXPANSION ｜ Scope: E1-E6 全部 ACCEPTED ｜ 关键决策: 3项确认
- NOT in scope（v2）: LLM 顾问小结（BYO key）、本地服务版桥接采集
- 下一步: P0 启动（仓库骨架+看板v1+决策引擎spec+脱敏示例）
