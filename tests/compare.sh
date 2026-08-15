#!/bin/bash
# JS vs Python 决策引擎对照测试（随机化：N 组随机输入，抓快照外漂移）
# 用法: bash tests/compare.sh [N]   N=随机用例数（默认 20）
# 覆盖: engine.js vs engine_py.py（含 disposable/agentFee/gjjMax 边界）
cd "$(dirname "$0")/.."
N="$1"
[ -z "$N" ] && N=20
ENGINE_JS="$(pwd)/web/engine.js"
INPUTS_JSON="/tmp/hs_rand_inputs.json"

# 生成 N 组随机输入（固定种子保证 JS/Py 输入对齐）
python3 - "$N" << 'PYGEN' > /tmp/hs_rand_inputs.json
import json, random, sys
random.seed(42)
n = int(sys.argv[1])
def rand_house(i):
    return {
        "id": "R%d" % i,
        "xq": "rand%d" % i,
        "price": random.choice([200, 260, 280, 300, 320, 350, 0]),
        "avgUnit": random.randint(15000, 40000),
        "unit": random.randint(10000, 50000),
        "years": random.choice(["满五唯一", "满五", "满二", "未满二", ""]),
        "age": random.choice([None, 5, 10, 20, 25, 30, 35, 40]),
        "elevator": random.choice(["有", "无", ""]),
        "floor": random.choice(["中楼层", "低楼层", "高楼层", "顶楼层", ""]),
        "orient": random.choice(["南北", "南", "东南", "北", ""]),
        "structure": random.choice(["板楼", "板塔", "塔楼", ""]),
        "metroM": random.choice([None, 100, 500, 1000, 2000, 3000]),
        "listDays": random.choice([None, 10, 30, 60, 90, 180, 200]),
        "layout": random.choice(["3室2厅", "2室1厅", "1室1厅", ""]),
        "area": random.choice([None, 45, 85, 90, 95, 100, 105, 110]),
        "biz": random.choice(["果园", "北苑", "梨园", "东坝", ""]),
        "parking": random.choice(["有车位", "地库", "无", ""]),
    }
def rand_user(i):
    return {
        "sellPrice": random.choice([120, 140, 150, 0, -5]),
        "mortgageLeft": random.choice([60, 93.1, 100]),
        "agentFee": random.choice([None, 0, 0.015, 0.027]),
        "taxVAT": 0, "taxIncome": 0,
        "incomeAfterTax": random.choice([20000, 27000, 30000]),
        "gjjWithdraw": random.choice([5000, 8500]),
        "cash": random.choice([10, 30, 100]),
        "creditTotal": random.choice([None, 50, 80]),
        "creditMonthly": random.choice([4000, 6868]),
        "hasYearlyRevolving": random.choice([True, False]),
        "borrowPower": random.choice([0, 20]),
        "gjjMax": random.choice([None, 120, 200, 240]),
    }
json.dump({"houses": [rand_house(i) for i in range(n)],
           "users": [rand_user(i) for i in range(n)],
           "policy": {"首付": {"首套": 0.15}, "利率": {"公积金首套": 2.6, "商贷首套": 3.05}}},
          open("/tmp/hs_rand_inputs.json", "w"), ensure_ascii=False)
import sys as _s
print("generated %d random cases" % n, file=_s.stderr)
PYGEN

# JS 侧：engine.js 算评分+资金+三方案
node -e '
const e = require(process.argv[1]);
const d = JSON.parse(require("fs").readFileSync(process.argv[2], "utf8"));
const out = d.houses.map(h => ({s: e.compositeScore(h)}));
const fs = d.users.map(u => {
  const f = e.financeCalc(u, d.policy);
  return {f, idx: e.feasibilityIndex(f, u), plans: e.threePlans(300, f, u, 3.05)};
});
console.log(JSON.stringify({scores: out, finances: fs}));
' "$ENGINE_JS" /tmp/hs_rand_inputs.json > /tmp/hs_js_rand.json

# Python 侧：engine_py 计算
python3 - /tmp/hs_rand_inputs.json << 'PYRUN' > /tmp/hs_py_rand.json
import json, sys
sys.path.insert(0, "skills/house-analyze/scripts")
from engine_py import composite_score, finance_calc, feasibility_index, three_plans
d = json.load(open(sys.argv[1], encoding="utf-8"))
out = {"scores": [{"s": composite_score(h)} for h in d["houses"]],
       "finances": []}
for u in d["users"]:
    f = finance_calc(u, d["policy"])
    out["finances"].append({"f": f, "idx": feasibility_index(f, u), "plans": three_plans(300, f, u, 3.05)})
print(json.dumps(out, ensure_ascii=False))
PYRUN

python3 - << 'PYCMP'
import json
a = json.load(open("/tmp/hs_js_rand.json"))
b = json.load(open("/tmp/hs_py_rand.json"))

def num_eq(x, y, tol=1e-6):
    if isinstance(x, dict) and isinstance(y, dict):
        xk, yk = {str(k) for k in x}, {str(k) for k in y}
        if xk != yk:
            return False
        for k in x:
            ky = next(ky for ky in y if str(ky) == str(k))
            if not num_eq(x[k], y[ky], tol):
                return False
        return True
    if isinstance(x, (int, float)) and isinstance(y, (int, float)):
        if x != x and y != y:  # 双方 NaN 一致视为一致（守卫场景）
            return True
        return abs(x - y) < tol
    return x == y

ok = num_eq(a, b)
n = len(a["scores"])
print(("OK 双引擎一致（%d 组随机输入，含缺省/边界）" % n) if ok else "FAIL 不一致!")
import sys; sys.exit(0 if ok else 1)
PYCMP
