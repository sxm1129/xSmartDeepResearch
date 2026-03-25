---
description: End-to-end feature development — from requirement alignment to verified commit. Enforces DISCOVER → RESEARCH → PLAN → EXECUTE → VERIFY mode transitions.
---

# Feature Development Workflow

**适用场景：** 新增功能、重构、跨组件改动。
**团队模型：** 小团队 + AI 辅助，单/多仓库架构。
**核心目标：** 鲁棒性 > 速度 > 覆盖率。

```
DISCOVER (可跳过) → RESEARCH → PLAN → EXECUTE → VERIFY
```

---

## Phase 0: DISCOVER (Requirement Alignment)

> 需求已 100% 明确时跳过此阶段。
> 只有**跨层功能**或**需求边界模糊**时才走 DISCOVER。

**Step 1: 复述理解** — 用 2-3 句话总结：
- 功能做什么（Functional）
- 谁用（User-facing / Admin / Backend-only）
- 在哪层（Frontend / Backend API / Infra / Cross-cutting）

**Step 2: 澄清提问** — 有疑问时，用以下格式**批量**提问：

```
**Q1: [问题描述]**

| 选项 | 描述 | 优劣 |
|------|------|------|
| A | ... | 优：... / 缺：... |
| B | ... | 优：... / 缺：... |

> **推荐方案：B** — [一句话理由]
```

**提问规则：**
- 每个问题 MUST 带 2-3 个选项 + 优劣 + 明确推荐
- 独立问题一次问完，依赖问题只问第一个
- 信息足够就跳过

**Step 3: 划定边界**
```
IN SCOPE:  [...]
OUT OF SCOPE: [...（后续迭代）]
ROLLBACK: [如果上线后出问题，可安全 revert 的 commit 范围]
```

**EXIT GATE:** 用户确认理解正确。ZERO code read, ZERO code changes.

---

## Phase 1: RESEARCH

> 读代码、想方案、分析影响面一气呵成。

### 1.1 环境准备
```bash
git checkout -b task/<id>
mkdir -p .tasks && touch .tasks/<id>.md
```
// turbo

### 1.2 代码调研

读取所有受影响的文件（IN FULL），记录到 `.tasks/<id>.md`：
- Affected files（with line ranges）
- Existing patterns to follow
- API contracts, DB schemas
- Potential conflict points

### 1.3 方案设计

列 2-3 个候选方案，标注 **Pros / Cons / Complexity**，选定一个。
记录到 `.tasks/<id>.md ## Design Decision`。

### 1.4 影响面分析（CRITICAL）

> 跨组件 bug 必须在编码前映射。

**State Flow Mapping** — 对新增/修改的状态，grep 所有读写者：
```bash
grep -rn '<state_name>\|<setter_name>' src/
```
// turbo

**Cross-Module Check** — 如果修改了模块 A，grep 所有 import A 的文件。
记录每条跨模块调用链。

**Async Callback Audit** — 列出新功能涉及的所有异步回调（WS, polling, setTimeout），
对每个回答：closure 里引用的 state 在执行时是否可能已过期？

记录到 `.tasks/<id>.md ## Impact Surface`。

**EXIT GATE:** 方案选定 + 影响面文档化。ZERO code changes.

---

## Phase 2: PLAN

**Goal:** 按依赖序写有序 checklist，标注风险点和 rollback 策略。

### Checklist 格式

```markdown
## IMPLEMENTATION CHECKLIST

### Backend / API（先实现，先提交）
1. [ ] `<path>` — <description>
2. [ ] `<path>` — <description>

### Frontend / Web（后实现，后提交）
3. [ ] `<path>` — <description>
4. [ ] `<path>` — <description>

### Cross-Cutting（跨层风险项，必须显式标注）
5. [ ] [Cross-Module] `<path>` — <description>
6. [ ] [Async-Guard] `<path>` — 新 callback 需 ref 校验
7. [ ] [Parallel-Path] 如修改路径 A，同步修改路径 B

### Rollback 策略
- Backend commit 可独立 revert（不影响前端）
- Frontend commit 依赖 Backend，revert 需同时回退
```

