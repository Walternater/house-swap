# house-swap · 开源设计（office-hours 定稿）

> 生成：2026-08-15 ｜ 模式：Builder（开源社区）｜ 状态：DRAFT
> 由 /office-hours 流程收敛：目标模式 → landscape → 前提挑战 → 方案选择

---

## Problem Statement

做房产置换（卖一买一）的人，缺一个能回答"该不该换、换哪套、怎么换、钱够不够"的决策工具。市面有房贷计算器（单点）、AI经纪人（收费/绑定）、通用房产开源技能（不做置换场景）。**置换是"现金流约束下的双端决策"**——卖旧所得 → 买新缺口 → 信用贷/房贷置换，现有工具都没覆盖这个特定决策模型。

## What Makes This Cool（差异化）

- **置换场景专用**：双评分（市场×40%+适配×60%）、资金缺口情景表（300/280/260/250万）、信用贷"按年归本"风险检查——这是从真实置换案例（北京，44套数据+实测财务）提炼的决策模型，现有开源房产项目没有
- **双技能+看板三层**：采集（个人自用）→ 分析（开源技能）→ 看板（开源，手动输入零门槛）
- **多 agent 共建产物**：评分/测算/风险/时间表来自 7 个 agent 交叉验证，口径统一靠数据契约

## Premises（已确认）

1. **采集个人自用，不进开源分发**（合规安全；GitHub 对爬虫类仓库有下架风险）——用户确认
2. **看板手动输入为主**（普通人零门槛），采集导入作为进阶功能——用户确认
3. **开源核心 = house-analyze 技能 + 网页看板 + docs**；house-scrape 文档说明但不打包
4. **目标模式 = 开源社区**（免费开放，积累使用者和贡献者），非商业化
5. **口径统一**：user_profile.json（实测财务）为全模块唯一数据源，根治"各 agent 数字打架"

## Landscape（搜索发现）

- 已有：real-estate-mcp（通用房产工作流）、Realestate Advisor（Openclaw技能）、realty-ai-scout——都是"通用房产"，无置换场景
- 商业：八问易居小新（AI经纪人0佣金）、房宜美（个人房产服务）——收费/绑定
- **Eureka**：置换 = 现金流约束下的双端匹配，现有开源工具空白 → 差异化成立

## Approaches Considered

- **A. 看板优先**：纯前端看板+docs，最快开源（Completeness 7/10）
- **B. 技能+看板并行（✅ 选定）**：网页看板 + house-analyze CLI + 数据契约 + 城市配置化（Completeness 9/10）
- **C. 向导式**：问卷式交互向导，体验最像真人顾问（Completeness 6/10）

## Recommended Approach：B

### 架构

```
house-swap/（GitHub 仓库，MIT）
├── README.md + LICENSE + CONTRIBUTING.md
├── skills/house-analyze/        # 分析技能(开源)
│   ├── SKILL.md
│   ├── scripts/                 # score|finance|risk|compare|report|timeline 六模块
│   └── references/              # schema.md(输入契约) + policy.md(政策,按城市)
├── web/                         # 纯前端看板(开源,双击即用/GitHub Pages)
│   ├── index.html + app.js + style.css
│   └── 手动输入→评分/缺口/风险/报告 + 文件导入(进阶)
├── config/user_profile.example.json
├── data/sample/                 # 脱敏示例(假ID假价格)
└── docs/                        # 快速开始/FAQ/合规说明

## Open Questions

1. **城市扩展**：先做"北京深度"还是预留多城市配置？（建议：policy.md 按城市配置化，v1 只填北京，架构预留）
2. **看板算法一致性**：JS 版评分/测算需与 Python 版一致——是否接受"JS 实现一份 + Python 实现一份"的双实现（各有单测），还是 v1 只做 JS 看板版（分析技能后续补齐）？
3. **社区数据共享**：是否开放"脱敏房源数据贡献"（用户上传脱敏数据扩大样本）？

## Success Criteria

1. 普通人打开看板：手动输入房源+财务 → 10 分钟内得到双评分/缺口/风险/90天时间表/报告
2. 程序员跑 house-analyze CLI：一条命令从 JSON 出全套决策包
3. 数字与"合并修正版"口径一致（月供12,000/缺口63.5万/10,532）
4. GitHub 开源：MIT + 合规声明（采集个人自用、数据为估算）+ CI 测试

## Distribution Plan（合规）

- 开源仓库只含：house-analyze + web 看板 + docs + 脱敏示例 —— **不含采集技能**（避免爬虫下架风险）
- house-scrape 作为"个人技能"单独维护，README 链接说明（"进阶用户自行安装使用，遵守平台规则"）
- 示例数据脱敏：假 ID/假价格/假小区名（保留结构不保留真实数据）

## Next Steps（里程碑）

| 阶段 | 内容 | 认领 |
|---|---|---|
| P0 | 仓库骨架 + LICENSE/README/docs + 脱敏示例 + user_profile 契约 | deepseek |
| P1 | 网页看板 v1（手动输入→评分/缺口/风险/报告，纯前端） | deepseek 牵头 |
| P2 | house-analyze 技能（score/finance/risk/compare/report/timeline 六模块） | 按共建规划认领表 |
| P3 | 端到端验收 + GitHub 发布 | 共同 |

## What I noticed about how you think

- 你说"采集个人自用，但提供页面工具给外人"——一句话把合规风险和用户门槛同时解决了，这是产品 sense 不是技术 sense
- 选 B（9/10 完整版）而不是 A（7/10 快版）——你倾向把湖煮干，不愿留半成品给社区
- 你反复强调"给所有想做置换的人"——你把这个工具当成能帮别人的东西，不是自己的脚本
