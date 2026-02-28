"""研究请求/响应模型"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

# Import ComponentHealth from utils to avoid circular dependency
# It's defined as a dataclass in src.utils.health


class ResearchStatus(str, Enum):
    """研究任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class ResearchRequest(BaseModel):
    """研究请求"""
    question: str = Field(..., description="用户的研究问题", min_length=1)
    max_iterations: Optional[int] = Field(default=None, ge=1, le=100, description="最大迭代次数")
    tools: Optional[List[str]] = Field(default=None, description="启用的工具列表，None表示全部")
    stream: bool = Field(default=False, description="是否启用流式输出")
    callback_url: Optional[str] = Field(default=None, description="Webhook回调URL，每个进度事件会POST到此地址")
    callback_events: Optional[List[str]] = Field(
        default=None,
        description="需要回调的事件类型，None表示全部。可选: status/think/tool_start/tool_response/answer/final_answer/error"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "2024年诺贝尔物理学奖得主是谁？",
                "max_iterations": 50,
                "tools": None,
                "stream": False,
                "callback_url": "http://my-service:9000/webhook/research",
                "callback_events": ["status", "think", "answer", "final_answer", "error"]
            }
        }


class ResearchResponse(BaseModel):
    """研究响应"""
    task_id: str = Field(..., description="任务ID")
    question: str = Field(..., description="原始问题")
    answer: str = Field(..., description="研究答案")
    status: ResearchStatus = Field(..., description="任务状态")
    iterations: int = Field(default=0, description="实际迭代次数")
    execution_time: float = Field(default=0.0, description="执行时间(秒)")
    termination_reason: str = Field(default="", description="终止原因")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    is_bookmarked: bool = Field(default=False, description="是否收藏")
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "abc123",
                "question": "2024年诺贝尔物理学奖得主是谁？",
                "answer": "2024年诺贝尔物理学奖授予了...",
                "status": "completed",
                "iterations": 15,
                "execution_time": 45.2,
                "termination_reason": "answer",
                "created_at": "2024-01-28T10:00:00",
                "is_bookmarked": False
            }
        }


class BatchResearchRequest(BaseModel):
    """批量研究请求"""
    questions: List[str] = Field(..., description="研究问题列表", min_items=1)
    max_iterations: int = Field(default=50, ge=1, le=100)
    
    class Config:
        json_schema_extra = {
            "example": {
                "questions": ["问题1", "问题2"],
                "max_iterations": 50
            }
        }


class BatchResearchResponse(BaseModel):
    """批量研究响应"""
    batch_id: str
    task_ids: List[str]
    status: str = "accepted"


class TaskStatus(BaseModel):
    """任务状态查询响应"""
    task_id: str
    status: ResearchStatus
    progress: Optional[int] = Field(default=None, description="进度百分比")
    current_iteration: int = Field(default=0)
    message: str = Field(default="")


class ComponentHealth(BaseModel):
    """单个组件健康状态"""
    result: str = Field(..., description="succeed 或 fail")
    message: Optional[str] = Field(None, description="额外信息或错误描述")
    details: Optional[Dict[str, Any]] = Field(None, description="详细数据")


class HealthCheckDetail(BaseModel):
    """功能健康监控详细响应"""
    result: str = Field(..., description="总体状态: succeed 或 fail")
    timestamp: str = Field(..., description="检查时间 ISO 8601 格式")
    details: Dict[str, ComponentHealth] = Field(..., description="各组件健康状态")
    
    class Config:
        json_schema_extra = {
            "example": {
                "result": "succeed",
                "timestamp": "2026-02-10T16:05:00Z",
                "details": {
                    "database": {
                        "result": "succeed",
                        "message": "MySQL connection OK"
                    },
                    "disk": {
                        "result": "succeed",
                        "details": {"free_gb": "45GB", "usage_percent": "65%"}
                    }
                }
            }
        }


class HealthCheck(BaseModel):
    """简单健康检查响应 (保留兼容性)"""
    status: str = "healthy"
    version: str = "1.0.11"
    model: str
    tools_available: List[str]
    timestamp: datetime = Field(default_factory=datetime.now)

