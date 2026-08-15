# -*- coding: utf-8 -*-
"""
house-swap 风险评估模块 · 4 大风险检查 + markdown 雷达
配套 engine_py.py (Python) / web/engine.js (JS)；纯 Python3 标准库

调用约定：
    from risk import check, render_markdown
    risks = check(user, finance)        # user/user_profile, finance/finance_calc 输出
    print(render_markdown(risks))

约定字段（user）：
    revolving: bool                      # 信用贷是否"按年归本再贷"
    creditLeft: float (万)               # 信用贷剩余未结清金额；缺省视为 0
    creditMonthly: float (元)            # 信用贷月供
    cash: float (万)                     # 手头现金
    borrowPower: float (万)              # 短期可借款能力
    timing: str in {"先卖后买","先买后卖","同时","未知"/缺省}
    revolvingDate: str                   # 归本日提示（如 "2026-09 待确认"）

约定字段（finance = finance_calc 输出）：
    rows[300].gap: float (万)             # 300 万目标缺口
    monthly: float (元)                  # 置换后月供
    monthlyRatio: float (%)              # 月供占可支配比
    keepCreditMonthly / keepCreditRatio: 含信用贷的版本
"""
import json
from datetime import date

SEV_RED = "🔴"
SEV_ORANGE = "🟠"
SEV_YELLOW = "🟡"
SEV_GREEN = "🟢"


def _sev_rank(sev):
    return {SEV_RED: 3, SEV_ORANGE: 2, SEV_YELLOW: 1, SEV_GREEN: 0}.get(sev, -1)


# ---------- 1. 信用贷"按年归本再贷" ----------
def check_revolving(user):
    revolving = bool(user.get("revolving") or user.get("hasYearlyRevolving"))
    credit_left = float(user.get("creditLeft") or 0)
    credit_monthly = float(user.get("creditMonthly") or 0)
    date_hint = user.get("revolvingDate") or "待确认（联系银行）"

    if not revolving:
        return {
            "name": "归本炸弹",
            "severity": SEV_GREEN,
            "triggered": False,
            "trigger": "信用贷无按年归本条款",
            "detail": f"信用贷剩余 {credit_left:.1f} 万 / 月供 {credit_monthly:.0f} 元；无年度归本压力。",
            "advice": "维持当前还款节奏，置换前再次复核贷款合同条款。",
        }

    # revolving=True 且未结清（剩余>0）→ 触发归本炸弹
    if credit_left > 0:
        return {
            "name": "归本炸弹",
            "severity": SEV_RED,
            "triggered": True,
            "trigger": f"信用贷按年归本再贷，剩余 {credit_left:.1f} 万未结清",
            "detail": (
                f"年度需一次性归本约 {credit_left:.0f} 万并通过续贷审批；"
                f"若现金流紧张或银行压降额度，将被迫低价卖房或过桥垫资。"
                f"归本日：{date_hint}。"
            ),
            "advice": (
                "1) 提前 60 天与银行确认续贷额度/利率；"
                "2) 准备 ≥ 归本金额的过桥资金或 T+0 赎楼；"
                "3) 若续贷不确定，先结清再置换（牺牲资金周转）。"
            ),
        }

    # revolving=True 但已结清（剩余=0）→ 黄色提示
    return {
        "name": "归本炸弹",
        "severity": SEV_YELLOW,
        "triggered": False,
        "trigger": "历史曾有按年归本条款，本次已结清",
        "detail": f"已结清原 {credit_left:.1f} 万信用贷；下一笔贷款避免同结构。",
        "advice": "新办贷款优先选 3-5 年期等额本息，规避年度归本再贷风险。",
    }


