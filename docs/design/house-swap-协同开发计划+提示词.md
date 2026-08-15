# house-swap · 协同开发计划 + Agent 提示词包

> 2026-08-15 ｜ 仓库：/Users/wcf/personal/house-swap（P0 已完成，git 首个提交 3d48ae2）
> 用途：召唤 minimax/claude/opencode/zcode/workbuddy 等 agent 并行开发 P1-P3

---

## A. 总体规划

### 依赖图（谁先谁后）
```
P1a: engine_py.py（Python 决策引擎，对齐 spec）   ← 所有 Python 模块的依赖
   │
   ├─ P1b-1 finance.py（minimax）   ─┐
   ├─ P1b-2 risk.py（zcode）        ├─ 并行（都只依赖 engine_py）
   ├─ P1b-3 score/compare.py（deepseek）
   ├─ P1b-4 timeline.py（minimax）
   └─ P1b-5 report.py（claude）
          │
P1c: house_analyze.py CLI 单入口（deepseek 集成六模块）
P2a: 看板打磨+截图验证（deepseek）
P2b: 政策扩展-上海示例（workbuddy）
P3:  20组对照测试补全 + docs + 发布准备（workbuddy/共同）
```

### 里程碑与验收
| 里程碑 | 内容 | 验收 |
|---|---|---|
| M1 | engine_py + 10组对照测试(JS vs Py) | 同输入同输出 |
| M2 | 六模块齐全 + CLI 跑通 | 一条命令出全套决策包 |
| M3 | 看板打磨 + 集成 | 看板与 CLI 输出一致 |
| M4 | 测试补全20组 + docs + 发布 | CI 绿 + GitHub 就绪 |

### 铁律（所有 agent 必须遵守）
1. **docs/决策引擎-spec.md 是唯一契约**：改公式必须 spec+JS+Python 三处同步+对照测试
2. **policy 改动带 updated_at + 官方来源**；不提交真实数据（脱敏铁律）
3. **纯 Python3 标准库**（零第三方依赖，与项目一致）
4. 输出到指定路径，不覆盖他人文件

---

## B. 任务认领表

| 任务 | 认领 | 输出 | 依赖 |
|---|---|---|---|
| engine_py.py | deepseek（P1a） | skills/house-analyze/scripts/engine_py.py | spec |
| finance.py | minimax | 同上/finance.py | engine_py |
| risk.py | zcode | 同上/risk.py | engine_py |
| timeline.py | minimax | 同上/timeline.py | — |
| report.py | claude | 同上/report.py | finance/risk |
| score/compare.py | deepseek | 同上/score.py | engine_py |
| CLI 集成 | deepseek | 同上/house_analyze.py | 全部 |
| 看板打磨 | deepseek | web/ | — |
| 上海政策示例 | workbuddy | config/policy-shanghai.json | — |
| 测试补全+docs | workbuddy/共同 | tests/ + docs/ | 全部 |

---

## C. Agent 提示词包（可直接复制转发）

### 📋 共同前置（每份提示词开头都贴这段）

```
【前置】这是一个开源项目 house-swap（房产置换助手），仓库在 /Users/wcf/personal/house-swap。
1. 先读 /Users/wcf/personal/house-swap/docs/决策引擎-spec.md（数学公式/权重/边界的唯一契约）和 README.md、CONTRIBUTING.md
2. 铁律：纯 Python3 标准库（禁第三方依赖）；决策引擎 spec 是唯一契约（改公式必须 spec+JS+Python 三处同步）；不提交任何真实数据（示例必须脱敏）
3. 已有代码参考：web/engine.js（JS 实现，与你的 Python 实现必须一致，跑 tests/engine.test.js 对照）
4. 你的产出写到指定文件路径；完成后跑一遍本地验证，报告：改了什么、验证结果、依赖谁
```

---

### 🎯 提示词 1（minimax · finance 模块）

