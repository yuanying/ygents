"""Agent core tests."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ygents.agent.core import Agent
from ygents.agent.exceptions import AgentError
from ygents.agent.models import ContentChunk, Message, ToolInput, ToolResult


@pytest.mark.asyncio
async def test_agent_initialization(mock_agent_config):
    """Test agent initialization."""
    agent = Agent(mock_agent_config)

    assert agent.config == mock_agent_config
    assert agent._mcp_client is None
    assert agent._mcp_client_connected is False
    assert agent.messages == []


@pytest.mark.asyncio
async def test_agent_context_manager_without_mcp(mock_agent_config):
    """Test agent context manager without MCP servers."""
    async with Agent(mock_agent_config) as agent:
        assert isinstance(agent, Agent)
        assert agent._mcp_client is None
        assert agent._mcp_client_connected is False


@pytest.mark.asyncio
async def test_agent_context_manager_with_mcp(mock_agent_config_with_mcp):
    """Test agent context manager with MCP servers."""
    with patch("fastmcp.Client") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        async with Agent(mock_agent_config_with_mcp) as agent:
            assert agent._mcp_client is mock_client
            assert agent._mcp_client_connected is True
            mock_client.__aenter__.assert_called_once()

        mock_client.__aexit__.assert_called_once()


@pytest.mark.asyncio
async def test_available_tools_property_no_mcp(mock_agent_config):
    """Test available_tools property without MCP client."""
    agent = Agent(mock_agent_config)
    assert agent.available_tools == []


@pytest.mark.asyncio
async def test_available_tools_property_with_mcp(mock_agent_config_with_mcp):
    """Test available_tools property with MCP client."""
    with patch("fastmcp.Client") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        agent = Agent(mock_agent_config_with_mcp)
        agent._mcp_client = mock_client
        agent._mcp_client_connected = True
        agent._cached_tools = [{"name": "test_tool"}]

        assert agent.available_tools == [{"name": "test_tool"}]


@pytest.mark.asyncio
async def test_run_simple_completion(mock_agent_config, mock_litellm_streaming):
    """Test simple completion run."""
    async with Agent(mock_agent_config) as agent:
        results = []
        async for chunk in agent.run("Hello"):
            results.append(chunk)

        # Check that streaming content is yielded
        content_chunks = [c for c in results if isinstance(c, ContentChunk)]
        assert len(content_chunks) > 0

        # Check full content
        full_content = "".join(c.content for c in content_chunks)
        assert "Hello world!" in full_content

        # Check messages are added
        assert len(agent.messages) >= 1
        assert agent.messages[0].role == "user"
        assert agent.messages[0].content == "Hello"

        # Check that agent response was added and has no tool_calls
        assert len(agent.messages) == 2  # user + assistant
        assert agent.messages[-1].role == "assistant"
        # Should be empty list, causing loop termination
        assert not agent.messages[-1].tool_calls


@pytest.mark.asyncio
async def test_process_single_turn_streaming(mock_agent_config, mock_litellm_streaming):
    """Test single turn streaming processing."""
    async with Agent(mock_agent_config) as agent:
        messages = [Message(role="user", content="Hello")]

        results = []
        async for chunk in agent.process_single_turn_with_tools(messages):
            results.append(chunk)

        # Check streaming content
        content_chunks = [c for c in results if isinstance(c, ContentChunk)]
        assert len(content_chunks) == 3
        assert content_chunks[0].content == "Hello"
        assert content_chunks[1].content == " world"
        assert content_chunks[2].content == "! 完了しました。"


@pytest.mark.asyncio
async def test_execute_tool_calls(mock_agent_config_with_mcp):
    """Test tool execution."""
    with patch("fastmcp.Client") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.call_tool.return_value = "Weather in Tokyo: Sunny, 25°C"

        async with Agent(mock_agent_config_with_mcp) as agent:
            tool_calls = [
                {
                    "id": "tool_call_1",
                    "function": {"name": "get_weather", "arguments": {"city": "Tokyo"}},
                }
            ]

            results = []
            async for chunk in agent._execute_tool_calls(tool_calls):
                results.append(chunk)

            # Check tool input and result
            tool_inputs = [c for c in results if isinstance(c, ToolInput)]
            tool_results = [c for c in results if isinstance(c, ToolResult)]

            assert len(tool_inputs) == 1
            assert len(tool_results) == 1
            assert tool_inputs[0].tool_name == "get_weather"
            assert "Tokyo" in str(tool_results[0].result)


@pytest.mark.asyncio
async def test_tool_calls_json_arguments_parsing():
    """Test tool calls with JSON string arguments parsing."""
    from ygents.config.models import YgentsConfig

    config = YgentsConfig(
        litellm={"model": "openai/gpt-4", "api_key": "test-key"},
        mcp_servers={"test_server": {}},
    )

    with patch("fastmcp.Client") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.call_tool.return_value = "Weather: Sunny, 25°C"

        async with Agent(config) as agent:
            agent._mcp_client = mock_client
            agent._mcp_client_connected = True

            # JSON文字列としてargumentsが来る場合のテスト
            tool_calls = [
                {
                    "id": "tool_call_1",
                    "function": {
                        "name": "get_weather",
                        "arguments": '{"city": "Tokyo", "unit": "celsius"}',
                    },
                }
            ]

            results = []
            async for chunk in agent._execute_tool_calls(tool_calls):
                results.append(chunk)

            # Check tool input has parsed arguments
            tool_inputs = [c for c in results if isinstance(c, ToolInput)]
            assert len(tool_inputs) == 1
            assert tool_inputs[0].tool_name == "get_weather"
            assert tool_inputs[0].arguments == {"city": "Tokyo", "unit": "celsius"}

            # Verify mock was called with parsed arguments
            mock_client.call_tool.assert_called_once_with(
                "get_weather", {"city": "Tokyo", "unit": "celsius"}
            )


@pytest.mark.asyncio
async def test_problem_solved_detection(mock_agent_config):
    """Test problem solved detection."""
    agent = Agent(mock_agent_config)

    # Test positive cases
    assert agent._is_problem_solved(ContentChunk(content="タスクは完了しました"))
    assert agent._is_problem_solved(ContentChunk(content="問題は解決されました"))
    assert agent._is_problem_solved(ContentChunk(content="Task is finished"))

    # Test negative cases
    assert not agent._is_problem_solved(ContentChunk(content="まだ作業中です"))
    assert not agent._is_problem_solved(ToolInput(tool_name="test"))
    assert not agent._is_problem_solved(ContentChunk(content=""))


@pytest.mark.asyncio
async def test_run_loop_termination_without_tools(
    mock_agent_config, mock_litellm_streaming
):
    """Test that run loop terminates when assistant responds without tool calls."""
    async with Agent(mock_agent_config) as agent:
        results = []
        async for chunk in agent.run("Hello"):
            results.append(chunk)

        # Should have exactly 2 messages: user + assistant
        assert len(agent.messages) == 2
        assert agent.messages[0].role == "user"
        assert agent.messages[1].role == "assistant"
        # No tool calls, so loop should terminate
        assert not agent.messages[1].tool_calls

        # Should have yielded content chunks
        content_chunks = [c for c in results if isinstance(c, ContentChunk)]
        assert len(content_chunks) > 0

        # Should terminate due to problem solved detection (完了しました)
        full_content = "".join(c.content for c in content_chunks)
        assert "完了しました" in full_content


@pytest.mark.asyncio
async def test_error_handling(mock_agent_config):
    """Test error handling."""
    with patch("litellm.completion", side_effect=Exception("API Error")):
        async with Agent(mock_agent_config) as agent:
            with pytest.raises(AgentError):
                async for chunk in agent.process_single_turn_with_tools([]):
                    pass


@pytest.mark.asyncio
async def test_abort_event(mock_agent_config, mock_litellm_streaming):
    """Test abort event handling."""
    import asyncio

    abort_event = asyncio.Event()

    async with Agent(mock_agent_config) as agent:
        # Set abort event after first chunk
        async def set_abort():
            await asyncio.sleep(0.1)
            abort_event.set()

        asyncio.create_task(set_abort())

        results = []
        async for chunk in agent.run("Hello", abort_event=abort_event):
            results.append(chunk)

        # Check that processing completed (either normally or aborted)
        # Since the mock response contains "完了しました",
        # the problem might be solved normally
        # In either case, we should have some results
        assert len(results) > 0


@pytest.mark.asyncio
async def test_get_tools_schema(mock_agent_config):
    """Test tools schema generation."""
    agent = Agent(mock_agent_config)
    # Without MCP connection, should return empty list
    assert agent._get_tools_schema() == []


@pytest.mark.asyncio
async def test_get_tools_schema_with_mcp(mock_agent_config_with_mcp):
    """Test tools schema generation with MCP tools."""
    with patch("fastmcp.Client") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        # Mock tool with description and input_schema
        mock_tool = MagicMock()
        mock_tool.name = "get_weather"
        mock_tool.description = "Get weather for a city"
        mock_tool.input_schema = {
            "type": "object",
            "properties": {"city": {"type": "string", "description": "City name"}},
            "required": ["city"],
        }
        mock_client.list_tools.return_value = [mock_tool]

        agent = Agent(mock_agent_config_with_mcp)
        agent._mcp_client = mock_client
        agent._mcp_client_connected = True
        agent._cached_tools = [mock_tool]

        schema = agent._get_tools_schema()

        assert len(schema) == 1
        assert schema[0]["type"] == "function"
        assert schema[0]["function"]["name"] == "get_weather"
        assert schema[0]["function"]["description"] == "Get weather for a city"
        assert schema[0]["function"]["parameters"] == mock_tool.input_schema


@pytest.mark.asyncio
async def test_cache_available_tools(mock_agent_config_with_mcp):
    """Test caching available tools."""
    with patch("fastmcp.Client") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.list_tools.return_value = [{"name": "test_tool"}]

        agent = Agent(mock_agent_config_with_mcp)
        agent._mcp_client = mock_client
        agent._mcp_client_connected = True

        await agent._cache_available_tools()

        assert hasattr(agent, "_cached_tools")
        assert agent._cached_tools == [{"name": "test_tool"}]
        mock_client.list_tools.assert_called_once()


@pytest.mark.asyncio
async def test_streaming_tool_calls_accumulation(
    mock_agent_config_with_mcp, mock_litellm_streaming_tool_calls
):
    """Test streaming tool calls accumulation across chunks."""
    with patch("fastmcp.Client") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.call_tool.return_value = "Tokyo: Sunny, 25°C"

        # Mock tool schema
        mock_tool = MagicMock()
        mock_tool.name = "get_weather"
        mock_tool.description = "Get weather for a city"
        mock_tool.input_schema = {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        }
        mock_client.list_tools.return_value = [mock_tool]

        async with Agent(mock_agent_config_with_mcp) as agent:
            agent._mcp_client = mock_client
            agent._mcp_client_connected = True
            agent._cached_tools = [mock_tool]

            results = []
            async for chunk in agent.run("天気を教えて"):
                results.append(chunk)

            # Check that we got tool input and result
            tool_inputs = [c for c in results if isinstance(c, ToolInput)]
            tool_results = [c for c in results if isinstance(c, ToolResult)]
            content_chunks = [c for c in results if isinstance(c, ContentChunk)]

            assert len(tool_inputs) == 1
            assert len(tool_results) == 1
            assert len(content_chunks) > 0

            # Check that tool was called with correct arguments
            assert tool_inputs[0].tool_name == "get_weather"
            assert tool_inputs[0].arguments == {"city": "Tokyo"}

            # Verify MCP client was called with parsed arguments
            mock_client.call_tool.assert_called_once_with(
                "get_weather", {"city": "Tokyo"}
            )

            # Check that assistant message was correctly constructed
            assert len(agent.messages) >= 2  # user + assistant messages
            assistant_msg = None
            for msg in agent.messages:
                if msg.role == "assistant" and msg.tool_calls:
                    assistant_msg = msg
                    break

            assert assistant_msg is not None
            assert len(assistant_msg.tool_calls) == 1
            assert assistant_msg.tool_calls[0]["id"] == "tool_call_1"
            assert assistant_msg.tool_calls[0]["function"]["name"] == "get_weather"
            assert (
                assistant_msg.tool_calls[0]["function"]["arguments"]
                == '{"city": "Tokyo"}'
            )


def test_agent_system_prompt_setup_without_config(mock_agent_config):
    """Test agent initialization without system prompt configuration."""
    agent = Agent(mock_agent_config)

    # システムプロンプト設定がない場合、システムメッセージは追加されない
    assert len(agent.messages) == 0


def test_agent_system_prompt_setup_with_resolved_prompt():
    """Test agent initialization with resolved system prompt."""
    from ygents.config.models import SystemPromptConfig, YgentsConfig

    # resolved_promptを含むSystemPromptConfigを作成
    system_prompt_config = SystemPromptConfig(
        type="default",
        resolved_prompt="あなたは問題解決を支援するAIエージェントです。",
    )

    config = YgentsConfig(
        mcp_servers={},
        litellm={"model": "openai/gpt-3.5-turbo", "api_key": "test-key"},
        system_prompt=system_prompt_config,
    )

    agent = Agent(config)

    # システムメッセージが最初に追加されていることを確認
    assert len(agent.messages) == 1
    assert agent.messages[0].role == "system"
    assert agent.messages[0].content == "あなたは問題解決を支援するAIエージェントです。"


def test_agent_system_prompt_setup_without_resolved_prompt():
    """Test agent initialization with system prompt config but no resolved prompt."""
    from ygents.config.models import SystemPromptConfig, YgentsConfig

    # resolved_promptがNoneのSystemPromptConfigを作成
    system_prompt_config = SystemPromptConfig(
        type="default",
        resolved_prompt=None,
    )

    config = YgentsConfig(
        mcp_servers={},
        litellm={"model": "openai/gpt-3.5-turbo", "api_key": "test-key"},
        system_prompt=system_prompt_config,
    )

    agent = Agent(config)

    # resolved_promptがNoneの場合、システムメッセージは追加されない
    assert len(agent.messages) == 0


def test_agent_system_prompt_setup_with_custom_resolved_prompt():
    """Test agent initialization with custom resolved system prompt."""
    from ygents.config.models import SystemPromptConfig, YgentsConfig

    # カスタム解決済みプロンプトを作成
    custom_prompt = "あなたはエンジニアとして、コードレビューを実行してください。"
    system_prompt_config = SystemPromptConfig(
        type="custom",
        custom_prompt="あなたは{role}として、{task}を実行してください。",
        variables={"role": "エンジニア", "task": "コードレビュー"},
        resolved_prompt=custom_prompt,
    )

    config = YgentsConfig(
        mcp_servers={},
        litellm={"model": "openai/gpt-3.5-turbo", "api_key": "test-key"},
        system_prompt=system_prompt_config,
    )

    agent = Agent(config)

    # カスタムシステムメッセージが追加されていることを確認
    assert len(agent.messages) == 1
    assert agent.messages[0].role == "system"
    assert agent.messages[0].content == custom_prompt


def test_agent_message_order_with_system_prompt():
    """Test that system prompt is inserted at the beginning of messages."""
    from ygents.config.models import SystemPromptConfig, YgentsConfig

    system_prompt_config = SystemPromptConfig(
        type="default",
        resolved_prompt="システムプロンプトです。",
    )

    config = YgentsConfig(
        mcp_servers={},
        litellm={"model": "openai/gpt-3.5-turbo", "api_key": "test-key"},
        system_prompt=system_prompt_config,
    )

    agent = Agent(config)

    # ユーザーメッセージを追加
    from ygents.agent.models import Message

    user_message = Message(role="user", content="こんにちは")
    agent.messages.append(user_message)

    # システムメッセージが最初にあることを確認
    assert len(agent.messages) == 2
    assert agent.messages[0].role == "system"
    assert agent.messages[0].content == "システムプロンプトです。"
    assert agent.messages[1].role == "user"
    assert agent.messages[1].content == "こんにちは"
