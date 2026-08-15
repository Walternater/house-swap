#!/bin/bash
# JS vs Python 决策引擎对照测试
# 用法: bash tests/compare.sh
cd "$(dirname "$0")/.."
ENGINE_JS="/Users/wcf/personal/house-swap/web/engine.js"

JS_OUT=$(node -e '
const e = require(process.argv[1]);
const h = {price:260, avgUnit:29000, unit:26531, years:"满五", age:24, elevator:"有",
  floor:"中楼层", orient:"南", structure:"塔楼", metroM:340, biz:"果园", layout:"2室1厅", area:98};
const u = {sellPrice:140, mortgageLeft:93.1, agentFee:0.015, taxVAT:0, taxIncome:0,
  incomeAfterTax:27000, gjjWithdraw:8500, cash:30, creditTotal:80, creditMonthly:6868,
  hasYearlyRevolving:true, borrowPower:0, gjjMax:120};
const policy = {首付:{首套:0.15}, 利率:{公积金首套:2.6, 商贷首套:3.05}};
const s = e.compositeScore(h);
const f = e.financeCalc(u, policy);
console.log(JSON.stringify({s, monthly:f.monthly, ratio:f.monthlyRatio, rows:f.rows, idx:e.feasibilityIndex(f,u)}));
' "$ENGINE_JS")

PY_OUT=$(python3 -c "
import sys, json; sys.path.insert(0,'skills/house-analyze/scripts')
from engine_py import *
h = {'price':260,'avgUnit':29000,'unit':26531,'years':'满五','age':24,'elevator':'有','floor':'中楼层','orient':'南','structure':'塔楼','metroM':340,'biz':'果园','layout':'2室1厅','area':98}
u = {'sellPrice':140,'mortgageLeft':93.1,'agentFee':0.015,'taxVAT':0,'taxIncome':0,'incomeAfterTax':27000,'gjjWithdraw':8500,'cash':30,'creditTotal':80,'creditMonthly':6868,'hasYearlyRevolving':True,'borrowPower':0,'gjjMax':120}
policy = {'首付':{'首套':0.15},'利率':{'公积金首套':2.6,'商贷首套':3.05}}
s = composite_score(h)
f = finance_calc(u, policy)
print(json.dumps({'s':s,'monthly':f['monthly'],'ratio':f['monthlyRatio'],'rows':f['rows'],'idx':feasibility_index(f,u)}))
")

echo "$JS_OUT" > /tmp/hs_js.json
echo "$PY_OUT" > /tmp/hs_py.json
python3 << 'PYEOF'
import json
a = json.load(open('/tmp/hs_js.json'))
b = json.load(open('/tmp/hs_py.json'))
# 数值比较(容忍浮点极小差)
def num_eq(x, y, tol=1e-6):
    if isinstance(x, dict) and isinstance(y, dict):
        return set(x.keys()) == set(y.keys()) and all(num_eq(x[k], y[k], tol) for k in x)
    if isinstance(x, (int, float)) and isinstance(y, (int, float)):
        return abs(x - y) < tol
    return x == y
ok = num_eq(a, b)
print("JS    :", json.dumps(a, ensure_ascii=False))
print("Python:", json.dumps(b, ensure_ascii=False))
print("✅ 双引擎一致(含rows全字段)" if ok else "❌ 不一致!")
import sys; sys.exit(0 if ok else 1)
PYEOF
