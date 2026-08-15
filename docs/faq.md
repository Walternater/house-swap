# 常见问题 FAQ

## 采集 → 分析：数据链路

### 为什么采集技能 house-scrape 不在本仓库？

合规原因。`house-scrape` 从链家/贝壳等平台抓取房源数据，涉及平台数据使用条款与隐私，
属于**个人自用技能**，不随本开源仓库分发。

- 本仓库（`house-swap`）只含**分析决策**：`web/` 看板 + `skills/house-analyze` 分析技能。
- 两端通过**格式契约**解耦，不共享代码：`skills/house-analyze/references/schema.md`。

### 怎么把采集的数据导入分析？

1. **采集端**：`house-scrape` 输出房源 JSON（原始字段见
   `data/sample/sample-houses.json` 的结构：小区/商圈/户型/面积/朝向/楼层/电梯/挂牌价万/单价元平/年限）。
2. **归一化**：按 `references/schema.md` §2.3 的映射表，把原始字段转成
   `xq/hx/area/price/avg/floor/lift/metro/years/biz` + 评分补充字段（`age/unit/orient/structure/listDays/parking`）。
3. **财务**：填 `config/user_profile.json`（复制 `config/user_profile.example.json`，已被 `.gitignore` 忽略，不会提交）。
4. **组装**：`{ "houses": [...], "user": {...}, "policy": {...} }` 存为 `data/input.json`，
   参考 `references/schema.md` §5 端到端示例（脱敏）。
5. **跑分析**：
   ```bash
   python3 skills/house-analyze/scripts/house_analyze.py --help   # CLI（脚本见 README）
   # 或直接调模块：
   python3 -c "import json,sys; sys.path.insert(0,'skills/house-analyze/scripts'); from engine_py import *; \
   d=json.load(open('data/input.json')); [print(h['xq'],composite_score(h)) for h in d['houses']]"
   ```

### 数据脱敏要求（铁律）

- 提交到本仓库的任何**示例**数据必须脱敏：结构保留 + 数值扰动（价格 ±15%）、ID 伪造、小区名改为 `示例·XX区`。
- 真实房源/真实财务数据只放本地（`config/user_profile.json`、`data/` 下的私有文件），禁止提交。

### 数据隐私

- `web/` 看板所有计算在浏览器本地完成，数据不上传；财务数据仅存 localStorage，可一键清除。
- 政策口径（利率/首付/税费）见 `config/policy.example.json`，带 `updated_at` + 来源；政策会变，以银行/税务面签为准。

## 其他

- 决策引擎的 JS / Python 双实现与 spec 的关系见 `CONTRIBUTING.md`。
- 输出为**估算参考**，不构成投资/贷款建议。
