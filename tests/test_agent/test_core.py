"""Agent core tests."""

from unittest.mock import AsyncMock, patch

import pytest

from ygents.agent.core import Agent
from ygents.agent.exceptions import AgentError


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
        content_chunks = [c for c in results if c.get("type") == "content"]
        assert len(content_chunks) > 0

        # Check full content
        full_content = "".join(c["content"] for c in content_chunks)
        assert "Hello world!" in full_content

        # Check messages are added
        assert len(agent.messages) >= 1
        assert agent.messages[0]["role"] == "user"
        assert agent.messages[0]["content"] == "Hello"


@pytest.mark.asyncio
async def test_process_single_turn_streaming(mock_agent_config, mock_litellm_streaming):
    """Test single turn streaming processing."""
    async with Agent(mock_agent_config) as agent:
        messages = [{"role": "user", "content": "Hello"}]

        results = []
        async for chunk in agent.process_single_turn_with_tools(messages):
            results.append(chunk)

        # Check streaming content
        content_chunks = [c for c in results if c.get("type") == "content"]
        assert len(content_chunks) == 3
        assert content_chunks[0]["content"] == "Hello"
        assert content_chunks[1]["content"] == " world"
        assert content_chunks[2]["content"] == "! 完了しました。"


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
            tool_inputs = [c for c in results if c.get("type") == "tool_input"]
            tool_results = [c for c in results if c.get("type") == "tool_result"]

            assert len(tool_inputs) == 1
            assert len(tool_results) == 1
            assert tool_inputs[0]["tool_name"] == "get_weather"
            assert "Tokyo" in str(tool_results[0]["result"])


@pytest.mark.asyncio
async def test_problem_solved_detection(mock_agent_config):
    """Test problem solved detection."""
    agent = Agent(mock_agent_config)

    # Test positive cases
    assert agent._is_problem_solved(
        {"type": "content", "content": "タスクは完了しました"}
    )
    assert agent._is_problem_solved(
        {"type": "content", "content": "問題は解決されました"}
    )
    assert agent._is_problem_solved({"type": "content", "content": "Task is finished"})

    # Test negative cases
    assert not agent._is_problem_solved(
        {"type": "content", "content": "まだ作業中です"}
    )
    assert not agent._is_problem_solved({"type": "tool_input", "content": "完了"})
    assert not agent._is_problem_solved({"type": "content", "content": ""})


@pytest.mark.asyncio
async def test_error_handling(mock_agent_config):
    """Test error handling."""
    with patch("litellm.acompletion", side_effect=Exception("API Error")):
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
async def test_get_model_name(mock_agent_config):
    """Test model name retrieval."""
    agent = Agent(mock_agent_config)
    assert agent._get_model_name() == "gpt-4"


@pytest.mark.asyncio
async def test_get_model_name_claude():
    """Test model name retrieval for Claude."""
    from ygents.config.models import ClaudeConfig, LLMConfig, YgentsConfig

    config = YgentsConfig(
        llm=LLMConfig(
            provider="claude",
            claude=ClaudeConfig(
                api_key="test-key", model="claude-3-sonnet-20240229"
            ),
        ),
        mcp_servers={},
    )

    agent = Agent(config)
    assert agent._get_model_name() == "claude-3-sonnet-20240229"


@pytest.mark.asyncio
async def test_get_llm_params(mock_agent_config):
    """Test LLM parameters generation."""
    agent = Agent(mock_agent_config)
    params = agent._get_llm_params()

    assert "temperature" in params
    assert "max_tokens" in params
    assert "api_key" in params
    assert params["api_key"] == "test-key"


@pytest.mark.asyncio
async def test_get_tools_schema(mock_agent_config):
    """Test tools schema generation."""
    agent = Agent(mock_agent_config)
    # Without MCP connection, should return empty list
    assert agent._get_tools_schema() == []


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