```
【任务】为 house-swap 写 Python 版资金测算模块：skills/house-analyze/scripts/finance.py
【功能】（严格按 docs/决策引擎-spec.md §2/§4/§5）
1. finance_calc(user, policy)：卖房净得→现金回笼→可用资金→四档缺口情景表(300/280/260/250万)→置换后月供(公积金+商贷组合)→月供占可支配比（含保留信用贷时）
2. reverse_calc(target_monthly, years, rate, down_ratio)：目标月供→可贷总额→可买总价（E1 反向计算）
3. three_plans(budget, finance, user)：稳健/平衡/激进三方案（E4）
【输入】user_profile 结构见 config/user_profile.example.json；policy 见 config/policy.example.json
【对齐】web/engine.js 的 financeCalc/reverseCalc/threePlans 已实现 JS 版，你的 Python 版必须同输入同输出（±1元内）
【验证】用样例（卖房140/房贷93.1/中介1.5%/现金30/信用贷80/月薪27000+公积金8500）跑一遍，输出应与合并修正版口径一致：月供约10,532元、300万缺口约56万
【输出】finance.py + 自测（打印验证结果）；别动其它文件
```

### 🎯 提示词 2（minimax · timeline 模块）

```
【任务】为 house-swap 写执行时间表模块：skills/house-analyze/scripts/timeline.py
【功能】（参考 spec 与你的 07 章分册）
1. 90天三阶段时间表（第1-30/31-60/61-90天），含：挂牌→看房→归本日避让→成交→贷款→过户，每阶段具体任务清单
2. 决策检查表（勾选项）：归本日确认、中介费率谈判、现金准备、贷款材料、风险确认
3. 输入 user_profile（含归本日），输出 markdown 时间表+检查表文本
【对齐】输出直接可写进决策报告；格式用 markdown 表格
【验证】用样例 profile 生成一份完整 90 天表（检查项 ≥10 条）
【输出】timeline.py + 生成的示例时间表
```

### 🎯 提示词 3（zcode · risk 模块）

```
【任务】为 house-swap 写风险评估模块：skills/house-analyze/scripts/risk.py
【功能】（你最擅长的：归本炸弹/资金悖论/DTI/时间错配）
1. check(user, finance)：输出 4 大风险检查结果（每条：风险名/严重度🔴🟠/触发条件/缓解建议）
   - 信用贷"按年归本再贷"：若 user.revolving=true 且未结清 → 年度归本炸弹 + 归本日提醒
   - 资金悖论：全清信用贷+首付的缺口 vs 可用资金 → 无法同时满足
   - DTI：置换后月供占可支配比（>50% 红灯 / 40-50% 黄灯 / <30% 绿）
   - 时间错配：先卖后买 vs 先买后卖提示
2. 输出 markdown 风险雷达（可直接进决策报告）
【对齐】web/engine.js 的 feasibilityIndex 相关逻辑已实现指数，risk.py 输出更细的风险条目
【验证】用样例 profile 跑一遍，输出 4 条风险（含归本炸弹🔴）
【输出】risk.py + 自测结果
```

### 🎯 提示词 4（claude · report 模块）

```
【任务】为 house-swap 写决策报告生成器：skills/house-analyze/scripts/report.py
【功能】
1. 输入：user_profile + 房源数据 + 六模块结果（score/finance/risk/timeline/compare）
2. 输出：一份可打印的 markdown 决策报告（结构：结论摘要→资金测算→风险→房源对比→90天计划→免责）
3. 结论摘要含"综合可行性指数"结论卡（≥80 强烈建议换 / 60-79 可换需准备 / <60 暂缓）
【对齐】参考 /Users/wcf/personal/房产置换/deepseek/房产置换风险评估与资金成本测算报告-合并修正版.md 的结构与口径（这是本项目"数字正确"的基准）
【验证】用样例数据生成一份完整报告（含免责声明）
【输出】report.py + 样例报告
```

### 🎯 提示词 5（opencode · 数据衔接层）

