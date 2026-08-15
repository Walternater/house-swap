# house-analyze 输入 Schema（采集 → 分析 数据契约）

> 本文声明 house-analyze（Python 引擎）与 web/ 看板共用的**输入 JSON 结构**，
> 对齐三处：`web/engine.js` 读取字段 + `config/user_profile.example.json` + `config/policy.example.json`。
>
> **唯一数学契约**：`docs/决策引擎-spec.md`（公式/权重/边界以 spec 为准，改公式三处同步）。
> **采集技能** house-scrape **不在本仓库**（合规，见 `docs/faq.md`）；本文只做格式对接。

---

## 1. 顶层结构

一个完整的分析输入（建议单文件，如 `data/input.json`）：

```jsonc
{
  "houses": [ /* 房屋记录数组，来自 house-scrape 采集或手动录入 */ ],
  "user":   { /* 用户财务，对齐 config/user_profile.example.json */ },
  "policy": { /* 政策，对齐 config/policy.example.json */ }
}
```

## 2. 房屋记录 houses[]

### 2.1 核心字段（与 web/engine.js + 看板导入字段对齐）

> 字段名与 `web/app.js` 采集的 `.house-row` 输入完全一致（`xq/hx/area/price/avg/floor/lift/metro/years/biz`），
> 采集输出经**归一化**后直接可喂引擎。

| 字段 | 类型 | 必填 | 说明 | 看板/引擎对应 | 示例 |
|---|---|---|---|---|---|
| `xq` | string | 建议 | 小区名（**脱敏**） | 展示用，不参与评分 | `示例·北苑1区` |
| `hx` | string | 建议 | 户型，如 `2室1厅` | 评分需映射 `layout` | `2室1厅` |
| `area` | number | **必填** | 面积（㎡） | 引擎 `area` | `98.0` |
| `price` | number | **必填** | 总价（万） | 引擎 `price` | `270.9` |
| `avg` | number | 建议 | 小区均价（元/㎡），计算单价性价比 | 引擎 `avgUnit` | `24092` |
| `floor` | string | 建议 | 楼层：中/低/高/顶/底 | 引擎 `floor` | `中楼层` |
| `lift` | string | 建议 | 电梯：`有` / `无` | 引擎 `elevator` | `有` |
| `metro` | number | 建议 | 最近地铁距离（米） | 引擎 `metroM` | `800` |
| `years` | string | 建议 | `满五唯一` / `满五` / `满二` / `未满二` | 引擎 `years` | `满五` |
| `biz` | string | 建议 | 商圈 | 引擎 `biz` | `通州北苑` |

### 2.2 评分补充字段（引擎直接读取；采集可带 / 可推导 / 缺省走最保守）

| 字段 | 类型 | 必填 | 说明 | 缺省（引擎默认档） | 示例 |
|---|---|---|---|---|---|
| `age` | number | 选填 | 楼龄（年） | 缺省 `30`（最保守，spec §6） | `24` |
| `unit` | number | 选填 | 单价（元/㎡）；**可推导** `price×10000/area` | 缺省跳过性价比评分 | `27643` |
| `orient` | string | 选填 | 朝向：南北/南/东南/西南/东/西/东北/西北/北 | 其他档 | `南` |
| `structure` | string | 选填 | 建筑结构：板楼/板塔/塔楼 | 其他档 | `板塔` |
| `listDays` | number | 选填 | 挂牌天数（滞销信号） | 缺省 `3` 分档 | `60` |
| `parking` | string | 选填 | 车位：`有车位`/`地库`/`无` | 无 → 0 分 | `有车位` |

### 2.3 字段映射：采集原始字段 → 分析字段

house-scrape 原始输出（参考 `data/sample/sample-houses.json`）与引擎字段的换算关系：

