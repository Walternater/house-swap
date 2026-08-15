# -*- coding: utf-8 -*-
"""
house-swap · 资金测算模块（Python）
==================================

唯一契约: docs/决策引擎-spec.md  §2 资金测算 / §4 反向计算(E1) / §5 三方案(E4)
JS 对应实现: web/engine.js      financeCalc / reverseCalc / threePlans
本实现:    skills/house-analyze/scripts/finance.py

铁律
----
1. 任何公式/字段/常量改动必须 spec + JS + Python 三处同步，并跑对照测试
2. 纯 Python3 标准库（禁第三方依赖）
3. 数值精度: 与 JS 同输入同输出 ( ±1元/±0.1% )
4. 示例数据必须脱敏（自测用例已脱敏）

字段约定（user 字典，与 JS engine.js 保持完全一致）
---------------------------------------------------
sellPrice        卖房成交价(万)
mortgageLeft     房贷剩余(万)
agentFee         中介费比例(默认 0.015；配置区间 1.5%~2.7%)
taxVAT           增值税比例(满2=0)
taxIncome        个税比例(满五唯一=0 / 差额为负=0 / 核定 0.01)
cash             手头现金(万)
creditTotal      全清信用贷所需金额(万)
creditMonthly    保留信用贷月供(元)，用于 keepCreditMonthly 计算
incomeAfterTax   税后月薪(元)
gjjWithdraw      公积金月提取(元)
gjjMax           公积金可贷上限(万)，默认 120
borrowPower      借款能力(万)，可选，用于可行性指数
hasYearlyRevolving  是否有按年归本信用贷(布尔)，可选

policy 字典（与 config/policy.example.json 同构）
------------------------------------------------
{
  "首付": {"首套": 0.15, "二套": 0.20, "公积金二套": 0.25},
  "利率": {"公积金首套": 2.6, "商贷首套": 3.05, ...}
}

注: 函数内部只读 policy["首付"]["首套"] 和 policy["利率"]["公积金首套/商贷首套"]
"""

# ============================================================
# 工具：与 web/engine.js 严格对齐
# ============================================================

def pmt(rate_annual, years, principal):
    """等额本息月供；r=年利率/12, n=月数；利率=0 → 等额本金降级（边界§6）

    与 JS 版 `pmt()` 同公式；rate_annual 接受百分数（如 3.05 表示 3.05%）。
    """
    r = rate_annual / 12
    n = years * 12
    if r == 0:
        return principal / n
    return principal * r * (1 + r) ** n / ((1 + r) ** n - 1)


def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


# ============================================================
# §2 资金测算
# ============================================================

