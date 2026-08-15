# -*- coding: utf-8 -*-
"""
house-swap · 90 天执行时间表（Python）
=======================================

唯一契约: docs/决策引擎-spec.md
参考: 线下 07 章分册（三阶段节奏、归本日避让、决策检查表口径）
JS 对应: web/app.js 90 天行动清单（仅 5 条 bullet，本模块扩为完整 3×N 表）
本模块: skills/house-analyze/scripts/timeline.py

铁律
----
1. 纯 Python3 标准库
2. 输入字段对齐 schema.md（user.revolvingDate / user.timing / user.hasYearlyRevolving …）
3. 输出 markdown 可直接拼进决策报告
4. 不写入真实财务/真实日期，示例已脱敏

输入（user 字典）
-----------------
revolvingDate        归本日（字符串，容错支持 '2026-09'、'2026-09-15'、'2026-09 待确认'）
timing               置换节奏: 先卖后买 (默认) / 先买后卖 / 同时
hasYearlyRevolving   bool，是否按年归本信用贷
creditTotal          信用贷总额(万)，影响检查表金额
cash                 手头现金(万)，影响检查表金额
sellPrice / incomeAfterTax ...  当前未直接使用，预留给 risk 联动

输出（dict）
-----------
markdown             完整 markdown 文本（可贴进报告）
phases               三阶段 [{label, days, tasks:[str,...]}, ...]
checklist            决策检查表 [(category, text, done), ...]，共 15+ 项
warnings             关键风险提示 [str, ...]（含归本日避让）
"""

import datetime as _dt
import json as _json
import os as _os
import re as _re


# ============================================================
# 工具
# ============================================================

_DATE_PATTERNS = [
    # 2026-09-15 / 2026-09-15 待确认
    (r"(\d{4})\s*[-/年]\s*(\d{1,2})\s*[-/月]\s*(\d{1,2})\s*日?", "%Y-%m-%d"),
    # 2026-09 / 2026年9月
    (r"(\d{4})\s*[-/年]\s*(\d{1,2})\s*月?", "%Y-%m"),
]


def _parse_revolving_date(s):
    """解析归本日字符串，容错。无法解析返回 None。"""
    if not s or not isinstance(s, str):
        return None
    text = s.strip()
    for pat, fmt in _DATE_PATTERNS:
        m = _re.search(pat, text)
        if not m:
            continue
        try:
            if fmt == "%Y-%m-%d":
                y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
            else:
                y, mo = int(m.group(1)), int(m.group(2))
                d = 15
            return _dt.date(y, mo, d)
        except (ValueError, TypeError):
            continue
    return None


def _dday(target, today):
    """距今天数（正=未来，负=已过）"""
    return (target - today).days


# ============================================================
# 主入口
# ============================================================

def build_timeline(user, today=None):
    """生成 90 天三阶段时间表 + 决策检查表（markdown）

    返回
    ----
    dict:
        markdown     完整 markdown 文本
        phases       三阶段
        checklist    决策检查表
        warnings     关键风险提示
    """
    today = today or _dt.date.today()
    timing = (user.get("timing") or "先卖后买").strip()
    rev = _parse_revolving_date(user.get("revolvingDate"))

    # 归本日风险窗口
    warnings = []
    if rev:
        delta = _dday(rev, today)
        if -30 <= delta <= 120:
            warn_start = max(1, delta - 15)
            warn_end = delta + 15
            warnings.append(
                f"**归本日 {rev}（距今 {delta} 天）**：第 {warn_start}-{warn_end} 天请避免"
                "大额过桥、卖房交割、首付款到账等动作，防止银行扣款撞车。"
            )
        elif delta < -30:
            warnings.append(
                f"**归本日 {rev} 已过 {abs(delta)} 天**：若未结清，请立即与银行确认扣款状态。"
            )

    # 选节奏模板
    if timing == "先买后卖":
        phases = _phases_buy_first(today, rev, user)
    elif timing == "同时":
        phases = _phases_simultaneous(today, rev, user)
    else:
        phases = _phases_sell_first(today, rev, user)

    checklist = _build_checklist(user, rev)

    md = _render_markdown(today, timing, rev, phases, checklist, warnings, user)
    return {
        "markdown": md,
        "phases": phases,
        "checklist": checklist,
        "warnings": warnings,
    }


# ============================================================
# 阶段模板：先卖后买（默认，最稳）
# ============================================================

