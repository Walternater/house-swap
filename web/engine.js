/* house-swap 决策引擎 · 与 docs/决策引擎-spec.md 唯一对齐（JS 实现）
 * 所有公式/权重/边界以 spec 为准；Python 版在 skills/house-analyze
 */
"use strict";

// ---------- 工具 ----------
function pmt(rate_annual, years, principal) {
  // 等额本息月供；r=年利率/12, n=月数；利率=0 → 等额本金降级
  const r = rate_annual / 12;
  const n = years * 12;
  if (r === 0) return principal / n;
  return principal * r * Math.pow(1 + r, n) / (Math.pow(1 + r, n) - 1);
}
function fmtW(x) { return Math.round(x).toLocaleString("zh-CN"); }
function clamp(x, lo, hi) { return Math.max(lo, Math.min(hi, x)); }

// ---------- 1. 双评分 ----------
function marketScore(h) {
  let s = 0;
  const avg = h.avgUnit || 0, up = h.unit || 0;
  if (avg > 0 && up > 0) {
    const r = up / avg;
    s += r <= 1.00 ? 30 : r <= 1.05 ? 26 : r <= 1.10 ? 22 : r <= 1.15 ? 16 : r <= 1.25 ? 10 : 5;
  } else s += 15;
  const y = h.years || "";
  s += y.includes("满五唯一") ? 15 : y.includes("满五") ? 11 : y.includes("满二") ? 7 : y.includes("满") ? 5 : 2;
  const age = h.age;
  s += age == null ? 8 : age <= 10 ? 15 : age <= 20 ? 12 : age <= 25 ? 9 : age <= 30 ? 6 : 2;
  s += h.elevator === "有" ? 10 : h.elevator === "无" ? 4 : 7;
  const f = h.floor || "";
  s += f.includes("中") ? 10 : (f.includes("低") || f.includes("底")) ? 7 : f.includes("高") ? 6 : f.includes("顶") ? 3 : 7;
  const c = h.orient || "";
  s += c.includes("南北") ? 10 : c === "南" ? 8 : ["东南", "西南"].includes(c) ? 7 : ["东", "西"].includes(c) ? 5 : ["东北", "西北"].includes(c) ? 3 : c === "北" ? 2 : 6;
  const days = h.listDays;
  s += days == null ? 3 : days <= 30 ? 5 : days <= 60 ? 4 : days <= 90 ? 3 : days <= 180 ? 2 : 1;
  const st = h.structure || "";
  s += st.includes("板楼") && !st.includes("塔") ? 5 : st.includes("板塔") ? 4 : st.includes("塔楼") ? 3 : 4;
  return clamp(Math.round(s), 0, 100);
}

function fitScore(h, prefs) {
  let s = 0;
  const p = h.price || 0;
  s += p <= 260 ? 30 : p <= 280 ? 27 : p <= 300 ? 22 : p <= 320 ? 12 : 5;
  const m = h.metroM;
  s += m == null ? 10 : m <= 500 ? 20 : m <= 1000 ? 16 : m <= 2000 ? 10 : 4;
  const lift = h.elevator, f = h.floor || "";
  if (lift === "有") s += (f.includes("中")) ? 15 : 13;
  else if (lift === "无") s += f.includes("中") ? 10 : (f.includes("低") || f.includes("底")) ? 8 : (f.includes("高") || f.includes("顶")) ? 4 : 8;
  else s += 10;
  const hx = h.layout || "", area = h.area || 0;
  if (hx.includes("3室") || hx.includes("三居")) s += area >= 100 ? 15 : 13;
  else if (hx.includes("2室") || hx.includes("两居")) s += area >= 95 ? 13 : area >= 85 ? 12 : 10;
  else s += 8;
  const y = h.years || "";
  s += y.includes("满五唯一") ? 10 : y.includes("满五") ? 7 : y.includes("满二") ? 5 : 2;
  const biz = h.biz || "";
  if (biz.includes("果园") || biz.includes("北苑") || biz.includes("北关")) s += 5;
  else if (biz.includes("梨园") || biz.includes("九棵树") || biz.includes("潞苑") || biz.includes("东坝")) s += 4;
  else s += 3;
  s += (h.parking || "").includes("车位") || (h.parking || "").includes("地库") ? 5 : 0;
  if (h.age != null && h.age > 30) s -= 5;
  return clamp(Math.round(s), 0, 100);
}
function compositeScore(h, prefs) {
  const m = marketScore(h), f = fitScore(h, prefs || {});
  return { market: m, fit: f, composite: Math.round((m * 0.40 + f * 0.60) * 10) / 10 };
}

