---
description: End-to-end feature development — from requirement alignment to verified commit. Enforces DISCOVER → RESEARCH → PLAN → EXECUTE → VERIFY mode transitions.
---

# Feature Development Workflow

**适用场景：** 新增功能、重构、跨组件改动。
**团队模型：** 1 人开发 + AI 辅助，单仓库多服务架构。
**核心目标：** 鲁棒性 > 速度 > 覆盖率。

```
DISCOVER (可跳过) → RESEARCH → PLAN → EXECUTE → VERIFY
```

---

## Phase 0: DISCOVER (Requirement Alignment)

> 需求已经 100% 明确时（如"加个导出按钮"），跳过此阶段直接进 Phase 1。
> 只有**跨层功能**或**需求边界模糊**时才需要走 DISCOVER。

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
- 不为问而问——信息足够就跳过

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

读取所有受影响的文件（IN FULL — 不 skim），记录到 `.tasks/<id>.md`：
- Affected files（with line ranges）
- Existing patterns to follow
- API contracts, DB schemas
- Potential conflict points

### 1.3 方案设计

列 2-3 个候选方案，每个标注 **Pros / Cons / Complexity**，然后选定一个。
记录到 `.tasks/<id>.md ## Design Decision`。

### 1.4 影响面分析（CRITICAL）

> 这一步防止了 BUG-MR-1/2/3 和 BUG-SC-1 类跨组件 bug。

**State Flow Mapping** — 对每个新增/修改的状态，grep 出所有读写者：
```bash
grep -rn '<state_name>\|<setter_name>' web/src/
grep -rn '<api_field>\|<db_column>' src/
```
// turbo

**Cross-Store Check** — 如果修改了 Store A，grep 所有 import Store A 的文件。
记录每条跨 store 调用链（如 `workspaceStore.selectWorkspace → chatStore.clearChat`）。

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
1. [ ] `src/db/migrations/xxx.sql` — 新增 foo 表
2. [ ] `src/services/foo_service.py` — CRUD + 参数校验
3. [ ] `src/api/foo.py` — GET/POST /v1/foo endpoint

### Frontend / Web（后实现，后提交）
4. [ ] `web/services/api.ts` — fooApi 客户端
5. [ ] `web/stores/fooStore.ts` — zustand store
6. [ ] `web/components/FooCard.tsx` — UI 组件

### Cross-Cutting（跨层风险项，必须显式标注）
7. [ ] [Cross-Store] `workspaceStore.ts` — selectWorkspace 调用 fooStore.reset()
8. [ ] [Async-Guard] `ChatPanel.tsx` — 新 callback 需 currentWsIdRef 校验
9. [ ] [Parallel-Path] 如修改 done handler，同步修改 polling fallback

### Rollback 策略
- Backend commit 可独立 revert（不影响现有前端）
- Frontend commit 依赖 Backend，revert 需同时回退
```

**规则：**
- 按**层**分组（Backend → Frontend → Cross-Cutting），不按文件拆模块
- Cross-Cutting 项必须带 `[Cross-Store]` / `[Async-Guard]` / `[Parallel-Path]` 标签
- 每个 checklist 项标注文件路径 + 一句话说明
- 包含 Rollback 策略（哪些 commit 可以安全独立 revert）

**EXIT GATE:** 用户 approve checklist。ZERO implementation code written.

---

## Phase 3: EXECUTE

**Goal:** 按 checklist 顺序实现，按层提交，编译驱动验证。

> **自主执行：** checklist 项之间不需要询问用户。遇到阻塞时才报告。

### 3.1 实现

按 checklist 顺序逐项实现：
- Mark `[/]` when starting，`[x]` when done
- 遵循项目约定（strict types, zustand patterns, parameterized SQL）
- 已有文件用最小 diff 修改，不整文件重写
- 注释前缀 `// <FEATURE-ID>:` 保留可追溯性

### 3.2 验证（每完成一层）

**编译检查（必做）：**
```bash
pytest tests/
cd web && npm run build
```
// turbo

**状态 grep（涉及 store/event 时必做）：**
```bash
# 修了 done handler？检查 polling fallback 是否也修了
grep -rn 'loadTurns\|setActiveTurnId\|clearChat' web/src/
```
// turbo

**Self-Heal：** 编译失败 → 自主诊断修复，最多 3 次。3 次仍败 → 报告用户。

### 3.3 按层提交

**一个功能通常只需要 2-3 个 commit：**

```bash
# Backend 完成后
git add -A ':!.tasks/*'
git commit -m "feat(foo-api): add foo model, service, and API route

- Implementation: <技术决策说明>
- Affected files:
  * migrations/001_foo.sql
  * src/services/foo_service.py
  * src/api/foo.py"

# Frontend 完成后
git add -A ':!.tasks/*'
git commit -m "feat(foo-web): add fooStore, fooApi, and FooCard component

- Implementation: <技术决策说明>
- Cross-Store: selectWorkspace now calls fooStore.reset()
- Affected files:
  * web/services/api.ts
  * web/stores/fooStore.ts
  * stores/workspaceStore.ts
  * web/components/FooCard.tsx"
```