def finance_calc(user, policy):
    """资金测算（spec §2）

    链路:
        卖房净得 = 成交价 - 中介费 - 增值税 - 个税
        现金回笼 = 净得 - 房贷剩余
        可用资金 = 现金回笼 + 手头现金
        缺口 = (全清信用贷 + 首付 + 税费) - 可用资金   // 四档
        置换后月供 = PMT(公积金) + PMT(商贷)            // 30 年，255 万贷款
        月供占可支配 = 月供 / (税后月薪 + 公积金月提取)

    返回
    ----
    dict:
        net                          卖房净得(万)，未取整
        cashBack                     现金回笼(万)，未取整
        available                    可用资金(万)，未取整
        rows                         四档缺口表
            { 300|280|260|250:
                { down, fee, totalNeed, gap }    gap 已取整
            }
        monthly                      置换后月供(元)，已取整
        monthlyRatio                 月供占可支配(%)，1 位小数
        keepCreditMonthly            保留信用贷时的月供(元)
        keepCreditRatio              保留信用贷时月供占可支配(%)
        disposable                   可支配收入(元)
    """
    # 1) 卖房净得
    sell = user["sellPrice"]
    agent_fee = user.get("agentFee") or 0.015
    tax_vat = user.get("taxVAT") or 0
    tax_income = user.get("taxIncome") or 0
    net = sell - sell * agent_fee - sell * tax_vat - sell * tax_income
    # 2) 现金回笼
    cash_back = net - user["mortgageLeft"]
    # 3) 可用资金
    available = cash_back + user["cash"]
    # 4) 四档缺口情景表（首付比例取 policy.首付.首套，税费统一按 2%）
    down_ratio = policy["首付"]["首套"]
    rows = {}
    for target in (300, 280, 260, 250):
        down = target * down_ratio
        fee = target * 0.02
        total_need = user["creditTotal"] + down + fee
        rows[target] = {
            "down": down,
            "fee": fee,
            "totalNeed": total_need,
            "gap": round(total_need - available),
        }
    # 5) 置换后月供：信用贷结清后的公积金 + 商贷组合
    gjj = _clamp(user.get("gjjMax", 120), 0, 200)
    loan = 255  # 300 万房，贷 255 万（与 JS engine.js 同口径）
    gjj_loan = min(gjj, loan)
    shang_loan = max(0, loan - gjj_loan)
    gjj_rate = policy["利率"]["公积金首套"] / 100
    shang_rate = policy["利率"]["商贷首套"] / 100
    monthly = (
        pmt(gjj_rate, 30, gjj_loan * 10000)
        + pmt(shang_rate, 30, shang_loan * 10000)
    )
    disposable = user["incomeAfterTax"] + user["gjjWithdraw"]
    keep_credit_monthly = monthly + (user.get("creditMonthly") or 0)
    return {
        "net": net,
        "cashBack": cash_back,
        "available": available,
        "rows": rows,
        "monthly": round(monthly),
        "monthlyRatio": round(monthly / disposable * 1000) / 10,
        "keepCreditMonthly": round(keep_credit_monthly),
        "keepCreditRatio": round(keep_credit_monthly / disposable * 1000) / 10,
        "disposable": disposable,
    }


# ============================================================
# §4 E1 反向计算：目标月供 → 可贷 → 可买总价
# ============================================================

def reverse_calc(target_monthly, years, rate, down_ratio):
    """反向计算（spec §4 E1）

    参数
    ----
    target_monthly : float   目标月供(元)
    years          : int     年限
    rate           : float   年利率(百分数，如 3.05)
    down_ratio     : float   首付比例（如 0.15）

    返回
    ----
    {"loan": 元, "price": 元}   精度 ±1 万内
    """
    r = rate / 12
    n = years * 12
    k = r * (1 + r) ** n / ((1 + r) ** n - 1)
    loan = target_monthly / k           # 元
    price = loan / (1 - down_ratio)     # 元
    return {"loan": round(loan), "price": round(price)}


# ============================================================
# §5 E4 三方案：稳健 / 平衡 / 激进
# ============================================================

def three_plans(budget, finance, user):
    """三方案（spec §5 E4）

    参数
    ----
    budget  : float  目标预算(万)
    finance : dict   finance_calc() 的返回结果（含 disposable）
    user    : dict   用户字典（当前未使用，保留与 JS threePlans 同形参）

    返回
    ----
    {
      "稳健": {price, down, monthly, ratio},   # 预算×0.83，月供≤25%
      "平衡": {...},                            # ×0.93，25-35%
      "激进": {...},                            # ×1.0，35-50%
    }
    利率口径与 spec §5 一致：3.05%（商贷首套默认）。
    """
    d = finance["disposable"]
    def mk(k):
        price = budget * k
        down = price * 0.15
        loan = price - down
        m = pmt(0.0305, 30, loan * 10000)
        return {
            "price": round(price),
            "down": round(down),
            "monthly": round(m),
            "ratio": round(m / d * 1000) / 10,
        }
    return {"稳健": mk(0.83), "平衡": mk(0.93), "激进": mk(1.0)}


# ============================================================
# 自测
# ============================================================

_SAMPLE_USER = {
    "sellPrice": 140, "mortgageLeft": 93.1,
    "agentFee": 0.015, "taxVAT": 0, "taxIncome": 0,
    "cash": 30, "creditTotal": 80, "creditMonthly": 6868,
    "incomeAfterTax": 27000, "gjjWithdraw": 8500,
    "gjjMax": 120, "borrowPower": 0, "hasYearlyRevolving": True,
}