```
【任务】打通 house-scrape（你的采集技能）→ house-analyze（分析技能）的数据链路
【功能】
1. 写 skills/house-analyze/references/schema.md：声明 house-analyze 接受的输入 JSON 结构（对齐你的 house-scrape 输出字段 + config/user_profile.example.json）
2. 提供 1 条"采集→分析"端到端示例：用你采集的一套真实（脱敏后）数据，走一遍 house-analyze 输入格式
3. 在 README 补"采集→分析"衔接说明（docs/faq.md：采集技能个人自用、如何导入分析）
【注意】采集技能不进开源仓库（合规），这里只做格式对接文档
【验证】schema.md 字段名与 web/engine.js 读取的字段（xq/hx/area/price/avg/floor/lift/metro/years/biz）对齐
【输出】references/schema.md + docs/faq.md
```

### 🎯 提示词 6（workbuddy · 测试+政策）

```
【任务】为 house-swap 补测试和政策示例（两个小任务）
【任务A】tests/ 补全对照测试到 20 组：JS(web/engine.js) vs Python(engine_py.py，若还没建则先对照 spec 手算期望值) 的 PMT/评分/缺口/反向计算用例。写 tests/engine_test.py（Python 侧）+ 更新 tests/engine.test.js 到 20 组，运行都绿。
【任务B】写 config/policy-shanghai.json（上海示例政策）：结构对齐 policy.example.json，含 updated_at+来源。数值用公开的上海利率/税费/限购要点（2025-2026），不确定的标"待核实"。
【验证】node tests/engine.test.js 全绿；policy-shanghai.json 每个条目有 updated_at
【输出】tests/ 更新 + config/policy-shanghai.json
```

---

## D. 集成说明（deepseek 负责，各 agent 完成后）

- 六模块完成后，deepseek 组装 house_analyze.py CLI 单入口（score|finance|risk|compare|report|timeline）
- 对照测试全量跑（JS vs Python 20组）
- 看板与 CLI 输出一致性校验
- git 提交（按 CONTRIBUTING 规范）
---

# /autoplan 评审报告（Phase 1: CEO）

> 2026-08-15 ｜ 评审对象: house-swap 协同开发计划 ｜ Mode: SELECTIVE EXPANSION（autoplan 覆盖）

## CEO DUAL VOICES — CONSENSUS TABLE

| 维度 | Codex | Subagent | 共识 |
|---|---|---|---|
| 1. Premises valid? | 一半是一厢情愿（采集私有/手动输入/双引擎） | 手动输入 assumed 错；双引擎成本超收益 | DISAGREE（双引擎） |
| 2. Right problem? | 对，但框架错——应是"中介面前的底牌" | 对，但应把归本日做成产品脊柱 | 部分一致 |
| 3. 6-month regret? | 开源社区没来，时间花在镜像/CI/合规 | 花半年造工具，工具没做自己的决定 | CONFIRMED |
| 4. Alternatives? | JS-only + 向导式 + 采集桥接不该 defer | 看板优先才是 owner 的 MVP | 部分一致 |
| 5. Competitive risk? | 贝壳/链家 AI 经纪人实时数据碾压 | 平台把测算绑进自有数据 | CONFIRMED |
| 6. Trajectory? | E1-E6 全收是 scope creep 仪式 | E5/E6 可砍，加 CI 最高价值 | 部分一致 |

CONFIRMED: 2/6 ｜ DISAGREE: 1（双引擎） ｜ 部分一致: 3 ｜ 其余见各段

## Premise Gate（需用户确认，不自动决策）

### P1. 采集个人自用，不进开源分发
- 计划/设计: 采集不进仓库（合规）
- Codex: 自我阉割，采集+分析一锅端，合规声明即可
- Subagent: 采集→分析桥接 personal-first，仓库保持合规
- 我（deepseek）倾向: 维持不进仓库（GitHub 爬虫下架风险真实存在，real-estate-mcp 能活不代表所有爬虫仓库都安全；采集技能已存在 house-scrape），但接受"桥接文档"已在 schema.md/faq.md 落地

