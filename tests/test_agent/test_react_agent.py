"""Agent 测试"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.agent import xSmartReactAgent, ResearchResult
from src.tools import BaseTool


class MockTool(BaseTool):
    """模拟工具"""
    name = "mock_tool"
    description = "A mock tool for testing"
    parameters = {
        "type": "object",
        "properties": {
            "input": {"type": "string"}
        },
        "required": ["input"]
    }
    
    def call(self, params, **kwargs):
        return f"Mock response for: {params}"


class TestXSmartReactAgent:
    """xSmartReactAgent 测试类"""
    
    def test_init_default(self):
        """测试默认初始化"""
        agent = xSmartReactAgent()
        
        assert agent.max_iterations > 0
        assert agent.max_tokens > 0
        assert isinstance(agent.tools, dict)
    
    def test_register_tool(self):
        """测试工具注册"""
        agent = xSmartReactAgent()
        tool = MockTool()
        
        agent.register_tool(tool)
        
        assert "mock_tool" in agent.tools
        assert agent.tools["mock_tool"] == tool
    
    def test_has_answer(self):
        """测试答案检测"""
        agent = xSmartReactAgent()
        
        content_with_answer = "Some text <answer>This is the answer</answer>"
        content_without_answer = "Some text without answer tag"
        
        assert agent._has_answer(content_with_answer) == True
        assert agent._has_answer(content_without_answer) == False
    
    def test_has_tool_call(self):
        """测试工具调用检测"""
        agent = xSmartReactAgent()
        
        content_with_call = '<tool_call>{"name": "search"}</tool_call>'
        content_without_call = "No tool call here"
        
        assert agent._has_tool_call(content_with_call) == True
        assert agent._has_tool_call(content_without_call) == False
    
    def test_extract_answer(self):
        """测试答案提取"""
        agent = xSmartReactAgent()
        
        content = "Some text <answer>The extracted answer</answer> more text"
        answer = agent._extract_answer(content)
        
        assert answer == "The extracted answer"


class TestResearchResult:
    """ResearchResult 测试类"""
    
    def test_result_creation(self):
        """测试结果创建"""
        result = ResearchResult(
            question="Test question",
            answer="Expected answer",
            prediction="Predicted answer",
            messages=[],
            termination="answer"
        )
        
        assert result.question == "Test question"
        assert result.prediction == "Predicted answer"
        assert result.termination == "answer"
    
    def test_result_dict(self):
        """测试结果转字典"""
        result = ResearchResult(
            question="Test",
            answer="",
            prediction="Result",
            messages=[{"role": "user", "content": "hi"}],
            termination="answer",
            execution_time=10.5,
            iterations=5
        )
        
        data = result.dict()
        
        assert data["question"] == "Test"
        assert data["execution_time"] == 10.5
        assert data["iterations"] == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