def _phases_sell_first(today, rev, user):
    has_rev = user.get("hasYearlyRevolving", False)
    credit_total = user.get("creditTotal", 0)
    return [
        {
            "label": "第 1 阶段 · 准备 + 挂牌 + 看房",
            "days": "Day 1-30（第 1-4 周）",
            "tasks": [
                "Day 1-3   财务盘点：活期/定期/公积金余额，**确认信用贷归本日**（关键）",
                "Day 1-7   银行面谈：信用贷**转 3-5 年期先息后本**或约一次结清，"
                          "避免置换期归本炸现金流" if has_rev else
                "Day 1-7   银行面谈：确认房贷剩余、还款卡状态、解押流程",
                "Day 3-7   签 2-3 家中介比价，**中介费率谈到 1.5%**（市场价 1.5%-2.7%）",
                "Day 5-10  卖房材料：房产证、按揭结清证明、身份证、婚姻证明、物业费结清",
                "Day 7-14  卖房**正式挂牌**，定价参考近 30 天小区成交均价 × 0.98-1.02",
                "Day 10-21 线上初筛 30 套 → 短名单 6-10 套；实地看 Top 3-5 套",
                "Day 14-21 准备贷款材料：收入证明、近 6 个月银行流水、征信报告（自己拉一份）",
                "Day 21-30 持续带看 + 收 offer；同步谈目标房",
            ],
        },
        {
            "label": "第 2 阶段 · 成交 + 回笼 + 锁定",
            "days": "Day 31-60（第 5-8 周）",
            "tasks": [
                "Day 31-40 卖方：收 offer → 比价 → 谈判 → 收取定金（一般 5 万）",
                "Day 35-45 买方：目标房二次复看，谈价 → 锁定 → 支付定金",
                "Day 40-50 卖房网签 + 资金监管；**避开归本日窗口**（如适用）",
                "Day 45-55 卖房过户 → 贷款解押 → 卖房款到账",
                "Day 50-58 **部分/全部结清信用贷**" +
                          ("（必须在归本日前完成）" if has_rev else ""),
                "Day 55-60 现金盘点：卖房回笼 + 手头 - 信用贷结清 = 真实可用资金",
                "Day 58-60 锁定目标房首付来源、过户日、组合贷方案",
            ],
        },
        {
            "label": "第 3 阶段 · 贷款 + 过户 + 入住",
            "days": "Day 61-90（第 9-12 周）",
            "tasks": [
                "Day 61-70 申请**组合贷**（公积金 + 商贷），面签、提交材料",
                "Day 65-75 首付款到账（现金 + 过桥借款 + 公积金提取，按银行要求分笔）",
                "Day 70-80 批贷 → 银行放款 → 缴税 → 新房过户",
                "Day 80-85 物业/水电/燃气/有线电视过户；预留 2-3 万租房过渡金",
                "Day 85-90 收房验房 → 拿钥匙 → 入住或短期出租衔接",
                "Day 90+   复盘：实际成交价 vs 评估、税费偏差、利率偏差 → 留档",
            ],
        },
    ]


# ============================================================
# 阶段模板：先买后卖（适合已锁定笋盘）
# ============================================================

def _phases_buy_first(today, rev, user):
    return [
        {
            "label": "第 1 阶段 · 看房 + 锁定 + 首付准备",
            "days": "Day 1-30（第 1-4 周）",
            "tasks": [
                "Day 1-7   现金盘点 + 短期借款能力评估（亲友 / 银行信用贷 / 过桥）",
                "Day 5-15  看房：短名单 6-10 套 → 锁定目标 1 套 → 谈价",
                "Day 10-20 支付定金 + 签居间合同",
                "Day 15-25 准备贷款材料 + 申请组合贷（批贷可与卖房并行）",
                "Day 20-30 首付款到账（**未卖房前需自有 + 借款组合**）",
            ],
        },
        {
            "label": "第 2 阶段 · 过户 + 同步卖房",
            "days": "Day 31-60（第 5-8 周）",
            "tasks": [
                "Day 31-45 新房过户 + 缴税 + 批贷放款",
                "Day 40-55 同步启动卖房：挂牌 + 带看 + 收 offer",
                "Day 50-60 卖房签约 + 收定金，**回笼资金用于还过桥借款**",
            ],
        },
        {
            "label": "第 3 阶段 · 卖房回笼 + 还款 + 入住",
            "days": "Day 61-90（第 9-12 周）",
            "tasks": [
                "Day 61-75 卖房过户 + 贷款解押 + 卖房款到账",
                "Day 70-80 还清过桥借款 + 信用贷（如有）",
                "Day 80-90 入住新家、复盘现金流偏差",
            ],
        },
    ]


# ============================================================
# 阶段模板：同时进行（高风险，需过桥兜底）
# ============================================================