### P2. 看板手动输入为主
- 计划: 手动输入为主，采集导入进阶
- Codex: 退化成"又一个房贷计算器"
- Subagent: 44套手动录入一次性苦活即过期，杀死个人闭环
- 我倾向: 手动输入是"开源受众零门槛"的正确选择，但 owner 自己需要采集桥接——两者不矛盾：开源版手动、个人版桥接

### P3. 双引擎 JS+Python 一致性
- 计划: spec 唯一契约 + 双实现 + 20组对照（已完成）
- Codex: 90% 浪费，JS-only 正解
- Subagent: 20/20 已绿，单案例引擎三方同步成本超收益；冻结 spec 不加公式
- 我倾向: 双引擎已完成且验证通过，回滚成本高；**冻结 spec** 是合理折中（不加新公式，除非第二真实案例）

### P4. 开源社区模式（免费）
- 计划: 免费开放积累社区
- Codex: 为想象中的用户写代码
- Subagent: 零需求证据；开源=分发渠道而非战略
- 我倾向: 开源继续（仓库已就绪），但 M3/M4 优先级应转向"owner 真实决策先用起来"

### P5. 脱敏（结构保留+数值扰动）
- 计划/Codex/Subagent 一致: 必要性成立
- 唯一分歧: ±15% 扰动会让对照测试基线失效（Codex）——但实测 20/20 已绿，样例与引擎不共享基线，非问题

## 6-month regret（双 voice 一致, 高置信）
**花了半年造工具，工具没做我的决定。** 真实置换：归本日踩错时点、折价卖、收藏过期——负债每月烧利息。修复动作: 本周末用真实 profile + Top10 收藏跑一份真报告出短名单。

## 已发现的工程 bug（转 Phase 3 跟踪）
- [P1] JS threePlans 读 u.disposable → 看板显示 null%（Python 回退正常）
- [P2] CLI _load_json 静默回退样例（用户传错路径无感知）
- [P2] 无 CI workflow（.github 不存在），"数字一致"卖点无守护

## 待 Phase 3 补充
- 测试图（20组覆盖 vs 分支）、test plan artifact、TODOS.md


---

# /autoplan 评审报告（Phase 3: Eng）

> 2026-08-15 ｜ 实际代码审计（非记忆）

## 系统架构图

```
                        docs/决策引擎-spec.md（唯一契约）
                                   │ 三处同步
        ┌──────────────────────────┼──────────────────────────┐
        ▼                          ▼                          ▼
  web/engine.js (JS)        engine_py.py (Python)      tests/ (20组对照)
        │                          │                          │
        ├─ app.js (看板)           ├─ finance.py              ├─ engine.test.js (JS侧)
        │    │                     ├─ risk.py                 ├─ engine_test.py (Py侧)
        │    │                     ├─ timeline.py             └─ compare.sh (全字段)
        │    │                     ├─ report.py
        │    │                     └─ house_analyze.py (CLI 单入口, subprocess→report)
        │    └─ localStorage ──────┘
        └─ 纯前端无后端 (GitHub Pages 就绪)
```

## 测试覆盖图（20组 vs 引擎分支）

```
CODE PATH COVERAGE
===========================
[+] web/engine.js + engine_py.py（同一套公式,20组对照）
    ├── pmt()            [★★★] 5组: 255万/120万/135万/100万/利率0降级
    ├── marketScore()    [★★★] 高配/低配/空对象默认分支
    ├── fitScore()       [★★★] 高配/低配(超预算/步梯顶)
    ├── compositeScore() [★★★] 满配100 / 楼龄>30扣5
    ├── financeCalc()    [★★★] 月供/占比/保留信用贷 + 四档缺口
    ├── feasibilityIndex()[★★] 样例40 / 缺口≤现金+20 (缺: 月供>50% -20 分支)
    ├── reverseCalc()    [★★★] 2组 + ±1万精度
    ├── threePlans()     [★★] 300万预算 (缺: u.disposable 缺失边界 ← 已发现bug)
    └── validateInputs() [★★★] 非法输入4条

USER FLOW COVERAGE
===========================
[+] 看板 6 步向导 (web/app.js)
    ├── [GAP] 步骤跳转/prev/next — 无自动化测试（纯前端手动验证）
    ├── [GAP] 三方案显示 null% — 现网 bug（threePlans disposable）
    ├── [GAP] 城市选择器 citySel — 死 UI，无任何处理
    ├── [GAP] 空表单提交 — validateInputs 有提示但无测试
    └── [GAP] localStorage 损坏/清除 — save/load 有 try/catch 但未验证
─────────────────────────────────
COVERAGE: 引擎公式 ~90%（20/20组绿）；UI 流程 0% 自动化
```

