# -*- coding: utf-8 -*-
"""
house-analyze CLI 单入口 — 一条命令出全套置换决策包
用法:
  python3 house_analyze.py score     [--houses H.json] [--top N]
  python3 house_analyze.py finance   [--user U.json] [--policy P.json]
  python3 house_analyze.py risk      [--user U.json] [--policy P.json]
  python3 house_analyze.py compare   [--top N]
  python3 house_analyze.py timeline  [--user U.json] [-o OUT.md]
  python3 house_analyze.py report    [--user U] [--policy P] [--houses H] [-o OUT.md]
  python3 house_analyze.py all       [以上任意参数]

缺省输入用内置脱敏样例（引擎口径，与 tests/engine_test.py 同结构）。
--houses/--user/--policy 接受 JSON 文件路径（引擎口径: 见 docs/决策引擎-spec.md）。
纯 Python3 标准库。
"""
import sys, os, json, argparse, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import engine_py
import finance as finance_mod
import risk as risk_mod
import timeline as timeline_mod

# ---------- 内置脱敏样例（引擎口径） ----------
SAMPLE_USER = {
    "sellPrice": 140, "mortgageLeft": 93.1, "agentFee": 0.015, "taxVAT": 0, "taxIncome": 0,
    "incomeAfterTax": 27000, "gjjWithdraw": 8500, "cash": 30, "creditTotal": 80,
    "creditMonthly": 6868, "hasYearlyRevolving": True, "borrowPower": 0, "gjjMax": 120,
    "revolvingDate": "2026-09 待确认", "creditLeft": 60.0, "timing": "先卖后买",
}
SAMPLE_POLICY = {
    "首付": {"首套": 0.15, "二套": 0.20, "公积金二套": 0.25},
    "利率": {"公积金首套": 2.6, "商贷首套": 3.05, "LPR5年": 3.5},
}
SAMPLE_HOUSES = [
    {"id": "DEMO-01", "xq": "示例·果园A", "price": 260, "avgUnit": 29000, "unit": 26531,
     "years": "满五", "age": 24, "elevator": "有", "floor": "中楼层", "orient": "南",
     "structure": "塔楼", "metroM": 340, "biz": "果园", "layout": "2室1厅", "area": 98, "parking": ""},
    {"id": "DEMO-02", "xq": "示例·果园B", "price": 280, "avgUnit": 29000, "unit": 31000,
     "years": "满五", "age": 18, "elevator": "有", "floor": "中楼层", "orient": "南北",
     "structure": "板楼", "metroM": 800, "biz": "果园", "layout": "3室1厅", "area": 105, "parking": "地库"},
    {"id": "DEMO-03", "xq": "示例·北苑C", "price": 300, "avgUnit": 28000, "unit": 29500,
     "years": "满二", "age": 6, "elevator": "有", "floor": "高楼层", "orient": "东南",
     "structure": "板塔结合", "metroM": 1500, "biz": "北苑", "layout": "3室2厅", "area": 110, "parking": ""},
]


def _load_json(path, default, label="文件"):
    """读取 JSON 文件；路径不存在或内容非法时明确报错，不静默回退样例。
    想用内置样例就不传 path（None）。"""
    if not path:
        return default
    if not os.path.exists(path):
        raise SystemExit("错误: %s不存在: %s（不传该参数则用内置脱敏样例）" % (label, path))
    try:
        with open(path, encoding="utf-8") as fp:
            return json.load(fp)
    except json.JSONDecodeError as e:
        raise SystemExit("错误: %s不是合法 JSON: %s（第 %d 行: %s）" % (label, path, e.lineno, e.msg))


def _user(args):
    return _load_json(args.user, SAMPLE_USER)


def _policy(args):
    return _load_json(args.policy, SAMPLE_POLICY)


def _houses(args):
    data = _load_json(args.houses, SAMPLE_HOUSES)
    if isinstance(data, dict):
        data = data.get("houses", data)
    if not isinstance(data, list):
        raise SystemExit("--houses 需为房源 JSON 数组（或含 houses 数组的对象）")
    return data


def cmd_score(args):
    houses = _houses(args)
    rows = []
    for h in houses:
        s = engine_py.composite_score(h)
        rows.append((h.get("xq") or h.get("小区") or h.get("id", "?"), h.get("price"), s))
    rows.sort(key=lambda r: -r[2]["composite"])
    top = rows[: args.top]
    print("## 房源双评分 Top%d（市场x40%% + 适配x60%%）" % len(top))
    print()
    print("| 小区 | 总价万 | 市场 | 适配 | 综合 |")
    print("|---|---|---|---|---|")
    for xq, price, s in top:
        print("| %s | %s | %s | %s | **%s** |" % (xq, price, s["market"], s["fit"], s["composite"]))
    print()
    if len(rows) > len(top):
        print("（共 %d 套，仅显示前 %d）" % (len(rows), len(top)))