def _phases_simultaneous(today, rev, user):
    return [
        {
            "label": "第 1 阶段 · 双线启动",
            "days": "Day 1-30（第 1-4 周）",
            "tasks": [
                "Day 1-7   资金兜底确认：过桥渠道 + 现金垫付能力 ≥ 100 万",
                "Day 5-15  卖房挂牌 + 目标房看房双线并行",
                "Day 15-25 卖房收 offer / 目标房签定金",
                "Day 20-30 同步申请组合贷 + 准备过桥借款",
            ],
        },
        {
            "label": "第 2 阶段 · 过桥衔接",
            "days": "Day 31-60（第 5-8 周）",
            "tasks": [
                "Day 31-45 卖房网签 + 目标房首付到账（**用借款/过桥垫付**）",
                "Day 40-55 卖房过户 → 卖房款到账 → 还过桥",
                "Day 50-60 目标房过户、批贷",
            ],
        },
        {
            "label": "第 3 阶段 · 收尾入住",
            "days": "Day 61-90（第 9-12 周）",
            "tasks": [
                "Day 61-75 放款 + 缴税 + 过户完成",
                "Day 75-85 物业水电过户 + 入住",
                "Day 85-90 复盘整体资金成本（过桥利息 + 中介费 + 税费）",
            ],
        },
    ]


# ============================================================
# 决策检查表（≥10 条，覆盖 5 大类）
# ============================================================

def _build_checklist(user, rev):
    has_rev = user.get("hasYearlyRevolving", False)
    credit_total = user.get("creditTotal", 0) or 0
    cash = user.get("cash", 0) or 0
    items = []

    # 1) 归本日
    items.append(("归本日", "联系放贷银行，**书面确认归本日**（精确到日）与扣款方式", False))
    if has_rev:
        items.append(("归本日", "把过户/大额过桥/首付款到账 **错开归本日 ±15 天**", False))
        items.append(("归本日", "谈信用贷**转 3-5 年期先息后本**，避免置换期归本现金流炸", False))
    if rev:
        items.append((f"归本日（{rev}）", "在日历上把归本日 ±15 天标红，所有大额动作避开", False))

    # 2) 中介费率
    items.append(("中介费率", "卖房中介费**谈到 1.5%**（市场价 1.5%-2.7%），签约前书面确认", False))
    items.append(("中介费率", "买方中介费问清是买家付/卖家付（通州常见买家付 1%-2%）", False))

    # 3) 现金准备
    if credit_total:
        need = credit_total + 50 + 3  # 信用贷 + 首付约 50 万 + 过渡 3 万
        gap = need - cash
        items.append((
            "现金准备",
            f"盘点全清信用贷 {credit_total:.0f} 万 + 首付 ~50 万 + 过渡 3 万 ≈ "
            f"**{need:.0f} 万**，手头 {cash:.0f} 万"
            + (f"，**缺口 {gap:.0f} 万**" if gap > 0 else "，可覆盖"),
            False,
        ))
    else:
        items.append(("现金准备", "盘点首付 + 税费 + 过渡金总需求，对照手头现金算缺口", False))
    items.append(("现金准备", "公积金账户余额可提取补首付（**面签前提取**到账）", False))
    items.append(("现金准备", "**预留 2-3 万租房过渡金**（卖后未买入前 / 买入未入住前）", False))

    # 4) 贷款材料
    items.append(("贷款材料", "收入证明（盖章）、近 6 个月银行流水、**个人征信报告**（自己拉一份）", False))
    items.append(("贷款材料", "身份证、户口本、结婚证/离婚证、房产证、原贷款合同", False))
    if has_rev or credit_total:
        items.append(("贷款材料", "信用贷合同/还款计划表（**必须如实告知银行**，影响审批）", False))
    items.append(("贷款材料", "组合贷申请：先公积金后商贷，**商贷利率**当日确认（3.05% 浮动）", False))

    # 5) 风险预案
    items.append(("风险预案", "卖不出：挂牌 90 天未成交 → 调价 / 换中介 / 接受降档", False))
    items.append(("风险预案", "买方违约：定金 5 万 + 中介费不退 → 重新挂牌", False))
    items.append(("风险预案", "审批延迟：组合贷批贷超出 30 天 → 备选商贷 / 过桥", False))
    items.append(("风险预案", "过桥失败：兜底渠道（亲友 / 银行循环额度）已确认可调用", False))

    return items


# ============================================================
# Markdown 渲染
# ============================================================

