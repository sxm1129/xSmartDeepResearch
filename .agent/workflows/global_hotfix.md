---
description: Rapid batch fix loop — audit finding → code fix → compile → commit. For fixing multiple known issues.
---

# Hotfix Workflow

**适用场景：** 批量修复来自审计报告或 bug 列表的已知问题。
**与 /global_bugfix 的区别：** bugfix 深度调查单个 bug；hotfix 用于多个已确认问题的快速逐个修复。
**流程：** `理解 → 修复 → 编译 → 下一个`（循环）

---

## Setup

1. 读取审计报告或 issue 列表。
2. 制定执行计划：
   - 按**文件**分组（减少上下文切换）
   - 按依赖序排列
   - 合并涉及**同一行**的修复

---

## Per-Issue Loop

### Step 1: Understand
- `view_file` 读取受影响代码
- 追踪调用链，确认 bug 存在
- NOT real → skip, note as "downgraded"

### Step 2: Fix
- targeted edits only（`replace_file_content` / `multi_replace_file_content`）
- 注释前缀 `// AUDIT <ID> fix:`
- **NEVER 整文件重写**

### Step 3: Parallel Path Check
```bash
grep -rn '<修复涉及的函数/模式名>' src/
```
// turbo

### Step 4: Compile
- 每个**文件**改完后编译（使用项目的编译命令）
- 编译失败 → 立即修

### Step 5: Next

---

## Batch Commit

1. 展示 diff 概览：
```bash
git diff --stat HEAD
```
// turbo

2. Commit:
```bash
git add -A ':!.tasks/*'
git commit -m "<type>(<scope>): <summary>

- <ID-1>: <fix>
- <ID-2>: <fix>"
```

---

## Anti-Patterns

1. **不要逐 issue 提交** — 批量一次 commit
2. **不要跳过文件间编译** — 早发现回归
3. **不要忘记平行路径** — 修一条路必须检查所有平行路径
4. **不要只 grep 当前文件** — env var 改名要 grep ALL config files
