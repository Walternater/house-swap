// tests/engine.test.js — 决策引擎对照测试（JS vs Python 必须一致）
// 运行: node tests/engine.test.js   (Python 对照见 tests/engine_test.py)
const e = require("../web/engine.js");
const cases = [
  ["PMT 255万/3.05%/30年", Math.round(e.pmt(0.0305,30,2550000)), 10820],
  ["PMT 120万/2.6%/30年", Math.round(e.pmt(0.026,30,1200000)), 4804],
  ["PMT 135万/3.05%/30年", Math.round(e.pmt(0.0305,30,1350000)), 5728],
];
let pass = 0;
for (const [name, got, want] of cases) {
  const ok = Math.abs(got - want) <= 1;
  console.log((ok?"✅":"❌"), name, "=", got, ok?"":"期望"+want);
  if (ok) pass++;
}
console.log(pass + "/" + cases.length + " 通过");
process.exit(pass === cases.length ? 0 : 1);
