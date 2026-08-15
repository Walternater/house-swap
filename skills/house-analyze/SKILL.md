---
name: house-analyze
description: 房产置换分析决策技能（开源）。消费房源数据 + 用户实测财务，产出双评分、资金缺口测算、风险评估、对比排序、90天时间表、决策报告。与 house-swap/web 看板共用同一决策引擎 spec。
triggers: ["置换分析", "评分", "资金测算", "换房", "house-analyze", "置换决策"]
---

# /house-analyze

房产置换**分析决策**技能（采集由 house-scrape 单独提供，本技能不含采集）。

## 数据输入

- 房源数据：house-scrape 输出 JSON 或手动录入（对齐 docs/决策引擎-spec.md）
- 财务数据：config/user_profile.json（实测，一次填写全模块复用）

## 能力（CLI 子命令，脚本待共建）

| 子命令 | 功能 | 对应 spec |
|---|---|---|
| score | 双评分+点评 | §1 |
| finance | 资金缺口情景表+置换后月供 | §2 |
| risk | 归本炸弹/悖论/DTI/错配检查 | §2/§3 |
| compare | 排序/画像/Top6 | §1 |
| report | 决策报告 md/html | — |
| timeline | 90天三阶段+检查表 | — |

## 铁律

1. **决策引擎 spec.md 是唯一契约**：JS(web/engine.js) 与 Python 双实现必须一致，改公式跑 tests/ 对照测试
2. **policy 改动带 updated_at + 来源**（CI 校验）
3. 财务数据本地，不提交（.gitignore）

## 与看板的关系

- web/ 看板是同一引擎的浏览器版（手动输入零门槛）
- 本技能是 CLI 版（程序化/批量）
- 两份输出必须一致（对照测试保证）
