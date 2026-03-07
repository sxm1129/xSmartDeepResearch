"""高级研究 API 端点测试"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def get_test_client():
    """创建测试客户端（兼容不同 httpx/starlette 版本）"""
    from fastapi.testclient import TestClient
    from src.api.main import app
    return TestClient(app)


class TestAdvancedResearchEndpoints:
    """高级研究端点测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        try:
            return get_test_client()
        except TypeError:
            pytest.skip("TestClient incompatible with current httpx version")

    def test_clarify_endpoint_validation_empty_question(self, client):
        """测试请求验证 - 空问题应失败"""
        response = client.post(
            "/api/v1/advanced-research/clarify",
            json={"question": "", "round": 1}
        )
        assert response.status_code == 422

    def test_clarify_endpoint_validation_invalid_round(self, client):
        """测试请求验证 - 无效轮次"""
        response = client.post(
            "/api/v1/advanced-research/clarify",
            json={"question": "test", "round": 5}
        )
        assert response.status_code == 422

    def test_clarify_endpoint_exists(self, client):
        """测试澄清端点存在"""
        response = client.post(
            "/api/v1/advanced-research/clarify",
            json={"question": "test question", "round": 1}
        )
        assert response.status_code != 404
        assert response.status_code != 405

    def test_stream_endpoint_exists(self, client):
        """测试流式端点存在"""
        response = client.post(
            "/api/v1/advanced-research/stream",
            json={
                "refined_query": "test query",
                "original_question": "test"
            }
        )
        assert response.status_code != 404
        assert response.status_code != 405

    def test_stream_endpoint_validation(self, client):
        """测试流式端点请求验证 - 空查询应失败"""
        response = client.post(
            "/api/v1/advanced-research/stream",
            json={
                "refined_query": "",
                "original_question": ""
            }
        )
        assert response.status_code == 422

    def test_existing_research_endpoints_unaffected(self, client):
        """回归测试 - 确保现有研究端点不受影响"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

        response = client.get("/")
        assert response.status_code == 200

        response = client.post("/api/v1/research", json={"question": ""})
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
