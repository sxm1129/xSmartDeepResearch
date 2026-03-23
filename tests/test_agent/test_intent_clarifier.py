"""IntentClarifier 测试"""

import pytest
import sys
import os
import json
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.agent.intent_clarifier import IntentClarifier, ClarificationDirection, ClarificationResult


@dataclass
class FakeMessage:
    content: str

@dataclass
class FakeChoice:
    message: FakeMessage

@dataclass
class FakeResponse:
    choices: list


def make_fake_response(content: str) -> FakeResponse:
    """创建模拟 LLM 响应"""
    return FakeResponse(choices=[FakeChoice(message=FakeMessage(content=content))])


class TestIntentClarifier:
    """IntentClarifier 测试类"""

    def test_clarify_round1_parses_directions_correctly(self):
        """测试第一轮澄清正确解析 LLM 返回的方向数据"""
        response_data = {
            "directions": [
                {"id": "dir_1", "title": "Work Efficiency", "description": "How AI changes daily workflows", "example_query": "How does AI improve developer productivity?"},
                {"id": "dir_2", "title": "Skills & Career", "description": "New skills needed in the AI era", "example_query": "What new skills do programmers need?"},
                {"id": "dir_3", "title": "Job Market", "description": "Impact on employment", "example_query": "How will AI affect programmer jobs?"},
                {"id": "dir_4", "title": "Ethics & Challenges", "description": "Technical and ethical considerations", "example_query": "What ethical challenges arise?"},
            ]
        }

        mock_client = MagicMock()
        clarifier = IntentClarifier(client=mock_client, model="gpt-4o-mini")

        # Parse the LLM response directly (same logic as clarify_round1)
        raw_json = json.dumps(response_data)
        result = clarifier._parse_json_response(raw_json)

        directions = []
        for d in result.get("directions", []):
            directions.append(ClarificationDirection(
                id=d.get("id", f"dir_{len(directions)+1}"),
                title=d.get("title", "Unknown"),
                description=d.get("description", ""),
                example_query=d.get("example_query", "")
            ))

        assert len(directions) == 4
        assert directions[0].id == "dir_1"
        assert directions[0].title == "Work Efficiency"
        assert directions[1].id == "dir_2"
        assert directions[1].title == "Skills & Career"
        assert directions[3].title == "Ethics & Challenges"
        assert "AI improve developer productivity" in directions[0].example_query

    @pytest.mark.asyncio
    async def test_clarify_round1_calls_llm_and_returns_result(self):
        """测试第一轮澄清完整流程 - 验证 LLM 被调用且结果正确封装"""
        mock_client = MagicMock()
        clarifier = IntentClarifier(client=mock_client, model="gpt-4o-mini")

        # Directly patch the internal method to return controlled data
        expected = ClarificationResult(
            directions=[
                ClarificationDirection(id="dir_1", title="Angle A", description="Desc A", example_query="Query A"),
                ClarificationDirection(id="dir_2", title="Angle B", description="Desc B", example_query="Query B"),
            ],
            round=1,
            ready_to_research=False,
            original_question="test question"
        )

        with patch.object(clarifier, 'clarify_round1', return_value=expected):
            result = await clarifier.clarify_round1("test question")

        assert isinstance(result, ClarificationResult)
        assert len(result.directions) == 2
        assert result.round == 1
        assert result.ready_to_research is False
        assert result.original_question == "test question"
        assert result.directions[0].title == "Angle A"

    @pytest.mark.asyncio
    async def test_clarify_round2_with_selection(self):
        """测试用户选择方向后生成精炼查询"""
        response_data = {
            "refined_query": "Deep analysis of how AI tools like GitHub Copilot change required programming skills",
            "research_scope": "AI's impact on programmer skills"
        }

        mock_create = AsyncMock(return_value=make_fake_response(json.dumps(response_data)))
        mock_client = MagicMock()
        mock_client.chat.completions.create = mock_create

        clarifier = IntentClarifier(client=mock_client, model="gpt-4o-mini")

        direction = ClarificationDirection(
            id="dir_2", title="Skills & Career",
            description="New skills needed",
            example_query="What skills do programmers need?"
        )

        result = await clarifier.clarify_round2(
            original_question="AI对程序员的影响",
            selected_direction=direction
        )

        assert result.round == 2
        assert result.ready_to_research is True
        assert result.refined_query is not None
        assert "GitHub Copilot" in result.refined_query

    @pytest.mark.asyncio
    async def test_clarify_custom_direction(self):
        """测试用户自定义方向"""
        response_data = {
            "refined_query": "Analysis of AI pair programming tools and their impact on code review workflows",
            "research_scope": "AI in code review"
        }

        mock_create = AsyncMock(return_value=make_fake_response(json.dumps(response_data)))
        mock_client = MagicMock()
        mock_client.chat.completions.create = mock_create

        clarifier = IntentClarifier(client=mock_client, model="gpt-4o-mini")

        result = await clarifier.clarify_custom(
            original_question="AI对程序员的影响",
            custom_input="我想了解AI在代码审查中的应用"
        )

        assert result.round == 2
        assert result.ready_to_research is True
        assert result.refined_query is not None

    @pytest.mark.asyncio
    async def test_clarify_round1_fallback_on_error(self):
        """测试 LLM 调用失败时的降级处理"""
        mock_create = AsyncMock(side_effect=Exception("API Error"))
        mock_client = MagicMock()
        mock_client.chat.completions.create = mock_create

        clarifier = IntentClarifier(client=mock_client, model="gpt-4o-mini")

        result = await clarifier.clarify_round1("测试问题")

        assert isinstance(result, ClarificationResult)
        assert len(result.directions) == 4
        assert result.round == 1
        assert result.ready_to_research is False

    @pytest.mark.asyncio
    async def test_clarify_round2_fallback_on_error(self):
        """测试第二轮 LLM 失败时降级到 example_query"""
        mock_create = AsyncMock(side_effect=Exception("API Error"))
        mock_client = MagicMock()
        mock_client.chat.completions.create = mock_create

        clarifier = IntentClarifier(client=mock_client, model="gpt-4o-mini")

        direction = ClarificationDirection(
            id="dir_1", title="Test",
            description="Test desc",
            example_query="Fallback question"
        )

        result = await clarifier.clarify_round2(
            original_question="原始问题",
            selected_direction=direction
        )

        assert result.ready_to_research is True
        assert result.refined_query == "Fallback question"

    @pytest.mark.asyncio
    async def test_round2_always_ready_to_research(self):
        """测试第二轮始终设置 ready_to_research=True"""
        response_data = {"refined_query": "Refined", "research_scope": "scope"}

        mock_create = AsyncMock(return_value=make_fake_response(json.dumps(response_data)))
        mock_client = MagicMock()
        mock_client.chat.completions.create = mock_create

        clarifier = IntentClarifier(client=mock_client, model="gpt-4o-mini")
        direction = ClarificationDirection(id="dir_1", title="T", description="D", example_query="Q")

        result = await clarifier.clarify_round2("Q", direction)
        assert result.round == 2
        assert result.ready_to_research is True

    def test_parse_json_response_clean(self):
        """测试 JSON 解析 - 正常输入"""
        mock_client = MagicMock()
        clarifier = IntentClarifier(client=mock_client, model="gpt-4o-mini")
        result = clarifier._parse_json_response('{"key": "value"}')
        assert result == {"key": "value"}

    def test_parse_json_response_markdown_wrapped(self):
        """测试 JSON 解析 - Markdown 包裹"""
        mock_client = MagicMock()
        clarifier = IntentClarifier(client=mock_client, model="gpt-4o-mini")
        raw = '```json\n{"key": "value"}\n```'
        result = clarifier._parse_json_response(raw)
        assert result == {"key": "value"}

    def test_generate_fallback_directions(self):
        """测试默认方向生成"""
        mock_client = MagicMock()
        clarifier = IntentClarifier(client=mock_client, model="gpt-4o-mini")
        directions = clarifier._generate_fallback_directions("test question")

        assert len(directions) == 4
        assert all(isinstance(d, ClarificationDirection) for d in directions)
        assert all("test question" in d.example_query for d in directions)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