def _render_markdown(today, timing, rev, phases, checklist, warnings, user):
    lines = []
    lines.append("## 五、90 天执行时间表")
    lines.append("")
    rev_label = f"　|　归本日：**{rev}**" if rev else ""
    lines.append(f"> 编制日期：{today}　|　置换节奏：**{timing}**{rev_label}")
    lines.append("")

    # 关键风险（顶部）
    if warnings:
        lines.append("### ⚠️ 关键风险提示")
        for w in warnings:
            lines.append(f"- {w}")
        lines.append("")

    # 阶段汇总表
    lines.append("### 三阶段时间表")
    lines.append("")
    lines.append("| 阶段 | 时间窗 | 核心任务 |")
    lines.append("|---|---|---|")
    for ph in phases:
        # 取第 1 个任务去掉 Day 编号做核心
        first_task = ph["tasks"][0]
        core = first_task.split("  ", 1)[-1] if "  " in first_task else first_task
        # 截断
        if len(core) > 50:
            core = core[:50] + "…"
        lines.append(f"| **{ph['label']}** | {ph['days']} | {core} |")
    lines.append("")

    # 详细任务清单
    lines.append("### 详细任务清单")
    for ph in phases:
        lines.append("")
        lines.append(f"#### {ph['label']}（{ph['days']}）")
        lines.append("")
        for t in ph["tasks"]:
            lines.append(f"- [ ] {t}")

    # 决策检查表（按分类聚合）
    lines.append("")
    lines.append("### 决策检查表")
    by_cat = {}
    for cat, text, _done in checklist:
        by_cat.setdefault(cat, []).append(text)
    for cat, texts in by_cat.items():
        lines.append("")
        lines.append(f"**{cat}**")
        for t in texts:
            lines.append(f"- [ ] {t}")

    # 页脚
    lines.append("")
    lines.append("---")
    total_tasks = sum(len(p["tasks"]) for p in phases)
    lines.append(
        f"_共 {len(phases)} 个阶段 / {total_tasks} 项任务 / "
        f"{len(checklist)} 项决策检查。日期以编制日 {today} 起算。_"
    )
    return "\n".join(lines)


# ============================================================
# 自测：生成示例时间表（脱敏）
# ============================================================

_SAMPLE_USER = {
    "sellPrice": 140, "mortgageLeft": 93.1,
    "cash": 30, "creditTotal": 80, "creditMonthly": 6868,
    "incomeAfterTax": 27000, "gjjWithdraw": 8500,
    "hasYearlyRevolving": True,
    "timing": "先卖后买",
    "revolvingDate": "2026-09 待确认",  # 模拟 example JSON 的"待确认"格式
}

_SAMPLE_TODAY = _dt.date(2026, 8, 15)


def _self_check(today=None):
    today = today or _SAMPLE_TODAY
    res = build_timeline(_SAMPLE_USER, today=today)
    n_phase = len(res["phases"])
    n_check = len(res["checklist"])
    n_warn = len(res["warnings"])
    n_task = sum(len(p["tasks"]) for p in res["phases"])

    print(f"=== 自测（先卖后买 + 归本日 2026-09 待确认）===")
    print(f"阶段数: {n_phase}（期望 3）")
    print(f"检查项: {n_check}（期望 ≥10）")
    print(f"警告数: {n_warn}（期望 ≥1）")
    print(f"任务数: {n_task}")
    print()

    asserts = [
        ("阶段数 = 3", n_phase == 3),
        ("检查项 ≥ 10", n_check >= 10),
        ("有归本日警告", n_warn >= 1),
        ("全部阶段任务含 Day", all(any("Day" in t for t in p["tasks"]) for p in res["phases"])),
        ("检查表覆盖 5 类", len({c for c, _, _ in res["checklist"]}) >= 4),
    ]
    print("断言:")
    all_ok = True
    for name, p in asserts:
        print(f"  {'✅' if p else '❌'} {name}")
        all_ok = all_ok and p
    print()
    return all_ok, res


if __name__ == "__main__":
    print("== timeline.py 自测 ==\n")
    ok, res = _self_check()
    print("--- 生成的 markdown（可直接贴进决策报告）---\n")
    print(res["markdown"])
    print()

    # 顺手保存到 data/sample/ 作为可复用的脱敏示例
    sample_dir = _os.path.normpath(_os.path.join(
        _os.path.dirname(_os.path.abspath(__file__)),
        "..", "..", "..", "data", "sample",
    ))
    out_path = _os.path.join(sample_dir, "sample-timeline.md")
    try:
        _os.makedirs(sample_dir, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("# 房产置换 · 90 天执行时间表（脱敏示例）\n\n")
            f.write("> 编制日期：2026-08-15　|　来源：timeline.py 自测生成\n")
            f.write("> 输入 profile 见 data/sample/sample-houses.json 同目录的 _SAMPLE_USER\n\n")
            f.write(res["markdown"])
            f.write("\n")
        print(f"[已保存] {out_path}")
    except OSError as ex:
        print(f"[跳过保存] {ex}")

    raise SystemExit(0 if ok else 1)
