"""API 依赖项"""

from functools import lru_cache
from typing import Dict, Any

from openai import AsyncOpenAI

from config import settings
from src.agent import xSmartReactAgent
from src.tools import SearchTool, VisitTool, PythonInterpreterTool, ScholarTool, FileParserTool


# 全局 Agent 实例
_agent_instance = None


@lru_cache()
def get_openai_client() -> AsyncOpenAI:
    """获取 OpenAI 客户端单例"""
    return AsyncOpenAI(
        api_key=settings.openrouter_key or settings.api_key,
        base_url=settings.api_base,
        timeout=600.0,
        default_headers={
            "HTTP-Referer": "https://github.com/sxm1129/DeepResearch",
            "X-Title": "xSmartDeepResearch",
        }
    )


@lru_cache()
def get_summary_client() -> AsyncOpenAI:
    """获取摘要用 OpenAI 客户端"""
    return AsyncOpenAI(
        api_key=settings.openrouter_key or settings.api_key,
        base_url=settings.api_base,
        timeout=60.0
    )


def get_agent() -> xSmartReactAgent:
    """获取或创建 Agent 实例"""
    global _agent_instance
    
    if _agent_instance is None:
        client = get_openai_client()
        summary_client = get_summary_client()
        
        # 初始化工具
        tools = []
        
        if settings.serper_api_key:
            tools.append(SearchTool(api_key=settings.serper_api_key))
            tools.append(ScholarTool(api_key=settings.serper_api_key))
        
        if settings.jina_api_key:
            tools.append(VisitTool(
                jina_api_key=settings.jina_api_key,
                summary_client=summary_client,
                summary_model=settings.summary_model_name
            ))
        
        tools.append(PythonInterpreterTool(
            sandbox_endpoints=settings.sandbox_endpoints_list
        ))
        tools.append(FileParserTool())
        
        _agent_instance = xSmartReactAgent(
            client=client,
            model=settings.model_name,
            tools=tools
        )
    
    return _agent_instance


def get_available_tools() -> list:
    """获取可用工具列表"""
    tools = []
    
    if settings.serper_api_key:
        tools.extend(["search", "google_scholar"])
    
    if settings.jina_api_key:
        tools.append("visit")
    
    tools.extend(["PythonInterpreter", "parse_file"])
    
    return tools


def get_task_store() -> Dict[str, Any]:
    """获取任务存储（简单实现）"""
    # 生产环境应该使用 Redis
    return {}
