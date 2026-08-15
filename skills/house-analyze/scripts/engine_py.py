# -*- coding: utf-8 -*-
"""
house-swap 决策引擎 (Python 实现) · 与 docs/决策引擎-spec.md 唯一对齐
对应 JS 版: web/engine.js —— 两实现必须同输入同输出(±1元/±1分)
纯 Python3 标准库
"""
import json

def pmt(rate_annual, years, principal):
    """等额本息月供; 利率=0 → 等额本金"""
    r = rate_annual / 12
    n = years * 12
    if r == 0:
        return principal / n
    return principal * r * (1 + r) ** n / ((1 + r) ** n - 1)

def _clamp(x, lo, hi):
    return max(lo, min(hi, x))

# ---------- 1. 双评分 ----------
def market_score(h):
    s = 0
    avg, up = h.get("avgUnit") or 0, h.get("unit") or 0
    if avg > 0 and up > 0:
        r = up / avg
        s += 30 if r <= 1.00 else 26 if r <= 1.05 else 22 if r <= 1.10 else 16 if r <= 1.15 else 10 if r <= 1.25 else 5
    else:
        s += 15
    y = h.get("years") or ""
    s += 15 if "满五唯一" in y else 11 if "满五" in y else 7 if "满二" in y else 5 if "满" in y else 2
    age = h.get("age")
    s += 8 if age is None else 15 if age <= 10 else 12 if age <= 20 else 9 if age <= 25 else 6 if age <= 30 else 2
    s += 10 if h.get("elevator") == "有" else 4 if h.get("elevator") == "无" else 7
    f = h.get("floor") or ""
    s += 10 if "中" in f else 7 if ("低" in f or "底" in f) else 6 if "高" in f else 3 if "顶" in f else 7
    c = h.get("orient") or ""
    s += 10 if "南北" in c else 8 if c == "南" else 7 if c in ("东南","西南") else 5 if c in ("东","西") else 3 if c in ("东北","西北") else 2 if c == "北" else 6
    days = h.get("listDays")
    s += 3 if days is None else 5 if days <= 30 else 4 if days <= 60 else 3 if days <= 90 else 2 if days <= 180 else 1
    st = h.get("structure") or ""
    s += 5 if ("板楼" in st and "塔" not in st) else 4 if "板塔" in st else 3 if "塔楼" in st else 4
    return _clamp(round(s), 0, 100)

def fit_score(h, prefs=None):
    s = 0
    p = h.get("price") or 0
    s += 30 if p <= 260 else 27 if p <= 280 else 22 if p <= 300 else 12 if p <= 320 else 5
    m = h.get("metroM")
    s += 10 if m is None else 20 if m <= 500 else 16 if m <= 1000 else 10 if m <= 2000 else 4
    lift, f = h.get("elevator"), h.get("floor") or ""
    if lift == "有":
        s += 15 if "中" in f else 13
    elif lift == "无":
        s += 10 if "中" in f else 8 if ("低" in f or "底" in f) else 4 if ("高" in f or "顶" in f) else 8
    else:
        s += 10
    hx, area = h.get("layout") or "", h.get("area") or 0
    if "3室" in hx or "三居" in hx:
        s += 15 if area >= 100 else 13
    elif "2室" in hx or "两居" in hx:
        s += 13 if area >= 95 else 12 if area >= 85 else 10
    else:
        s += 8
    y = h.get("years") or ""
    s += 10 if "满五唯一" in y else 7 if "满五" in y else 5 if "满二" in y else 2
    biz = h.get("biz") or ""
    if any(k in biz for k in ["果园","北苑","北关"]): s += 5
    elif any(k in biz for k in ["梨园","九棵树","潞苑","东坝"]): s += 4
    else: s += 3
    s += 5 if ("车位" in (h.get("parking") or "") or "地库" in (h.get("parking") or "")) else 0
    if h.get("age") is not None and h["age"] > 30:
        s -= 5
    return _clamp(round(s), 0, 100)

def composite_score(h, prefs=None):
    m = market_score(h)
    f = fit_score(h, prefs or {})
    return {"market": m, "fit": f, "composite": round(m * 0.40 + f * 0.60, 1)}