# ---------- 2. 资金悖论 ----------
def check_paradox(user, finance):
    cash = float(user.get("cash") or 0)
    borrow_power = float(user.get("borrowPower") or 0)
    # finance.rows[300].gap 是 300 万目标的缺口（万）
    gap = float(finance.get("rows", {}).get(300, {}).get("gap", 0))
    credit_total = float(user.get("creditTotal") or 0)
    credit_left = float(user.get("creditLeft") or 0)

    # 可用 = 手头现金 + 借款能力（不含信用贷再贷，信用贷已算入 creditTotal）
    coverable = cash + borrow_power

    if gap <= 0:
        surplus = -gap
        return {
            "name": "资金悖论",
            "severity": SEV_GREEN,
            "triggered": False,
            "trigger": f"300 万目标资金盈余 {surplus:.1f} 万" if surplus > 0 else "300 万目标资金刚好覆盖",
            "detail": f"资金可覆盖，无需额外借款。",
            "advice": "保留 3-6 月月供的应急金后即可推进。",
        }

    if gap <= cash:
        sev = SEV_GREEN
        msg = f"缺口 {gap:.1f} 万 ≤ 手头现金 {cash:.1f} 万"
        advice = "现金充裕，可直接全清信用贷 + 首付 + 税费。"
    elif gap <= coverable:
        sev = SEV_ORANGE
        msg = f"缺口 {gap:.1f} 万 > 现金 {cash:.1f} 万，但 ≤ 现金+借款能力 {coverable:.1f} 万"
        advice = "需动用短期借款或过桥；建议先确认借款额度与利率，再签买房合同。"
    else:
        sev = SEV_RED
        msg = f"缺口 {gap:.1f} 万 > 现金+借款能力 {coverable:.1f} 万"
        advice = (
            "1) 降低目标总价至 260-280 万；"
            "2) 或先提升手头现金（缩减开支/提前回收理财）；"
            "3) 或先卖后买释放流动性。"
        )

    return {
        "name": "资金悖论",
        "severity": sev,
        "triggered": sev in (SEV_RED, SEV_ORANGE),
        "trigger": msg,
        "detail": (
            f"目标 300 万需一次性支出：信用贷结清 {credit_left:.1f} 万 + "
            f"首付 + 税费 ≈ 缺口 {gap:.1f} 万；"
            f"手头现金 {cash:.1f} 万 + 借款能力 {borrow_power:.1f} 万 = 可动用 {coverable:.1f} 万。"
        ),
        "advice": advice,
    }


# ---------- 3. DTI（月供占可支配） ----------
def check_dti(finance):
    ratio = float(finance.get("monthlyRatio") or 0)
    keep_ratio = float(finance.get("keepCreditRatio") or ratio)
    monthly = float(finance.get("monthly") or 0)
    keep_monthly = float(finance.get("keepCreditMonthly") or monthly)
    disposable = float(finance.get("disposable") or 0)

    if ratio > 50:
        sev, band = SEV_RED, "高危"
    elif ratio > 40:
        sev, band = SEV_ORANGE, "警戒"
    elif ratio > 30:
        sev, band = SEV_YELLOW, "注意"
    else:
        sev, band = SEV_GREEN, "健康"

    # 若含信用贷版本突破下一档
    if keep_ratio > 50 and ratio <= 50:
        sev, band = SEV_RED, "高危（含信用贷）"
    elif keep_ratio > 40 and ratio <= 40:
        sev, band = SEV_ORANGE, "警戒（含信用贷）"

    return {
        "name": "DTI 月供压力",
        "severity": sev,
        "triggered": sev in (SEV_RED, SEV_ORANGE),
        "trigger": f"置换后月供 {monthly:.0f} 元 / 可支配 {disposable:.0f} 元 = {ratio:.1f}%（{band}）",
        "detail": (
            f"不含信用贷：{monthly:.0f} 元 ({ratio:.1f}%)；"
            f"含信用贷：{keep_monthly:.0f} 元 ({keep_ratio:.1f}%)。"
            f"阈值：≤30% 健康 / 30-40% 注意 / 40-50% 警戒 / >50% 高危。"
        ),
        "advice": _dti_advice(sev, ratio, keep_ratio),
    }


def _dti_advice(sev, ratio, keep_ratio):
    if sev == SEV_RED:
        return (
            "1) 立即下调总价档至 260 万或拉长贷款年限至 30 年；"
            "2) 优先结清信用贷（即便贴现过桥）以降低 DTI；"
            "3) 提升共同还款人收入证明。"
        )
    if sev == SEV_ORANGE:
        return (
            "1) 压缩总价至 280 万内或首付提到 30%；"
            "2) 提前部分还信用贷以降低 keep_ratio；"
            "3) 预留 6 个月月供的应急金。"
        )
    if sev == SEV_YELLOW:
        return "30-40% 区间属可承受上限，建议保留 3-6 月应急金，避免新增消费贷。"
    return "DTI 健康；保持当前收入与负债结构。"


