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
console.log(JSON.stringify({s, monthly:f.monthly, ratio:f.monthlyRatio, gap300:f.rows[300].gap, idx:e.feasibilityIndex(f,u)}));
' "$ENGINE_JS")
PY_OUT=$(python3 -c "
import sys, json; sys.path.insert(0,'skills/house-analyze/scripts')
from engine_py import *
h = {'price':260,'avgUnit':29000,'unit':26531,'years':'满五','age':24,'elevator':'有','floor':'中楼层','orient':'南','structure':'塔楼','metroM':340,'biz':'果园','layout':'2室1厅','area':98}
u = {'sellPrice':140,'mortgageLeft':93.1,'agentFee':0.015,'taxVAT':0,'taxIncome':0,'incomeAfterTax':27000,'gjjWithdraw':8500,'cash':30,'creditTotal':80,'creditMonthly':6868,'hasYearlyRevolving':True,'borrowPower':0,'gjjMax':120}
policy = {'首付':{'首套':0.15},'利率':{'公积金首套':2.6,'商贷首套':3.05}}
s = composite_score(h)
f = finance_calc(u, policy)
print(json.dumps({'s':s,'monthly':f['monthly'],'ratio':f['monthlyRatio'],'gap300':f['rows'][300]['gap'],'idx':feasibility_index(f,u)}))
")
echo "JS    : $JS_OUT"
echo "Python: $PY_OUT"
echo "$JS_OUT" > /tmp/hs_js.json
echo "$PY_OUT" > /tmp/hs_py.json
python3 -c "
import json
a = json.load(open('/tmp/hs_js.json')); b = json.load(open('/tmp/hs_py.json'))
print('✅ 双引擎一致' if a == b else '❌ 不一致!')
import sys; sys.exit(0 if a == b else 1)
"
# 追加: 全字段比对（含 down/fee/totalNeed，锁取整一致）
PYFULL=$(python3 -c "
import sys, json; sys.path.insert(0,'skills/house-analyze/scripts')
from engine_py import *
u={'sellPrice':140,'mortgageLeft':93.1,'agentFee':0.015,'taxVAT':0,'taxIncome':0,'incomeAfterTax':27000,'gjjWithdraw':8500,'cash':30,'creditTotal':80,'creditMonthly':6868,'hasYearlyRevolving':True,'borrowPower':0,'gjjMax':120}
policy={'首付':{'首套':0.15},'利率':{'公积金首套':2.6,'商贷首套':3.05}}
f=finance_calc(u,policy)
print(json.dumps({'rows':f['rows']}))
")
JSFULL=$(node -e "
const e=require('/Users/wcf/personal/house-swap/web/engine.js');
const u={sellPrice:140,mortgageLeft:93.1,agentFee:0.015,taxVAT:0,taxIncome:0,incomeAfterTax:27000,gjjWithdraw:8500,cash:30,creditTotal:80,creditMonthly:6868,hasYearlyRevolving:true,borrowPower:0,gjjMax:120};
const policy={首付:{首套:0.15},利率:{公积金首套:2.6,商贷首套:3.05}};
console.log(JSON.stringify({rows:e.financeCalc(u,policy).rows}));
")
echo "$PYFULL" > /tmp/hs_full_py.json; echo "$JSFULL" > /tmp/hs_full_js.json
python3 -c "
import json
a=json.load(open('/tmp/hs_full_py.json')); b=json.load(open('/tmp/hs_full_js.json'))
print('✅ 全字段一致(含down/fee/totalNeed)' if a==b else '❌ 全字段不一致
'+repr(a)+'
'+repr(b))
import sys; sys.exit(0 if a==b else 1)
"
