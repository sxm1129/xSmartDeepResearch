import asyncio
import httpx
import sys
import os
import json
import time
from typing import List

# 配置
API_BASE = "http://localhost:8000/api/v1"
CHECK_INTERVAL = 5  # 状态轮询间隔

async def run_batch_research(questions: List[str]):
    """执行批量研究任务"""
    print(f"🚀 Starting batch research for {len(questions)} questions...")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # 1. 提交批量任务
        try:
            response = await client.post(
                f"{API_BASE}/research/batch",
                json={"questions": questions, "max_iterations": 50}
            )
            response.raise_for_status()
            batch_info = response.json()
            task_ids = batch_info["task_ids"]
            print(f"✅ Batch accepted. Batch ID: {batch_info['batch_id']}")
            print(f"📋 Tasks: {', '.join(task_ids)}")
        except Exception as e:
            print(f"❌ Failed to submit batch: {e}")
            return

        # 2. 轮询状态
        completed_tasks = {}
        pending_ids = task_ids.copy()
        
        while pending_ids:
            print(f"\n⏳ Checking status ({len(completed_tasks)}/{len(task_ids)} completed)...")
            to_remove = []
            
            for tid in pending_ids:
                try:
                    res = await client.get(f"{API_BASE}/research/{tid}/status")
                    res.raise_for_status()
                    status_data = res.json()
                    
                    if status_data["status"] in ["completed", "failed", "timeout"]:
                        # 获取最终结果
                        res_full = await client.get(f"{API_BASE}/research/{tid}")
                        full_data = res_full.json()
                        completed_tasks[tid] = full_data
                        to_remove.append(tid)
                        print(f"✨ Task {tid} finished: {status_data['status']}")
                except Exception as e:
                    print(f"⚠️ Error checking task {tid}: {e}")
            
            for tid in to_remove:
                pending_ids.remove(tid)
            
            if pending_ids:
                await asyncio.sleep(CHECK_INTERVAL)

        # 3. 汇总结果
        print("\n" + "="*50)
        print("📊 BATCH RESEARCH RESULTS")
        print("="*50)
        
        for tid, data in completed_tasks.items():
            print(f"\n❓ Question: {data['question']}")
            print(f"🆔 Task ID: {tid}")
            print(f"⏱️  Time: {data['execution_time']:.2f}s | Iterations: {data['iterations']}")
            print("-" * 20)
            answer_preview = data['answer'][:200].replace('\n', ' ') + "..."
            print(f"💡 Answer: {answer_preview}")
            print("-" * 50)

if __name__ == "__main__":
    # 示例问题
    questions_list = [
        "2024年诺贝尔物理学奖得主是谁？",
        "DeepSeek-V3相比V2的主要性能改进有哪些？",
        "如何评价2024下半年的全球低空经济发展现状？"
    ]
    
    # 如果提供文件，按行读取
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                questions_list = [line.strip() for line in f if line.strip()]
        else:
            print(f"File not found: {file_path}")
            sys.exit(1)

    asyncio.run(run_batch_research(questions_list))
