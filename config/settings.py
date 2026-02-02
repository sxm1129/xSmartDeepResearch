"""xSmartDeepResearch 配置模块"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """全局配置"""
    
    # ==========================================================================
    # API Keys
    # ==========================================================================
    serper_api_key: str = Field(default="", env="SERPER_API_KEY")
    jina_api_key: str = Field(default="", env="JINA_API_KEY")
    api_key: str = Field(default="", env="API_KEY") # Legacy fallback
    openrouter_key: str = Field(default="", env="OPENROUTER_KEY") # Primary LLM Key
    api_base: str = Field(default="https://openrouter.ai/api/v1", env="API_BASE")
    dashscope_api_key: str = Field(default="", env="DASHSCOPE_API_KEY")
    
    # ==========================================================================
    # Model Configuration
    # ==========================================================================
    model_path: str = Field(default="", env="MODEL_PATH")
    model_name: str = Field(default="gpt-4o", env="MODEL_NAME")
    summary_model_name: str = Field(default="gpt-4o-mini", env="SUMMARY_MODEL_NAME")
    
    # ==========================================================================
    # Agent Configuration
    # ==========================================================================
    max_llm_call_per_run: int = Field(default=100, env="MAX_LLM_CALL_PER_RUN")
    max_context_tokens: int = Field(default=110000, env="MAX_CONTEXT_TOKENS")
    temperature: float = Field(default=0.6, env="TEMPERATURE")
    top_p: float = Field(default=0.95, env="TOP_P")
    presence_penalty: float = Field(default=1.1, env="PRESENCE_PENALTY")
    
    # ==========================================================================
    # Tool Configuration
    # ==========================================================================
    sandbox_fusion_endpoints: str = Field(default="", env="SANDBOX_FUSION_ENDPOINT")
    visit_server_timeout: int = Field(default=200, env="VISIT_SERVER_TIMEOUT")
    webcontent_maxlength: int = Field(default=150000, env="WEBCONTENT_MAXLENGTH")
    allow_local_python: bool = Field(default=True, env="ALLOW_LOCAL_PYTHON")
    
    # ==========================================================================
    # Server Configuration
    # ==========================================================================
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # Cache Expiry (seconds)
    cache_expiry_search: int = Field(default=86400, env="CACHE_EXPIRY_SEARCH")  # 1 day
    cache_expiry_visit: int = Field(default=604800, env="CACHE_EXPIRY_VISIT")   # 7 days
    
    # Multimodal Model
    multimodal_model_name: str = Field(default="gpt-4o", env="MULTIMODAL_MODEL_NAME")
    
    # ==========================================================================
    # Logging
    # ==========================================================================
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_dir: str = Field(default="./logs", env="LOG_DIR")
    
    @property
    def sandbox_endpoints_list(self) -> List[str]:
        """解析沙箱端点列表"""
        if not self.sandbox_fusion_endpoints:
            return []
        return [ep.strip() for ep in self.sandbox_fusion_endpoints.split(",") if ep.strip()]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


# 便捷访问
settings = get_settings()
