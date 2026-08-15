# TODOS.md — house-swap 待办池

> 由 /autoplan 2026-08-15 收集（跨 Phase 自动写入）

## P0（发布阻塞 — 修复后 CI 才能绿）
- [ ] 修复 JS threePlans disposable 回退（web/engine.js:125）→ 看板 null% 消失
- [ ] CLI _load_json 失败时报错（不再静默回退样例）
- [ ] 添加 .github/workflows/ci.yml（node test + python test + compare.sh + policy updated_at 校验）

## P1（发布前完成）
- [ ] citySel 城市切换接入（E5 真正落地）或从 UI 移除（死 UI 二选一）
- [ ] policy-shanghai.json 接入 CLI --policy 用法文档
- [ ] 非法 JSON 输入 → 友好报错而非裸 traceback

## P2（v1.1 / 按需）
- [ ] risk.py 9 边界用例补进 __main__ 自测
- [ ] 看板 UI 自动化测试（无框架，可用 Playwright 或手工清单）
- [ ] 社区脱敏样本库 E6（先观望，0 需求证据）

## Deferred（v2 — CEO/Eng 双 voice 共识）
- [ ] LLM 自然语言顾问小结（BYO key）
- [ ] 本地服务版（house-scrape 桥接采集）
- [ ] 向导式交互（替代手动表单，Option C 复活）

## 战略优先级（双 voice 高置信）
- [ ] 本周末：真实 profile + Top10 收藏跑 finance+risk，出短名单（owner 决策优先于开源打磨）