**Commit 规范：**
- Types: `feat`, `fix`, `refactor`, `perf`, `docs`, `test`, `chore`
- Scope: `<feature>-<layer>`（如 `foo-api`, `foo-web`）
- Body: 必须包含 Implementation 说明 + Affected files
- 跨层变更显式标注 `Cross-Store:` / `Async-Guard:`

### 3.4 进度记录

在 `.tasks/<id>.md` 更新执行状态：
```markdown
## 执行记录
| Layer | Status | Files | Commit | Notes |
|-------|--------|-------|--------|-------|
| Backend | [x] DONE | 3 files, +85 lines | abc1234 | — |
| Frontend | [x] DONE | 4 files, +120 lines | def5678 | Cross-Store: workspaceStore 已更新 |
```

**EXIT GATE (per layer):** 该层编译通过 + 已提交 + 进度已记录。

---

## Phase 4: VERIFY

> 功能全部开发完成后，一次性做完整验证。

### 4.1 Plan vs Implementation

对照 Phase 2 的 checklist，逐项确认：
- `IMPLEMENTATION MATCHES PLAN EXACTLY`，或
- 列出偏差及理由

### 4.2 Cross-Cutting Audit

**Parallel Path Grep** — 修了任何事件/状态路径后，grep 所有平行路径：
```bash
grep -rn 'loadTurns\|setActiveTurnId\|clearChat' web/src/ | grep -v node_modules
```
// turbo

**Cross-Store Integrity** — 重读修改过的 store 的所有 importer：
- `selectWorkspace` 是否正确 reset 所有新增 state？
- 是否有 `useEffect` / `setTimeout` 闭包捕获了过期引用？
- 所有入口（sidebar click, keyboard shortcut, URL navigation）是否走同一个 reset 路径？

**Smell Sweep** — 扫描所有 diff：
- `// TODO` 或 placeholder（FORBIDDEN）
- Boolean 标志应为 AbortController
- `catch {}` 缺日志
- Hardcoded magic number 应提为 config

### 4.3 Scenario Path Verification

用完成的完整功能走以下场景（mental walk-through 或 E2E 测试）：
- [ ] Happy path: 功能按设计工作
- [ ] 操作过程中切换上下文（如切 workspace）→ 状态正确隔离？
- [ ] 异步操作超时或失败 → 错误处理和 UI 回退正确？
- [ ] 与现有功能交互 → 无回归？
- [ ] F5 刷新 → 状态正确恢复？

### 4.4 E2E 浏览器验证（可选但推荐）

对于 UI 可见的功能，用 `/e2e-test` workflow 做浏览器端验证。

### 4.5 全量编译 Final Check

```bash
pytest tests/
cd web && npm run build
```
// turbo

### 4.6 修复 & 收尾

如发现问题，修复后 amend 最近的 commit：
```bash
git add -A ':!.tasks/*'
git commit --amend --no-edit
```

更新 `.tasks/<id>.md` 最终状态。

**EXIT GATE:** 所有 checklist [x] DONE + 场景验证通过 + 全量编译通过 + Smell 零发现。

---

## Testing Strategy（混合策略）

> 不同层采用不同测试策略，平衡投入与收益。

| 层 | 测试方式 | 理由 |
|---|---|---|
| **后端核心**（scheduler, run.service, fastpath）| 单元测试（vitest/jest） | 逻辑复杂、状态多、回归成本高 |
| **后端路由** | 编译 + 手动验证 | 主要是 CRUD 胶水代码，编译覆盖大部分类型错误 |
| **前端 Store** | 编译 + Cross-Store grep | 跨 store 交互是主要风险点，grep 比单元测试更有效 |
| **前端 UI** | E2E 浏览器测试（`/e2e-test`）| 视觉和交互只能在浏览器验证 |

---

## Proven Patterns

1. **Impact Surface First** — 在写 Plan 之前先 grep 出所有"谁在读我改的状态"。
   大部分 bug 在你不知道的读者那里。

2. **修一个路径，grep 所有平行路径** — done handler 和 polling fallback
   是同一逻辑的两条路。修一条必须同时检查另一条。

3. **Closure 过期检查** — `useEffect` / `setTimeout` 回调里引用的 store state
   必须用 ref（`currentWsIdRef`）或在执行时重新获取，否则切换上下文后会读到旧值。

4. **Cross-Store Reset 集中化** — Store A 的 action 要触发 Store B 的 reset，
   应该放在 Store A 内部统一调用，不要分散在 UI 组件里。

5. **No Deferred Smells** — 发现的 smell 立即修复。
   "下次再说" 等于 "用户在生产环境发现"。

6. **按层提交，不按文件** — 一个完整的 backend 变更是一个 commit，
   一个完整的 frontend 变更是一个 commit。既方便 revert 又保持 git log 可读。

7. **Rollback 前置** — Plan 阶段就标注 rollback 策略，
   不要等上线出问题了再想"这些 commit 能不能单独回退"。
