"""高级研究 API 路由 - 意图澄清 + 深度研究 (完全独立于现有 research 路由)"""

import uuid
import asyncio
import json
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from src.api.schemas.advanced_research import (
    ClarifyRequest,
    ClarifyResponse,
    ClarificationDirectionSchema,
    AdvancedResearchRequest
)
from src.utils.logger import logger
from src.api.dependencies import get_agent, get_session_manager
from src.api.schemas import ResearchStatus


router = APIRouter(prefix="/advanced-research", tags=["Advanced Research"])


# Cached IntentClarifier singleton
_clarifier_instance = None


def _get_clarifier():
    """获取 IntentClarifier 单例 (复用 dependencies 中的 client，避免资源泄漏)"""
    global _clarifier_instance
    if _clarifier_instance is None:
        from config import settings
        from src.agent.intent_clarifier import IntentClarifier
        from src.api.dependencies import get_openai_client
        
        # 复用已有的 openai_client 单例 (包含 OpenRouter 所需的 headers)
        client = get_openai_client()
        # 从配置读取模型，默认 gpt-4o-mini
        model = getattr(settings, 'clarifier_model', None) or 'gpt-4o-mini'
        _clarifier_instance = IntentClarifier(client=client, model=model)
    return _clarifier_instance


@router.post("/clarify", response_model=ClarifyResponse)
async def clarify_intent(request: ClarifyRequest):
    """
    意图澄清端点
    
    **第一轮 (round=1)**：分析用户问题，返回 3-5 个研究方向供选择。
    
    **第二轮 (round=2)**：根据用户选择的方向，生成精炼的研究查询。
    
    当 `ready_to_research=True` 时，使用 `refined_query` 调用 `/stream` 端点开始深度研究。
    """
    clarifier = _get_clarifier()
    
    if request.round == 1:
        # 第一轮：生成研究方向
        result = await clarifier.clarify_round1(request.question, language=request.language)
        
        return ClarifyResponse(
            directions=[
                ClarificationDirectionSchema(
                    id=d.id,
                    title=d.title,
                    description=d.description,
                    example_query=d.example_query
                ) for d in result.directions
            ],
            round=1,
            ready_to_research=False,
            original_question=request.question
        )
    
    elif request.round == 2:
        # 第二轮：用户已选择方向或自定义
        if request.custom_input:
            # 用户输入了自定义方向
            result = await clarifier.clarify_custom(
                original_question=request.question,
                custom_input=request.custom_input,
                language=request.language
            )
        elif request.selected_direction:
            # 用户选择了预设方向
            from src.agent.intent_clarifier import ClarificationDirection
            direction = ClarificationDirection(
                id=request.selected_direction.id,
                title=request.selected_direction.title,
                description=request.selected_direction.description,
                example_query=request.selected_direction.example_query
            )
            result = await clarifier.clarify_round2(
                original_question=request.question,
                selected_direction=direction,
                user_context=request.user_context or "",
                language=request.language
            )
        else:
            # 没有选择也没有自定义，直接使用原始问题
            return ClarifyResponse(
                directions=[],
                round=2,
                ready_to_research=True,
                refined_query=request.question,
                original_question=request.question
            )
        
        return ClarifyResponse(
            directions=[],
            round=2,
            ready_to_research=result.ready_to_research,
            refined_query=result.refined_query,
            original_question=request.question
        )


@router.post("/stream")
async def stream_advanced_research(
    request: Request,
    research_request: AdvancedResearchRequest,
):
    """
    高级研究流式端点 (SSE)
    
    接收经过意图澄清后的精炼查询，调用现有 ReAct Agent 进行深度研究。
    返回与 `/research/stream` 相同格式的 SSE 事件流。
    """
    session_manager = get_session_manager()
    
    async def event_generator():
        agent = get_agent()
        from config import settings
        effective_max_iterations = research_request.max_iterations or settings.max_llm_call_per_run
        
        task_id = str(uuid.uuid4())[:8]
        queue = asyncio.Queue()
        done_event = asyncio.Event()
        
        async def heartbeat_task():
            """每15秒发送SSE心跳"""
            while not done_event.is_set():
                try:
                    await asyncio.wait_for(done_event.wait(), timeout=15)
                    break
                except asyncio.TimeoutError:
                    await queue.put(": keepalive\n\n")
        
        async def research_task():
            """执行研究并将事件推入队列"""
            try:
                await asyncio.to_thread(
                    session_manager.create_research_task,
                    task_id=task_id,
                    question=research_request.original_question,
                    status=ResearchStatus.RUNNING
                )
                
                final_answer_data = None
                
                # 发送任务创建事件，附带原始问题和精炼查询
                await queue.put(f"data: {json.dumps({'type': 'task_created', 'content': 'Advanced research initiated', 'task_id': task_id, 'original_question': research_request.original_question, 'refined_query': research_request.refined_query}, ensure_ascii=False)}\n\n")
                
                # 使用精炼后的查询调用现有 Agent
                async for event in agent.stream_run(research_request.refined_query, max_iterations=effective_max_iterations):
                    if await request.is_disconnected():
                        logger.info("Client disconnected, stopping advanced research stream.")
                        break
                    
                    if isinstance(event, dict) and event.get("type") == "final_answer":
                        final_answer_data = event
                    
                    await queue.put(f"data: {json.dumps(event, ensure_ascii=False)}\n\n")
                
                # 更新任务状态
                update_data = {"status": ResearchStatus.COMPLETED}
                if final_answer_data:
                    update_data.update({
                        "answer": final_answer_data.get("content", ""),
                        "iterations": final_answer_data.get("iterations", 0),
                        "termination_reason": final_answer_data.get("termination", "answer")
                    })
                
                await asyncio.to_thread(session_manager.update_research_task, task_id, update_data)
                
            except Exception as e:
                logger.error(f"Advanced research stream failed: {e}")
                await asyncio.to_thread(session_manager.update_research_task, task_id, {
                    "status": ResearchStatus.FAILED,
                    "termination_reason": str(e)
                })
                await queue.put(f"data: {json.dumps({'type': 'error', 'content': str(e)}, ensure_ascii=False)}\n\n")
            finally:
                done_event.set()
                await queue.put(None)
        
        # Start tasks
        heartbeat = asyncio.create_task(heartbeat_task())
        research = asyncio.create_task(research_task())
        
        try:
            while True:
                item = await queue.get()
                if item is None:
                    break
                yield item
        finally:
            done_event.set()
            heartbeat.cancel()
            if not research.done():
                research.cancel()
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
