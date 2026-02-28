"""
xSmartDeepResearch Webhook 集成示例

展示如何从外部服务调用 DeepResearch 的 async API 并通过 Webhook 回调接收进度。

使用方式:
  # 1. 确保 DeepResearch 服务已运行在 localhost:8000
  
  # 2. 启动回调接收服务 (一个终端)
  python examples/webhook_integration.py --mode server

  # 3. 发起研究任务 (另一个终端)
  python examples/webhook_integration.py --mode client --question "量子计算最新进展"
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime

# ============================================================================
# 方案一: 回调接收服务 (你的业务服务中的回调端点)
# ============================================================================

def run_callback_server(port: int = 9000):
    """启动一个简单的 FastAPI 服务来接收 Webhook 回调"""
    try:
        from fastapi import FastAPI, Request
        import uvicorn
    except ImportError:
        print("请安装 fastapi 和 uvicorn: pip install fastapi uvicorn")
        sys.exit(1)
    
    app = FastAPI(title="Webhook Callback Receiver")
    
    # 存储接收到的事件
    received_events = []
    
    @app.post("/webhook/research")
    async def receive_callback(request: Request):
        """接收 DeepResearch 的进度回调"""
        event = await request.json()
        received_events.append(event)
        
        event_type = event.get("type", "unknown")
        task_id = event.get("task_id", "?")
        content = event.get("content", "")
        iteration = event.get("iteration")
        tool = event.get("tool")
        
        # 根据事件类型格式化输出
        if event_type == "status":
            print(f"  📌 [{task_id}] 状态: {content}")
        elif event_type == "think":
            preview = content[:150].replace('\n', ' ')
            print(f"  🧠 [{task_id}] 思考: {preview}...")
        elif event_type == "tool_start":
            print(f"  🔧 [{task_id}] 调用工具: {tool} (迭代 {iteration})")
        elif event_type == "tool_response":
            print(f"  📦 [{task_id}] 工具响应: {tool} 返回 {len(content)} 字符")
        elif event_type == "answer":
            preview = content[:200].replace('\n', ' ')
            print(f"  ✅ [{task_id}] 答案预览: {preview}...")
        elif event_type == "final_answer":
            print(f"  🎯 [{task_id}] 研究完成! 答案长度: {len(content)} 字符")
            print(f"      迭代次数: {event.get('iterations', '?')}")
        elif event_type == "error":
            print(f"  ❌ [{task_id}] 错误: {content}")
        else:
            print(f"  ❓ [{task_id}] {event_type}: {content[:100]}")
        
        return {"status": "received"}
    
    @app.get("/webhook/events")
    async def list_events():
        """查看所有接收到的事件"""
        return {"total": len(received_events), "events": received_events}
    
    print(f"🚀 Webhook 回调接收服务启动在 http://0.0.0.0:{port}")
    print(f"   回调端点: POST http://localhost:{port}/webhook/research")
    print(f"   事件查询: GET  http://localhost:{port}/webhook/events")
    print("=" * 60)
    print("等待 DeepResearch 回调...\n")
    
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")


# ============================================================================
# 方案二: 调用客户端 (你的业务服务中发起研究请求的代码)
# ============================================================================

async def submit_research(
    question: str,
    deep_research_url: str = "http://localhost:8000",
    callback_url: str = "http://localhost:9000/webhook/research",
    callback_events: list = None,
    max_iterations: int = None
):
    """
    向 DeepResearch 提交异步研究任务 (带 Webhook 回调)
    
    这是你在自己的服务中调用 DeepResearch 的方式。
    
    Args:
        question: 研究问题
        deep_research_url: DeepResearch 服务地址
        callback_url: 你的回调接收地址
        callback_events: 需要接收的事件类型 (None = 全部)
        max_iterations: 最大迭代次数
    
    Returns:
        task_id: 任务ID, 可用于后续查询
    """
    try:
        import httpx
    except ImportError:
        print("请安装 httpx: pip install httpx")
        sys.exit(1)
    
    payload = {
        "question": question,
        "callback_url": callback_url,
    }
    
    if callback_events:
        payload["callback_events"] = callback_events
    if max_iterations:
        payload["max_iterations"] = max_iterations
    
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{deep_research_url}/api/v1/research/async",
            json=payload
        )
        response.raise_for_status()
        result = response.json()
    
    task_id = result["task_id"]
    print(f"✅ 任务已提交! task_id: {task_id}")
    print(f"   问题: {question}")
    print(f"   回调地址: {callback_url}")
    print(f"   查询状态: GET {deep_research_url}/api/v1/research/{task_id}/status")
    print(f"   获取结果: GET {deep_research_url}/api/v1/research/{task_id}")
    
    return task_id


async def poll_until_done(
    task_id: str,
    deep_research_url: str = "http://localhost:8000",
    interval: int = 5
):
    """
    轮询任务状态直到完成 (可选, 配合回调使用)
    
    即使有 Webhook 回调, 你也可能需要轮询来确认最终状态。
    """
    try:
        import httpx
    except ImportError:
        print("请安装 httpx: pip install httpx")
        sys.exit(1)
    
    print(f"\n⏳ 轮询任务状态 (每 {interval} 秒)...")
    
    async with httpx.AsyncClient(timeout=30) as client:
        while True:
            response = await client.get(
                f"{deep_research_url}/api/v1/research/{task_id}/status"
            )
            status_data = response.json()
            
            status = status_data["status"]
            progress = status_data.get("progress", "?")
            iteration = status_data.get("current_iteration", 0)
            
            print(f"   状态: {status} | 进度: {progress}% | 迭代: {iteration}")
            
            if status in ["completed", "failed", "timeout"]:
                # 获取完整结果
                result_response = await client.get(
                    f"{deep_research_url}/api/v1/research/{task_id}"
                )
                return result_response.json()
            
            await asyncio.sleep(interval)


# ============================================================================
# CLI 入口
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="xSmartDeepResearch Webhook 集成示例")
    parser.add_argument(
        "--mode", choices=["server", "client"], required=True,
        help="server: 启动回调接收服务 | client: 提交研究任务"
    )
    parser.add_argument("--question", default="人工智能在医疗领域的最新应用有哪些？", help="研究问题")
    parser.add_argument("--port", type=int, default=9000, help="回调服务端口")
    parser.add_argument("--research-url", default="http://localhost:8000", help="DeepResearch 服务地址")
    parser.add_argument(
        "--events", nargs="*",
        default=["status", "think", "tool_start", "answer", "final_answer", "error"],
        help="需要接收的事件类型"
    )
    parser.add_argument("--poll", action="store_true", help="提交后轮询等待结果")
    
    args = parser.parse_args()
    
    if args.mode == "server":
        run_callback_server(port=args.port)
    else:
        async def _run():
            callback_url = f"http://localhost:{args.port}/webhook/research"
            task_id = await submit_research(
                question=args.question,
                deep_research_url=args.research_url,
                callback_url=callback_url,
                callback_events=args.events
            )
            
            if args.poll:
                result = await poll_until_done(task_id, args.research_url)
                print(f"\n{'=' * 60}")
                print(f"📋 最终结果:")
                print(f"   状态: {result.get('status')}")
                print(f"   迭代: {result.get('iterations')}")
                print(f"   答案: {result.get('answer', '')[:500]}...")
        
        asyncio.run(_run())


if __name__ == "__main__":
    main()