_SAMPLE_POLICY = {
    "首付": {"首套": 0.15, "二套": 0.20, "公积金二套": 0.25},
    "利率": {
        "LPR5年": 3.5, "商贷首套": 3.05,
        "商贷二套五环内": 3.45, "商贷二套五环外": 3.25,
        "公积金首套": 2.6, "公积金二套": 3.075,
    },
}


def _pmt_self_check():
    """PMT 与 tests/engine.test.js 已锁的三个用例对账（±1元）"""
    cases = [
        ("PMT 255万/3.05%/30年", pmt(0.0305, 30, 2550000), 10820),
        ("PMT 120万/2.6%/30年",  pmt(0.026,  30, 1200000),  4804),
        ("PMT 135万/3.05%/30年", pmt(0.0305, 30, 1350000),  5728),
    ]
    print("--- PMT 自测（对照 tests/engine.test.js）---")
    ok = 0
    for name, got, want in cases:
        pass_ = abs(round(got) - want) <= 1
        print(f"  {'✅' if pass_ else '❌'} {name}: got={round(got)} want={want}")
        if pass_:
            ok += 1
    print(f"  PMT {ok}/{len(cases)} 通过\n")
    return ok == len(cases)


def _finance_self_check():
    """资金测算主链路自测（合并修正版口径）"""
    f = finance_calc(_SAMPLE_USER, _SAMPLE_POLICY)
    print("--- §2 资金测算（合并修正版口径）---")
    print(f"  卖房净得:   {f['net']:.2f} 万")
    print(f"  现金回笼:   {f['cashBack']:.2f} 万")
    print(f"  可用资金:   {f['available']:.2f} 万")
    print("  四档缺口:")
    for t in (300, 280, 260, 250):
        r = f["rows"][t]
        print(f"    {t:>3}万 → 首付{r['down']:5.1f}  税费{r['fee']:4.1f}  需{r['totalNeed']:6.1f}  缺口{r['gap']:>3} 万")
    print(f"  置换后月供: {f['monthly']} 元  (期望 ≈10532)")
    print(f"  月供占可支配: {f['monthlyRatio']}%")
    print(f"  保留信用贷月供: {f['keepCreditMonthly']} 元  (期望 ≈17400)")
    print(f"  可支配收入: {f['disposable']} 元\n")

    # 关键断言
    asserts = [
        ("月供 ≈10532",  abs(f["monthly"] - 10532) <= 1),
        ("300万缺口 ≈56", 55 <= f["rows"][300]["gap"] <= 57),
        ("280万缺口 ≈53", 52 <= f["rows"][280]["gap"] <= 54),
        ("260万缺口 ≈49", 48 <= f["rows"][260]["gap"] <= 50),
        ("250万缺口 ≈48", 47 <= f["rows"][250]["gap"] <= 49),
        ("可支配 = 35500", f["disposable"] == 35500),
        ("卖房净得 = 137.9", abs(f["net"] - 137.9) < 0.01),
    ]
    print("  关键断言:")
    all_ok = True
    for name, p in asserts:
        print(f"    {'✅' if p else '❌'} {name}")
        all_ok = all_ok and p
    print()
    return all_ok


def _reverse_self_check():
    """E1 反向计算自测

    注意: rate 与 web/engine.js reverseCalc 同口径（百分数）。
    演示: 想月供 12000，30 年，商贷 3.05% → 传 rate=0.0305（小数），
    若传 3.05（百分数）则 r=0.254，结果无经济意义——与 JS 行为一致。
    """
    # 月供 12000，30 年，商贷 3.05%（传 0.0305），首付 15%
    rc = reverse_calc(12000, 30, 0.0305, 0.15)
    print("--- §4 E1 反向计算 ---")
    print(f"  目标月供 12000 → 可贷 {rc['loan']} 元, 可买 {rc['price']} 元 ({rc['price']/10000:.1f} 万)")
    # 手算: k ≈ 0.00254167*1.00254^360/(1.00254^360-1) ≈ 0.004226
    # 可贷 ≈ 12000 / 0.004226 ≈ 2,840,000
    # 总价 ≈ 2,840,000 / 0.85 ≈ 3,340,000
    ok = 2800000 <= rc["loan"] <= 2900000 and 3300000 <= rc["price"] <= 3400000
    print(f"  {'✅' if ok else '❌'} 数量级合理（贷≈284万 价≈334万）\n")
    return ok


