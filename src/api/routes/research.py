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
from src.utils.logger import logger
from src.api.dependencies import get_agent, get_task_store


router = APIRouter(prefix="/research", tags=["Research"])


# 任务存储（简单内存实现，生产环境应使用Redis）
_tasks: Dict[str, Dict[str, Any]] = {}


@router.post("/stream")
async def stream_research(
    request: Request,
    research_request: ResearchRequest,
):
    """
    流式执行研究任务 (SSE)
    
    实时返回研究过程中的思考、工具调用和最终结果。
    """
    async def event_generator():
        agent = get_agent()
        agent.max_iterations = research_request.max_iterations
        
        try:
            # agent.stream_run 是同步生成器
            for event in agent.stream_run(research_request.question):
                # 检查客户端是否已断开
                if await request.is_disconnected():
                    logger.info("Client disconnected, stopping research stream.")
                    break
                    
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                # 给一点时间让IO发生，支持协程切换
                await asyncio.sleep(0.01)
                
        except Exception as e:
            logger.error(f"Stream research failed: {e}")
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
        
        # 设置迭代次数
        agent.max_iterations = request.max_iterations
        
        # 执行研究
        result = agent.run(request.question)
        
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
    
    # 初始化任务状态
    _tasks[task_id] = {
        "status": ResearchStatus.PENDING,
        "question": request.question,
        "answer": None,
        "iterations": 0,
        "execution_time": 0,
        "termination_reason": "",
        "created_at": datetime.now()
    }
    
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
    try:
        _tasks[task_id]["status"] = ResearchStatus.RUNNING
        
        agent = get_agent()
        agent.max_iterations = request.max_iterations
        
        # 在线程池中执行同步代码
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: agent.run(request.question)
        )
        
        _tasks[task_id].update({
            "status": ResearchStatus.COMPLETED,
            "answer": result.prediction,
            "iterations": result.iterations,
            "execution_time": result.execution_time,
            "termination_reason": result.termination
        })
        
    except Exception as e:
        _tasks[task_id].update({
            "status": ResearchStatus.FAILED,
            "answer": f"Error: {str(e)}",
            "termination_reason": "error"
        })


@router.get("/{task_id}", response_model=ResearchResponse)
async def get_research_result(task_id: str):
    """
    获取研究任务结果
    
    根据任务ID查询研究结果。
    """
    if task_id not in _tasks:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    task = _tasks[task_id]
    
    return ResearchResponse(
        task_id=task_id,
        question=task["question"],
        answer=task.get("answer", ""),
        status=task["status"],
        iterations=task.get("iterations", 0),
        execution_time=task.get("execution_time", 0),
        termination_reason=task.get("termination_reason", ""),
        created_at=task.get("created_at", datetime.now())
    )


@router.get("/{task_id}/status", response_model=TaskStatus)
async def get_research_status(task_id: str):
    """
    获取研究任务状态
    
    快速查询任务当前状态。
    """
    if task_id not in _tasks:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    task = _tasks[task_id]
    
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
        message=task.get("termination_reason", "")
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
        
        # 初始化任务状态
        _tasks[task_id] = {
            "status": ResearchStatus.PENDING,
            "question": question,
            "answer": None,
            "iterations": 0,
            "execution_time": 0,
            "termination_reason": "",
            "created_at": datetime.now(),
            "batch_id": batch_id
        }
        
        # 在后台并行启动
        research_req = ResearchRequest(
            question=question,
            max_iterations=request.max_iterations
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
async def cancel_research(task_id: str):
    """
    取消研究任务（仅支持PENDING状态的任务）
    """
    if task_id not in _tasks:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    task = _tasks[task_id]
    
    if task["status"] not in [ResearchStatus.PENDING, ResearchStatus.RUNNING]:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot cancel task in {task['status']} status"
        )
    
    # 标记为取消（实际取消需要更复杂的实现）
    _tasks[task_id]["status"] = ResearchStatus.FAILED
    _tasks[task_id]["termination_reason"] = "cancelled"
    
    return {"message": f"Task {task_id} cancelled"}