// ---------- 2. 资金测算 ----------
function financeCalc(u, policy) {
  // u: 实测财务; policy: 利率/税费
  const net = u.sellPrice - (u.sellPrice * u.agentFee) - (u.sellPrice * (u.taxVAT || 0)) - (u.sellPrice * (u.taxIncome || 0));
  const cashBack = net - u.mortgageLeft;
  const available = cashBack + u.cash;
  const rows = {};
  for (const target of [300, 280, 260, 250]) {
    const down = target * policy.首付.首套;
    const fee = target * 0.02;
    const totalNeed = u.creditTotal + down + fee;
    rows[target] = { down, fee, totalNeed, gap: Math.round(totalNeed - available) };
  }
  // 置换后月供（信用贷结清后）：公积金+商贷
  const gjj = clamp(u.gjjMax || 120, 0, 200);
  const loan = 255; // 300万房 贷255万
  const gjjLoan = Math.min(gjj, loan);
  const shangLoan = Math.max(0, loan - gjjLoan);
  const monthly = pmt(policy.利率.公积金首套 / 100, 30, gjjLoan * 10000) + pmt(policy.利率.商贷首套 / 100, 30, shangLoan * 10000);
  const disposable = u.incomeAfterTax + u.gjjWithdraw;
  const keepCreditMonthly = monthly + u.creditMonthly;
  return {
    net, cashBack, available, rows,
    monthly: Math.round(monthly),
    monthlyRatio: Math.round(monthly / disposable * 1000) / 10,
    keepCreditMonthly: Math.round(keepCreditMonthly),
    keepCreditRatio: Math.round(keepCreditMonthly / disposable * 1000) / 10,
    disposable
  };
}

// ---------- 3. 综合可行性指数（E2） ----------
function feasibilityIndex(f, u) {
  let s = 60;
  const g300 = f.rows[300].gap;
  if (g300 <= u.cash) s += 20;
  else if (g300 <= u.cash + (u.borrowPower || 0)) s += 10;
  else s -= 20;
  const r = f.monthlyRatio;
  s += r <= 30 ? 10 : r <= 40 ? 5 : r > 50 ? -20 : 0;
  if (u.hasYearlyRevolving) s -= 10;
  return clamp(s, 0, 100);
}

// ---------- 4. 反向计算（E1） ----------
function reverseCalc(targetMonthly, years, rate, downRatio) {
  const r = rate / 12, n = years * 12;
  const k = r * Math.pow(1 + r, n) / (Math.pow(1 + r, n) - 1);
  const loan = targetMonthly / k;          // 元
  const price = loan / (1 - downRatio);     // 元
  return { loan: Math.round(loan), price: Math.round(price) };
}

// ---------- 5. 三方案（E4） ----------
function threePlans(budget, f, u) {
  const d = u.disposable;
  const mk = (k) => {
    const price = budget * k;
    const down = price * 0.15;
    const loan = price - down;
    const m = pmt(0.0305, 30, loan * 10000);
    return { price: Math.round(price), down: Math.round(down), monthly: Math.round(m), ratio: Math.round(m / d * 1000) / 10 };
  };
  return { 稳健: mk(0.83), 平衡: mk(0.93), 激进: mk(1.0) };
}

// ---------- 6. 边界校验 ----------
function validateInputs(inputs) {
  const errs = [];
  if (!(inputs.sellPrice > 0)) errs.push("成交价必须大于0");
  if (!(inputs.incomeAfterTax > 0)) errs.push("月收入必须大于0");
  if (!(inputs.mortgageLeft >= 0)) errs.push("房贷剩余不能为负");
  if (inputs.cash < 0) errs.push("现金不能为负");
  return errs;
}

if (typeof module !== "undefined") module.exports = {
  pmt, marketScore, fitScore, compositeScore, financeCalc,
  feasibilityIndex, reverseCalc, threePlans, validateInputs
};
