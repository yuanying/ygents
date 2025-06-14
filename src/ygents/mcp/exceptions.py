"""MCP exceptions."""


class MCPException(Exception):
    """MCP base exception."""

    pass


class MCPConnectionError(MCPException):
    """MCP connection error."""

    pass


class MCPToolError(MCPException):
    """MCP tool execution error."""

    @classmethod
    def from_fastmcp_error(cls, error: Exception) -> "MCPToolError":
        """Create MCPToolError from FastMCP error."""
        return cls(f"Tool execution failed: {error}")


class MCPTimeoutError(MCPException):
    """MCP timeout error."""

    pass
