"""研究 API 路由"""

import uuid
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

import httpx
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
import json

from src.api.schemas import (
    ResearchRequest, 
    ResearchResponse, 
    ResearchStatus,
    TaskStatus,
    BatchResearchRequest,
    BatchResearchResponse
)
from typing import List, Dict
from src.utils.logger import logger
from src.api.dependencies import get_agent, get_task_store
from src.utils.session_manager import SessionManager
from src.api.dependencies import get_session_manager

from arq import create_pool
from arq.connections import ArqRedis
from src.config.queue import redis_settings

router = APIRouter(prefix="/research", tags=["Research"])

_arq_pool: Optional[ArqRedis] = None

async def get_arq_pool() -> ArqRedis:
    global _arq_pool
    if _arq_pool is None:
        _arq_pool = await create_pool(redis_settings)
    return _arq_pool


@router.post("", response_model=TaskStatus)
async def create_research(request: ResearchRequest):
    """
    创建异步研究任务 (被提交给 arq Worker)
    立即返回任务ID，前端应使用 GET /research/{task_id}/stream 监听进度。
    """
    task_id = str(uuid.uuid4())[:10]
    session_manager = get_session_manager()
    from config import settings
    
    await asyncio.to_thread(
        session_manager.create_research_task,
        task_id=task_id,
        question=request.question,
        status=ResearchStatus.PENDING
    )
    
    pool = await get_arq_pool()
    await pool.enqueue_job(
        "run_research_task",
        task_id,
        request.question,
        {
            "original_question": request.question,
            "callback_url": getattr(request, "callback_url", None),
            "callback_events": getattr(request, "callback_events", None)
        },
        _job_id=task_id
    )
    
    return TaskStatus(
        task_id=task_id,
        status=ResearchStatus.PENDING,
        current_iteration=0,
        message="Task queued"
    )

@router.get("/{task_id}/stream")
async def stream_task_events(task_id: str, request: Request):
    """
    订阅 Redis Pub/Sub 中的任务事件，流式返回 (SSE)。
    """
    from config import settings
    import redis.asyncio as aioredis
    
    async def event_generator():
        redis = aioredis.from_url(settings.redis_url)
        pubsub = redis.pubsub()
        channel = f"task_events_{task_id}"
        await pubsub.subscribe(channel)
        
        try:
            while True:
                if await request.is_disconnected():
                    logger.info(f"Client disconnected from {task_id} stream.")
                    break
                
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message is not None:
                    data = message['data'].decode('utf-8')
                    # Check for EOF sentinel
                    try:
                        event_data = json.loads(data)
                        if event_data.get("content") == "EOF":
                            break
                    except Exception:
                        pass
                    
                    yield f"data: {data}\n\n"
                
                # keepalive for Nginx 504
                yield ": keepalive\n\n"
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()
            await redis.aclose()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# Keep old sync route available if needed for backwards compat, or remove it. We'll rename old POST "" to /sync if needed, 
# But wait, we just overwrote POST "". So let's delete the old create_research and create_async_research methods.
# For /async endpoint it now maps directly to POST "" logic, but to keep backwards compat we can map it too.
@router.post("/async", response_model=TaskStatus)
async def create_async_research_legacy(request: ResearchRequest):
    return await create_research(request)
@router.post("/{task_id}/cancel")
async def cancel_task_endpoint(task_id: str):
    """
    发送中断信号到 arq Worker
    """
    session_manager = get_session_manager()
    await asyncio.to_thread(session_manager.update_research_task, task_id, {
        "status": ResearchStatus.FAILED,
        "termination_reason": "cancelled"
    })
    
    from arq.jobs import Job
    pool = await get_arq_pool()
    job = Job(task_id, pool)
    try:
        await job.abort()
        return {"status": "cancelled"}
    except Exception as e:
        logger.warning(f"Could not cleanly abort arq job {task_id}: {e}")
        return {"status": "error_or_completed"}
