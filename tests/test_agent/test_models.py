"""Agent models tests."""

from ygents.agent.models import (
    ContentChunk,
    ErrorMessage,
    Message,
    StatusUpdate,
    ToolError,
    ToolInput,
    ToolResult,
)


class TestMessage:
    """Message model tests."""

    def test_message_basic_creation(self):
        """Test basic message creation."""
        message = Message(role="user", content="Hello")
        assert message.role == "user"
        assert message.content == "Hello"
        assert message.tool_calls == []
        assert message.tool_call_id == ""
        assert message.name == ""

    def test_message_to_dict_user_role(self):
        """Test message to_dict for user role."""
        message = Message(role="user", content="Hello")
        result = message.to_dict()
        expected = {"role": "user", "content": "Hello"}
        assert result == expected

    def test_message_to_dict_assistant_role(self):
        """Test message to_dict for assistant role."""
        message = Message(role="assistant", content="Hi there")
        result = message.to_dict()
        expected = {"role": "assistant", "content": "Hi there"}
        assert result == expected

    def test_message_to_dict_assistant_with_tool_calls(self):
        """Test message to_dict for assistant with tool calls."""
        tool_calls = [{"id": "call_1", "function": {"name": "get_weather"}}]
        message = Message(role="assistant", content="", tool_calls=tool_calls)
        result = message.to_dict()
        expected = {
            "role": "assistant",
            "content": "",
            "tool_calls": tool_calls,
        }
        assert result == expected

    def test_message_to_dict_tool_role(self):
        """Test message to_dict for tool role."""
        message = Message(role="tool", content="Weather: Sunny", tool_call_id="call_1")
        result = message.to_dict()
        expected = {
            "role": "tool",
            "content": "Weather: Sunny",
            "tool_call_id": "call_1",
        }
        assert result == expected

    def test_message_to_dict_tool_role_empty_content(self):
        """Test message to_dict for tool role with empty content."""
        message = Message(role="tool", tool_call_id="call_1")
        result = message.to_dict()
        expected = {"role": "tool", "tool_call_id": "call_1"}
        assert result == expected

    def test_message_to_dict_with_name(self):
        """Test message to_dict with name field."""
        message = Message(role="user", content="Hello", name="John")
        result = message.to_dict()
        expected = {"role": "user", "content": "Hello", "name": "John"}
        assert result == expected

    def test_message_to_dict_system_role(self):
        """Test message to_dict for system role."""
        message = Message(role="system", content="You are a helpful assistant")
        result = message.to_dict()
        expected = {"role": "system", "content": "You are a helpful assistant"}
        assert result == expected

    def test_message_to_dict_system_role_empty_content(self):
        """Test message to_dict for system role with empty content."""
        message = Message(role="system")
        result = message.to_dict()
        expected = {"role": "system", "content": ""}
        assert result == expected


class TestAgentYieldItems:
    """Agent yield item tests."""

    def test_content_chunk_creation(self):
        """Test ContentChunk creation."""
        chunk = ContentChunk(content="Hello world")
        assert chunk.type == "content"
        assert chunk.content == "Hello world"

    def test_content_chunk_default(self):
        """Test ContentChunk with defaults."""
        chunk = ContentChunk()
        assert chunk.type == "content"
        assert chunk.content == ""

    def test_tool_input_creation(self):
        """Test ToolInput creation."""
        tool_input = ToolInput(tool_name="get_weather", arguments={"city": "Tokyo"})
        assert tool_input.type == "tool_input"
        assert tool_input.tool_name == "get_weather"
        assert tool_input.arguments == {"city": "Tokyo"}

    def test_tool_input_default(self):
        """Test ToolInput with defaults."""
        tool_input = ToolInput()
        assert tool_input.type == "tool_input"
        assert tool_input.tool_name == ""
        assert tool_input.arguments == {}

    def test_tool_result_creation(self):
        """Test ToolResult creation."""
        tool_result = ToolResult(tool_name="get_weather", result="Sunny, 25°C")
        assert tool_result.type == "tool_result"
        assert tool_result.tool_name == "get_weather"
        assert tool_result.result == "Sunny, 25°C"

    def test_tool_result_default(self):
        """Test ToolResult with defaults."""
        tool_result = ToolResult()
        assert tool_result.type == "tool_result"
        assert tool_result.tool_name == ""
        assert tool_result.result is None

    def test_tool_error_creation(self):
        """Test ToolError creation."""
        tool_error = ToolError(content="Tool execution failed")
        assert tool_error.type == "tool_error"
        assert tool_error.content == "Tool execution failed"

    def test_tool_error_default(self):
        """Test ToolError with defaults."""
        tool_error = ToolError()
        assert tool_error.type == "tool_error"
        assert tool_error.content == ""

    def test_error_message_creation(self):
        """Test ErrorMessage creation."""
        error_msg = ErrorMessage(content="An error occurred")
        assert error_msg.type == "error"
        assert error_msg.content == "An error occurred"

    def test_error_message_default(self):
        """Test ErrorMessage with defaults."""
        error_msg = ErrorMessage()
        assert error_msg.type == "error"
        assert error_msg.content == ""

    def test_status_update_creation(self):
        """Test StatusUpdate creation."""
        status = StatusUpdate(content="Processing completed")
        assert status.type == "status"
        assert status.content == "Processing completed"

    def test_status_update_default(self):
        """Test StatusUpdate with defaults."""
        status = StatusUpdate()
        assert status.type == "status"
        assert status.content == ""