# ---------- 4. 时间错配 ----------
def check_timing(user):
    timing = (user.get("timing") or "").strip() or "未知"
    sell_days = user.get("sellDays")  # 预计卖房周期（天），可选
    buy_days = user.get("buyDays")

    # 先买后卖：典型高风险路径
    if "先买后卖" in timing:
        return {
            "name": "时间错配",
            "severity": SEV_RED,
            "triggered": True,
            "trigger": "策略 = 先买后卖",
            "detail": (
                "需同时承担两套房贷月供 + 首付资金占用；"
                "若旧房滞销，将被迫降价或断供。"
                + (f"预计卖房周期 {sell_days} 天。" if sell_days else "")
            ),
            "advice": (
                "1) 旧房挂牌价低于小区均价 5% 以加速去化；"
                "2) 准备 ≥ 12 个月双倍月供的过桥资金；"
                "3) 与买家约定 ≥ 60 天交付，给自己留搬家/结清窗口。"
            ),
        }

    if "先卖后买" in timing:
        return {
            "name": "时间错配",
            "severity": SEV_GREEN,
            "triggered": False,
            "trigger": "策略 = 先卖后买",
            "detail": (
                "流动性风险最低；卖房回款后再支付首付与装修。"
                + (f"预计卖房周期 {sell_days} 天。" if sell_days else "")
            ),
            "advice": "过渡期租房 1-3 个月，避免连环单时间冲突。",
        }

    if "同时" in timing or "连环" in timing:
        return {
            "name": "时间错配",
            "severity": SEV_ORANGE,
            "triggered": True,
            "trigger": "策略 = 同时买卖（连环单）",
            "detail": "需精确对齐两个合同节点；任一环节延期将导致违约金或资金链断裂。",
            "advice": (
                "1) 合同明确违约责任与宽限期；"
                "2) 留 ≥ 30 天交付缓冲；"
                "3) 提前与银行/中介确认资金到账节点。"
            ),
        }

    # 未知
    return {
        "name": "时间错配",
        "severity": SEV_YELLOW,
        "triggered": False,
        "trigger": "未指定买卖顺序",
        "detail": "未在 user_profile 中声明 timing，无法评估连环单风险。",
        "advice": "在 user_profile.json 补 'timing' 字段（先卖后买/先买后卖/同时）。",
    }


# ---------- 汇总 ----------
def check(user, finance):
    """4 大风险检查；返回 list，按严重度倒序"""
    risks = [
        check_revolving(user),
        check_paradox(user, finance),
        check_dti(finance),
        check_timing(user),
    ]
    risks.sort(key=lambda r: (-_sev_rank(r["severity"]), r["name"]))
    return risks


def render_markdown(risks):
    """markdown 风险雷达：可粘贴进决策报告"""
    lines = ["## 风险雷达", ""]
    # 概览表
    lines.append("| 风险 | 严重度 | 是否触发 | 关键信号 |")
    lines.append("|---|---|---|---|")
    for r in risks:
        lines.append(f"| {r['name']} | {r['severity']} | {'是' if r['triggered'] else '否'} | {r['trigger']} |")
    lines.append("")
    # 详情
    lines.append("### 风险详情")
    lines.append("")
    for r in risks:
        lines.append(f"#### {r['severity']} {r['name']}")
        lines.append("")
        lines.append(f"- **触发条件**：{r['trigger']}")
        lines.append(f"- **明细**：{r['detail']}")
        lines.append(f"- **缓解建议**：{r['advice']}")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    # 脱敏样例（来自 config/user_profile.example.json 的同结构扰动版）
    sample_user = {
        "revolving": True,            # 按年归本再贷 → 触发归本炸弹🔴
        "creditLeft": 60.0,           # 60 万未结清
        "creditMonthly": 6868,
        "cash": 30,
        "borrowPower": 0,
        "creditTotal": 80,
        "revolvingDate": "2026-09 待确认",
        "timing": "先卖后买",
    }
    sample_finance = {
        "monthly": 10532,
        "monthlyRatio": 29.7,
        "keepCreditMonthly": 17400,
        "keepCreditRatio": 49.0,
        "disposable": 35500,
        "rows": {
            300: {"down": 45, "fee": 6, "totalNeed": 131, "gap": 56}
        },
    }
    risks = check(sample_user, sample_finance)
    print(render_markdown(risks))
    print("---JSON---")
    print(json.dumps([{"name": r["name"], "severity": r["severity"], "triggered": r["triggered"]} for r in risks], ensure_ascii=False, indent=2))