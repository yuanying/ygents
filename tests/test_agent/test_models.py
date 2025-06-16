"""Agent models tests."""

from ygents.agent.models import Message


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
