"""Agent test fixtures."""

from unittest.mock import MagicMock, patch

import pytest

from ygents.config.models import LLMConfig, OpenAIConfig, YgentsConfig


@pytest.fixture
def mock_agent_config():
    """Test agent configuration."""
    return YgentsConfig(
        llm=LLMConfig(
            provider="openai", openai=OpenAIConfig(api_key="test-key", model="gpt-4")
        ),
        mcp_servers={},
    )


@pytest.fixture
def mock_agent_config_with_mcp():
    """Test agent configuration with MCP servers."""
    return YgentsConfig(
        llm=LLMConfig(
            provider="openai", openai=OpenAIConfig(api_key="test-key", model="gpt-4")
        ),
        mcp_servers={"test_server": {}},
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
            return MagicMock(
                choices=[
                    MagicMock(message=MagicMock(content="Hello world! 完了しました。"))
                ]
            )

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
            return MagicMock(
                choices=[
                    MagicMock(
                        message=MagicMock(content="天気を確認します。完了しました。")
                    )
                ]
            )

    with patch("litellm.completion", side_effect=mock_completion):
        yield


@pytest.fixture
def mock_litellm_streaming_tool_calls():
    """Mock LiteLLM streaming response with fragmented tool calls."""

    class MockToolCallFunction:
        def __init__(self, name=None, arguments=None):
            self.name = name
            self.arguments = arguments

    class MockToolCall:
        def __init__(self, id=None, function=None):
            self.id = id
            self.function = function

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
                # First chunk: start tool call with ID and function name
                yield MockChunk(
                    tool_calls=[
                        MockToolCall(
                            id="tool_call_1",
                            function=MockToolCallFunction(
                                name="get_weather", arguments=""
                            ),
                        )
                    ]
                )

                # Second chunk: partial arguments
                yield MockChunk(
                    tool_calls=[
                        MockToolCall(
                            id="tool_call_1",
                            function=MockToolCallFunction(
                                name=None, arguments='{"city": '
                            ),
                        )
                    ]
                )

                # Third chunk: remaining arguments
                yield MockChunk(
                    tool_calls=[
                        MockToolCall(
                            id="tool_call_1",
                            function=MockToolCallFunction(
                                name=None, arguments='"Tokyo"}'
                            ),
                        )
                    ]
                )

                # Final chunk: content response
                yield MockChunk("天気情報を取得しました。完了しました。")

            return chunk_generator()
        else:
            return MagicMock(
                choices=[
                    MagicMock(
                        message=MagicMock(
                            content="天気情報を取得しました。完了しました。",
                            tool_calls=[
                                {
                                    "id": "tool_call_1",
                                    "function": {
                                        "name": "get_weather",
                                        "arguments": '{"city": "Tokyo"}',
                                    },
                                }
                            ],
                        )
                    )
                ]
            )

    with patch("litellm.completion", side_effect=mock_completion):
        yield
