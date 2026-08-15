# house-swap · 房产置换助手（开源）

> 给"卖一买一"的人一个能回答 **该不该换、换哪套、怎么换、钱够不够** 的决策工具。

## 这是什么

- **web/**：纯前端网页看板（双击 index.html 即用，数据全本地不上传）。手动输入卖房+财务+目标 → 得到：综合可行性指数、双评分、资金缺口情景表、三方案对比、90天行动清单、可打印报告。
- **skills/house-analyze/**：分析决策技能（CLI），程序化产出同一套决策包。
- **不包含**：房源采集（贝壳/链家）。采集技能 house-scrape 个人自用，见 docs/faq.md 说明。

## 快速开始（非程序员）

1. 下载本仓库（或打开 GitHub Pages 在线版）
2. 打开 web/index.html
3. 按 6 步向导填：卖房信息 → 财务 → 目标偏好 → 看结果
4. 点"导出报告"打印或存 PDF

## 快速开始（程序员）

```bash
# 看板（零依赖）
open web/index.html

# 分析技能（Python3 标准库）
python3 skills/house-analyze/scripts/house_analyze.py --help
```

## 数据与隐私

- 所有计算在浏览器本地完成，**数据不上传**
- 财务数据仅存 localStorage，可"一键清除"
- 示例数据已脱敏（假 ID/假小区/价格扰动）

## 采集 → 分析（数据链路）

- **house-scrape（采集）**：个人自用技能，**不进本仓库**（合规）。从链家/贝壳抓取房源，输出 JSON。
- **house-analyze（分析）**：本仓库 `skills/house-analyze`，消费房源 JSON + `config/user_profile.json` 产出决策包。
- **格式契约**：两端通过 `skills/house-analyze/references/schema.md` 解耦（字段与 `web/engine.js` 读取对齐）。
- **衔接步骤**：采集输出 → 按 schema 归一化 → 组装 `data/input.json` → 跑分析。示例见 schema.md §5。
- 采集合规边界、导入步骤、脱敏要求：见 `docs/faq.md`。

## 政策口径

- 利率/首付/税费见 config/policy.example.json（带更新日期+来源；按城市：北京/上海示例）
- ⚠️ 政策会变：看板显示"政策更新日期"，请以银行/税务面签为准

## 免责声明

本工具输出为**估算参考**，不构成投资/贷款建议。价格、利率、税费以实际挂牌、银行审批、税务征收为准。

## 贡献

见 CONTRIBUTING.md。核心：决策引擎 spec.md 是 JS/Python 双实现的唯一契约，改公式必须同步两份+对照测试。
