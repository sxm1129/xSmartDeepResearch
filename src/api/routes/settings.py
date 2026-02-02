"""Settings API 路由"""

from fastapi import APIRouter, HTTPException
import httpx
import time
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from config import settings

router = APIRouter(prefix="/settings", tags=["Settings"])

# In-memory cache for models
_models_cache = {
    "data": [],
    "expiry": 0
}
CACHE_TTL = 3600  # 1 hour

class SettingsUpdate(BaseModel):
    model_name: Optional[str] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_iterations: Optional[int] = None
    max_context_tokens: Optional[int] = None
    # API Keys (optional updates)
    openrouter_api_key: Optional[str] = None
    serper_api_key: Optional[str] = None
    jina_api_key: Optional[str] = None
    
class SettingsResponse(BaseModel):
    model_name: str
    temperature: float
    top_p: float
    max_iterations: int
    max_context_tokens: int
    # Do not return full keys for security
    openrouter_api_key_masked: str
    serper_api_key_masked: str
    jina_api_key_masked: str

def mask_key(key: str) -> str:
    if not key or len(key) < 8:
        return "****"
    return f"{key[:3]}****{key[-4:]}"

@router.get("", response_model=SettingsResponse)
async def get_settings():
    """获取当前系统设置"""
    return SettingsResponse(
        model_name=settings.model_name,
        temperature=settings.temperature,
        top_p=settings.top_p,
        max_iterations=settings.max_llm_call_per_run,
        max_context_tokens=settings.max_context_tokens,
        openrouter_api_key_masked=mask_key(settings.openrouter_key or settings.api_key),
        serper_api_key_masked=mask_key(settings.serper_api_key),
        jina_api_key_masked=mask_key(settings.jina_api_key)
    )

@router.post("", response_model=SettingsResponse)
async def update_settings(update: SettingsUpdate):
    """更新系统设置 (运行时更新 + 持久化)"""
    from src.api.dependencies import get_session_manager
    session_manager = get_session_manager()
    
    if update.model_name is not None:
        settings.model_name = update.model_name
        session_manager.save_setting("model_name", update.model_name)
    if update.temperature is not None:
        settings.temperature = update.temperature
        session_manager.save_setting("temperature", str(update.temperature))
    if update.top_p is not None:
        settings.top_p = update.top_p
        session_manager.save_setting("top_p", str(update.top_p))
    if update.max_iterations is not None:
        settings.max_llm_call_per_run = update.max_iterations
        session_manager.save_setting("max_llm_call_per_run", str(update.max_iterations))
    if update.max_context_tokens is not None:
        settings.max_context_tokens = update.max_context_tokens
        session_manager.save_setting("max_context_tokens", str(update.max_context_tokens))
        
    if update.openrouter_api_key:
        settings.openrouter_key = update.openrouter_api_key
        # Also sync to api_key for legacy support
        settings.api_key = update.openrouter_api_key
        session_manager.save_setting("openrouter_key", update.openrouter_api_key)
        session_manager.save_setting("api_key", update.openrouter_api_key)
        
    if update.serper_api_key:
        settings.serper_api_key = update.serper_api_key
        session_manager.save_setting("serper_api_key", update.serper_api_key)
        
    if update.jina_api_key:
        settings.jina_api_key = update.jina_api_key
        session_manager.save_setting("jina_api_key", update.jina_api_key)
        
    return await get_settings()
        
    return await get_settings()

@router.get("/models")
async def get_available_models():
    """从 OpenRouter 获取可用模型列表"""
    global _models_cache
    
    # Check cache
    now = time.time()
    if _models_cache["data"] and now < _models_cache["expiry"]:
        return _models_cache["data"]
        
    api_key = settings.openrouter_key or settings.api_key
    if not api_key or "your" in api_key:
        # Return fallback models if no key
        return [
            {"id": "gpt-4o", "name": "GPT-4o"},
            {"id": "openai/gpt-4o-mini", "name": "GPT-4o Mini"},
            {"id": "z-ai/glm-4.7-flash", "name": "GLM-4.7 Flash"},
            {"id": "deepseek/deepseek-chat", "name": "DeepSeek Chat"}
        ]
        
    try:
            print(f"DEBUG: Fetching models with key: {api_key[:10]}...")
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://openrouter.ai/api/v1/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=10.0
                )
                print(f"DEBUG: OpenRouter status: {response.status_code}")
                # response.raise_for_status() # Let's handle it manually to see body
                if response.status_code != 200:
                    print(f"DEBUG: OpenRouter error: {response.text}")
                    return [
                        {"id": "gpt-4o", "name": "GPT-4o (Fallback)"},
                        {"id": "openai/gpt-4o-mini", "name": "GPT-4o Mini"},
                        {"id": "z-ai/glm-4.7-flash", "name": "GLM-4.7 Flash"},
                        {"id": "deepseek/deepseek-chat", "name": "DeepSeek Chat"}
                    ]
                
                response.raise_for_status()
            data = response.json()
            print(f"DEBUG: OpenRouter data keys: {data.keys()}")
            print(f"DEBUG: OpenRouter data sample: {str(data)[:200]}")
            
            models = []
            for m in data.get("data", []):
                models.append({
                    "id": m.get("id"),
                    "name": m.get("name"),
                    "context_length": m.get("context_length"),
                    "pricing": m.get("pricing")
                })
            
            # Update cache
            _models_cache["data"] = models
            _models_cache["expiry"] = now + CACHE_TTL
            
            return models
    except Exception as e:
        # If error, return fallback and don't cache expiry
        return [
            {"id": "gpt-4o", "name": "GPT-4o"},
            {"id": "openai/gpt-4o-mini", "name": "GPT-4o Mini"}
        ]
