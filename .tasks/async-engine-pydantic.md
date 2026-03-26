# Research & Discovery: Async Engine & Pydantic Structured Outputs

## 1. Context & Objective
Upgrade `xSmartDeepResearch` into an industrial-grade research engine by:
1. **JSON Parsing & Intent Recognition**: Migrating from fragile Regex post-processing to 100% robust Pydantic Structured Outputs (via OpenAI compatible structured formats or direct Pydantic `.model_validate_json`).
2. **Async Task Queuing**: Eliminating the blocking HTTP SSE architecture (which suffers from Nginx 504 timeouts) and replacing it with a `FastAPI -> Redis/arq Queue -> Worker` architecture.
3. **Frontend Observable UI**: Implementing a reconnectable SSE API `/api/v1/tasks/{id}/stream` to push `Chain-of-Thought` events to the React UI seamlessly.

## 2. Affected Files Analysis
- `src/agent/intent_classifier.py`
  - Current state: Uses manual `try-except` JSON parsing with regex fallbacks.
  - Required change: Use OpenAI SDK's `beta.chat.completions.parse` method with a defined Pydantic Schema model, or simply enforce stricter JSON format validation using Pydantic.
- `src/api/routes/research.py` & `src/api/routes/advanced_research.py`
  - Current state: Directly yields SSE streams invoking the heavy Agent `stream_run`. Blocks the main API thread over HTTP.
  - Required change: Implement async endpoints that:
    1. POST `/research` -> push `TaskRequest` to `arq` or Redis -> returns `{"task_id": "xxx"}`.
    2. GET `/tasks/{task_id}/stream` -> Subscribes to Redis Pub/Sub topic `task_events_{task_id}` and yields SSE.
- `src/worker/` (New directory)
  - Required change: Needs a standalone Python worker script to consume internal queue tasks and execute the LLM chain, pushing chunks to Redis Pub/Sub.
- `web/services/api.ts` & `web/services/advancedResearchApi.ts`
  - Current state: Uses blocking `fetch().getReader()` directly to `POST /stream`.
  - Required change: Switch to calling `POST /` to get an ID, then hook `EventSource` (or stream fetcher) to `GET /tasks/{task_id}/stream`.
- `web/contexts/ResearchContext.tsx` & `web/contexts/AdvancedResearchContext.tsx`
  - Current state: Tightly coupled to the single `streamResearch` fetch action and AbortController.
  - Required change: Abstract task initialization from event subscription to allow reconnecting to existing active tasks.

## 3. Candidate Approaches

### Candidate A: Direct Redis PubSub + Custom FastAPI Background Tasks
- **Pros:** No extra dependencies (like `arq` or `Celery`), utilizes built-in `asyncio.create_task`.
- **Cons:** If FastAPI restarts, the background task is lost. No built-in retry mechanisms or concurrency limits across multiple instances.
- **Complexity:** Low.

### Candidate B: python-arq (Redis Async Queue) + Redis Pub/Sub (RECOMMENDED)
- **Pros:** Extremely lightweight async queue for Python `asyncio`. Safe process restart and concurrency control. Native Redis integration (which we use for Pub/Sub anyway).
- **Cons:** Requires a separate `arq` worker process in `docker-compose.prod.yml`.
- **Complexity:** Medium. Highly robust for production.

### Candidate C: Celery + RabbitMQ / Redis
- **Pros:** Ultimate industrial grade.
- **Cons:** Sync-heavy, doesn't play perfectly with `asyncio` out of the box without heavy tuning. Overkill for this project scale.
- **Complexity:** High.

**Decision:** We will proceed with **Candidate B (python-arq + Redis Pub/Sub)**.

## 4. Impact Surface / Cross-Component Risks (CRITICAL)
- **[Cross-Store] Frontend Context State:** `AdvancedResearchContext.tsx` maintains its own `useRef(AbortController)` and state for SSE. When shifting to `arq`, cancelling a task on the frontend should probably send a `POST /tasks/{id}/cancel` to the backend payload so the worker can kill the task.
- **[Async-Guard] Redis Pub/Sub Cleanup:** When parsing events, if a client disconnects, we MUST ensure the Redis PubSub connection is neatly unsubscribed, otherwise we will leak memory per connection.
- **[Parallel-Path] Fallback Routing:** If Redis is down, does the application crash? We need graceful connection handling in FastAPI startup/shutdown.

---
**Next Step:** Transition to `[MODE: PLAN]` to define the precise `implementation_plan.md` checklist.
