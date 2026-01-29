"""Settings API 路由"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from config import settings

router = APIRouter(prefix="/settings", tags=["Settings"])

class SettingsUpdate(BaseModel):
    model_name: Optional[str] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_iterations: Optional[int] = None
    max_context_tokens: Optional[int] = None
    # API Keys (optional updates)
    openai_api_key: Optional[str] = None
    serper_api_key: Optional[str] = None
    
class SettingsResponse(BaseModel):
    model_name: str
    temperature: float
    top_p: float
    max_iterations: int
    max_context_tokens: int
    # Do not return full keys for security
    openai_api_key_masked: str
    serper_api_key_masked: str

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
        openai_api_key_masked=mask_key(settings.api_key),
        serper_api_key_masked=mask_key(settings.serper_api_key)
    )

@router.post("", response_model=SettingsResponse)
async def update_settings(update: SettingsUpdate):
    """更新系统设置 (运行时更新)"""
    if update.model_name is not None:
        settings.model_name = update.model_name
    if update.temperature is not None:
        settings.temperature = update.temperature
    if update.top_p is not None:
        settings.top_p = update.top_p
    if update.max_iterations is not None:
        settings.max_llm_call_per_run = update.max_iterations
    if update.max_context_tokens is not None:
        settings.max_context_tokens = update.max_context_tokens
        
    if update.openai_api_key:
        settings.api_key = update.openai_api_key
    if update.serper_api_key:
        settings.serper_api_key = update.serper_api_key
        
    return await get_settings()
