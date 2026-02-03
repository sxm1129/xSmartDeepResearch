"""研究 API 路由"""

import uuid
import asyncio
from typing import Dict, Any
from datetime import datetime

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
from typing import List
from src.utils.logger import logger
from src.api.dependencies import get_agent, get_task_store


router = APIRouter(prefix="/research", tags=["Research"])


from src.utils.session_manager import SessionManager
from src.api.dependencies import get_session_manager

# Deprecated: session_manager = SessionManager()


@router.post("/stream")
async def stream_research(
    request: Request,
    research_request: ResearchRequest,
):
    session_manager = get_session_manager()
    """
    流式执行研究任务 (SSE)
    
    实时返回研究过程中的思考、工具调用和最终结果。
    """
    async def event_generator():
        agent = get_agent()
        # Fallback to global settings if not provided in request
        from config import settings
        agent.max_iterations = research_request.max_iterations or settings.max_llm_call_per_run
        
        task_id = str(uuid.uuid4())[:8]
        try:
            # Create task record
            await asyncio.to_thread(
                session_manager.create_research_task,
                task_id=task_id,
                question=research_request.question,
                status=ResearchStatus.RUNNING
            )

            final_answer_data = None
            
            # Send initial task_created event
            yield f"data: {json.dumps({'type': 'task_created', 'content': 'Task initiated', 'task_id': task_id}, ensure_ascii=False)}\n\n"
            
            async for event in agent.stream_run(research_request.question):
                # Check client disconnection
                if await request.is_disconnected():
                    logger.info("Client disconnected, stopping research stream.")
                    break
                
                # Capture final result if yielded
                if isinstance(event, dict) and event.get("type") == "final_answer":
                    final_answer_data = event
                
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.01)
            
            # Update task on completion
            update_data = {"status": ResearchStatus.COMPLETED}
            if final_answer_data:
                update_data.update({
                    "answer": final_answer_data.get("content", ""),
                    "iterations": final_answer_data.get("iterations", 0),
                    "termination_reason": final_answer_data.get("termination", "answer")
                })
            
            await asyncio.to_thread(session_manager.update_research_task, task_id, update_data)

        except Exception as e:
            logger.error(f"Stream research failed: {e}")
            await asyncio.to_thread(session_manager.update_research_task, task_id, {
                "status": ResearchStatus.FAILED,
                "termination_reason": str(e)
            })
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


@router.post("", response_model=ResearchResponse)
async def create_research(
    request: ResearchRequest,
    background_tasks: BackgroundTasks
):
    """
    创建研究任务
    
    同步执行研究任务并返回结果。对于长时间任务，考虑使用 /research/async 端点。
    """
    task_id = str(uuid.uuid4())[:8]
    
    try:
        agent = get_agent()
        
        # 设置迭代次数 (Fallback to global settings)
        from config import settings
        agent.max_iterations = request.max_iterations or settings.max_llm_call_per_run
        
        # 执行研究
        result = await agent.run(request.question)
        
        return ResearchResponse(
            task_id=task_id,
            question=request.question,
            answer=result.prediction,
            status=ResearchStatus.COMPLETED,
            iterations=result.iterations,
            execution_time=result.execution_time,
            termination_reason=result.termination,
            created_at=datetime.now()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Research failed: {str(e)}")


@router.post("/async", response_model=TaskStatus)
async def create_async_research(
    request: ResearchRequest,
    background_tasks: BackgroundTasks
):
    """
    创建异步研究任务
    
    立即返回任务ID，后台执行研究。使用 GET /research/{task_id} 查询结果。
    """
    task_id = str(uuid.uuid4())[:8]
    
    # 初始化任务状态 (MySQL)
    session_manager = get_session_manager()
    await asyncio.to_thread(
        session_manager.create_research_task,
        task_id=task_id,
        question=request.question,
        status=ResearchStatus.PENDING
    )
    
    # 在后台执行研究
    background_tasks.add_task(
        _run_research_task,
        task_id,
        request
    )
    
    return TaskStatus(
        task_id=task_id,
        status=ResearchStatus.PENDING,
        current_iteration=0,
        message="Task created, processing in background"
    )


async def _run_research_task(task_id: str, request: ResearchRequest):
    """后台执行研究任务"""
    session_manager = get_session_manager()
    try:
        await asyncio.to_thread(session_manager.update_research_task, task_id, {"status": ResearchStatus.RUNNING})
        
        agent = get_agent()
        from config import settings
        agent.max_iterations = request.max_iterations or settings.max_llm_call_per_run
        
        # 在线程池中执行同步代码
        loop = asyncio.get_event_loop()
        result = await agent.run(request.question)
        
        await asyncio.to_thread(session_manager.update_research_task, task_id, {
            "status": ResearchStatus.COMPLETED,
            "answer": result.prediction,
            "iterations": result.iterations,
            "execution_time": result.execution_time,
            "termination_reason": result.termination
        })
        
    except Exception as e:
        await asyncio.to_thread(session_manager.update_research_task, task_id, {
            "status": ResearchStatus.FAILED,
            "answer": f"Error: {str(e)}",
            "termination_reason": "error"
        })


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
        max_iter = 50  # 默认最大迭代
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
async def create_batch_research(
    request: BatchResearchRequest,
    background_tasks: BackgroundTasks
):
    """
    创建批量研究任务
    
    一次性提交多个问题，并行启动后台任务。返回批次ID和所有子任务ID。
    """
    batch_id = str(uuid.uuid4())[:8]
    task_ids = []
    
    for question in request.questions:
        task_id = str(uuid.uuid4())[:10]
        task_ids.append(task_id)
        
        task_ids.append(task_id)
        
        task_ids.append(task_id)
        
        # 初始化任务状态 (MySQL)
        session_manager = get_session_manager()
        await asyncio.to_thread(
            session_manager.create_research_task,
            task_id=task_id,
            question=question,
            status=ResearchStatus.PENDING
        )
        
        
        # 在后台并行启动
        research_req = ResearchRequest(
            question=question,
            max_iterations=request.max_iterations # Batch request handles its own defaults or passes explicit
        )
        background_tasks.add_task(
            _run_research_task,
            task_id,
            research_req
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
    
    - 如果任务正在运行且 force=False (默认): 标记为 Failed (取消)
    - 如果任务已完成/失败 或 force=True: 从数据库永久删除
    """
    session_manager = get_session_manager()
    task = session_manager.get_research_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    # Check if we should just delete it record
    if force or task["status"] in [ResearchStatus.COMPLETED, ResearchStatus.FAILED, ResearchStatus.TIMEOUT]:
         await asyncio.to_thread(session_manager.delete_research_task, task_id)
         return {"message": f"Task {task_id} deleted"}

    if task["status"] not in [ResearchStatus.PENDING, ResearchStatus.RUNNING]:
        # Should have been handled above, but just in case
        await asyncio.to_thread(session_manager.delete_research_task, task_id)
        return {"message": f"Task {task_id} deleted"}
    
    # If running and not forced, cancel it
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
    task = session_manager.get_research_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
    is_bookmarked = await asyncio.to_thread(session_manager.toggle_research_bookmark, task_id)
    
    return {"message": "Bookmark updated", "is_bookmarked": is_bookmarked}
