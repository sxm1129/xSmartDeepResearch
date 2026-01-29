"""工具基类定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel


class BaseTool(ABC):
    """工具基类
    
    所有工具都需要继承此类并实现 call 方法
    """
    
    # 工具名称
    name: str = ""
    
    # 工具描述
    description: str = ""
    
    # 参数定义 (JSON Schema格式)
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {},
        "required": []
    }
    
    def __init__(self, cfg: Optional[Dict] = None):
        """初始化工具
        
        Args:
            cfg: 配置字典
        """
        self.cfg = cfg or {}
    
    @abstractmethod
    def call(self, params: Union[str, Dict[str, Any]], **kwargs) -> str:
        """执行工具调用
        
        Args:
            params: 工具参数
            **kwargs: 额外参数
            
        Returns:
            工具执行结果字符串
        """
        pass
    
    async def acall(self, params: Union[str, Dict[str, Any]], **kwargs) -> str:
        """异步执行工具调用
        
        默认实现调用同步方法，子类可以重写此方法实现真正的异步调用
        
        Args:
            params: 工具参数
            **kwargs: 额外参数
            
        Returns:
            工具执行结果字符串
        """
        return self.call(params, **kwargs)
    
    def get_function_definition(self) -> Dict[str, Any]:
        """获取OpenAI格式的函数定义
        
        Returns:
            符合OpenAI function calling格式的工具定义
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }
    
    def _parse_params(self, params: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """解析参数
        
        Args:
            params: 字符串或字典形式的参数
            
        Returns:
            解析后的字典参数
        """
        if isinstance(params, str):
            import json
            try:
                return json.loads(params)
            except json.JSONDecodeError:
                import json5
                try:
                    return json5.loads(params)
                except:
                    return {"raw": params}
        return params
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}')>"