| 采集原始字段 | 分析字段 | 换算规则 |
|---|---|---|
| `小区` | `xq` | 直接复制（脱敏后） |
| `户型` | `hx` / `layout` | 复制；引擎评分用 `layout`（含 `2室/3室/两居/三居`） |
| `面积` | `area` | 直接复制 |
| `挂牌价万` | `price` | 直接复制 |
| `单价元平` | `avg` | 作小区均价；本房 `unit` 建议用 `挂牌价万×10000/面积` 重算（与看板一致） |
| `楼层` | `floor` | 取关键词：中/低/高/顶/底（引擎按 `includes` 匹配） |
| `电梯` | `lift` | 直接复制（有/无） |
| `朝向` | `orient` | 直接复制 |
| `年限` | `years` | 归一化：`满五年→满五`、`未满两年→未满二`、`满五年唯一→满五唯一`（引擎按 `includes("满五"/"满二"/"满")` 匹配，可容错） |
| `商圈` | `biz` | 直接复制（果园/北苑/北关/梨园/九棵树/潞苑/东坝 命中加分） |
| — | `age` / `structure` / `listDays` / `parking` / `metro` | 采集接口未提供时手动补或走缺省（§2.2） |

### 2.4 与 web/engine.js 评分函数实际读取字段对照

| schema 字段 | `marketScore` 读取 | `fitScore` 读取 | 说明 |
|---|---|---|---|
| `xq` | — | — | 展示 |
| `hx` | — | `layout` | **需映射 `layout`** |
| `area` | — | `area` | |
| `price` | — | `price` | |
| `avg` | `avgUnit` | — | **需映射 `avgUnit`** |
| `floor` | `floor` | `floor` | |
| `lift` | `elevator` | `elevator` | **需映射 `elevator`** |
| `metro` | — | `metroM` | **需映射 `metroM`** |
| `years` | `years` | `years` | |
| `biz` | — | `biz` | |
| `age` | `age` | `age` | |
| `unit` | `unit` | — | 推导 |
| `orient` | `orient` | — | |
| `structure` | `structure` | — | |
| `listDays` | `listDays` | — | |
| `parking` | — | `parking` | |

## 3. 用户财务 user（对齐 config/user_profile.example.json）

| 字段 | 类型 | 必填 | 默认 | 说明 | user_profile.example.json 对应 |
|---|---|---|---|---|---|
| `sellPrice` | number | **必填** | — | 卖房成交价（万），须 >0 | `卖房预估成交万` |
| `mortgageLeft` | number | **必填** | — | 房贷剩余（万），须 ≥0 | `房贷剩余.公积金万 + 商贷万` |
| `incomeAfterTax` | number | **必填** | — | 税后月薪（元），须 >0 | `收入.税后月薪` |
| `gjjWithdraw` | number | 建议 | `0` | 公积金月提取（元） | `收入.公积金月提取` |
| `cash` | number | **必填** | — | 手头现金（万），须 ≥0 | `手头现金万` |
| `agentFee` | number | 选填 | `0.015` | 中介费率（1.5%~2.7%） | — |
| `taxVAT` | number | 选填 | `0` | 增值税比例（满2年=0） | — |
| `taxIncome` | number | 选填 | `0` | 个税比例（满五唯一=0/核定1%） | — |
| `creditTotal` | number | 选填 | `0` | 全清信用贷所需（万） | `信用贷结构`（汇总） |
| `creditMonthly` | number | 选填 | `0` | 保留信用贷月供（元） | `月供.信用贷` |
| `hasYearlyRevolving` | boolean | 选填 | `false` | 是否"按年归本再贷"（E2 -10） | `信用贷结构`（含"按年归本再贷"） |
| `borrowPower` | number | 选填 | `0` | 短期可借款能力（万） | — |
| `gjjMax` | number | 选填 | `120` | 公积金可贷上限（万），clamp 0~200 | — |
| `timing` | string | 选填 | — | `先卖后买`/`先买后卖`/`同时`（risk 模块） | — |
| `revolvingDate` | string | 选填 | — | 归本日提示（risk 模块） | `归本日` |

