---
description: Structured bug investigation and fix — root cause analysis, minimal fix, regression check.
---

# Bug Fix Workflow

**适用场景：** 单个 bug 的诊断和修复。批量修复用 `/global_hotfix`。
**流程：** `RESEARCH → PLAN → EXECUTE → VERIFY`

---

## Phase 1: RESEARCH — Root Cause Analysis

1. Create branch and task log:
```bash
git checkout -b fix/<id>
mkdir -p .tasks && touch .tasks/<id>.md
```
// turbo

2. **Reproduce** — 追踪触发路径：
   - 读 error logs、stack traces、用户描述
   - 确定入口点（API endpoint / UI 操作 / background task）
   - 沿调用链跟踪：caller → function → downstream effects

3. **Isolate** — 定位到具体代码：
   - 用 `rg` 和 `view_file` 追踪数据流
   - 检查上游 guard/fallback
   - **确认 bug 可触发**（不是理论风险）

4. **Cross-Impact Check** — 检查平行路径是否存在相同 bug：
```bash
grep -rn '<buggy_pattern>' src/
```
// turbo

5. 记录到 `.tasks/<id>.md`：
```markdown
## Root Cause
- **Trigger:** [exact steps]
- **Location:** [file:line]
- **Cause:** [why it fails]
- **Impact:** [user-visible effect]
- **Parallel paths:** [同一 bug 的其他出处]
```

**EXIT GATE:** 根因确认 + 平行路径检查完成。

---

## Phase 2: PLAN — Minimal Fix

6. 设计最小修复方案：
   - MUST 修复根因，不是症状
   - MUST NOT 引入修复之外的行为改变
   - 平行路径有同样 bug → **一起修**

7. 写 checklist：
```markdown
## FIX CHECKLIST
1. [ ] [file:line] Change X to Y (reason)
2. [ ] [parallel-file:line] Same fix applied to parallel path
3. [ ] Compilation check
```

**EXIT GATE:** 修复计划就绪。ZERO code changes.

---

## Phase 3: EXECUTE

8. 按 checklist 精确修复。注释前缀 `// FIX-<id>:`。

9. 编译/Lint 检查（使用项目的编译命令）。

10. Self-Heal: 编译失败 → 自主修复，最多 3 次。

**EXIT GATE:** 修复完成，编译通过。

---

## Phase 4: VERIFY

11. 验证：
    - 根因消除（不只是症状消失）
    - 平行路径一起修了
    - 无 unrelated code 被改动

12. Commit:
```bash
git add -A ':!.tasks/*'
git commit -m "fix(<scope>): <description>

Root cause: <one-line explanation>
Parallel fix: <if applicable>"
```

**EXIT GATE:** Committed. Root cause in commit body.

---

## Anti-Patterns

1. **不要只修症状** — UI 显示错，要找数据源头
2. **不要忘记平行路径** — handler A 修了，handler B 也要检查
3. **不要扩大范围** — 修 bug 时发现 smell，另开 task 处理
