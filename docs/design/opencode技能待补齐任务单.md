~~# house-scrape 技能 · 待补齐任务单（deepseek 审查后转交 opencode）

> 审查对象：`/Users/wcf/personal/tinypowers/skills/house-scrape`（完成度约 75%）
> 审查时间：2026-08-15 ｜ 审查人：deepseek（房产置换工作区 agent）

## ✅ 已认可的部分（无需改）
- Kimi WebBridge 通道方案（已登录真实浏览器绕 CAPTCHA）——正确且当前唯一可靠
- 反爬对抗：登录 handoff / CAPTCHA 重试+--wait-captcha / 极验自动点击
- 工程健壮性：限流抖动+冷却、progress.json 断点续传、--retry-failed/--force、failed.json
- SKILL.md 文档与 29 字段对齐 收藏房源/房源数据.csv

---

## 🔴 P0-1：诸葛兜底通道已失效（证据确凿）

**现象**：`scripts/zhuge_fallback.py` 的 `search_xiaoqu('京贸国际公寓')` 实测返回：
`['天通苑东一区','龙湖长城源著2号院','北京像素北区','百子湾家园','芍药居北里']`
——即诸葛搜索页的**热门推荐**，而非搜索目标小区。**keyword 参数未生效**（m.zhuge.com 已改版前端渲染 SPA，服务端不处理 keyword；与项目旧 fetch_houses.py 失效原因相同）。

**建议**：
1. 移除或标注"已知失效"；若保留需改造
2. 兜底通道改为**幸福里（m.xflapp.com）**——实测可访问且能拿到小区级在售数据：
   - 小区在售分布页：`https://m.xflapp.com/xiaoqu/bj-{小区ID}.html`（含在售户型/面积/价格区间/建造年代，SSR JSON）
   - 小区二手房列表：`https://m.xflapp.com/ershoufang/bj-{小区ID}/`
   - 幸福里小区ID需搜索（web_search "小区名 幸福里 xflapp"）
   - 精度：挂牌口径、小区级汇总，非具体房源——定位为"选房方向兜底"，不替代贝壳

---

## 🔴 P1-2：add_listing.py 未收编（核心价值缺失）

**现状**：SKILL.md 只"引用 `收藏房源/scripts/add_listing.py` 算评分"——技能不自带，跨项目即失效。

**要求**（提示词 5.1 原意）：把 add_listing.py 的**双评分（市场×40%+适配×60%）+ 逐套点评 + JSON/CSV/MD/HTML 四同步 + --dry-run/--manual/--update** 能力**复制进技能并改造**（路径解耦为 --out 配置化），而非跨目录引用。

**验收**：在空目录 `--out ./houses_db_test` 全新初始化，用技能抓3套→评分→点评→四同步全流程跑通。

---

## 🟠 P1-3：build_html.py 未收编（CLI 缺 build-html）

**现状**：SKILL.md 明说"对比分析/报告生成不属本 skill 范围"——但提示词 5.3 要求 `house build-html`。

**要求**：收编 `收藏房源/scripts/build_html.py`（AI点评列+楼龄标红+整体建议区），做成 `house build-html` 子命令。

---

## 🟠 P1-4：CLI 未统一单入口

**现状**：5 个散脚本（scrape_beike/download_images/zhuge_fallback + 2 个 js）。
**要求**：统一为 `house scrape|add|images|build-html` 单入口多子命令（提示词 5.3）。

---

## 🟡 P2-5：户型图标记缺失

**现状**：`download_images.py` 只有 --all 下载全部图集，无户型图识别。
**要求**：参考 `收藏房源/scripts/download_huxing.py`：
- 识别含 `huxing` 命名或 `alt="户型图"` 的图片 → 文件名加 `_户型图` 后缀
- 补 `--html` 离线模式（从已存 HTML 提取图片URL→CDN直下）

---

## 🟡 P2-6（顺带）：XQ_META 外置 + 路径配置化
- 小区→(地铁,均价) 字典抽到 `xq_meta.json`；未知小区自动占位+提示
- `--out` 默认值/配置文件，技能可任意项目复用

---

## 📋 验收清单（补齐后）
1. ✅ 幸福里兜底实测：`search` 返回目标小区（非热门推荐）
2. ✅ 空目录 --out 全新初始化 + 抓3套 + 评分 + 点评 + 四同步
3. ✅ `house build-html` 生成对比 HTML
4. ✅ `house add --url xxx --dry-run` 行为与原 add_listing 一致
5. ✅ download_images 输出含 `_户型图` 后缀文件
6. ✅ 未知小区自动占位 + 提示用户补充

---
> 环境备注：当前主 IP 被贝壳标记，但 Kimi WebBridge 用本机已登录浏览器会话，可绕过 CAPTCHA——冒烟测试应走 Webbridge 通道验证。~~
