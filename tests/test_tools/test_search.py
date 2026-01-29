"""搜索工具测试"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.tools import SearchTool


class TestSearchTool:
    """SearchTool 测试类"""
    
    def test_init(self):
        """测试初始化"""
        tool = SearchTool(api_key="test_key")
        assert tool.name == "search"
        assert tool.api_key == "test_key"
    
    def test_contains_chinese(self):
        """测试中文检测"""
        tool = SearchTool()
        
        assert tool._contains_chinese("你好世界") == True
        assert tool._contains_chinese("Hello World") == False
        assert tool._contains_chinese("Hello 你好") == True
    
    def test_parse_params_dict(self):
        """测试字典参数解析"""
        tool = SearchTool()
        
        params = {"query": ["test query"]}
        result = tool._parse_params(params)
        
        assert result == params
    
    def test_parse_params_string(self):
        """测试字符串参数解析"""
        tool = SearchTool()
        
        params = '{"query": ["test query"]}'
        result = tool._parse_params(params)
        
        assert result == {"query": ["test query"]}
    
    def test_function_definition(self):
        """测试函数定义生成"""
        tool = SearchTool()
        
        definition = tool.get_function_definition()
        
        assert definition["type"] == "function"
        assert definition["function"]["name"] == "search"
        assert "query" in definition["function"]["parameters"]["properties"]


class TestScholarTool:
    """ScholarTool 测试类"""
    
    def test_init(self):
        """测试初始化"""
        from src.tools import ScholarTool
        
        tool = ScholarTool(api_key="test_key")
        assert tool.name == "google_scholar"
        assert tool.api_key == "test_key"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
