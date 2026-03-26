import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
import redis.asyncio as aioredis
import httpx
from datetime import datetime

from src.agent.react_agent import AdvancedResearchAgent
from config.settings import Settings

logger = logging.getLogger(__name__)
settings = Settings()

async def get_redis_connection():
    return aioredis.from_url(settings.redis_url)

async def _dispatch_webhook(
    callback_url: str,
    event: dict,
    callback_events: Optional[List[str]] = None
):
    if callback_events and event.get("type") not in callback_events:
        return
    
    payload = {
        "task_id": event.get("task_id"),
        "type": event["type"],
        "content": event.get("content", ""),
        "iteration": event.get("iteration"),
        "tool": event.get("tool"),
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(callback_url, json=payload)
    except Exception as e:
        logger.warning(f"Webhook dispatch to {callback_url} failed: {e}")

async def run_research_task(ctx: Dict[Any, Any], task_id: str, query: str, config: Dict[str, Any]):
    """
    Execute deep research asynchronously.
    Pushes events to Redis Pub/Sub so clients can subscribe via SSE.
    """
    logger.info(f"🚀 Worker starting task {task_id} for query: {query[:50]}")
    redis = await get_redis_connection()
    channel = f"task_events_{task_id}"
    
    agent = AdvancedResearchAgent()
    
    from src.utils.session_manager import SessionManager
    from src.api.schemas import ResearchStatus
    session_manager = SessionManager(settings.db_url)
    
    # Recover original context
    original_question = config.get("original_question", query)
    callback_url = config.get("callback_url")
    callback_events = config.get("callback_events")
    
    await asyncio.to_thread(session_manager.update_research_task, task_id, {"status": ResearchStatus.RUNNING})
    final_answer_data = None
    
    try:
        from src.utils.language import get_language
        lang = get_language(query)
        
        async for event in agent.stream_run(query, original_question=original_question, language=lang, max_steps=settings.max_llm_call_per_run):
            event["task_id"] = task_id
            
            if callback_url:
                 asyncio.create_task(_dispatch_webhook(callback_url, dict(event), callback_events))
            
            if event.get("type") == "final_answer":
                final_answer_data = event
                
            event_json = json.dumps(event, ensure_ascii=False)
            await redis.publish(channel, event_json)
            # Yield control to allow cancellation to propagate
            await asyncio.sleep(0)
            
        update_data = {"status": ResearchStatus.COMPLETED}
        if final_answer_data:
            update_data.update({
                "answer": final_answer_data.get("content", ""),
                "iterations": final_answer_data.get("iterations", 0),
                "execution_time": 0,
                "termination_reason": final_answer_data.get("termination", "answer")
            })
        await asyncio.to_thread(session_manager.update_research_task, task_id, update_data)
            
    except asyncio.CancelledError:
        logger.warning(f"⚠️ Task {task_id} was cancelled by user/queue.")
        await asyncio.to_thread(session_manager.update_research_task, task_id, {"status": ResearchStatus.FAILED, "termination_reason": "cancelled"})
        cancel_event = {
            "type": "error",
            "content": "Researcher Interrupted: Task was cancelled.",
            "tool": None
        }
        await redis.publish(channel, json.dumps(cancel_event))
        raise
        
    except Exception as e:
        logger.error(f"❌ Error in task {task_id}: {e}", exc_info=True)
        if callback_url:
            await _dispatch_webhook(callback_url, {"task_id": task_id, "type": "error", "content": str(e)}, callback_events)
            
        await asyncio.to_thread(session_manager.update_research_task, task_id, {
            "status": ResearchStatus.FAILED,
            "answer": f"Error: {str(e)}",
            "termination_reason": "error"
        })
        error_event = {
            "type": "error",
            "content": f"Internal Error: {str(e)}",
            "tool": None
        }
        await redis.publish(channel, json.dumps(error_event))
        
    finally:
        # Publish a special EOF token so listeners know to disconnect
        eof_event = {"type": "ping", "content": "EOF"}
        await redis.publish(channel, json.dumps(eof_event))
        logger.info(f"🛑 Worker finished task {task_id}")
        await redis.aclose()