def cmd_finance(args):
    u, p = _user(args), _policy(args)
    f = finance_mod.finance_calc(u, p)
    print("## 资金测算")
    print()
    print("- 卖房净得: %.1f 万" % f["net"])
    print("- 现金回笼: %.1f 万（净得 - 房贷剩余 %.1f）" % (f["cashBack"], u.get("mortgageLeft", 0)))
    print("- 可用资金: %.1f 万（回笼 + 手头现金 %s）" % (f["available"], u.get("cash", 0)))
    print("- 置换后月供: **%d 元/月**，占可支配 %s%%" % (f["monthly"], f["monthlyRatio"]))
    print("- 保留信用贷月供: %d 元/月，占可支配 %s%%（可支配=%d）" % (
        f["keepCreditMonthly"], f["keepCreditRatio"], f["disposable"]))
    print()
    print("| 总价 | 首付 | 税费 | 全清信用贷+买入 | 缺口 |")
    print("|---|---|---|---|---|")
    for k, v in f["rows"].items():
        print("| %s万 | %.1f | %.1f | %.1f | **%s** |" % (k, v["down"], v["fee"], v["totalNeed"], v["gap"]))


def cmd_risk(args):
    u, p = _user(args), _policy(args)
    f = finance_mod.finance_calc(u, p)
    risks = risk_mod.check(u, f)
    print(risk_mod.render_markdown(risks))


def cmd_compare(args):
    """双引擎对照：JS(web/engine.js) vs Python(engine_py.py)，同输入同输出"""
    import tempfile
    js_engine = os.path.join(os.path.dirname(HERE), os.pardir, os.pardir, "web", "engine.js")
    if not os.path.exists(js_engine):
        raise SystemExit("未找到 web/engine.js（需在 house-swap 仓库根目录运行）")
    houses = _houses(args)[: args.top]
    u, p = _user(args), _policy(args)
    js_src = """
const e = require(process.argv[2]);
const u = JSON.parse(process.argv[3]);
const p = JSON.parse(process.argv[4]);
const hs = JSON.parse(process.argv[5]);
const out = {scores: hs.map(h => e.compositeScore(h)), f: e.financeCalc(u, p), idx: e.feasibilityIndex(e.financeCalc(u,p), u)};
console.log(JSON.stringify(out));
"""
    js_runner = os.path.join(tempfile.gettempdir(), "hs_js_runner.js")
    with open(js_runner, "w", encoding="utf-8") as fp:
        fp.write(js_src)
    js_out = subprocess.run(
        ["node", js_runner, js_engine, json.dumps(u), json.dumps(p), json.dumps(houses)],
        capture_output=True, text=True)
    if js_out.returncode != 0:
        raise SystemExit("JS 引擎执行失败: " + js_out.stderr)
    a = json.loads(js_out.stdout)

    py_scores = [engine_py.composite_score(h) for h in houses]
    f = finance_mod.finance_calc(u, p)
    b = {"scores": py_scores, "f": f, "idx": engine_py.feasibility_index(f, u)}

    def num_eq(x, y, tol=1e-6):
        if isinstance(x, dict) and isinstance(y, dict):
            xk = {str(k) for k in x}
            yk = {str(k) for k in y}
            if xk != yk:
                return False
            return all(num_eq(x[k], y[next(ky for ky in y if str(ky) == str(k))], tol) for k in x)
        if isinstance(x, (int, float)) and isinstance(y, (int, float)):
            return abs(x - y) < tol
        return x == y

    ok = num_eq(a, b)
    print("JS    :", json.dumps(a, ensure_ascii=False))
    print("Python:", json.dumps(b, ensure_ascii=False))
    print("== 双引擎一致（含评分/资金/可行性全字段）==" if ok else "== 不一致! ==")
    raise SystemExit(0 if ok else 1)


def cmd_timeline(args):
    u = _user(args)
    out = timeline_mod.build_timeline(u)
    md = out["markdown"]
    print(md)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fp:
            fp.write(md)
        print("已保存: %s" % args.out)


def cmd_report(args):
    report_py = os.path.join(HERE, "report.py")
    cmd = [sys.executable, report_py]
    if args.user:
        cmd += ["--user", args.user]
    if args.policy:
        cmd += ["--policy", args.policy]
    if args.houses:
        cmd += ["--houses", args.houses]
    if args.out:
        cmd += ["-o", args.out]
    cmd += ["--top", str(args.top)]
    subprocess.run(cmd, check=True)


def cmd_all(args):
    for name, fn in [
        ("1/6 双评分 score", cmd_score),
        ("2/6 资金测算 finance", cmd_finance),
        ("3/6 风险雷达 risk", cmd_risk),
        ("4/6 双引擎对照 compare", cmd_compare),
        ("5/6 90天时间表 timeline", cmd_timeline),
        ("6/6 决策报告 report", cmd_report),
    ]:
        print()
        print("=" * 20, name, "=" * 20)
        try:
            fn(args)
        except SystemExit:
            pass


def main():
    ap = argparse.ArgumentParser(description="house-analyze CLI 单入口（六模块）")
    ap.add_argument("cmd", choices=["score", "finance", "risk", "compare", "timeline", "report", "all"])
    ap.add_argument("--user", help="user JSON（引擎口径，缺省内置脱敏样例）")
    ap.add_argument("--policy", help="policy JSON（缺省内置样例）")
    ap.add_argument("--houses", help="房源 JSON 数组文件（缺省内置样例）")
    ap.add_argument("-o", "--out", help="输出 md 路径（timeline/report）")
    ap.add_argument("--top", type=int, default=6, help="TopN（默认6）")
    args = ap.parse_args()
    globals()["cmd_" + args.cmd](args)


if __name__ == "__main__":
    main()
