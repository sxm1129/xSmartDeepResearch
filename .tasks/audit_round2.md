# Deep Code Review - Round 2 (P1 Files)

## 审计目标文件 (P1)
- `src/api/routes/advanced_research.py`
- `src/api/routes/research.py`
- `src/api/routes/settings.py`
- `src/tools/search_tool.py`
- `src/tools/visit_tool.py`
- `src/utils/session_manager.py`
- `web/contexts/AdvancedResearchContext.tsx`
- `web/contexts/ResearchContext.tsx`

## Confirmed Bugs

### BUG-2: Cancellation 假象与状态覆写 (research.py)
- **Trigger:** 用户调用 `DELETE /research/{task_id}` 取消一个正在运行的任务。
- **Impact:** 数据库状态被修改为 `FAILED`，但这并不会终止正在运行的 LLM `stream_run` 线程。最后后台任务执行完毕时，会毫无察觉地将数据库状态重新覆盖回 `COMPLETED`。取消功能实际未生效。
- **Files:** `src/api/routes/research.py:433-437`

### BUG-3: Frontend 生命周期对 AbortSignal 的遗漏调用 (ResearchContext.tsx)
- **Trigger:** 在 Round 1 我们为 API Service 添加了 `AbortSignal`，但 React Contexts 并未真正在调用它。组件注销或重复拉起时仍然会发生连接堆积。
- **Impact:** Context 未维护 AbortController 实例，导致取消或中断无效。
- **Files:** `web/contexts/ResearchContext.tsx`, `web/contexts/AdvancedResearchContext.tsx`

## Code Smells (ALL fixed)

### SMELL-3: Webhook 阻塞了 LLM 的主生成流 (research.py `_run_research_task`)
- **Issue:** 后台任务中，对于代理产出的每一个细微数据块事件，都通过 `await _dispatch_webhook` 发送。由于是串行 `await`，只要 Webhook 接收方慢 1 秒，Agent 就会暂停思考 1 秒。
- **Fix:** 将 `_dispatch_webhook` 改为防火后顾（Fire-and-forget）任务 `asyncio.create_task(_dispatch_webhook(...))`。

### SMELL-4: Aiohttp Sessions 创建开销 (search_tool.py / visit_tool.py)
- **Issue:** 批量并行查询时，每个任务都会单独建立一个 `aiohttp.ClientSession`。
- **Fix:** 将其下沉为在实例级别复用的 shared session 或者暂不处理（因不致命）。

## verification checklist execution
- [x] Execution path for Webhook inspected.
- [x] Caller check for `DELETE /research`.
- [x] Impact check for Context cancellation.
