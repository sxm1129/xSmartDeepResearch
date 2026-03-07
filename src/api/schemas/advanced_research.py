"""高级研究（意图澄清）请求/响应模型 - 完全独立于现有 research.py"""

from typing import List, Optional
from pydantic import BaseModel, Field


class ClarificationDirectionSchema(BaseModel):
    """单个澄清方向"""
    id: str = Field(..., description="方向唯一标识")
    title: str = Field(..., description="方向标题")
    description: str = Field(..., description="方向描述")
    example_query: str = Field(..., description="该方向下的示例研究查询")


class ClarifyRequest(BaseModel):
    """意图澄清请求"""
    question: str = Field(..., description="用户的研究问题", min_length=1)
    selected_direction_id: Optional[str] = Field(
        default=None, 
        description="用户选择的方向 ID (第二轮澄清时必填)"
    )
    selected_direction: Optional[ClarificationDirectionSchema] = Field(
        default=None,
        description="用户选择的完整方向 (第二轮澄清时必填)"
    )
    custom_input: Optional[str] = Field(
        default=None,
        description="用户自定义的研究方向描述 (当用户选择'其他'时)"
    )
    round: int = Field(default=1, ge=1, le=2, description="当前澄清轮次")
    user_context: Optional[str] = Field(
        default=None,
        description="用户额外补充的上下文信息"
    )
    language: str = Field(default="en", description="输出语言 ('zh' 或 'en')")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "summary": "Round 1 - Initial clarification",
                    "value": {
                        "question": "AI对程序员的影响",
                        "round": 1
                    }
                },
                {
                    "summary": "Round 2 - Direction selected",
                    "value": {
                        "question": "AI对程序员的影响",
                        "round": 2,
                        "selected_direction_id": "dir_2",
                        "selected_direction": {
                            "id": "dir_2",
                            "title": "技能要求和职业发展",
                            "description": "AI工具的出现对程序员需要掌握的技能组合有何变化",
                            "example_query": "AI工具如何改变程序员的技能要求和职业发展路径"
                        }
                    }
                }
            ]
        }


class ClarifyResponse(BaseModel):
    """意图澄清响应"""
    directions: List[ClarificationDirectionSchema] = Field(
        default_factory=list,
        description="研究方向列表 (第一轮时有值)"
    )
    round: int = Field(..., description="当前完成的澄清轮次")
    ready_to_research: bool = Field(
        ..., 
        description="是否已准备好开始深度研究"
    )
    refined_query: Optional[str] = Field(
        default=None,
        description="精炼后的研究查询 (ready_to_research=True 时有值)"
    )
    original_question: str = Field(..., description="用户原始问题")

    class Config:
        json_schema_extra = {
            "example": {
                "directions": [
                    {
                        "id": "dir_1",
                        "title": "工作方式和效率",
                        "description": "AI如何改变程序员的日常工作流程、提升开发效率",
                        "example_query": "AI工具如何改变程序员的工作方式和开发效率"
                    }
                ],
                "round": 1,
                "ready_to_research": False,
                "refined_query": None,
                "original_question": "AI对程序员的影响"
            }
        }


class AdvancedResearchRequest(BaseModel):
    """高级研究请求 (澄清完成后)"""
    refined_query: str = Field(
        ..., 
        description="经过澄清精炼的研究查询",
        min_length=1
    )
    original_question: str = Field(
        ..., 
        description="用户原始问题",
        min_length=1
    )
    max_iterations: Optional[int] = Field(
        default=None, ge=1, le=100, 
        description="最大迭代次数"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "refined_query": "分析AI工具(如GitHub Copilot, ChatGPT)对程序员技能要求的影响...",
                "original_question": "AI对程序员的影响",
                "max_iterations": 50
            }
        }