## Eng 发现汇总（我的审计）

| # | 级别 | 置信 | 发现 | 位置 |
|---|---|---|---|---|
| E1 | P1 | 10/10 | JS threePlans 读 u.disposable=null → 看板三方案 null% | web/engine.js:125, web/app.js:102 |
| E2 | P1 | 9/10 | CLI _load_json 静默回退样例，用户传错路径无感知（已实证） | house_analyze.py:61 |
| E3 | P2 | 9/10 | citySel 城市选择是死 UI，E5 未真正接入 | web/index.html:13, app.js 无引用 |
| E4 | P2 | 10/10 | 无 CI（.github 不存在）——"数字一致"卖点无守护 | 仓库根 |
| E5 | P2 | 8/10 | policy-shanghai.json 无任何代码引用 | 全仓库 grep 空 |
| E6 | P3 | 7/10 | 非法 JSON 抛裸 JSONDecodeError traceback（exit=0 掩盖） | house_analyze.py:63 |
| E7 | P3 | 8/10 | __pycache__ 已提交进 git（.gitignore 未覆盖?） | 仓库树 |

## 失败模式登记（双引擎 drift 风险）
- 三处同步靠人工纪律：spec 改一处 → JS/Py 忘了同步 → 测试不覆盖新分支 → 静默漂移
- 对照测试是"已知输入快照"，非生成式：新公式没有对应用例就检测不到
- 看板与 CLI 走不同引擎实现（JS vs Py），行为差异只有手工对比能发现（compare.sh 是固定样例）


---

# /autoplan 评审报告（Phase 2: Design）

> 2026-08-15 ｜ 基于实际看板代码（web/index.html + app.js + style.css）

## Step 0: 初始评分
**设计完整度: 6/10**（工具型 UI 合格，但交互状态覆盖不足）
- 10 分长什么样：6 步向导 + 每步即时校验 + 结果页空/错/加载状态 + 移动端专门布局 + 结论卡可打印

## DESIGN.md 状态
**NO DESIGN.md** — 无设计系统。用通用设计原则评审（此项目规模可不建 DESIGN.md，暂记 TODO）

## 7 维评分

| 维度 | 分 | 依据 |
|---|---|---|
| 1. 信息架构 | 7 | 结论先行正确（指数卡→资金→月供→三方案→评分→反向）；6 步向导路径清晰 |
| 2. 交互状态覆盖 | 4 | 有空状态（无房源提示）+ 错误态（errs 修正卡）；缺 loading/partial；三方案 null% bug 是状态 bug |
| 3. 用户旅程 | 6 | 情感弧线合理（填数→看指数→算方案→导报告）；但死 UI（城市选择）制造困惑 |
| 4. 特异性 | 6 | 具体组件/颜色/间距都在 CSS；无"generic 模式" |
| 5. AI slop 风险 | 7 | 低——不是通用卡片网格，是决策工具布局 |
| 6. 响应式 | 6 | grid auto-fit 自适应；无专门移动导航；打印媒体查询已做 |
| 7. 可访问性 | 3 | 无键盘导航/aria/label 关联；对比度部分 ok；无焦点样式 |

