/* house-swap 看板 UI 逻辑（原生 JS，零依赖） */
"use strict";
const $ = (id) => document.getElementById(id);
const STORE_KEY = "houseSwap_v1";
// HTML 转义（防 XSS：用户输入拼进 innerHTML 前必须过 esc）
function esc(s) {
  return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

// ---------- 状态 ----------
let state = { step: 1, houses: [], finance: {}, target: {} };
function save() { try { localStorage.setItem(STORE_KEY, JSON.stringify(state)); } catch (e) {} }
function load() { try { const d = JSON.parse(localStorage.getItem(STORE_KEY)); if (d) state = Object.assign(state, d); } catch (e) {} }
load();

// ---------- 步骤管理 ----------
function gotoStep(n) {
  state.step = n; save();
  document.querySelectorAll(".panel").forEach(p => p.classList.add("hidden"));
  $("step" + n).classList.remove("hidden");
  document.querySelectorAll(".step-dot").forEach(d => d.classList.toggle("active", +d.dataset.step === n));
  if (n === 5) renderResult();
  window.scrollTo(0, 0);
}
document.querySelectorAll(".next").forEach(b => b.onclick = () => gotoStep(Math.min(5, state.step + 1)));
document.querySelectorAll(".prev").forEach(b => b.onclick = () => gotoStep(Math.max(1, state.step - 1)));
document.querySelectorAll(".step-dot").forEach(d => d.onclick = () => gotoStep(+d.dataset.step));

// ---------- 表单读取 ----------
function readStep1() {
  state.sell = {
    sellPrice: +$("sellPrice").value || 0,
    mortgageLeft: +$("mortgageLeft").value || 0,
    agentFee: (+$("agentFee").value || 1.5) / 100
  };
}
function readStep2() {
  state.finance = {
    incomeAfterTax: +$("incomeAfterTax").value || 0,
    gjjWithdraw: +$("gjjWithdraw").value || 0,
    cash: +$("cash").value || 0,
    creditTotal: +$("creditTotal").value || 0,
    creditMonthly: +$("creditMonthly").value || 0,
    revolving: $("revolving").value === "yes",
    borrowPower: +$("borrowPower").value || 0
  };
}
function readStep3() {
  state.target = {
    budget: +$("budget").value || 300,
    regionPref: $("regionPref").value,
    liftPref: $("liftPref").value,
    metroPref: +$("metroPref").value || 1000,
    layoutPref: $("layoutPref").value
  };
}

// ---------- 房源表单 ----------
function houseFormHTML(h, i) {
  return '<div class="house-row" data-i="' + i + '">' +
    '<input class="h-xq" placeholder="小区" value="' + esc(h.xq) + '">' +
    '<input class="h-hx" placeholder="户型(如2室1厅)" value="' + esc(h.hx) + '">' +
    '<input class="h-area" type="number" placeholder="面积㎡" value="' + esc(h.area) + '">' +
    '<input class="h-price" type="number" placeholder="总价(万)" value="' + esc(h.price) + '">' +
    '<input class="h-avg" type="number" placeholder="小区均价(元/㎡)" value="' + esc(h.avg) + '">' +
    '<input class="h-floor" placeholder="楼层(中/低/高/顶)" value="' + esc(h.floor) + '">' +
    '<input class="h-age" type="number" placeholder="楼龄(年,选填)" value="' + esc(h.age || "") + '">' +
    '<select class="h-lift"><option value="有"'+(h.lift==="有"?" selected":"")+'>电梯</option><option value="无"'+(h.lift==="无"?" selected":"")+'>无电梯</option></select>' +
    '<input class="h-metro" type="number" placeholder="地铁(米)" value="' + esc(h.metro) + '">' +
    '<select class="h-years"><option value="满五唯一"'+(h.years==="满五唯一"?" selected":"")+'>满五唯一</option><option value="满五"'+(h.years==="满五"?" selected":"")+'>满五</option><option value="满二"'+(h.years==="满二"?" selected":"")+'>满二</option><option value="未满二"'+(h.years==="未满二"?" selected":"")+'>未满二</option></select>' +
    '<input class="h-biz" placeholder="商圈(果园/北苑…)" value="' + esc(h.biz) + '">' +
    '<button class="btn ghost del">删除</button></div>';
}
function renderHouses() {
  $("housesForm").innerHTML = state.houses.length ? state.houses.map(houseFormHTML).join("") : '<p class="hint">还没有房源。点"载入脱敏示例"体验，或手动添加。</p>';
  document.querySelectorAll(".del").forEach(b => b.onclick = () => {
    const i = +b.parentNode.dataset.i; state.houses.splice(i, 1); save(); renderHouses();
  });
}
$("addHouse").onclick = () => { state.houses.push({}); save(); renderHouses(); };
function collectHouses() {
  state.houses = Array.from(document.querySelectorAll(".house-row")).map(r => ({
    xq: r.querySelector(".h-xq").value, hx: r.querySelector(".h-hx").value,
    area: +r.querySelector(".h-area").value, price: +r.querySelector(".h-price").value,
    avg: +r.querySelector(".h-avg").value, floor: r.querySelector(".h-floor").value,
    age: +r.querySelector(".h-age").value || null,
    lift: r.querySelector(".h-lift").value, metro: +r.querySelector(".h-metro").value,
    years: r.querySelector(".h-years").value, biz: r.querySelector(".h-biz").value,
    orient: r.querySelector(".h-orient") ? r.querySelector(".h-orient").value : "",
    structure: r.querySelector(".h-structure") ? r.querySelector(".h-structure").value : "",
    parking: r.querySelector(".h-parking") ? r.querySelector(".h-parking").value : "",
    listDays: r.querySelector(".h-listdays") ? +r.querySelector(".h-listdays").value || null : null
  })).filter(h => h.price > 0);
}

// ---------- 结果渲染 ----------
function renderResult() {
  readStep1(); readStep2(); readStep3(); collectHouses(); save();
  const policy = POLICY;
  const u = Object.assign({
    sellPrice: state.sell.sellPrice, mortgageLeft: state.sell.mortgageLeft,
    agentFee: state.sell.agentFee, taxVAT: 0, taxIncome: 0,
    incomeAfterTax: state.finance.incomeAfterTax, gjjWithdraw: state.finance.gjjWithdraw,
    cash: state.finance.cash, creditTotal: state.finance.creditTotal,
    creditMonthly: state.finance.creditMonthly, hasYearlyRevolving: state.finance.revolving,
    borrowPower: state.finance.borrowPower, gjjMax: 120
  }, state.finance, state.sell);
  const errs = validateInputs(u);
  const f = financeCalc(u, policy);
  const idx = feasibilityIndex(f, u);
  const plans = threePlans(state.target.budget, f, u, POLICY.利率.商贷首套);
  let html = "";
  if (errs.length) {
    html += '<div class="card"><h3>⚠️ 请先修正</h3><ul>' + errs.map(e => "<li>" + e + "</li>").join("") + "</ul></div>";
  } else {
    const color = idx >= 80 ? "#2f9e44" : idx >= 60 ? "#e8590c" : "#e03131";
    html += '<div class="index-card" style="background:' + color + '">' +
      '<div>综合可行性指数</div><div class="num">' + idx + '</div>' +
      '<div>' + (idx>=80?"强烈建议换":idx>=60?"可换，需准备":"暂缓") + '</div></div>';
    html += '<div class="card"><h3>💰 资金测算</h3><table><tr><th>新房总价</th><th>首付15%</th><th>税费约2%</th><th>全清信用贷+买入</th><th>缺口</th></tr>' +
      Object.entries(f.rows).map(([k,v]) => '<tr><td>' + k + '万</td><td>' + v.down + '万</td><td>' + v.fee + '万</td><td>' + v.totalNeed + '万</td><td class="' + (v.gap<=0?"gap-ok":"gap-bad") + '">' + v.gap + '万</td></tr>').join("") +
      '</table><p class="hint">可用资金 = 卖房回笼 ' + fmtW(f.cashBack) + '万 + 现金 ' + esc(u.cash) + '万 = ' + fmtW(f.available) + '万</p></div>';
    html += '<div class="card"><h3>📊 置换后月供（贷255万，信用贷结清）</h3>' +
      '<p><b>' + fmtW(f.monthly) + '</b> 元/月，占可支配 ' + f.monthlyRatio + '%' + (f.monthlyRatio<=30?' ✅':f.monthlyRatio<=40?' ⚠️':' 🔴') + '</p>' +
      '<p class="hint">保留信用贷时：' + fmtW(f.keepCreditMonthly) + ' 元/月，占 ' + f.keepCreditRatio + '%（&gt;40% 审批和生活双压力）</p></div>';
    html += '<div class="card"><h3>🧭 三方案（预算 ' + esc(state.target.budget) + '万）</h3><table><tr><th>方案</th><th>总价</th><th>首付</th><th>月供</th><th>占可支配</th></tr>' +
      Object.entries(plans).map(([k,v]) => '<tr><td>' + k + '</td><td>' + v.price + '万</td><td>' + v.down + '万</td><td>' + fmtW(v.monthly) + '</td><td>' + v.ratio + '%</td></tr>').join("") + '</table></div>';
    if (state.houses.length) {
      const scored = state.houses.map(h => compositeScore({
        ...h, avgUnit: h.avg, unit: h.price && h.area ? Math.round(h.price*10000/h.area) : 0,
        elevator: h.lift, metroM: h.metro, layout: h.hx,
        orient: h.orient||"", structure: h.structure||"", parking: h.parking||"", listDays: h.listDays
      })).map((s,i) => Object.assign({}, state.houses[i], s)).sort((a,b)=>b.composite-a.composite);
      html += '<div class="card"><h3>🏠 候选房源双评分</h3><table><tr><th>小区</th><th>户型/面积</th><th>总价</th><th>市场</th><th>适配</th><th>综合</th></tr>' +
        scored.map(h => '<tr><td>' + esc(h.xq) + '</td><td>' + esc(h.hx) + '/' + esc(h.area) + '㎡</td><td>' + esc(h.price) + '万</td><td><span class="score-badge blue">' + h.market + '</span></td><td><span class="score-badge orange">' + h.fit + '</span></td><td><span class="score-badge green">' + h.composite + '</span></td></tr>').join("") + '</table></div>';
    }
    html += '<div class="card"><h3>🔁 反向计算（E1）</h3><label>我每月能还（元）<input id="revInput" type="number" placeholder="8000"></label>' +
      '<button class="btn" id="revBtn">反推可买总价</button><p id="revOut"></p></div>';
  }
  $("resultArea").innerHTML = html;
  const rb = $("revBtn"); if (rb) rb.onclick = () => {
    const m = +$("revInput").value || 0;
    const r = reverseCalc(m, 30, 0.0305, 0.15);
    $("revOut").textContent = "可贷约 " + fmtW(r.loan) + " 元 → 可买总价约 " + fmtW(r.price) + " 元（" + Math.round(r.price/10000) + "万，首付15%）";
  };
}

// ---------- 政策（与 config/policy.example.json 对齐；改 policy 必须三处同步 + updated_at） ----------
const POLICY = { 首付: {首套:0.15, 二套:0.20}, 利率: {公积金首套:2.6, 商贷首套:3.05} };

// ---------- 示例数据（脱敏） ----------
const SAMPLE_HOUSES = [
  {xq:"示例·果园A区", hx:"2室1厅", area:98, price:260, avg:29000, floor:"中", lift:"有", metro:340, years:"满五", biz:"果园", age:24},
  {xq:"示例·北苑B区", hx:"2室2厅", area:99, price:228, avg:29000, floor:"高", lift:"有", metro:400, years:"满五", biz:"果园"},
  {xq:"示例·梨园C区", hx:"3室1厅", area:100, price:299, avg:32000, floor:"中", lift:"有", metro:100, years:"满五", biz:"梨园"},
  {xq:"示例·东坝D区", hx:"2室1厅", area:66, price:178, avg:29000, floor:"中", lift:"有", metro:1500, years:"满五", biz:"东坝"},
  {xq:"示例·回龙观E区", hx:"2室1厅", area:72, price:295, avg:42000, floor:"中", lift:"无", metro:800, years:"满二", biz:"回龙观"}
];
$("loadSample").onclick = () => { state.houses = SAMPLE_HOUSES.slice(); save(); renderHouses(); };
$("clearData").onclick = () => { localStorage.removeItem(STORE_KEY); location.reload(); };
$("printBtn").onclick = () => window.print();
$("calcBtn").onclick = () => gotoStep(5);

// 初始化
renderHouses();
["sellPrice","mortgageLeft","incomeAfterTax","cash","creditTotal","budget"].forEach(id => {
  if (state.sell && id in state.sell) $("revolving"); // noop 保持简单
});
