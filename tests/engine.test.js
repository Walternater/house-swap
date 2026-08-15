// tests/engine.test.js — 决策引擎对照测试（JS vs Python 必须一致）
// 运行: node tests/engine.test.js   (Python 对照见 tests/engine_test.py)
// 期望值来源：docs/决策引擎-spec.md 逐条手算，与 tests/engine_test.py 完全一致
const e = require("../web/engine.js");

// ---------- 公共夹具（脱敏样例，与 engine_test.py 完全一致） ----------
const H_ALL = {price:260, avgUnit:30000, unit:28000, years:"满五唯一", age:8, elevator:"有",
  floor:"中楼层", orient:"南北", listDays:20, structure:"板楼",
  metroM:400, layout:"3室2厅", area:105, biz:"果园", parking:"有车位"};
const H_OLD = {price:260, avgUnit:30000, unit:28000, years:"满五", age:35, elevator:"有",
  floor:"低楼层", orient:"南", listDays:100, structure:"板塔",
  metroM:1500, layout:"2室1厅", area:90, biz:"梨园", parking:"无"};
const U = {sellPrice:140, mortgageLeft:93.1, agentFee:0.015, taxVAT:0, taxIncome:0,
  incomeAfterTax:27000, gjjWithdraw:8500, cash:30, creditTotal:80, creditMonthly:6868,
  hasYearlyRevolving:true, borrowPower:0, gjjMax:120};
const POLICY = {首付:{首套:0.15}, 利率:{公积金首套:2.6, 商贷首套:3.05}};
const F = e.financeCalc(U, POLICY);

// 递归比较：数字用容差，其余精确相等
function close(a, b, tol) {
  if (typeof a === "number" && typeof b === "number") return Math.abs(a - b) <= tol;
  if (Array.isArray(a) && Array.isArray(b)) {
    if (a.length !== b.length) return false;
    return a.every((x, i) => close(x, b[i], tol));
  }
  if (a && b && typeof a === "object" && typeof b === "object") {
    const ka = Object.keys(a), kb = Object.keys(b);
    if (ka.length !== kb.length) return false;
    return ka.every(k => k in b && close(a[k], b[k], tol));
  }
  return a === b;
}

// ---------- 20 组用例：name / 期望值 / 容差 / 计算函数（与 engine_test.py 同名） ----------
const CASES = [
  // 1-5 等额本息 PMT（spec §2）
  ["PMT 255万/3.05%/30年", 10820, 1, () => Math.round(e.pmt(0.0305,30,2550000))],
  ["PMT 120万/2.6%/30年", 4804, 1, () => Math.round(e.pmt(0.026,30,1200000))],
  ["PMT 135万/3.05%/30年", 5728, 1, () => Math.round(e.pmt(0.0305,30,1350000))],
  ["PMT 100万/4.1%/20年", 6113, 1, () => Math.round(e.pmt(0.041,20,1000000))],
  ["PMT 利率0=等额本金降级", 7083, 1, () => Math.round(e.pmt(0,30,2550000))],

  // 6-8 市场评分（spec §1）
  ["市场评分-高配房", 100, 0, () => e.marketScore(H_ALL)],
  ["市场评分-低配房(未满二/顶楼/北向/塔楼)", 27, 0,
    () => e.marketScore({avgUnit:20000, unit:30000, years:"未满二", age:35, elevator:"无",
      floor:"顶楼层", orient:"北", listDays:200, structure:"塔楼"})],
  ["市场评分-空对象走默认分支", 52, 0, () => e.marketScore({})],

  // 9-10 适配评分（spec §1）
  ["适配评分-高配房", 100, 0, () => e.fitScore(H_ALL)],
  ["适配评分-低配房(超预算/无地铁/步梯顶)", 24, 0,
    () => e.fitScore({price:350, metroM:3000, elevator:"无", floor:"顶楼层",
      layout:"1室1厅", area:45, years:"未满二", biz:"别处", parking:"无", age:35})],

  // 11-12 综合评分 = 市场×0.4 + 适配×0.6（spec §1）
  ["综合评分-满配=100", [100, 100, 100.0], 0.1,
    () => { const s = e.compositeScore(H_ALL); return [s.market, s.fit, s.composite]; }],
  ["综合评分-楼龄>30扣5", [74, 71, 72.2], 0.1,
    () => { const s = e.compositeScore(H_OLD); return [s.market, s.fit, s.composite]; }],

  // 13-14 资金测算（spec §2）
  ["资金-月供/占比/保留信用贷", [10532, 29.7, 17400, 49.0, 35500], 1,
    () => [F.monthly, F.monthlyRatio, F.keepCreditMonthly, F.keepCreditRatio, F.disposable]],
  ["资金-四档缺口300/280/260/250", {"300":56, "280":53, "260":49, "250":48}, 1,
    () => { const r = {}; for (const k of [300,280,260,250]) r[k] = F.rows[k].gap; return r; }],

  // 15-16 综合可行性指数 E2（spec §3）
  ["指数-样例(缺口56>现金30,月供占比29.7)", 40, 0, () => e.feasibilityIndex(F, U)],
  ["指数-缺口≤现金则+20", 90, 0,
    () => e.feasibilityIndex(F, {cash:100, borrowPower:0})],

  // 17-18 反向计算 E1（spec §4，输出精度±1万）
  ["反向-月供8000/3.05%/30年/首付15%", {loan:1885434, price:2218158}, 10000,
    () => e.reverseCalc(8000, 30, 0.0305, 0.15)],
  ["反向-月供12000/2.6%/30年/首付20%", {loan:2997454, price:3746818}, 10000,
    () => e.reverseCalc(12000, 30, 0.026, 0.20)],

  // 19 三方案 E4（spec §5）
  ["三方案-300万预算", {稳健:{price:249, down:37, monthly:8980, ratio:25.3},
                      平衡:{price:279, down:42, monthly:10062, ratio:28.3},
                      激进:{price:300, down:45, monthly:10820, ratio:30.5}}, 1,
    () => e.threePlans(300, F, Object.assign({}, U, {disposable:35500}))],

  // 20 边界校验（spec §6）
  ["边界-非法输入报错", ["成交价必须大于0", "月收入必须大于0", "房贷剩余不能为负", "现金不能为负"], 0,
    () => e.validateInputs({sellPrice:0, incomeAfterTax:0, mortgageLeft:-1, cash:-5})],
];

let pass = 0;
for (const [name, want, tol, fn] of CASES) {
  let got, ok;
  try { got = fn(); ok = close(got, want, tol); }
  catch (err) { got = String(err); ok = false; }
  console.log((ok?"✅":"❌"), name, "=", JSON.stringify(got), ok ? "" : "期望" + JSON.stringify(want));
  if (ok) pass++;
}
console.log(pass + "/" + CASES.length + " 通过");
process.exit(pass === CASES.length ? 0 : 1);