@router.get("/history", response_model=List[ResearchResponse])
async def list_research_history():
    """
    获取研究历史任务列表
    """
    session_manager = get_session_manager()
    history = []
    tasks = await asyncio.to_thread(session_manager.list_research_tasks, limit=100)
    
    for task in tasks:
        history.append(ResearchResponse(
            task_id=task["task_id"],
            question=task["question"],
            answer=task.get("answer") or "",
            status=task["status"],
            iterations=task.get("iterations", 0),
            execution_time=task.get("execution_time", 0),
            termination_reason=task.get("termination_reason") or "",
            created_at=task.get("created_at"),
            is_bookmarked=task.get("is_bookmarked") or False
        ))
    
    return history


@router.get("/{task_id}", response_model=ResearchResponse)
async def get_research_result(task_id: str):
    """
    获取研究任务结果
    
    根据任务ID查询研究结果。
    """
    session_manager = get_session_manager()
    task = await asyncio.to_thread(session_manager.get_research_task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    return ResearchResponse(
        task_id=task_id,
        question=task["question"],
        answer=task.get("answer") or "",
        status=task["status"],
        iterations=task.get("iterations", 0),
        execution_time=task.get("execution_time", 0),
        termination_reason=task.get("termination_reason") or "",
        created_at=task.get("created_at"),
        is_bookmarked=task.get("is_bookmarked") or False
    )


@router.get("/{task_id}/status", response_model=TaskStatus)
async def get_research_status(task_id: str):
    """
    获取研究任务状态
    
    快速查询任务当前状态。
    """
    session_manager = get_session_manager()
    task = await asyncio.to_thread(session_manager.get_research_task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    # 计算进度
    progress = None
    if task["status"] == ResearchStatus.RUNNING:
        from config import settings as app_settings
        max_iter = app_settings.max_llm_call_per_run or 50
        progress = min(100, int(task.get("iterations", 0) / max_iter * 100))
    elif task["status"] == ResearchStatus.COMPLETED:
        progress = 100
    
    return TaskStatus(
        task_id=task_id,
        status=task["status"],
        progress=progress,
        current_iteration=task.get("iterations", 0),
        message=task.get("termination_reason") or ""
    )


@router.post("/batch", response_model=BatchResearchResponse)
async def create_batch_research(request: BatchResearchRequest):
    batch_id = str(uuid.uuid4())[:10]
    task_ids = []
    
    session_manager = get_session_manager()
    pool = await get_arq_pool()
    
    for question in request.questions:
        task_id = str(uuid.uuid4())[:10]
        task_ids.append(task_id)
        
        await asyncio.to_thread(
            session_manager.create_research_task,
            task_id=task_id,
            question=question,
            status=ResearchStatus.PENDING
        )
        
        await pool.enqueue_job(
            "run_research_task",
            task_id,
            question,
            {
                "original_question": question,
                "callback_url": getattr(request, "callback_url", None),
                "callback_events": getattr(request, "callback_events", None)
            },
            _job_id=task_id
        )
    
    return BatchResearchResponse(
        batch_id=batch_id,
        task_ids=task_ids,
        status="accepted"
    )

@router.delete("/{task_id}")
async def cancel_research(task_id: str, force: bool = False):
    """
    取消或删除研究任务
    """
    session_manager = get_session_manager()
    task = await asyncio.to_thread(session_manager.get_research_task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    # 尝试从队列中止任务
    try:
        from arq.jobs import Job
        pool = await get_arq_pool()
        job = Job(task_id, pool)
        await job.abort()
    except Exception:
        pass
        
    if force or task["status"] in [ResearchStatus.COMPLETED, ResearchStatus.FAILED, ResearchStatus.TIMEOUT]:
         await asyncio.to_thread(session_manager.delete_research_task, task_id)
         return {"message": f"Task {task_id} deleted"}
    
    await asyncio.to_thread(session_manager.update_research_task, task_id, {
        "status": ResearchStatus.FAILED,
        "termination_reason": "cancelled"
    })
    
    return {"message": f"Task {task_id} cancelled"}

@router.post("/{task_id}/bookmark")
async def toggle_bookmark(task_id: str):
    """
    切换研究任务的收藏状态
    """
    # Check existence
    session_manager = get_session_manager()
    task = await asyncio.to_thread(session_manager.get_research_task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
    is_bookmarked = await asyncio.to_thread(session_manager.toggle_research_bookmark, task_id)
    
    return {"message": "Bookmark updated", "is_bookmarked": is_bookmarked}