## 关键发现
- **D1 (P2, 9/10)**: 城市选择器死 UI — 用户选了上海无任何反应（E5 未接入）
- **D2 (P2, 8/10)**: 结果页无"数据已保存"反馈 — localStorage save() 静默
- **D3 (P3, 7/10)**: 无移动端优化（真实用户可能在手机上看房）— 但 v1 纯桌面可接受
- **D4 (P3, 6/10)**: 无障碍缺口（键盘导航/焦点可见）— OSS 贡献者友好项

## 设计工具
DESIGN_READY（gstack designer 可用）— 但本评审聚焦已实现看板的改进，mockup 非必需（看板已存在且可用）


---

# /autoplan 评审报告（Phase 3.5: DX）

> 2026-08-15 ｜ 开发者视角（CLI 技能为主）

## 开发者旅程（9 阶段）

| 阶段 | 现状 | 评分 |
|---|---|---|
| 1. 发现 | README 开头 3 段讲清"这是什么"✅ | 7 |
| 2. 安装 | 零依赖，clone + 打开即用 ✅ | 9 |
| 3. 快速开始 | README 双路径（非程序员/程序员）✅ | 8 |
| 4. 首个输出 | CLI --help 清晰，all 一条命令出全套 ✅ | 8 |
| 5. 理解输出 | 中文 markdown 表格式，可读 | 7 |
| 6. 定制 | --user/--policy/--houses JSON 传入 | 6 |
| 7. 错误处理 | ❌ 静默回退样例（已实证） | 3 |
| 8. 贡献 | CONTRIBUTING 铁律清晰 ✅ | 8 |
| 9. 升级 | 无版本/迁移概念（v1 阶段） | 5 |

## DX Scorecard

| 维度 | 分 | 备注 |
|---|---|---|
| TTHW（零到 hello world） | 8 | <1 分钟（open index.html 或 python3 -h） |
| CLI 命名可猜测 | 8 | score/finance/risk/compare/timeline/report/all 自解释 |
| 错误信息可操作 | 3 | 文件不存在静默；JSON 错误裸 traceback |
| 文档可发现 | 7 | README 好；SKILL.md 写"脚本待共建"已过期 ❌ |
| 升级路径 | 5 | 无 changelog/版本，v1 可接受 |
| 开发环境无摩擦 | 9 | 零依赖双栈（Node + Python3） |

**DX 总评: 7/10** ｜ TTHW: <1 分钟（目标达成）

## 关键发现
- **X1 (P2, 9/10)**: SKILL.md 表格说"脚本待共建" — 六模块已完成，文档过期误导
- **X2 (P2, 8/10)**: README 引 config/policy.json，实际文件是 policy.example.json（不一致）
- **X3 (P2, 8/10)**: CLI 错误路径差（静默回退 + 裸 traceback）— 与 E2 同源
- **X4 (P3, 7/10)**: compare 依赖 node 环境（README 未注明"需 Node 跑对照测试"）

## DX Implementation Checklist
1. [ ] SKILL.md 更新为"脚本已就绪"（去"待共建"）
2. [ ] README 修正 policy.json → policy.example.json 引用
3. [ ] CLI 错误路径修复（--user 不存在 → exit≠0 + 明确报错）
4. [ ] README 注明 compare/对照测试需要 Node


## Eng 发现更新（合并 codex voice，2026-08-15）

