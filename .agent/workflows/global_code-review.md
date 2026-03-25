---
description: Code quality review — quick or deep mode. Covers file scan, cross-component audit, and fix loop.
---

# Code Review Workflow

**Invoke:** `/global_code-review [quick|deep] [scope]`

| 模式 | 深度 | 轮次 | 适用 |
|------|------|------|------|
| **quick** | 指定文件/目录，1 轮 | 1 | PR review、单次改动后 |
| **deep** | 全量扫描+多轮迭代+场景验证 | 直到 0 bug | 发版前、重构后 |

---

## Classification Rules

### Confirmed Bug
- 具体触发路径 + 错误行为
- 必须包含：Trigger / Actual vs Expected / Impact

### Code Smell / Tech Debt
- **所有 Smell 必须立即修复，不分 P 级**

### Theoretical Risk
- 标注概率和触发条件

### Verification Checklist（报告 Bug 前必须完成）
- [ ] **Caller check:** 函数真的被调用了？完整调用链？
- [ ] **Execution path:** 逐步走运行时流程，bug 真的触发？
- [ ] **Guard check:** 有上游 guard/fallback 阻止 bug？
- [ ] **Impact check:** 用户可见的实际影响？

任一失败 → 降级为 Smell 或 Risk。

---

## Quick Mode

1. 读取指定范围文件（IN FULL）
2. 应用 Classification Rules
3. 修复所有 Bug + Smell
4. 编译验证 + Commit

---

## Deep Mode

### Phase 1: Scope & Inventory
- 列出范围内所有源文件
- 按关键度排序（P0 → P1 → P2）
- 创建 `.tasks/audit-<date>.md`

### Phase 2: Read & Classify（每轮）
- 逐文件 IN FULL 读取
- 写轮次报告
- **不 inflate smells into bugs**

### Phase 3: Fix & Verify（每轮）
- 修复 ALL bugs + ALL smells
- 注释前缀 `// AUDIT <ID> fix:`
- 编译失败 → 立即修

### Phase 4: Iterate
- Commit 本轮
- Round N+1: 重读修改过的文件，检查回归和**平行路径漏修**
- 重复直到 zero confirmed bugs

### Phase 5: Scenario-Based Cross-Component Audit
- 枚举关键用户场景
- 对每个场景追踪完整调用链（component → store → API → service）
- 修复后强制 grep 平行路径

### Phase 6: Final Report
- `walkthrough.md`：rounds / fixes / files / deferred items

---

## Output Format

```markdown
## Confirmed Bugs
### BUG-1: [title]
- **Trigger:** [steps]
- **Impact:** [user-visible]
- **Files:** [file:line]

## Code Smells (ALL fixed)
### SMELL-1: [title]
- **Issue / Fix:** [description]

## Theoretical Risks
### RISK-1: [title]
- **Condition / Probability:** [details]
```

---

## Proven Patterns

1. **Parallel path regression** — 修一条路径必须 grep 所有平行路径
2. **Config drift** — 改名后 grep ALL config/compose/env files
3. **Duplicate cleanup** — 两处 cleanup = 数据丢失，选一个权威位置
4. **Smell = immediate fix** — 发现就修，不留"下次"
5. **Cross-module leakage** — Module A 调 B.reset()，验证所有入口都走这条路