# ---------- 2. 资金测算 ----------
def finance_calc(u, policy):
    net = u["sellPrice"] - u["sellPrice"] * u.get("agentFee", 0.015) - u["sellPrice"] * u.get("taxVAT", 0) - u["sellPrice"] * u.get("taxIncome", 0)
    cash_back = net - u["mortgageLeft"]
    available = cash_back + u["cash"]
    rows = {}
    for target in (300, 280, 260, 250):
        down = target * policy["首付"]["首套"]
        fee = target * 0.02
        total_need = u["creditTotal"] + down + fee
        rows[target] = {"down": down, "fee": fee, "totalNeed": total_need, "gap": round(total_need - available)}
    gjj = _clamp(u.get("gjjMax", 120), 0, 200)
    loan = 255
    gjj_loan = min(gjj, loan)
    shang_loan = max(0, loan - gjj_loan)
    monthly = pmt(policy["利率"]["公积金首套"] / 100, 30, gjj_loan * 10000) + pmt(policy["利率"]["商贷首套"] / 100, 30, shang_loan * 10000)
    disposable = u["incomeAfterTax"] + u["gjjWithdraw"]
    keep = monthly + u.get("creditMonthly", 0)
    return {
        "net": round(net), "cashBack": round(cash_back), "available": round(available), "rows": rows,
        "monthly": round(monthly), "monthlyRatio": round(monthly / disposable * 1000) / 10,
        "keepCreditMonthly": round(keep), "keepCreditRatio": round(keep / disposable * 1000) / 10,
        "disposable": round(disposable)
    }

# ---------- 3. 可行性指数 ----------
def feasibility_index(f, u):
    s = 60
    g300 = f["rows"][300]["gap"]
    if g300 <= u["cash"]: s += 20
    elif g300 <= u["cash"] + u.get("borrowPower", 0): s += 10
    else: s -= 20
    r = f["monthlyRatio"]
    s += 10 if r <= 30 else 5 if r <= 40 else -20 if r > 50 else 0
    if u.get("hasYearlyRevolving"): s -= 10
    return _clamp(s, 0, 100)

# ---------- 4. 反向计算 ----------
def reverse_calc(target_monthly, years, rate, down_ratio):
    r, n = rate / 12, years * 12
    k = r * (1 + r) ** n / ((1 + r) ** n - 1)
    loan = target_monthly / k
    price = loan / (1 - down_ratio)
    return {"loan": round(loan), "price": round(price)}

# ---------- 5. 三方案 ----------
def three_plans(budget, f, u):
    d = u["disposable"] if "disposable" in u else f["disposable"]
    def mk(k):
        price = budget * k
        down = price * 0.15
        loan = price - down
        m = pmt(0.0305, 30, loan * 10000)
        return {"price": round(price), "down": round(down), "monthly": round(m), "ratio": round(m / d * 1000) / 10}
    return {"稳健": mk(0.83), "平衡": mk(0.93), "激进": mk(1.0)}

# ---------- 6. 边界校验 ----------
def validate_inputs(inputs):
    errs = []
    if not (inputs.get("sellPrice", 0) > 0): errs.append("成交价必须大于0")
    if not (inputs.get("incomeAfterTax", 0) > 0): errs.append("月收入必须大于0")
    if inputs.get("mortgageLeft", 0) < 0: errs.append("房贷剩余不能为负")
    if inputs.get("cash", 0) < 0: errs.append("现金不能为负")
    return errs

if __name__ == "__main__":
    # 冒烟测试：与合并修正版口径对齐
    u = {"sellPrice":140, "mortgageLeft":93.1, "agentFee":0.015, "taxVAT":0, "taxIncome":0,
         "incomeAfterTax":27000, "gjjWithdraw":8500, "cash":30, "creditTotal":80, "creditMonthly":6868,
         "hasYearlyRevolving":True, "borrowPower":0, "gjjMax":120}
    policy = {"首付":{"首套":0.15}, "利率":{"公积金首套":2.6, "商贷首套":3.05}}
    f = finance_calc(u, policy)
    print("月供:", f["monthly"], "元 (期望≈10532)", "| 占比:", f["monthlyRatio"], "%")
    print("300万缺口:", f["rows"][300]["gap"], "万 (期望≈56-63)")
    print("可行性指数:", feasibility_index(f, u))
    h = {"price":260, "avgUnit":29000, "unit":26531, "years":"满五", "age":24, "elevator":"有",
         "floor":"中楼层", "orient":"南", "structure":"塔楼", "metroM":340, "biz":"果园", "layout":"2室1厅", "area":98}
    print("京贸双评分:", composite_score(h))