**规则：**
- 按**层**分组（Backend → Frontend → Cross-Cutting）
- Cross-Cutting 项必须带标签：`[Cross-Module]` / `[Async-Guard]` / `[Parallel-Path]`
- 包含 Rollback 策略

**EXIT GATE:** 用户 approve checklist。ZERO implementation code written.

---

## Phase 3: EXECUTE

**Goal:** 按 checklist 实现，按层提交，编译驱动验证。

> **自主执行：** checklist 项之间不需要询问用户。遇到阻塞时才报告。

### 3.1 实现

按 checklist 顺序逐项实现：
- Mark `[/]` when starting，`[x]` when done
- 遵循项目已有编码约定
- 已有文件用最小 diff 修改，不整文件重写
- 注释前缀 `// <FEATURE-ID>:` 保留可追溯性

### 3.2 验证（每完成一层）

**编译/Lint 检查（必做）** — 使用项目的编译命令。
**状态 grep（涉及共享状态变更时必做）：**
```bash
grep -rn '<new_setter_or_handler>' src/
```
// turbo

**Self-Heal：** 编译失败 → 自主诊断修复，最多 3 次。3 次仍败 → 报告用户。

### 3.3 按层提交

**一个功能通常 2-3 个 commit：**

```bash
git add -A ':!.tasks/*'
git commit -m "<type>(<layer>): <description>

- Implementation: <技术决策说明>
- Affected files:
  * <path1>
  * <path2>"
```

**Commit 规范：**
- Types: `feat`, `fix`, `refactor`, `perf`, `docs`, `test`, `chore`
- Scope: `<feature>-<layer>`
- Body: 必须包含 Implementation 说明 + Affected files
- 跨模块变更显式标注 `Cross-Module:` / `Async-Guard:`

### 3.4 进度记录

在 `.tasks/<id>.md` 更新执行状态。

**EXIT GATE (per layer):** 编译通过 + 已提交 + 进度已记录。

---

## Phase 4: VERIFY

> 功能全部开发完成后，一次性做完整验证。

### 4.1 Plan vs Implementation

对照 checklist 逐项确认。

### 4.2 Cross-Cutting Audit

**Parallel Path Grep** — 修了任何事件/状态路径后，grep 所有平行路径。
**Cross-Module Integrity** — 重读修改过的模块的所有 importer。
**Smell Sweep** — `// TODO`、`catch {}`、hardcoded values、boolean flags。

### 4.3 Scenario Path Verification

- [ ] Happy path
- [ ] 操作过程中切换上下文 → 状态隔离？
- [ ] 异步操作超时/失败 → 错误处理正确？
- [ ] 与现有功能交互 → 无回归？
- [ ] 页面刷新 → 状态恢复？

### 4.4 E2E 验证（可选但推荐）

对 UI 可见的功能，用 `/global_e2e-test` 做浏览器端验证。

### 4.5 修复 & 收尾

发现问题则修复后 amend 最近的 commit。

**EXIT GATE:** checklist 全 [x] + 场景验证通过 + 编译通过 + Smell 零发现。

---

## Testing Strategy（根据项目调整）

| 层 | 推荐测试方式 | 理由 |
|---|---|---|
| **核心业务逻辑** | 单元测试（vitest/jest/pytest） | 逻辑复杂、状态多、回归成本高 |
| **API/路由** | 编译 + 手动验证 | 主要是胶水代码 |
| **前端 Store/State** | 编译 + Cross-Module grep | 跨模块交互是主要风险 |
| **前端 UI** | E2E 浏览器测试 | 视觉和交互只能在浏览器验证 |

---

## Proven Patterns

1. **Impact Surface First** — 写 Plan 前先 grep "谁在读我改的状态"
2. **修一条路径，grep 所有平行路径** — handler A 和 handler B 是同一逻辑的两条路
3. **Closure 过期检查** — 异步回调引用的 state 必须用 ref 或执行时重新获取
4. **Cross-Module Reset 集中化** — 模块 A 调模块 B.reset() 放在 A 内部，不分散在 UI 层
5. **No Deferred Smells** — 发现就修，不留"下次"
6. **按层提交** — 方便独立 revert，保持 git log 可读
7. **Rollback 前置** — Plan 阶段就标注 rollback 策略
