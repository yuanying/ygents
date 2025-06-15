"""Agent test fixtures."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from ygents.config.models import YgentsConfig, LLMConfig, OpenAIConfig, ClaudeConfig


@pytest.fixture
def mock_agent_config():
    """Test agent configuration."""
    return YgentsConfig(
        llm=LLMConfig(
            provider="openai",
            openai=OpenAIConfig(api_key="test-key", model="gpt-4")
        ),
        mcp_servers={}
    )


@pytest.fixture
def mock_agent_config_with_mcp():
    """Test agent configuration with MCP servers."""
    return YgentsConfig(
        llm=LLMConfig(
            provider="openai",
            openai=OpenAIConfig(api_key="test-key", model="gpt-4")
        ),
        mcp_servers={
            "test_server": {}
        }
    )


@pytest.fixture
def mock_litellm_streaming():
    """Mock LiteLLM streaming response."""
    class MockChoice:
        def __init__(self, content=None, tool_calls=None):
            self.delta = MagicMock()
            self.delta.content = content
            self.delta.tool_calls = tool_calls

    class MockChunk:
        def __init__(self, content=None, tool_calls=None):
            self.choices = [MockChoice(content, tool_calls)]

    def mock_completion(*args, **kwargs):
        if kwargs.get("stream", False):
            # ストリーミングの場合、generator を返す
            def chunk_generator():
                yield MockChunk("Hello")
                yield MockChunk(" world")
                yield MockChunk("! 完了しました。")  # 問題解決キーワード
            return chunk_generator()
        else:
            # 非ストリーミングの場合
            return MagicMock(choices=[MagicMock(message=MagicMock(content="Hello world! 完了しました。"))])
    
    with patch("litellm.completion", side_effect=mock_completion):
        yield


@pytest.fixture
def mock_litellm_with_tools():
    """Mock LiteLLM response with tool calls."""
    class MockChoice:
        def __init__(self, content=None, tool_calls=None):
            self.delta = MagicMock()
            self.delta.content = content
            self.delta.tool_calls = tool_calls

    class MockChunk:
        def __init__(self, content=None, tool_calls=None):
            self.choices = [MockChoice(content, tool_calls)]

    def mock_completion(*args, **kwargs):
        if kwargs.get("stream", False):
            def chunk_generator():
                yield MockChunk("天気を確認します")
                yield MockChunk("。完了しました。")
            return chunk_generator()
        else:
            return MagicMock(choices=[MagicMock(message=MagicMock(content="天気を確認します。完了しました。"))])
    
    with patch("litellm.completion", side_effect=mock_completion):
        yield