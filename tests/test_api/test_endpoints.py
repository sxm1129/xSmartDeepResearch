"""API 测试"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """健康检查端点测试"""
    
    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from src.api.main import app
        return TestClient(app)
    
    def test_health_check(self, client):
        """测试健康检查"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "model" in data
    
    def test_root(self, client):
        """测试根路径"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "docs" in data


class TestResearchEndpoint:
    """研究端点测试"""
    
    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from src.api.main import app
        return TestClient(app)
    
    def test_research_request_validation(self, client):
        """测试请求验证"""
        # 空问题应该失败
        response = client.post(
            "/api/v1/research",
            json={"question": ""}
        )
        
        assert response.status_code == 422  # Validation error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
