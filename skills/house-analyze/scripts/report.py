# -*- coding: utf-8 -*-
"""
house-swap · 决策报告生成器（Python）
====================================

输入: user(引擎口径字典) + policy + 房源列表 → 输出可打印 markdown 决策报告
结构: 结论摘要(含可行性结论卡) → 资金测算 → 风险 → 房源对比 → 90天计划 → 免责

口径基准: docs/决策引擎-spec.md 与合并修正版报告（月供10,532 / 缺口56 / 指数40）
铁律: 公式一律调 engine_py（唯一实现），本文件不做任何计算口径的再实现
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine_py import (
    composite_score, finance_calc, feasibility_index, three_plans, pmt,
)

DISCLAIMER = (
    "本报告输出为**估算参考**，不构成投资/贷款建议。"
    "价格、利率、税费以实际挂牌、银行审批、税务征收为准；"
    "政策口径见 config/policy.json（附更新日期），面签前请再核实。"
)

# 结论卡（spec §3）
def _verdict(idx):
    if idx >= 80:
        return "✅ 强烈建议换"
    if idx >= 60:
        return "🟡 可换，需准备"
    return "🔴 暂缓"


def _norm_house(h):
    """兼容脱敏样例的中文字段名 → 引擎字段名"""
    return {
        "id": h.get("id"),
        "name": h.get("name") or h.get("小区") or "",
        "biz": h.get("biz") or h.get("商圈") or "",
        "layout": h.get("layout") or h.get("户型") or "",
        "area": h.get("area") or h.get("面积") or 0,
        "orient": h.get("orient") or h.get("朝向") or "",
        "floor": h.get("floor") or h.get("楼层") or "",
        "elevator": h.get("elevator") or h.get("电梯") or "",
        "price": h.get("price") or h.get("挂牌价万") or 0,
        "unit": h.get("unit") or h.get("单价元平") or 0,
        "avgUnit": h.get("avgUnit") or h.get("小区均价元平") or 0,
        "years": h.get("years") or h.get("年限") or "",
        "age": h.get("age") if h.get("age") is not None else h.get("楼龄"),
        "structure": h.get("structure") or h.get("建筑结构") or "",
        "metroM": h.get("metroM") if h.get("metroM") is not None else h.get("地铁米"),
        "listDays": h.get("listDays") if h.get("listDays") is not None else h.get("挂牌天数"),
        "parking": h.get("parking") or h.get("车位") or "",
    }


def build_report(user, policy, houses, top_n=6, today=""):
    """生成决策报告 markdown 字符串"""
    f = finance_calc(user, policy)
    idx = feasibility_index(f, user)
    plans = three_plans(300, f, user)
    hs = [_norm_house(h) for h in houses]
    scored = sorted(
        ((composite_score(h), h) for h in hs if h["price"] > 0),
        key=lambda t: t[0]["composite"], reverse=True,
    )
    g300 = f["rows"][300]["gap"]
    gjj_loan = min(max(user.get("gjjMax", 120), 0), 255)
    sd_loan = 255 - gjj_loan
    gjj_m = round(pmt(policy["利率"]["公积金首套"] / 100, 30, gjj_loan * 10000))
    sd_m = round(pmt(policy["利率"]["商贷首套"] / 100, 30, sd_loan * 10000))

    L = []
    L.append("# 房产置换决策报告")
    L.append("")
    L.append(f"> 编制：{today} ｜ 引擎：docs/决策引擎-spec.md（JS/Python 双实现一致）")
    L.append("")

    # ---- 一、结论摘要 ----
    L.append("## 一、结论摘要")
    L.append("")
    L.append(f"### 综合可行性指数：{idx} / 100 —— {_verdict(idx)}")
    L.append("")
    L.append("| 维度 | 结论 |")
    L.append("|---|---|")
    L.append(f"| 可支配收入 | {f['disposable']:,} 元/月 |")
    L.append(f"| 可用资金 | {f['available']:.1f} 万（卖房回笼{f['cashBack']:.1f} + 现金{user['cash']}） |")
    L.append(f"| 300万档资金缺口 | **{g300} 万** |")
    L.append(f"| 置换后月供（信用贷结清） | **{f['monthly']:,} 元/月**，占可支配 {f['monthlyRatio']}% |")
    L.append(f"| 若保留信用贷 | {f['keepCreditMonthly']:,} 元/月，占 {f['keepCreditRatio']}% |")
    L.append("")
    if idx >= 80:
        L.append("**结论**：资金与月供双达标，可按计划推进置换。")
    elif idx >= 60:
        L.append("**结论**：可行但需先解决资金缺口/借款安排，再启动置换。")
    else:
        L.append("**结论**：缺口为硬约束，建议先\"部分结清信用贷+降档总价\"，暂缓直接置换。")
    L.append("")

    # ---- 二、资金测算 ----
    L.append("## 二、资金测算（spec §2）")
    L.append("")
    L.append("### 2.1 卖房回笼")
    L.append("")
    L.append("| 项目 | 金额 |")
    L.append("|---|---|")
    L.append(f"| 成交价 | {user['sellPrice']} 万 |")
    L.append(f"| 中介费 {user.get('agentFee') or 0.015:.1%} | -{user['sellPrice'] * (user.get('agentFee') or 0.015):.1f} 万 |")
    L.append(f"| 增值税/个税 | -{user['sellPrice'] * ((user.get('taxVAT') or 0) + (user.get('taxIncome') or 0)):.1f} 万 |")
    L.append(f"| 还房贷剩余 | -{user['mortgageLeft']} 万 |")
    L.append(f"| **卖房净得/现金回笼** | **{f['net']:.1f} / {f['cashBack']:.1f} 万** |")
    L.append("")
    L.append("### 2.2 缺口情景表（全清信用贷 + 首付 + 税费2%）")
    L.append("")
    L.append("| 新房总价 | 首付 | 税费 | 总需求 | 缺口 |")
    L.append("|---|---|---|---|---|")
    for t in (300, 280, 260, 250):
        r = f["rows"][t]
        L.append(f"| {t}万 | {r['down']:.1f} | {r['fee']:.1f} | {r['totalNeed']:.1f} | **{r['gap']}** |")
    L.append("")
    L.append("### 2.3 置换后月供（300万贷255万 = 公积金 + 商贷，30年）")
    L.append("")
    L.append("| 项 | 月供 |")
    L.append("|---|---|")
    L.append(f"| 公积金 {gjj_loan}万 @{policy['利率']['公积金首套']}% | {gjj_m:,} 元 |")
    L.append(f"| 商贷 {sd_loan}万 @{policy['利率']['商贷首套']}% | {sd_m:,} 元 |")
    L.append(f"| **合计** | **{f['monthly']:,} 元（占 {f['monthlyRatio']}%）** |")
    L.append("")
    L.append("### 2.4 三方案（spec §5，预算300万）")
    L.append("")
    L.append("| 方案 | 总价 | 首付 | 月供 | 占可支配 |")
    L.append("|---|---|---|---|---|")
    for name in ("稳健", "平衡", "激进"):
        p = plans[name]
        L.append(f"| {name} | {p['price']}万 | {p['down']}万 | {p['monthly']:,}元 | {p['ratio']}% |")
    L.append("")

    # ---- 三、风险 ----
    L.append("## 三、风险提示")
    L.append("")
    if user.get("hasYearlyRevolving"):
        L.append("- 🔴 **按年归本信用贷 = 年度现金流炸弹**：置换必须避开归本窗口，或先结清/转长期。")
    if g300 > 0:
        L.append(f"- 🔴 **全清信用贷+首付缺口 {g300} 万是硬约束**：需部分结清/降档/借款过桥，非\"努力一下\"可解。")
    if f["keepCreditRatio"] > 40:
        L.append(f"- 🔴 **保留信用贷则月供占 {f['keepCreditRatio']}% 超红线**，审批与生活双失败。")
    elif f["keepCreditRatio"] > 30:
        L.append(f"- 🟠 保留信用贷月供占 {f['keepCreditRatio']}%，逼近红线，谨慎。")
    bad_tax = [h for h in hs if "满" not in (h["years"] or "")]
    if bad_tax:
        L.append(f"- 🟠 候选中 {len(bad_tax)} 套未满两年（增值税约5.3%，成本+10-16万）："
                 + "、".join(h["name"] or str(h["id"]) for h in bad_tax))
    old = [h for h in hs if h["age"] is not None and h["age"] > 30]
    if old:
        L.append(f"- 🟠 {len(old)} 套楼龄>30年，贷款受限，评分已按 spec 扣分。")
    L.append("- 🟡 中介费可谈（1.5%~2.7%），卖房净得差约1-2万；公积金余额可提取补首付。")
    L.append("")

    # ---- 四、房源对比 ----
    L.append("## 四、房源对比（双评分，spec §1）")
    L.append("")
    if scored:
        L.append(f"| 排名 | 小区 | 商圈 | 户型/面积 | 电梯 | 挂牌价 | 年限 | 市场/适配/综合 |")
        L.append("|---|---|---|---|---|---|---|---|")
        for i, (s, h) in enumerate(scored[:top_n], 1):
            L.append(
                f"| {i} | {h['name']} | {h['biz']} | {h['layout']}/{h['area']:g}㎡ "
                f"| {h['elevator']} | {h['price']:g}万 | {h['years']} "
                f"| {s['market']}/{s['fit']}/**{s['composite']}** |"
            )
        L.append("")
        L.append(f"> 共评 {len(scored)} 套，上表为综合分 Top{min(top_n, len(scored))}。")
    else:
        L.append("（无候选房源数据）")
    L.append("")

    # ---- 五、90天行动计划 ----
    L.append("## 五、90天行动计划")
    L.append("")
    L.append("- [ ] **第1-2周**：确认信用贷归本日+能否转长期；盘点现金与借款渠道")
    L.append("- [ ] **第1-2周**：按近30天成交口径挂牌卖房（中介费率谈到1.5%）")
    L.append("- [ ] **第1个月**：实地看 Top 房源短名单")
    L.append("- [ ] **第2个月**：卖房回笼 → 部分/全部结清信用贷 → 锁定目标总价档")
    L.append("- [ ] **第3个月**：申请组合贷（公积金+商贷）；预留租房过渡金2-3万")
    L.append("")

    # ---- 六、免责声明 ----
    L.append("## 六、免责声明")
    L.append("")
    L.append(DISCLAIMER)
    L.append("")
    return "\n".join(L)


# 脱敏样例（数值与 finance.py/engine_py.py 自测一致，已扰动）
_SAMPLE_USER = {
    "sellPrice": 140, "mortgageLeft": 93.1,
    "agentFee": 0.015, "taxVAT": 0, "taxIncome": 0,
    "cash": 30, "creditTotal": 80, "creditMonthly": 6868,
    "incomeAfterTax": 27000, "gjjWithdraw": 8500,
    "gjjMax": 120, "borrowPower": 0, "hasYearlyRevolving": True,
}
_SAMPLE_POLICY = {
    "首付": {"首套": 0.15},
    "利率": {"公积金首套": 2.6, "商贷首套": 3.05},
}
_SAMPLE_HOUSES = [
    {"id": "HS0001", "小区": "示例·北苑1区", "商圈": "通州北苑", "户型": "2室1厅1卫",
     "面积": 98.0, "朝向": "南", "楼层": "中楼层/24层", "电梯": "有",
     "挂牌价万": 270.9, "单价元平": 24092, "年限": "满五年"},
    {"id": "HS0003", "小区": "示例·果园3区", "商圈": "通州果园", "户型": "2室2厅1卫",
     "面积": 99.0, "朝向": "南", "楼层": "高楼层/18层", "电梯": "有",
     "挂牌价万": 244.2, "单价元平": 23811, "年限": "满五年"},
    {"id": "HS0005", "小区": "示例·梨园5区", "商圈": "通州梨园", "户型": "3室1厅1卫",
     "面积": 100.0, "朝向": "东南", "楼层": "中楼层/19层", "电梯": "有",
     "挂牌价万": 292.0, "单价元平": 27037, "年限": "满五年"},
    {"id": "HS0010", "小区": "示例·豆各庄10区", "商圈": "朝阳豆各庄", "户型": "2室1厅1卫",
     "面积": 85.0, "朝向": "南", "楼层": "高楼层/26层", "电梯": "有",
     "挂牌价万": 261.2, "单价元平": 25242, "年限": "未满两年"},
    {"id": "HS0013", "小区": "示例·果园13区", "商圈": "通州果园", "户型": "3室2厅2卫",
     "面积": 115.0, "朝向": "南", "楼层": "中楼层/7层", "电梯": "无",
     "挂牌价万": 340.0, "单价元平": 25236, "年限": "满五年"},
]


def main():
    ap = argparse.ArgumentParser(description="house-swap 决策报告生成器")
    ap.add_argument("--user", help="user_profile JSON（引擎口径）；缺省用脱敏样例")
    ap.add_argument("--policy", help="policy JSON；缺省用样例")
    ap.add_argument("--houses", help="房源 JSON 数组；缺省用脱敏样例")
    ap.add_argument("-o", "--out", help="输出 md 路径；缺省打印到 stdout")
    ap.add_argument("--top", type=int, default=6, help="房源对比 TopN（默认6）")
    args = ap.parse_args()

    user = json.load(open(args.user, encoding="utf-8")) if args.user else _SAMPLE_USER
    policy = json.load(open(args.policy, encoding="utf-8")) if args.policy else _SAMPLE_POLICY
    houses = json.load(open(args.houses, encoding="utf-8")) if args.houses else _SAMPLE_HOUSES

    import datetime
    md = build_report(user, policy, houses, top_n=args.top,
                      today=datetime.date.today().isoformat())
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fp:
            fp.write(md)
        print(f"已写出: {args.out}")
    else:
        print(md)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main()
    else:
        # 自检：样例报告必须锁定基准口径数字
        md = build_report(_SAMPLE_USER, _SAMPLE_POLICY, _SAMPLE_HOUSES, today="2026-08-15")
        checks = [
            ("月供10,532", "10,532" in md),
            ("月供占比29.7%", "29.7%" in md),
            ("300万缺口56", "| 300万 | 45.0 | 6.0 | 131.0 | **56** |" in md),
            ("可行性指数40→暂缓", "综合可行性指数：40 / 100 —— 🔴 暂缓" in md),
            ("归本炸弹提示", "按年归本信用贷" in md),
            ("未满二提示", "未满两年" in md),
            ("免责声明", "估算参考" in md),
            ("六章结构", all(f"## {s}" in md for s in
                          ("一、结论摘要", "二、资金测算", "三、风险提示",
                           "四、房源对比", "五、90天行动计划", "六、免责声明"))),
        ]
        for name, ok in checks:
            print(f"{'✅' if ok else '❌'} {name}")
        ok_all = all(ok for _, ok in checks)
        print(f"{sum(ok for _, ok in checks)}/{len(checks)} 通过")
        raise SystemExit(0 if ok_all else 1)
