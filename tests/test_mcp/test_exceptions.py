"""MCP exceptions tests."""

from fastmcp.exceptions import ClientError

from ygents.mcp.exceptions import MCPException, MCPToolError


class TestMCPExceptions:
    """Test cases for MCP exceptions."""

    def test_mcp_exception_base(self):
        """Test MCP base exception."""
        exc = MCPException("test message")
        assert str(exc) == "test message"
        assert isinstance(exc, Exception)

    def test_mcp_tool_error_wrapping(self):
        """Test MCPToolError wrapping FastMCP ClientError."""
        original_error = ClientError("Tool execution failed")
        wrapped_error = MCPToolError.from_fastmcp_error(original_error)

        assert isinstance(wrapped_error, MCPToolError)
        assert isinstance(wrapped_error, MCPException)
        assert "Tool execution failed" in str(wrapped_error)
