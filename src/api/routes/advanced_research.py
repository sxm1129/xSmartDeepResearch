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
from src.api.schemas import ResearchStatus, TaskStatus


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


@router.post("", response_model=TaskStatus)
async def create_advanced_research(
    request: AdvancedResearchRequest,
):
    """
    高级研究队列端点
    
    接收经过意图澄清后的精炼查询，提交到后台异步队列。
    前端应使用 GET /research/{task_id}/stream 监听进度。
    """
    from src.api.routes.research import get_arq_pool
    
    task_id = str(uuid.uuid4())[:10]
    session_manager = get_session_manager()
    
    await asyncio.to_thread(
        session_manager.create_research_task,
        task_id=task_id,
        question=request.original_question,
        status=ResearchStatus.PENDING
    )
    
    pool = await get_arq_pool()
    await pool.enqueue_job(
        "run_research_task",
        task_id,
        request.refined_query,
        {"original_question": request.original_question},
        _job_id=task_id
    )
    
    from src.api.schemas import TaskStatus
    return TaskStatus(
        task_id=task_id,
        status=ResearchStatus.PENDING,
        current_iteration=0,
        message="Advanced task queued"
    )
