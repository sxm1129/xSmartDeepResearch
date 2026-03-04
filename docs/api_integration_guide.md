# xSmartDeepResearch API Integration Guide

> **Base URL**: `https://xsmartdeepresearch.fusionxlink.com`
> **Version**: 1.0.15 | **Model**: moonshotai/kimi-k2.5
> **API Docs**: [Swagger UI](https://xsmartdeepresearch.fusionxlink.com/docs) | [ReDoc](https://xsmartdeepresearch.fusionxlink.com/redoc)

---

## 目录

- [快速开始](#快速开始)
- [API 端点一览](#api-端点一览)
- [1. 健康检查](#1-健康检查)
- [2. SSE 流式研究 (推荐)](#2-sse-流式研究-推荐)
- [3. 同步研究 (阻塞式)](#3-同步研究-阻塞式)
- [4. 异步研究 + 轮询](#4-异步研究--轮询)
- [5. 研究历史](#5-研究历史)
- [6. 批量研究](#6-批量研究)
- [7. Webhook 回调](#7-webhook-回调)
- [SSE 事件类型参考](#sse-事件类型参考)
- [错误处理](#错误处理)
- [完整示例](#完整示例)

---

## 快速开始

### Python (3 行代码)

```python
import httpx

resp = httpx.post("https://xsmartdeepresearch.fusionxlink.com/api/v1/research",
                  json={"question": "什么是量子计算？", "max_iterations": 5},
                  timeout=300)
print(resp.json()["answer"])
```

### JavaScript (3 行代码)

```javascript
const resp = await fetch("https://xsmartdeepresearch.fusionxlink.com/api/v1/research", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ question: "什么是量子计算？", max_iterations: 5 })
});
console.log((await resp.json()).answer);
```

---

## API 端点一览

| 方法 | 端点 | 说明 | 耗时 |
|------|------|------|------|
| `GET` | `/health` | 健康检查 | <1s |
| `POST` | `/api/v1/research/stream` | SSE 流式研究 (推荐) | 30s-300s |
| `POST` | `/api/v1/research` | 同步研究 (阻塞) | 30s-300s |
| `POST` | `/api/v1/research/async` | 异步研究 (立即返回) | <1s |
| `GET` | `/api/v1/research/{task_id}` | 查询任务结果 | <1s |
| `GET` | `/api/v1/research/{task_id}/status` | 查询任务状态 | <1s |
| `GET` | `/api/v1/research/history` | 研究历史列表 | <1s |
| `POST` | `/api/v1/research/batch` | 批量研究 | <1s |
| `DELETE` | `/api/v1/research/{task_id}` | 取消/删除任务 | <1s |
| `POST` | `/api/v1/research/{task_id}/bookmark` | 收藏/取消收藏 | <1s |

### 请求参数 (ResearchRequest)

```json
{
  "question": "你的研究问题",       // 必填, string
  "max_iterations": 10,            // 可选, 1-100, 默认由服务端决定
  "callback_url": "http://...",    // 可选, Webhook 回调地址 (仅 async 模式)
  "callback_events": ["status", "final_answer"]  // 可选, 过滤回调事件类型
}
```

---

## 1. 健康检查

### Python

```python
import httpx

resp = httpx.get("https://xsmartdeepresearch.fusionxlink.com/health")
data = resp.json()
print(f"Status: {data['status']}, Version: {data['version']}, Model: {data['model']}")
```

### JavaScript

```javascript
const resp = await fetch("https://xsmartdeepresearch.fusionxlink.com/health");
const data = await resp.json();
console.log(`Status: ${data.status}, Version: ${data.version}, Model: ${data.model}`);
```

**响应示例:**

```json
{
  "status": "healthy",
  "version": "1.0.15",
  "model": "moonshotai/kimi-k2.5",
  "tools_available": ["search", "google_scholar", "visit", "PythonInterpreter", "parse_file"],
  "timestamp": "2026-03-04T19:03:18"
}
```

---

## 2. SSE 流式研究 (推荐)

> **推荐方式**：实时获取研究过程 (思考、搜索、网页访问)，适合需要展示进度的场景。
> 服务内置 **15 秒心跳保活机制**，SSE 注释 `: keepalive` 保持连接不断开。

### Python

```python
import httpx
import json

BASE_URL = "https://xsmartdeepresearch.fusionxlink.com"

with httpx.Client(timeout=httpx.Timeout(600.0, connect=30.0)) as client:
    with client.stream(
        "POST",
        f"{BASE_URL}/api/v1/research/stream",
        json={"question": "OpenClaw是什么？有什么应用场景？", "max_iterations": 10}
    ) as response:
        for line in response.iter_lines():
            # 跳过心跳注释
            if line.startswith(":") or not line.startswith("data: "):
                continue
            
            event = json.loads(line[6:])
            event_type = event.get("type")
            content = event.get("content", "")
            
            if event_type == "task_created":
                print(f"[任务创建] task_id={event.get('task_id')}")
            elif event_type == "status":
                print(f"[状态] {content}")
            elif event_type == "think":
                print(f"[思考] {content[:100]}...")
            elif event_type == "tool_start":
                print(f"[工具调用] {event.get('tool')}")
            elif event_type == "tool_response":
                print(f"[工具结果] {event.get('tool')} ({len(content)} chars)")
            elif event_type == "answer":
                print(f"[答案] ({len(content)} chars)")
            elif event_type == "final_answer":
                print(f"\n===== 最终答案 =====")
                print(content)
                print(f"\n迭代次数: {event.get('iterations')}")
                print(f"终止原因: {event.get('termination')}")
            elif event_type == "error":
                print(f"[错误] {content}")
```

### Python (异步版本)

```python
import httpx
import asyncio
import json

async def stream_research(question: str, max_iterations: int = 10):
    BASE_URL = "https://xsmartdeepresearch.fusionxlink.com"
    
    async with httpx.AsyncClient(timeout=httpx.Timeout(600.0, connect=30.0)) as client:
        async with client.stream(
            "POST",
            f"{BASE_URL}/api/v1/research/stream",
            json={"question": question, "max_iterations": max_iterations}
        ) as response:
            final_answer = None
            async for line in response.aiter_lines():
                if line.startswith(":") or not line.startswith("data: "):
                    continue
                event = json.loads(line[6:])
                
                if event["type"] == "final_answer":
                    final_answer = event["content"]
                elif event["type"] == "status":
                    print(f"[{event['type']}] {event['content']}")
            
            return final_answer

# 使用
answer = asyncio.run(stream_research("2026年AI领域有哪些重大突破？"))
print(answer)
```

### JavaScript (浏览器 / Node.js)

```javascript
async function streamResearch(question, maxIterations = 10) {
  const BASE_URL = "https://xsmartdeepresearch.fusionxlink.com";
  
  const response = await fetch(`${BASE_URL}/api/v1/research/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, max_iterations: maxIterations })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let finalAnswer = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop(); // 保留不完整行

    for (const line of lines) {
      if (line.startsWith(":") || !line.startsWith("data: ")) continue;

      const event = JSON.parse(line.slice(6));
      
      switch (event.type) {
        case "task_created":
          console.log(`[任务创建] task_id=${event.task_id}`);
          break;
        case "status":
          console.log(`[状态] ${event.content}`);
          break;
        case "think":
          console.log(`[思考] ${event.content.slice(0, 100)}...`);
          break;
        case "tool_start":
          console.log(`[工具调用] ${event.tool}`);
          break;
        case "tool_response":
          console.log(`[工具结果] ${event.tool} (${event.content.length} chars)`);
          break;
        case "answer":
          console.log(`[答案] (${event.content.length} chars)`);
          break;
        case "final_answer":
          finalAnswer = event.content;
          console.log(`\n===== 最终答案 =====`);
          console.log(event.content);
          console.log(`迭代: ${event.iterations}, 终止: ${event.termination}`);
          break;
        case "error":
          console.error(`[错误] ${event.content}`);
          break;
      }
    }
  }

  return finalAnswer;
}

// 使用
streamResearch("OpenClaw是什么？有哪些应用场景？").then(answer => {
  console.log("研究完成, 答案长度:", answer?.length);
});
```

### JavaScript (Node.js 使用 EventSource)

```javascript
// npm install eventsource
const EventSource = require("eventsource");

function streamResearch(question, maxIterations = 10) {
  return new Promise(async (resolve, reject) => {
    const BASE_URL = "https://xsmartdeepresearch.fusionxlink.com";
    
    // EventSource 不支持 POST，改用 fetch + 手动解析
    const resp = await fetch(`${BASE_URL}/api/v1/research/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, max_iterations: maxIterations })
    });

    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let finalAnswer = null;

    async function read() {
      const { done, value } = await reader.read();
      if (done) return resolve(finalAnswer);
      
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop();

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        try {
          const event = JSON.parse(line.slice(6));
          if (event.type === "final_answer") finalAnswer = event.content;
          if (event.type === "status") console.log(`[${event.type}] ${event.content}`);
        } catch (e) {}
      }
      
      read();
    }
    
    read().catch(reject);
  });
}
```

---

## 3. 同步研究 (阻塞式)

> 适合简单集成场景。注意：请求可能持续 30-300 秒，请设置足够长的超时。

### Python

```python
import httpx

BASE_URL = "https://xsmartdeepresearch.fusionxlink.com"

resp = httpx.post(
    f"{BASE_URL}/api/v1/research",
    json={"question": "比较 React 和 Vue 的优缺点", "max_iterations": 5},
    timeout=300  # 必须设置足够长的超时
)

result = resp.json()
print(f"答案: {result['answer']}")
print(f"迭代: {result['iterations']}, 耗时: {result['execution_time']}s")
print(f"终止原因: {result['termination_reason']}")
```

### JavaScript

```javascript
const resp = await fetch("https://xsmartdeepresearch.fusionxlink.com/api/v1/research", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ question: "比较 React 和 Vue 的优缺点", max_iterations: 5 }),
  signal: AbortSignal.timeout(300000) // 300 秒超时
});

const result = await resp.json();
console.log(`答案: ${result.answer}`);
console.log(`迭代: ${result.iterations}, 终止: ${result.termination_reason}`);
```

**响应示例:**

```json
{
  "task_id": "abc123",
  "question": "比较 React 和 Vue 的优缺点",
  "answer": "## React vs Vue 对比分析\n\n### React 优势\n...",
  "status": "completed",
  "iterations": 5,
  "execution_time": 89.3,
  "termination_reason": "answer",
  "created_at": "2026-03-04T19:03:18",
  "is_bookmarked": false
}
```

---

## 4. 异步研究 + 轮询

> 适合后端服务集成：立即获得 `task_id`，后台执行，轮询查询结果。

### Python

```python
import httpx
import time

BASE_URL = "https://xsmartdeepresearch.fusionxlink.com"

# 1. 提交任务
resp = httpx.post(
    f"{BASE_URL}/api/v1/research/async",
    json={"question": "分析2026年全球经济走势", "max_iterations": 10}
)
task_id = resp.json()["task_id"]
print(f"任务已创建: {task_id}")

# 2. 轮询状态
while True:
    status_resp = httpx.get(f"{BASE_URL}/api/v1/research/{task_id}/status")
    status = status_resp.json()
    print(f"状态: {status['status']}, 进度: {status.get('progress', '?')}%")
    
    if status["status"] in ("completed", "failed", "timeout"):
        break
    time.sleep(5)

# 3. 获取结果
result = httpx.get(f"{BASE_URL}/api/v1/research/{task_id}").json()
print(f"\n答案:\n{result['answer']}")
```

### JavaScript

```javascript
const BASE_URL = "https://xsmartdeepresearch.fusionxlink.com";

// 1. 提交任务
const submitResp = await fetch(`${BASE_URL}/api/v1/research/async`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ question: "分析2026年全球经济走势", max_iterations: 10 })
});
const { task_id } = await submitResp.json();
console.log(`任务已创建: ${task_id}`);

// 2. 轮询状态
async function pollUntilDone(taskId, intervalMs = 5000, maxAttempts = 60) {
  for (let i = 0; i < maxAttempts; i++) {
    const resp = await fetch(`${BASE_URL}/api/v1/research/${taskId}/status`);
    const status = await resp.json();
    console.log(`状态: ${status.status}, 进度: ${status.progress ?? "?"}%`);
    
    if (["completed", "failed", "timeout"].includes(status.status)) {
      return status.status;
    }
    await new Promise(r => setTimeout(r, intervalMs));
  }
  throw new Error("轮询超时");
}

await pollUntilDone(task_id);

// 3. 获取结果
const result = await (await fetch(`${BASE_URL}/api/v1/research/${task_id}`)).json();
console.log(`答案:\n${result.answer}`);
```

---

## 5. 研究历史

### Python

```python
import httpx

resp = httpx.get("https://xsmartdeepresearch.fusionxlink.com/api/v1/research/history")
history = resp.json()

for item in history[:5]:
    print(f"[{item['status']}] {item['question'][:50]}... ({item['iterations']} iters)")
```

### JavaScript

```javascript
const resp = await fetch("https://xsmartdeepresearch.fusionxlink.com/api/v1/research/history");
const history = await resp.json();

history.slice(0, 5).forEach(item => {
  console.log(`[${item.status}] ${item.question.slice(0, 50)}... (${item.iterations} iters)`);
});
```

---

## 6. 批量研究

> 一次提交多个问题，后台并行执行。

### Python

```python
import httpx

resp = httpx.post(
    "https://xsmartdeepresearch.fusionxlink.com/api/v1/research/batch",
    json={
        "questions": [
            "Python 3.13 有哪些新特性？",
            "Rust 和 Go 的性能对比",
            "WebAssembly 的最新发展"
        ],
        "max_iterations": 5
    }
)

result = resp.json()
print(f"批次ID: {result['batch_id']}")
print(f"任务IDs: {result['task_ids']}")

# 然后用 /api/v1/research/{task_id} 逐一查询结果
```

---

## 7. Webhook 回调

> 异步模式下可配置 Webhook，服务端主动推送进度事件到指定 URL。

### Python

```python
import httpx

resp = httpx.post(
    "https://xsmartdeepresearch.fusionxlink.com/api/v1/research/async",
    json={
        "question": "分析新能源汽车市场趋势",
        "max_iterations": 10,
        "callback_url": "https://your-server.com/webhook/research",
        "callback_events": ["status", "final_answer", "error"]
    }
)
print(f"任务ID: {resp.json()['task_id']}")
# 你的服务器将收到 POST 请求，格式如下：
```

**Webhook 推送格式:**

```json
{
  "task_id": "abc123",
  "type": "final_answer",
  "content": "研究最终答案...",
  "iteration": 8,
  "tool": null,
  "timestamp": "2026-03-04T19:30:00"
}
```

**可订阅的事件类型:** `status` | `think` | `tool_start` | `tool_response` | `answer` | `final_answer` | `error`

---

## SSE 事件类型参考

| 事件类型 | 说明 | 关键字段 |
|----------|------|----------|
| `task_created` | 任务创建成功 | `task_id` |
| `status` | 状态更新 (迭代开始等) | `content`, `iteration` |
| `think` | Agent 思考过程 | `content` |
| `tool_start` | 开始调用工具 | `tool`, `arguments` |
| `tool_response` | 工具返回结果 | `tool`, `content` |
| `answer` | 生成答案 (可能非最终) | `content` |
| `final_answer` | **最终答案** | `content`, `iterations`, `termination` |
| `error` | 错误信息 | `content` |

### termination 终止原因

| 值 | 说明 |
|----|------|
| `answer` | Agent 自主生成了完整答案 |
| `token_limit_forced_answer` | Token 超限，强制总结 |
| `max_iterations_exceeded` | 达到最大迭代次数后强制总结 |
| `timeout` | 执行超时 |
| `error` | 执行出错 |

> **注意**: SSE 流包含 `: keepalive` 心跳注释 (每 15 秒)，客户端解析时应忽略以 `:` 开头的行。

---

## 错误处理

### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 404 | 任务未找到 |
| 422 | 请求参数验证失败 |
| 500 | 服务器内部错误 |

### Python 错误处理示例

```python
import httpx

try:
    resp = httpx.post(
        "https://xsmartdeepresearch.fusionxlink.com/api/v1/research",
        json={"question": "测试问题", "max_iterations": 5},
        timeout=300
    )
    resp.raise_for_status()
    result = resp.json()
    
    if result["status"] == "completed" and result["answer"]:
        print("研究成功:", result["answer"][:200])
    else:
        print(f"研究未完成: {result['termination_reason']}")
        
except httpx.TimeoutException:
    print("请求超时，请重试或使用异步模式")
except httpx.HTTPStatusError as e:
    print(f"HTTP 错误: {e.response.status_code} - {e.response.text}")
```

### JavaScript 错误处理示例

```javascript
try {
  const resp = await fetch("https://xsmartdeepresearch.fusionxlink.com/api/v1/research", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question: "测试问题", max_iterations: 5 }),
    signal: AbortSignal.timeout(300000)
  });
  
  if (!resp.ok) throw new Error(`HTTP ${resp.status}: ${await resp.text()}`);
  
  const result = await resp.json();
  if (result.status === "completed" && result.answer) {
    console.log("研究成功:", result.answer.slice(0, 200));
  } else {
    console.log(`研究未完成: ${result.termination_reason}`);
  }
} catch (e) {
  if (e.name === "TimeoutError") console.error("请求超时，请重试或使用异步模式");
  else console.error("错误:", e.message);
}
```

---

## 完整示例

### Python: 带进度条的流式研究

```python
"""完整示例: 带进度条的流式深度研究"""
import httpx
import json
import sys

def research(question: str, max_iters: int = 10):
    BASE = "https://xsmartdeepresearch.fusionxlink.com"
    
    print(f"🔬 开始研究: {question}\n")
    
    with httpx.Client(timeout=httpx.Timeout(600.0)) as c:
        with c.stream("POST", f"{BASE}/api/v1/research/stream",
                       json={"question": question, "max_iterations": max_iters}) as resp:
            for line in resp.iter_lines():
                if line.startswith(":") or not line.startswith("data: "):
                    continue
                ev = json.loads(line[6:])
                t = ev.get("type")
                
                if t == "status":
                    print(f"  📋 {ev['content']}", flush=True)
                elif t == "tool_start":
                    print(f"  🔧 调用 {ev['tool']}...", flush=True)
                elif t == "tool_response":
                    print(f"  ✅ {ev['tool']} 返回 {len(ev['content'])} 字符", flush=True)
                elif t == "final_answer":
                    print(f"\n{'='*60}")
                    print(f"📝 最终答案 (迭代 {ev['iterations']} 次)\n")
                    print(ev["content"])
                    return ev["content"]
    
    return None

if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "AI Agent 技术的最新发展趋势是什么？"
    research(q)
```

### JavaScript: React Hook

```javascript
import { useState, useCallback } from "react";

/**
 * React Hook: 流式深度研究
 * 
 * const { research, answer, events, isLoading, error } = useResearch();
 * research("你的问题");
 */
export function useResearch(baseUrl = "https://xsmartdeepresearch.fusionxlink.com") {
  const [answer, setAnswer] = useState(null);
  const [events, setEvents] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const research = useCallback(async (question, maxIterations = 10) => {
    setIsLoading(true);
    setAnswer(null);
    setEvents([]);
    setError(null);

    try {
      const resp = await fetch(`${baseUrl}/api/v1/research/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, max_iterations: maxIterations })
      });

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop();

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const event = JSON.parse(line.slice(6));
            setEvents(prev => [...prev, event]);
            
            if (event.type === "final_answer") {
              setAnswer(event.content);
            } else if (event.type === "error") {
              setError(event.content);
            }
          } catch {}
        }
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setIsLoading(false);
    }
  }, [baseUrl]);

  return { research, answer, events, isLoading, error };
}
```

---

## 接入建议

| 场景 | 推荐方式 | 原因 |
|------|----------|------|
| **前端展示研究过程** | SSE Stream | 实时展示思考/搜索进度，用户体验最佳 |
| **后端简单集成** | 同步 (Sync) | 最简单，一个请求获取结果 |
| **后端需要不阻塞** | 异步 + 轮询/Webhook | 提交后立即返回，不阻塞调用方 |
| **批量处理** | Batch + 轮询 | 一次提交多个问题并行处理 |
| **CI/CD 自动化** | 同步 + 超时重试 | 简单可靠 |

> **重要提示**: 
> - 同步和流式模式的超时建议设置 **≥ 300 秒**
> - SSE 流中的 `: keepalive` 注释是心跳信号，不是数据事件  
> - 所有响应的答案为 Markdown 格式
