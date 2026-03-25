# Deep Code Review - Round 1 Findings (P0 Files)

## Scope Analyzed
- `src/agent/react_agent.py`
- `src/agent/intent_classifier.py`
- `src/agent/intent_clarifier.py`
- `src/api/main.py`
- `web/services/advancedResearchApi.ts`
- `web/services/api.ts`

## Confirmed Bugs

### BUG-1: Missing AbortController in Frontend Streaming APIs
- **Trigger:** 用户发起 Advanced Research 或普通 Research 后，在长周期的流式返回期间（可能持续几分钟），点击了取消或离开了当前页面（Unmount）。
- **Impact:** `fetch` 请求没有绑定 `AbortSignal`，导致前端请求将继续在后台挂起并接收流式数据，造成前端连接泄漏。同时，后端也无法感知客户端断开，会继续执行高成本的 Deep Research。
- **Files:** 
  - `web/services/api.ts` (`streamResearch`)
  - `web/services/advancedResearchApi.ts` (`streamResearch`)

## Code Smells (Will be Fixed)

### SMELL-1: Weak Error Handling in _call_llm
- **Issue:** 在 `src/agent/react_agent.py` 的 `_call_llm` 方法中，当所有重试都失败后，它返回了一段硬编码文本 `"[LLM returned empty response after retries]"` 或 `"LLM call failed after all retries"`，而不是抛出异常。这会作为 assistant 的回答喂给下一轮，导致 LLM 判断错乱或解析崩溃。
- **Fix:** 应该抛出明确的异常 `RuntimeError`，并在上层 `stream_run` 中捕获，中断流程并通过 `yield {"type": "error", ...}` 优雅返回给客户端。

### SMELL-2: nest_asyncio Apply at Method Level
- **Issue:** `src/agent/intent_classifier.py` 中的同步方法 `classify()` 内每次都调用 `nest_asyncio.apply()`。这是一个全局 patched 行为，不应该放在频繁调用的实例方法里，可能导致不可预期的 Event Loop 污染。
- **Fix:** 提取到文件模块级，或者在系统初始化时 (如 main.py 启动时) 做一次 `apply()`。

## Theoretical Risks

### RISK-1: Token Limit Context Pruning
- **Condition:** 对话不断变长并触发 token 上限，`_prune_messages` 开始裁剪 `messages`（只保留首 2 条和尾 6 条）。
- **Probability:** Medium. 当研究深度加大时容易触发。如果刚好中间发生过重要的不可重复的 Tool Response，裁剪后模型可能 "失忆"，导致死循环尝试同一个动作。
- **Action:** 目前记录在案。未来需要引入摘要机制 (Semantic Summarization) 替代简单的物理截断。