## 4. 政策 policy（对齐 config/policy.example.json）

> 引擎只读取下面加粗两项；完整字段（含 updated_at/来源）供 CI 校验与展示。

```jsonc
{
  "首付": { "首套": 0.15 },                    // finance_calc 读取
  "利率": { "公积金首套": 2.6, "商贷首套": 3.05 },  // finance_calc / three_plans 读取
  "updated_at": "2026-08-15",
  "来源": "中国人民银行/北京市住建委/链家研究院公告"
}
```

## 5. 采集 → 分析 端到端示例（脱敏）

> 结构取自真实北京置换案例，**数值已扰动、ID 伪造、小区名脱敏**（铁律 3）。
> 保存为 `data/input.json` 后可直接被引擎消费。

```json
{
  "houses": [
    {
      "xq": "示例·北苑1区", "hx": "2室1厅", "area": 98.0, "price": 270.9,
      "avg": 24092, "floor": "中楼层", "lift": "有", "metro": 800,
      "years": "满五", "biz": "通州北苑",
      "age": 24, "unit": 27643, "orient": "南", "structure": "板塔",
      "listDays": 60, "parking": "有车位"
    },
    {
      "xq": "示例·梨园5区", "hx": "3室1厅", "area": 100.0, "price": 292.0,
      "avg": 27037, "floor": "中楼层", "lift": "有", "metro": 300,
      "years": "满五", "biz": "通州梨园",
      "age": 18, "unit": 29200, "orient": "东南", "structure": "板楼",
      "listDays": 45, "parking": "有车位"
    },
    {
      "xq": "示例·果园13区", "hx": "3室2厅", "area": 115.0, "price": 340.0,
      "avg": 25236, "floor": "中楼层", "lift": "无", "metro": 1500,
      "years": "满五", "biz": "通州果园",
      "age": 22, "unit": 29565, "orient": "南", "structure": "板塔",
      "listDays": 30, "parking": "无车位"
    }
  ],
  "user": {
    "sellPrice": 140, "mortgageLeft": 93.1, "agentFee": 0.015,
    "taxVAT": 0, "taxIncome": 0,
    "cash": 30, "creditTotal": 80, "creditMonthly": 6868,
    "incomeAfterTax": 27000, "gjjWithdraw": 8500, "gjjMax": 120,
    "borrowPower": 0, "hasYearlyRevolving": true,
    "timing": "先卖后买", "revolvingDate": "2026-09 待确认"
  },
  "policy": {
    "首付": { "首套": 0.15 },
    "利率": { "公积金首套": 2.6, "商贷首套": 3.05 },
    "updated_at": "2026-08-15",
    "来源": "中国人民银行/北京市住建委/链家研究院公告"
  }
}
```

### 5.1 消费方式（Python 引擎，纯标准库）

```python
import json, sys
sys.path.insert(0, "skills/house-analyze/scripts")
from engine_py import composite_score, finance_calc, feasibility_index

d = json.load(open("data/input.json"))
for h in d["houses"]:
    print(h["xq"], composite_score(h))
f = finance_calc(d["user"], d["policy"])
print("可行性指数:", feasibility_index(f, d["user"]))
```

> 注：CLI 入口 `house_analyze.py --help` 见 README；当前可直接调模块函数。

## 6. 边界与缺省（spec §6 生效）

- `price / area / incomeAfterTax / sellPrice ≤ 0`：拒绝计算（`validate_inputs` 提示）
- `mortgageLeft / cash < 0`：拒绝计算
- 楼龄缺失 → `age=30`（最保守）；年限缺失 → `years` 空串 → 得分档最低
- 月供计算 `years=0` 或利率 `=0` → 降级等额本金（`pmt`）
- 采集字段缺失按 §2.2 默认档计分，不报错
