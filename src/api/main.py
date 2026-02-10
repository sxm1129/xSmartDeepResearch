"""xSmartDeepResearch FastAPI 主应用"""

import sys
import os
from datetime import datetime
from contextlib import asynccontextmanager

# 添加项目根目录
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from src.api.schemas import HealthCheck
from src.api.routes import research_router, settings_router, health_router
from src.api.dependencies import get_available_tools


# 应用生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    print("🚀 xSmartDeepResearch API starting...")
    
    # Load settings from DB
    from src.api.dependencies import get_session_manager
    try:
        session_manager = get_session_manager()
        db_settings = session_manager.get_all_settings()
        
        if db_settings:
            print("📦 Loading settings from database...")
            # Map DB keys to settings attributes
            for key, value in db_settings.items():
                if hasattr(settings, key):
                    # Convert types if necessary (simple logic for now)
                    current_val = getattr(settings, key)
                    if isinstance(current_val, int):
                        try:
                            setattr(settings, key, int(value))
                        except: pass
                    elif isinstance(current_val, float):
                        try:
                            setattr(settings, key, float(value))
                        except: pass
                    elif isinstance(current_val, bool):
                        setattr(settings, key, value.lower() == 'true')
                    else:
                        setattr(settings, key, value)
            print("✅ Settings loaded from DB")
    except Exception as e:
        print(f"⚠️ Failed to load settings from DB: {e}")

    print(f"   Model: {settings.model_name}")
    print(f"   Tools: {get_available_tools()}")
    
    yield
    
    # 关闭时
    print("👋 xSmartDeepResearch API shutting down...")


# 创建应用
app = FastAPI(
    title="xSmartDeepResearch API",
    description="""
## 🔬 智能深度研究系统 API

基于 ReAct Agent 的多轮信息检索与推理系统。

### 功能特性
- **深度研究**：自动搜索、阅读和推理
- **多工具支持**：搜索、网页阅读、代码执行、学术搜索
- **异步任务**：支持长时间研究任务的异步执行

### 使用方式
1. 同步研究：`POST /api/v1/research`
2. 异步研究：`POST /api/v1/research/async`
3. 查询结果：`GET /api/v1/research/{task_id}`
    """,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": str(exc),
            "path": str(request.url)
        }
    )


# 健康检查 (简单版本,保留兼容性)
@app.get("/health", response_model=HealthCheck, tags=["System"])
async def simple_health_check():
    """
    简单健康检查端点 (保留兼容性)
    
    返回服务基本状态和配置信息。
    如需详细的组件健康检查,请使用 GET /api/health
    """
    return HealthCheck(
        status="healthy",
        version="0.1.0",
        model=settings.model_name,
        tools_available=get_available_tools(),
        timestamp=datetime.now()
    )


@app.get("/", tags=["System"])
async def root():
    """
    根路径
    
    返回API欢迎信息。
    """
    return {
        "message": "Welcome to xSmartDeepResearch API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "health_detail": "/api/health"
    }


# 注册路由
app.include_router(health_router, prefix="/api")
app.include_router(research_router, prefix="/api/v1")
app.include_router(settings_router, prefix="/api/v1")


# 直接运行
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
