---
description: Rapid batch fix loop — audit finding → code fix → compile → commit. For fixing multiple known issues.
---

# Hotfix Workflow

**适用场景：** 批量修复来自审计报告或 bug 列表的已知问题。
**与 /bugfix 的区别：** bugfix 用于单个 bug 的深度调查；hotfix 用于多个已确认问题的快速逐个修复。
**流程：** `理解 → 修复 → 编译 → 下一个`（循环）

**Invoke:** `/hotfix`
**Input:** 审计报告或 issue 列表。

---

## Setup

1. 读取审计报告或 issue 列表。

2. 制定执行计划：
   - 按**文件**分组（减少上下文切换）
   - 按依赖序排列（底层先修）
   - 合并涉及**同一行**的修复

---

## Per-Issue Loop

对每个 issue 执行紧凑循环：

### Step 1: Understand
- `view_file` 读取受影响代码
- 追踪调用链，确认 bug 存在
- NOT real → skip and note as "downgraded"

### Step 2: Fix
- `replace_file_content` 处理连续编辑
- `multi_replace_file_content` 处理分散编辑
- 注释前缀 `// AUDIT <ID> fix: <brief>`
- **NEVER 整文件重写**

### Step 3: Parallel Path Check
- 修完一个路径后，**立即 grep 平行路径**：
```bash
grep -rn '<修复涉及的函数或模式名>' web/src/ src/
```
// turbo
- 同一 bug 的平行路径一起修

### Step 4: Compile
- 每个**文件**改完后编译（不是每个 fix 后）：
```bash
pytest tests/
cd web && npm run build
```
// turbo
- 编译失败 → 立即修，不跳到下一个 issue

### Step 5: Next
- 标记 issue 完成
- 下一个 issue

---

## Batch Commit

全部 issue 修完且编译通过后：

1. 展示 diff 概览：
```bash
git diff --stat HEAD
```
// turbo

2. Commit:
```bash
git add -A ':!.tasks/*'
git commit -m "<type>(<scope>): <summary>

- <ID-1>: <fix description>
- <ID-2>: <fix description>
- <ID-N>: <fix description>"
```

---

## Anti-Patterns

1. **不要逐 issue 提交** — 批量一次 commit，效率优先
2. **不要跳过文件间编译** — 早发现回归
3. **不要忘记平行路径** — HOT PATH 修了，WARM/COLD PATH 也要检查
4. **不要 `write_to_file` + Overwrite** — 始终用 targeted edits
5. **不要只 grep 当前文件** — env var 改名要 grep ALL compose files + spawn commands
