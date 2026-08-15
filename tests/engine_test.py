# -*- coding: utf-8 -*-
"""tests/engine_test.py — 决策引擎 Python 侧对照测试（20 组）

期望值来源：docs/决策引擎-spec.md 逐条手算，并与 web/engine.js 输出对齐。
运行: python3 tests/engine_test.py   （JS 侧对照见 tests/engine.test.js）
纯 Python3 标准库，零第三方依赖。
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "skills", "house-analyze", "scripts"))
from engine_py import (pmt, market_score, fit_score, composite_score,
                       finance_calc, feasibility_index, reverse_calc,
                       three_plans, validate_inputs)

# ---------- 公共夹具（脱敏样例，与 engine.test.js 完全一致） ----------
H_ALL = {"price": 260, "avgUnit": 30000, "unit": 28000, "years": "满五唯一", "age": 8,
         "elevator": "有", "floor": "中楼层", "orient": "南北", "listDays": 20,
         "structure": "板楼", "metroM": 400, "layout": "3室2厅", "area": 105,
         "biz": "果园", "parking": "有车位"}
H_OLD = {"price": 260, "avgUnit": 30000, "unit": 28000, "years": "满五", "age": 35,
         "elevator": "有", "floor": "低楼层", "orient": "南", "listDays": 100,
         "structure": "板塔", "metroM": 1500, "layout": "2室1厅", "area": 90,
         "biz": "梨园", "parking": "无"}
U = {"sellPrice": 140, "mortgageLeft": 93.1, "agentFee": 0.015, "taxVAT": 0,
     "taxIncome": 0, "incomeAfterTax": 27000, "gjjWithdraw": 8500, "cash": 30,
     "creditTotal": 80, "creditMonthly": 6868, "hasYearlyRevolving": True,
     "borrowPower": 0, "gjjMax": 120}
POLICY = {"首付": {"首套": 0.15}, "利率": {"公积金首套": 2.6, "商贷首套": 3.05}}
F = finance_calc(U, POLICY)


def _close(a, b, tol):
    """递归比较：数字用容差，其余精确相等。"""
    if isinstance(a, dict) and isinstance(b, dict):
        return set(a) == set(b) and all(_close(a[k], b[k], tol) for k in a)
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(_close(x, y, tol) for x, y in zip(a, b))
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) <= tol
    return a == b


# ---------- 20 组用例：name / 期望值 / 容差 / 计算函数 ----------
# 用例编号对应 engine.test.js 同名用例，期望值两侧一致
CASES = [
    # 1-5 等额本息 PMT（spec §2）
    ("PMT 255万/3.05%/30年", 10820, 1, lambda: round(pmt(0.0305, 30, 2550000))),
    ("PMT 120万/2.6%/30年", 4804, 1, lambda: round(pmt(0.026, 30, 1200000))),
    ("PMT 135万/3.05%/30年", 5728, 1, lambda: round(pmt(0.0305, 30, 1350000))),
    ("PMT 100万/4.1%/20年", 6113, 1, lambda: round(pmt(0.041, 20, 1000000))),
    ("PMT 利率0=等额本金降级", 7083, 1, lambda: round(pmt(0, 30, 2550000))),

    # 6-8 市场评分（spec §1）
    ("市场评分-高配房", 100, 0, lambda: market_score(H_ALL)),
    ("市场评分-低配房(未满二/顶楼/北向/塔楼)", 27, 0,
     lambda: market_score({"avgUnit": 20000, "unit": 30000, "years": "未满二",
                           "age": 35, "elevator": "无", "floor": "顶楼层",
                           "orient": "北", "listDays": 200, "structure": "塔楼"})),
    ("市场评分-空对象走默认分支(spec:缺失按最保守)", 50, 0, lambda: market_score({})),

    # 9-10 适配评分（spec §1）
    ("适配评分-高配房", 100, 0, lambda: fit_score(H_ALL)),
    ("适配评分-低配房(超预算/无地铁/步梯顶)", 24, 0,
     lambda: fit_score({"price": 350, "metroM": 3000, "elevator": "无",
                        "floor": "顶楼层", "layout": "1室1厅", "area": 45,
                        "years": "未满二", "biz": "别处", "parking": "无", "age": 35})),

    # 11-12 综合评分 = 市场×0.4 + 适配×0.6（spec §1）
    ("综合评分-满配=100", (100, 100, 100.0), 0.1, lambda: (
        composite_score(H_ALL)["market"], composite_score(H_ALL)["fit"],
        composite_score(H_ALL)["composite"])),
    ("综合评分-楼龄>30扣5", (74, 71, 72.2), 0.1, lambda: (
        composite_score(H_OLD)["market"], composite_score(H_OLD)["fit"],
        composite_score(H_OLD)["composite"])),

    # 13-14 资金测算（spec §2）
    ("资金-月供/占比/保留信用贷", (10532, 29.7, 17400, 49.0, 35500), 1, lambda: (
        F["monthly"], F["monthlyRatio"], F["keepCreditMonthly"],
        F["keepCreditRatio"], F["disposable"])),
    ("资金-四档缺口300/280/260/250", {"300": 56, "280": 53, "260": 49, "250": 48}, 1,
     lambda: {str(k): v["gap"] for k, v in F["rows"].items()}),

    # 15-16 综合可行性指数 E2（spec §3）
    ("指数-样例(缺口56>现金30,月供占比29.7)", 40, 0, lambda: feasibility_index(F, U)),
    ("指数-缺口≤现金则+20", 90, 0,
     lambda: feasibility_index(F, {"cash": 100, "borrowPower": 0})),

    # 17-18 反向计算 E1（spec §4，输出精度±1万）
    ("反向-月供8000/3.05%/30年/首付15%", {"loan": 1885434, "price": 2218158}, 10000,
     lambda: reverse_calc(8000, 30, 0.0305, 0.15)),
    ("反向-月供12000/2.6%/30年/首付20%", {"loan": 2997454, "price": 3746818}, 10000,
     lambda: reverse_calc(12000, 30, 0.026, 0.20)),

    # 19 三方案 E4（spec §5）
    ("三方案-300万预算", {"稳健": {"price": 249, "down": 37, "monthly": 8980, "ratio": 25.3},
                        "平衡": {"price": 279, "down": 42, "monthly": 10062, "ratio": 28.3},
                        "激进": {"price": 300, "down": 45, "monthly": 10820, "ratio": 30.5}},
     1, lambda: three_plans(300, F, dict(U, disposable=35500))),

    # 20 边界校验（spec §6）
    ("边界-非法输入报错", ["成交价必须大于0", "月收入必须大于0",
                         "房贷剩余不能为负", "现金不能为负",
                         "信用贷总额必须≥0", "月收入必须大于0"], 0,
     lambda: validate_inputs({"sellPrice": 0, "incomeAfterTax": 0,
                              "mortgageLeft": -1, "cash": -5, "creditTotal": -1})),

    # 21-24 回归：/autoplan 2026-08-15 修复验证
    ("回归-三方案无disposable回退f", {"稳健": 25.3}, 0.1,
     lambda: {"稳健": three_plans(300, F, U)["稳健"]["ratio"]}),
    ("回归-pmt n=0 降级等额本金", 2550000, 1,
     lambda: round(pmt(0.0305, 0, 2550000))),
    ("回归-reverseCalc 非法输入守卫", {"loan": 0, "price": 0}, 0,
     lambda: reverse_calc(0, 30, 0.0305, 0.15)),
    ("回归-financeCalc 缺 creditTotal 不 NaN", 45, 1,
     lambda: finance_calc(dict(U, creditTotal=None), POLICY)["rows"][300]["down"]),
]

if __name__ == "__main__":
    pass_n = 0
    for name, want, tol, fn in CASES:
        try:
            got = fn()
            ok = _close(got, want, tol)
        except Exception as exc:  # 引擎抛异常视为失败
            got, ok = repr(exc), False
        mark = "✅" if ok else "❌"
        print(f"{mark} {name} = {got}" + ("" if ok else f"（期望 {want}，容差 {tol}）"))
        pass_n += ok
    print(f"\n{pass_n}/{len(CASES)} 通过")
    sys.exit(0 if pass_n == len(CASES) else 1)