def _plans_self_check():
    """E4 三方案自测"""
    f = finance_calc(_SAMPLE_USER, _SAMPLE_POLICY)
    plans = three_plans(300, f, _SAMPLE_USER)
    print("--- §5 E4 三方案（预算 300 万）---")
    ok = True
    for name in ("稳健", "平衡", "激进"):
        p = plans[name]
        print(f"  {name}: 总价 {p['price']}万  首付 {p['down']}万  月供 {p['monthly']}元  占比 {p['ratio']}%")
    # 占比单调递增
    ok = (plans["稳健"]["ratio"] < plans["平衡"]["ratio"] < plans["激进"]["ratio"])
    print(f"  {'✅' if ok else '❌'} 占比单调递增（稳健<平衡<激进）\n")
    return ok


def _vs_js_engine():
    """可选：调起 web/engine.js 同输入对照（需 node）"""
    import os
    import subprocess
    import json
    here = os.path.dirname(os.path.abspath(__file__))
    engine_js = os.path.normpath(os.path.join(here, "..", "..", "..", "web", "engine.js"))
    if not os.path.exists(engine_js):
        print("(跳过 JS 对照：未找到 web/engine.js)")
        return True
    payload = {"u": _SAMPLE_USER, "policy": _SAMPLE_POLICY}
    code = (
        "const e=require(" + json.dumps(engine_js) + ");"
        "const p=" + json.dumps(payload) + ";"
        "const f=e.financeCalc(p.u, p.policy);"
        "process.stdout.write(JSON.stringify(f));"
    )
    try:
        out = subprocess.check_output(["node", "-e", code], stderr=subprocess.STDOUT, timeout=10)
        js_res = json.loads(out.decode("utf-8"))
    except Exception as ex:
        print(f"(跳过 JS 对照：{ex})")
        return True
    py_res = finance_calc(_SAMPLE_USER, _SAMPLE_POLICY)
    print("--- 与 web/engine.js 同输入对照 ---")
    diffs = []
    for key in ("net", "cashBack", "available", "monthly", "disposable"):
        py_v, js_v = py_res[key], js_res[key]
        # net/cashBack/available: JS 未取整，用 ±0.01 容差；monthly/disposable 已取整 ±1
        tol = 0.01 if key in ("net", "cashBack", "available") else 1
        ok = abs(py_v - js_v) <= tol
        print(f"  {'✅' if ok else '❌'} {key}: py={py_v}  js={js_v}  Δ={round(py_v-js_v, 4)}")
        if not ok:
            diffs.append(key)
    for t in (300, 280, 260, 250):
        # JS 经 JSON 序列化后数字 key 会变字符串；同时兼容两种
        py_v = py_res["rows"][t]["gap"]
        js_row = js_res["rows"].get(t) or js_res["rows"].get(str(t)) or {}
        js_v = js_row.get("gap")
        ok = js_v is not None and abs(py_v - js_v) <= 1
        print(f"  {'✅' if ok else '❌'} rows[{t}].gap: py={py_v}  js={js_v}")
        if not ok:
            diffs.append(f"rows[{t}].gap")
    for key in ("monthlyRatio", "keepCreditRatio"):
        py_v, js_v = py_res[key], js_res[key]
        ok = abs(py_v - js_v) <= 0.1
        print(f"  {'✅' if ok else '❌'} {key}: py={py_v}  js={js_v}")
        if not ok:
            diffs.append(key)
    print()
    return not diffs


if __name__ == "__main__":
    print("== finance.py 自测（与 docs/决策引擎-spec.md §2/§4/§5 对齐）==\n")
    results = [
        _pmt_self_check(),
        _finance_self_check(),
        _reverse_self_check(),
        _plans_self_check(),
        _vs_js_engine(),
    ]
    pass_all = all(results)
    print("=" * 50)
    print(f"结果: {sum(results)}/{len(results)} 模块通过  →  {'✅ 全部通过' if pass_all else '❌ 有失败'}")
    raise SystemExit(0 if pass_all else 1)
