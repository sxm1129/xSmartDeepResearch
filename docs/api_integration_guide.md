# xSmartDeepResearch API 集成文档

> 本文档面向需要在自己的服务中集成 DeepResearch 深度研究能力的开发者。

---

## 快速开始

### 前置条件

| 条件 | 说明 |
|------|------|
| DeepResearch 服务 | 运行于 `http://<HOST>:8000` |
| 网络连通 | 你的服务能访问 DeepResearch API |
| (Webhook 模式) 回调端点 | 你的服务暴露一个 POST 端点接收进度 |

### 服务启动

```bash
cd xSmartDeepResearch
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

API 文档自动生成于: `http://localhost:8000/docs`

---

## API 端点总览

| 端点 | 方法 | 用途 |
|------|------|------|
| `/api/v1/research` | POST | 同步研究 (阻塞等待结果) |
| `/api/v1/research/async` | POST | 异步研究 (立即返回, 后台执行) |
| `/api/v1/research/stream` | POST | SSE 流式研究 (实时推送事件) |
| `/api/v1/research/{task_id}` | GET | 获取任务完整结果 |
| `/api/v1/research/{task_id}/status` | GET | 获取任务状态/进度 |
| `/api/v1/research/history` | GET | 研究历史列表 |
| `/api/v1/research/{task_id}` | DELETE | 取消/删除任务 |
| `/api/v1/research/batch` | POST | 批量研究 |

---

## 请求参数

```json
{
  "question": "量子计算的最新进展有哪些？",
  "max_iterations": 50,
  "callback_url": "http://my-service:9000/webhook/research",
  "callback_events": ["status", "think", "answer", "final_answer", "error"]
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `question` | string | 是 | 研究问题 |
| `max_iterations` | int | 否 | 最大迭代次数 (1-100, 默认使用服务端配置) |
| `callback_url` | string | 否 | Webhook 回调 URL |
| `callback_events` | string[] | 否 | 需要回调的事件类型, `null` 表示全部 |

---

## 进度事件类型

研究过程中产生以下事件, 通过 SSE 或 Webhook 回调推送:

| type | 说明 | 关键字段 |
|------|------|----------|
| `status` | 状态更新 (意图识别、迭代开始) | `content`, `iteration` |
| `think` | Agent 的推理思考过程 | `content` |
| `tool_start` | 开始调用工具 | `tool`, `arguments`, `iteration` |
| `tool_response` | 工具返回结果 | `tool`, `content`, `iteration` |
| `answer` | 最终答案 (预览) | `content` |
| `final_answer` | 研究完成, 包含完整结果 | `content`, `iterations`, `termination` |
| `error` | 错误 | `content` |
| `timeout` | 超时 | `content` |

---

## 集成方式一: 异步 + Webhook 回调 (推荐)

> 适用于: 服务间集成, 微服务架构

### 时序图

```
你的服务                          DeepResearch
  │                                    │
  │─ POST /research/async ────────────>│  {question, callback_url}
  │<─ 200 {task_id, status:"pending"} ─│
  │                                    │
  │    (后台自动执行)                    │
  │<── POST callback_url ─────────────│  {type:"status", content:"Identifying..."}
  │<── POST callback_url ─────────────│  {type:"think", content:"需要搜索..."}
  │<── POST callback_url ─────────────│  {type:"tool_start", tool:"search"}
  │<── POST callback_url ─────────────│  {type:"tool_response", tool:"search"}
  │<── POST callback_url ─────────────│  {type:"think", content:"根据搜索结果..."}
  │    ... (多轮迭代) ...              │
  │<── POST callback_url ─────────────│  {type:"final_answer", content:"完整结果"}
  │                                    │
  │─ GET /research/{task_id} ─────────>│  (可选: 兜底查询)
  │<─ 200 {answer, status, ...} ──────│
```

### Step 1: 提交研究任务

```python
import httpx

DEEP_RESEARCH_URL = "http://deep-research:8000"

async def start_research(question: str) -> str:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{DEEP_RESEARCH_URL}/api/v1/research/async",
            json={
                "question": question,
                "callback_url": "http://my-service:9000/webhook/research",
                "callback_events": ["status", "think", "answer", "final_answer", "error"]
            }
        )
        resp.raise_for_status()
        return resp.json()["task_id"]
