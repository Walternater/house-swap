# house-analyze 技能 · 共建规划（全 agent 分工）

> 定位：**分析决策技能**——消费 opencode house-scrape 采集的房源数据 + 用户实测财务，产出评分/测算/风险/对比/报告/时间表。
> 原则：**基于 8 项判断认领模块**（谁最擅长谁做）；每个模块独立产出+自测，deepseek 做集成。

---

## 一、边界（与 opencode 技能分工）

| | opencode house-scrape（采集层·已建） | house-analyze（分析层·本次共建） |
|---|---|---|
| 输入 | 贝壳链接/收藏页 | house-scrape 输出 JSON + 用户实测财务 |
| 输出 | 标准化房源数据 | 决策报告 + 评分/测算/时间表 |

---

## 二、架构与模块分工

```
tinypowers/skills/house-analyze/
├── SKILL.md                    # deepseek（规划+集成）
├── scripts/
│   ├── house_analyze.py        # CLI 单入口: score|finance|risk|compare|report|timeline (deepseek集成)
│   ├── score.py                # 双评分+点评+楼龄   ← deepseek（判断4：评分体系）
│   ├── finance.py              # 资金测算/缺口情景  ← minimax（判断6：财务骨架）+claude复核
│   ├── risk.py                 # 风险检查(归本/悖论/DTI/错配) ← opencode/minimax/zcode（判断2）
│   ├── compare.py              # 对比/画像/Top6     ← deepseek（判断4）
│   ├── report.py               # 综合报告 md+html   ← 合并配方(deepseek起草+minimax审财务)
│   └── timeline.py             # 执行时间表/检查表   ← minimax（判断8）
├── config/
│   └── user_profile.json       # ★实测财务(一次输入全模块复用)  ← deepseek规划
└── references/
    ├── schema.md               # 输入契约(对齐house-scrape 29字段) ← deepseek
    ├── policy.md               # 政策口径表(利率/首付/税费+更新日期) ← deepseek（判断1：政策精度）
    └── report_template.md      # 报告模板(合并修正版) ← deepseek
```

---

## 三、模块认领表（含验收）

| 模块 | 认领 | 收编来源 | 验收（smoke test） |
|---|---|---|---|
| **score** | deepseek | 收藏房源/add_listing.py | 输入3套→输出双评分+点评，与收藏房源一致 |
| **finance** | minimax(+claude) | calc_cost.py 升级 | 输入实测profile→月供12,000/缺口63.5万多情景表 |
| **risk** | opencode/minimax/zcode | 3.4核心悖论/03炸弹/决策树 | 输出4大风险检查项+归本日提醒 |
| **compare** | deepseek | build_html+regenerate | 输出排序表+画像+Top6+逐套点评 |
| **report** | deepseek+minimax | 合并修正版模板 | 一页决策报告md+html |
| **timeline** | minimax | 07骨架 | 90天三阶段+检查表 |
| **policy** | deepseek | 政策口径(2025-12后) | 利率/首付/税费全表+更新日期 |
| **user_profile** | deepseek | 实测数据契约 | 全模块读同一口径 |

---

## 四、关键设计（解决本项目最大坑）

1. **口径统一**：`user_profile.json` 存实测数据（月供12,000/信用贷20+60/现金30万/可支配35,500/归本日），全模块只读它——**消除"每件事数字打架"**
2. **输入契约**：`schema.md` 对齐 house-scrape 29 字段，分析层不管采集
3. **政策可更新**：`policy.md` 固化2025-12后口径，标注更新日期，避免再出"首付20%"旧口径

---

## 五、建设顺序（里程碑）

| 里程碑 | 内容 | 产出 |
|---|---|---|
| **M0** | 规划定稿+目录骨架+数据契约(user_profile/schema/policy) | 能跑通空流程 |
| **M1** | score + compare（deepseek） | 双评分/点评/对比可用 |
| **M2** | finance（minimax）+ risk（opencode等） | 测算/风险可用 |
| **M3** | report + timeline | 报告/时间表可用 |
| **M4** | 集成验收：house-scrape数据 → house-analyze 端到端 | 一条命令出决策包 |

---

## 六、协作机制

1. 每个模块独立交付：`scripts/<module>.py` + 自测 + 文档
2. 统一输入：从 `config/user_profile.json` + 房源数据读取
3. 集成人：deepseek（组装 CLI 单入口+最终验收）
4. 各 agent 产出放技能目录对应位置，互不覆盖

---

## 七、验收总标准（M4）

- 输入：opencode 抓的任意新房源 JSON
- 一键输出：`house-analyze score/finance/risk/compare/report/timeline` 六命令全部可用
- 数字与"合并修正版"口径一致（月供12,000/缺口63.5万/10,532）
- 双评分+点评+Top6+90天时间表齐全