| # | 级别 | 置信 | 发现 | 位置 |
|---|---|---|---|---|
| E8 | P0 | 10/10 | financeCalc: creditTotal 缺失 → 全链 NaN；validateInputs 不查 | engine.js:69 / engine_py.py:94 |
| E9 | P1 | 9/10 | pmt(r,0,P) → Infinity（n=0 分母为0），spec §6 要求等额本金降级但双引擎都没实现 | engine.js:9 / engine_py.py:11 |
| E10 | P1 | 9/10 | reverseCalc 无守卫：rate=0→NaN, downRatio=1→Infinity | engine.js:113 / engine_py.py:118 |
| E11 | P1 | 8/10 | threePlans 硬编码 3.05%（不走 policy），policy 改动无效 | engine.js:130 / engine_py.py:130 |
| E12 | P1 | 8/10 | loan=255 硬编码：二套 downRatio=0.20 时高估负债；无非默认首付测试 | engine.js:76 / engine_py.py:100 |
| E13 | P1 | 9/10 | 看板 XSS：houseFormHTML 拼接 value + resultArea.innerHTML 插值；localStorage 可被替换 | web/app.js:63,122 |
| E14 | P2 | 8/10 | policy 无 schema 验证：typo → KeyError 中途崩 | CLI/report |
| E15 | P2 | 7/10 | collectHouses filter price>0 静默丢弃 0 价房源，无警告 | web/app.js:79 |
| E16 | P2 | 6/10 | feasibilityIndex 边界 r=40 无测试（40→+5, 40.0001→0） | tests |
| E17 | P2 | 7/10 | load() 吞 JSON.parse 错误，houses:null 时 Object.assign 覆盖 → 下次 render 抛错 | web/app.js:12 |
| E18 | P2 | 8/10 | 看板硬编码 policy（与 CLI 读 policy.json 两套定义） | web/app.js:101 |

**Codex 原话引用（关键）**: "dashboard calls threePlans(state.target.budget, f, u) with u lacking disposable → all three-plan ratios render as NaN% in the browser. This is the documented P1; confirmed reproducible."（注意 codex 说 NaN%，我之前实测是 null%——JS 里 undefined/1000*... 实际是 NaN，JSON.stringify(NaN)→null，CLI 输出显示 null。浏览器渲染是 NaN%。）


---

# /autoplan Decision Audit Trail

| # | Phase | Decision | Classification | Principle | Rationale | Rejected |
|---|-------|----------|-----------|-----------|----------|----------|
| 1 | CEO | 采集个人自用不进开源：维持 | User-adjacent | P5 合规优先 | GitHub 爬虫下架风险真实，采集已存在 house-scrape | Codex 反建议（一锅端）|
| 2 | CEO | 看板手动输入为主：维持开源版，owner 需桥接 | User-adjacent | P6 用户主权 | 开源零门槛 vs 个人闭环不矛盾 | Codex 反建议 |
| 3 | CEO | 双引擎：冻结 spec 不再加公式 | Taste | P3 务实 | 20/20 已绿，单案例引擎三方同步成本超收益 | 回滚 JS-only（成本高）|
| 4 | CEO | 开源继续但 M3/M4 转向 owner 真实决策 | Taste | P6 bias to action | 先服务 owner 再谈社区 | — |
| 5 | CEO | E5 多城市/ E6 社区样本：降级为按需 | Taste | P3 务实 | 0 需求证据 + 静态样本过时 | E1-E6 全收原计划 |
| 6 | Eng | 修 threePlans disposable 回退（P1） | Mechanical | P1 完整 | 看板 NaN% 现网 bug | — |
| 7 | Eng | 修 _load_json 静默回退（P0） | Mechanical | P1 完整 | 传错路径出假报告，money tool 不可接受 | — |
| 8 | Eng | 修 creditTotal NaN 链（P0） | Mechanical | P1 完整 | validateInputs 补查 | — |
| 9 | Eng | 加 CI workflow（P2） | Mechanical | P1 完整 | "数字一致"卖点需要守护 | — |
| 10 | Eng | 补 pmt/reverseCalc 边界（P1） | Mechanical | P1 完整 | n=0 分母、rate=0、downRatio=1 | — |
| 11 | Eng | 看板 XSS 转义（P1） | Mechanical | P5 显式 | innerHTML 插值用户输入 | — |
| 12 | Eng | threePlans 硬编码 3.05%/255 改参数化（P1） | Taste | P5 显式 | policy 才是契约 | 保持简单硬编码（v1 单城市）|
| 13 | DX | SKILL.md 去"待共建"（P2） | Mechanical | P4 DRY | 文档过期误导 | — |
| 14 | DX | README policy.json→example 修正（P2） | Mechanical | P5 显式 | 引用不存在文件 | — |

