---
description: Code quality review — quick or deep mode. Covers file scan, cross-component audit, and fix loop.
---

# Code Review Workflow

**适用场景：** 代码质量审查，覆盖从快速扫描到生产级深度审计。
**Invoke:** `/code-review [quick|deep] [scope]`

| 模式 | 深度 | 轮次 | 适用 |
|------|------|------|------|
| **quick** | 只扫描指定文件/目录，1 轮 | 1 | PR review、单次改动后 |
| **deep** | 全量扫描+多轮迭代+场景验证 | 直到 0 bug | 发版前、重构后 |

**Scope examples:** `all`, `backend`, `frontend`, `scheduler`, `auth`

---

## Classification Rules（两种模式共用）

每个 finding MUST 归入以下三类之一：

### Confirmed Bug
- **要求：** 能描述具体的触发路径 + 错误行为
- **必须包含：** Trigger path / Actual vs Expected / Impact
- **排除：** 理论风险、死代码、"未来某人改了 X 会出问题"

### Code Smell / Tech Debt
- 冗余、死代码、次优模式
- 不导致错误行为，但影响可维护性
- **所有 Smell 必须立即修复，不分 P 级**

### Theoretical Risk
- 当前不可触达或极低概率的代码路径问题
- 必须标注概率和触发条件

### Verification Checklist（报告 Bug 前必须完成）

- [ ] **Caller check:** 这个函数真的被调用了吗？完整调用链是什么？
- [ ] **Execution path:** 逐步走一遍运行时流程。bug 真的会触发吗？
- [ ] **Guard check:** 有没有上游 guard/fallback 阻止了 bug？
- [ ] **Impact check:** 如果触发，实际可见的用户影响是什么？

任一检查失败 → 降级为 Smell 或 Risk。

---

## Quick Mode

### Step 1: Scan
- 读取指定范围内的文件（IN FULL）
- 应用 Classification Rules
- 输出 findings 列表

### Step 2: Fix
- 修复所有 Confirmed Bug + 所有 Smell
- 编译验证：
```bash
pytest tests/
cd web && npm run build
```
// turbo

### Step 3: Commit
```bash
git add -A ':!.tasks/*'
git commit -m "fix(review): <summary>"
```

---

## Deep Mode

### Phase 1: Scope & Inventory

1. 列出范围内所有源文件：
```bash
find src/src -name '*.ts' | head -30
find web/src -name '*.tsx' -o -name '*.ts' | head -30
find infra/ -name '*.sh' -o -name '*.yml' | head -20
```
// turbo

2. 按关键度排序：
   - **P0:** Entry points, schedulers, auth, data handling
   - **P1:** Routes, middleware, services
   - **P2:** UI components, utilities, config

3. 创建 `.tasks/audit-<date>.md`。

### Phase 2: Read & Classify（每轮）

4. 逐文件 IN FULL 读取 — 不 skim。
5. 应用 Classification Rules，写轮次报告 `audit_round<N>.md`。
6. **CRITICAL:** 不要 inflate smells into bugs.

### Phase 3: Fix & Verify（每轮）

7. 修复 ALL confirmed bugs + ALL smells（不分 P 级）。
   - 注释前缀 `// AUDIT <ID> fix:`
8. 编译验证。
9. 编译失败 → 立即修，不问用户。

### Phase 4: Iterate

10. Commit 本轮修复。
11. **Round N+1:** 重读所有 Round N 修改过的文件，检查：
    - 修复引入的回归
    - **平行路径漏修**（修了 done handler 但没修 polling fallback）
    - Env var 一致性（docker-compose files）
12. 重复 Phase 2→4 直到一轮产出 **zero confirmed bugs**。

### Phase 5: Scenario-Based Cross-Component Audit

> File-by-file 审计漏掉的 bug 在这里捕获。

13. 枚举关键用户场景：
    - [ ] 切换 workspace（run 进行中）→ activeTurnId 重置？WS 重连？
    - [ ] 发消息后立刻切 ws → optimistic turn 泄漏？
    - [ ] Run 完成后用户已切走 → done/polling 触发错误 loadTurns？
    - [ ] Cancel → 立即 retry → 状态机死锁？
    - [ ] F5 刷新 → workspace & activeTurnId 恢复？
    - [ ] WS 断连重连 → 事件去重？无遗漏？
    - [ ] 后端重启 → sandbox/run 状态恢复？

14. 对每个场景，追踪**完整调用链**：
    - Frontend: component → store → API → hook
    - Backend: route → service → scheduler → Redis → WS hub

15. 修复后强制 grep：
```bash
grep -rn 'loadTurns\|setActiveTurnId' web/src/
```
// turbo

### Phase 6: Final Report

16. 写 `walkthrough.md`：rounds / fixes / files / compilation / deferred items。

---

## Output Format

```markdown
## Confirmed Bugs

### BUG-1: [title]
- **Trigger:** [exact steps]
- **Impact:** [user-visible]
- **Files:** [file:line]

## Code Smells (ALL fixed)

### SMELL-1: [title]
- **Issue:** [description]
- **Fix:** [what was done]

## Theoretical Risks

### RISK-1: [title]
- **Condition:** [trigger requirement]
- **Probability:** [low/very low]
```

---

## Proven Patterns

1. **Parallel path regression** — 修一条路径必须 grep 所有平行路径
2. **Container env var drift** — 改名后 grep ALL compose files + spawn commands
3. **Duplicate cleanup** — 两处 cleanup = 数据丢失。选一个权威位置
4. **CLI fallback** — 依赖 docker.sock 的功能要有优雅降级
5. **Frontend auth cleanup** — `localStorage.clear()` 会删用户偏好
6. **Smell = immediate fix** — 发现就修，不留"下次"
7. **Cross-store leakage** — Store A 调 Store B.reset()，验证所有入口都走这条路
