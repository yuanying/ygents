"""Test configuration and fixtures for MCP tests."""

import pytest
from fastmcp import Client, FastMCP


@pytest.fixture
def mock_fastmcp_servers():
    """複数のFastMCPサーバーを作成"""
    weather_server = FastMCP(name="WeatherServer")
    assistant_server = FastMCP(name="AssistantServer")
    
    @weather_server.tool()
    def get_forecast(city: str) -> str:
        return f"Weather in {city}: Sunny"
    
    @assistant_server.tool()
    def answer_question(question: str) -> str:
        return f"Answer: {question}"
    
    return {
        "weather": weather_server,
        "assistant": assistant_server
    }


@pytest.fixture
def mcp_server_configs():
    """テスト用サーバー設定（生辞書形式）"""
    return {
        "weather": {"url": "https://test-weather.com/mcp"},
        "assistant": {"command": "python", "args": ["assistant.py"]}
    }


@pytest.fixture
async def fastmcp_multi_client(mock_fastmcp_servers):
    """FastMCPのMulti-Server Clientを直接使用"""
    config = {
        "mcpServers": {
            "weather": mock_fastmcp_servers["weather"],
            "assistant": mock_fastmcp_servers["assistant"]
        }
    }
    
    client = Client(config)
    async with client:
        yield client