**E11 验证（2026-08-15 实测）**: 改 policy 利率 2.6/3.05 → 2.0/2.5，financeCalc 月供 10532→9770（敏感），threePlans 月供 8980→8980（不变）→ 硬编码实锤。三方案利率应参数化。

---

# Eng SUBAGENT（fuzz 验证）发现 — 2026-08-15

> 方法：30k 随机输入对比 JS vs Python（/tmp/fuzz_gen.js, fuzz_py2.py, rep_check.py），
> 所有结论均执行验证，非代码阅读猜测。补充说明：测试全绿证明 JS≡Python 的"整数快照点"，
> 不证明 JS≡spec；且 JS≡Python 在非整数输入下也是碎的。

## 已实测确认（含复现）

| # | 级别 | 发现 | 复现结果 |
|---|---|---|---|
| F1 | P1 | disposable 漂移：JS 返回原始浮点，Python round() → 30k fuzz 全不同（24720.7 vs 24721） | ✅ 35500.5 vs 35500（我实测）|
| F2 | P1 | finance.py agentFee=0 bug：`or 0.015` 把 0 费率变 1.5% → net 137.9 vs 140 | ✅ 137.9（我实测）|
| F3 | P1 | report.py clamp 不匹配：引擎 gjjMax→200，report→255 → 报告自相矛盾 | 待复核 |
| F4 | P1 | spec 违规被测试固化：缺失 age→8（spec: 楼龄=30→6）；缺失 metro→10（spec: 无→4）| ✅ 引擎给 8/10，spec 要求 6/4 |
| F5 | P1 | threePlans 区间 vs spec：算 25.3/28.3/30.5%，spec 要求 ≤25/25-35/35-50%（25.3 微超稳健上限）| ✅ |
| F6 | P1 | JS financeCalc 缺 agentFee → NaN（两个 Python 都默认 0.015）| ✅ NaN（我实测）|
| F7 | P1 | CLI 静默回退样例（--user typo.json 出假报告）| ✅ 我实测 |
| F8 | P2 | pmt(years=0) → Infinity/ZeroDivisionError（spec §6 要求降级）| 逻辑确认 |
| F9 | P2 | compare.sh 硬编码绝对路径 + 只测 1 个输入点 | 代码确认 |
| F10 | P2 | collectHouses 硬编码 age:20 + 丢 4 字段 → 看板评分 ≠ CLI | 代码确认 |
| F11 | P2 | cmd_all 吞 compare 失败 exit（SystemExit 被 except 吃掉）| 代码确认 |
| F12 | P2 | 死 city 选择器（上海 policy 硬编码北京）| ✅ 我实测 |

## Subagent 修复优先级建议（采纳）
1. compare.sh 改为：跑两个 Python 模块 + JS，N 随机输入对比（一次抓 F1/F2/F6）
2. 加 spec 一致性断言（抓 F4）
3. 共享 clamp/loan helper（抓 F3）

## 共识：双引擎一致性的真实状态
- **20/20 绿 + compare.sh 绿 ≠ 双引擎一致**。它们在"整数快照点"一致，在任意输入下不一致。
- 修复路径不是"再补测试"，而是**先修引擎差异**（disposable 取整、agentFee 缺省、pmt n=0、clamp 统一），再让 compare.sh 随机化。
- 这改变了"双引擎已达成"的叙事：M1/M2 验收"同输入同输出"严格说**未达成**（仅快照达成）。



---

# /autoplan FINAL GATE — APPROVED (2026-08-15)

用户批准（3/3 全选 Recommended）：
1. 前提：全部接受（采集私有/手动输入/冻结 spec/owner 优先）
2. 修复：P0+P1 全部修复（约1-2h CC）
3. 战略：owner 决策优先 + 加 CI + 清理死 UI（E5 移除或接入）

后续动作：引擎差异修复 → 随机化 compare.sh → CI → 真实决策演练 → 提交