```

**响应示例:**
```json
{
  "task_id": "a1b2c3d4",
  "status": "pending",
  "current_iteration": 0,
  "message": "Task created, processing in background"
}
```

### Step 2: 接收 Webhook 回调

在你的服务中实现一个 POST 端点:

```python
from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/webhook/research")
async def handle_research_callback(request: Request):
    event = await request.json()
    
    task_id = event["task_id"]
    event_type = event["type"]
    content = event.get("content", "")
    timestamp = event.get("timestamp")
    
    if event_type == "status":
        # 更新 UI: "正在搜索中..."
        await update_progress(task_id, message=content)
    
    elif event_type == "think":
        # 展示 AI 思考过程
        await update_progress(task_id, thinking=content)
    
    elif event_type == "tool_start":
        tool_name = event.get("tool")
        await update_progress(task_id, message=f"正在使用 {tool_name} 工具...")
    
    elif event_type == "final_answer":
        # 研究完成, 保存结果
        await save_result(task_id, answer=content)
        await notify_user(task_id, message="研究已完成")
    
    elif event_type == "error":
        await mark_failed(task_id, error=content)
    
    return {"status": "received"}
```

**回调事件 payload 示例:**
```json
{
  "task_id": "a1b2c3d4",
  "type": "think",
  "content": "用户询问了量子计算的最新进展，需要搜索最新的学术论文和新闻...",
  "iteration": 3,
  "tool": null,
  "timestamp": "2026-02-27T17:30:00.123456"
}
```

### Step 3: 兜底查询 (可选)

万一 Webhook 回调丢失, 可主动查询:

```python
async def check_task_result(task_id: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{DEEP_RESEARCH_URL}/api/v1/research/{task_id}"
        )
        result = resp.json()
        
        if result["status"] == "completed":
            return result["answer"]
        elif result["status"] == "failed":
            raise Exception(result.get("termination_reason"))
        else:
            return None  # 仍在执行中
```

**响应示例:**
```json
{
  "task_id": "a1b2c3d4",
  "question": "量子计算的最新进展有哪些？",
  "answer": "## 量子计算最新进展\n\n### 1. 硬件突破\n...(完整研究报告)...",
  "status": "completed",
  "iterations": 15,
  "execution_time": 45.2,
  "termination_reason": "answer",
  "created_at": "2026-02-27T17:25:00",
  "is_bookmarked": false
}
```

---

## 集成方式二: SSE 流式 (适用于前端/长连接场景)

```python
import httpx
import json

async def stream_research(question: str):
    async with httpx.AsyncClient(timeout=600) as client:
        async with client.stream(
            "POST",
            f"{DEEP_RESEARCH_URL}/api/v1/research/stream",
            json={"question": question}
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    event = json.loads(line[6:])
                    
                    print(f"[{event['type']}] {event.get('content', '')[:100]}")
                    
                    if event["type"] == "final_answer":
                        return event["content"]
```

### JavaScript (前端)

```javascript
const response = await fetch('/api/v1/research/stream', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ question: '量子计算最新进展' })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  const lines = decoder.decode(value).split('\n');
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const event = JSON.parse(line.slice(6));
      
      switch (event.type) {
        case 'think':
          showThinking(event.content);
          break;
        case 'tool_start':
          showToolCall(event.tool);
          break;
        case 'final_answer':
          showResult(event.content);
          break;
      }
    }
  }
}
```

---

## 集成方式三: 同步调用 (简单场景)

> 注意: 会阻塞直到研究完成 (通常 30s-5min), 需设置足够长的超时。

```python
async with httpx.AsyncClient(timeout=600) as client:
    resp = await client.post(
        f"{DEEP_RESEARCH_URL}/api/v1/research",
        json={"question": "问题"}
    )
    answer = resp.json()["answer"]
```

```bash
curl -X POST "http://localhost:8000/api/v1/research" \
  -H "Content-Type: application/json" \
  -d '{"question": "量子计算的最新进展有哪些？"}' \
  --max-time 600
```

---

## 完整集成示例

项目内置了一个可运行的 demo:

```bash
# Terminal 1: 启动 DeepResearch
uvicorn src.api.main:app --port 8000

# Terminal 2: 启动回调接收服务
python examples/webhook_integration.py --mode server

# Terminal 3: 提交任务
python examples/webhook_integration.py --mode client --question "AI医疗最新应用"

# Terminal 3 (可选): 提交并轮询等待结果
python examples/webhook_integration.py --mode client --question "AI医疗最新应用" --poll
```

---

## 错误处理

| HTTP 状态码 | 含义 |
|-------------|------|
| 200 | 成功 |
| 404 | 任务不存在 |
| 422 | 请求参数校验失败 (如空问题) |
| 500 | 服务内部错误 |

Webhook 回调失败时不会重试, 建议配合 `GET /research/{task_id}` 做兜底查询。

---

## 方式选择指南

| 场景 | 推荐方式 |
|------|---------|
| 后端服务集成, 需要进度展示 | **Webhook 回调** |
| 前端实时展示思考过程 | SSE 流式 |
| 简单脚本/测试 | 同步调用 |
| 批量任务, 不关心过程 | 异步 + 轮询 |
