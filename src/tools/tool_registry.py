"""工具注册中心"""

from typing import Dict, List, Optional, Type, Any
from .base_tool import BaseTool


class ToolRegistry:
    """工具注册中心
    
    管理所有可用工具的注册和获取
    """
    
    _instance: Optional['ToolRegistry'] = None
    _tools: Dict[str, BaseTool] = {}
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._tools = {}
        return cls._instance
    
    @classmethod
    def register(cls, tool: BaseTool) -> None:
        """注册工具
        
        Args:
            tool: 工具实例
        """
        instance = cls()
        instance._tools[tool.name] = tool
    
    @classmethod
    def register_class(cls, tool_class: Type[BaseTool], **kwargs) -> None:
        """注册工具类
        
        Args:
            tool_class: 工具类
            **kwargs: 传递给工具构造函数的参数
        """
        tool = tool_class(**kwargs)
        cls.register(tool)
    
    @classmethod
    def get(cls, name: str) -> Optional[BaseTool]:
        """获取工具
        
        Args:
            name: 工具名称
            
        Returns:
            工具实例，如果不存在返回None
        """
        instance = cls()
        return instance._tools.get(name)
    
    @classmethod
    def get_all(cls) -> Dict[str, BaseTool]:
        """获取所有已注册的工具
        
        Returns:
            工具名称到实例的映射
        """
        instance = cls()
        return instance._tools.copy()
    
    @classmethod
    def get_tools(cls, names: List[str] = None) -> List[BaseTool]:
        """获取指定名称的工具列表
        
        Args:
            names: 工具名称列表，None表示获取全部
            
        Returns:
            工具实例列表
        """
        instance = cls()
        if names is None:
            return list(instance._tools.values())
        return [instance._tools[name] for name in names if name in instance._tools]
    
    @classmethod
    def get_function_definitions(cls, names: List[str] = None) -> List[Dict[str, Any]]:
        """获取工具的函数定义
        
        Args:
            names: 工具名称列表，None表示获取全部
            
        Returns:
            OpenAI格式的函数定义列表
        """
        tools = cls.get_tools(names)
        return [tool.get_function_definition() for tool in tools]
    
    @classmethod
    def unregister(cls, name: str) -> bool:
        """注销工具
        
        Args:
            name: 工具名称
            
        Returns:
            是否成功注销
        """
        instance = cls()
        if name in instance._tools:
            del instance._tools[name]
            return True
        return False
    
    @classmethod
    def clear(cls) -> None:
        """清空所有注册的工具"""
        instance = cls()
        instance._tools.clear()
    
    @classmethod
    def list_names(cls) -> List[str]:
        """获取所有已注册工具的名称
        
        Returns:
            工具名称列表
        """
        instance = cls()
        return list(instance._tools.keys())


def register_tool(name: str = None):
    """工具注册装饰器
    
    Args:
        name: 工具名称，默认使用类的name属性
        
    Returns:
        装饰器函数
        
    使用示例:
        @register_tool()
        class MyTool(BaseTool):
            name = "my_tool"
            ...
    """
    def decorator(cls: Type[BaseTool]):
        tool = cls()
        if name:
            tool.name = name
        ToolRegistry.register(tool)
        return cls
    return decorator
