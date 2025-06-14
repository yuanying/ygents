"""MCP client implementation."""

from typing import Any, Dict, List, Optional

from fastmcp import Client
from fastmcp.exceptions import ClientError

from .exceptions import MCPException, MCPToolError


class MCPClient:
    """FastMCP Multi-Server Clientのラッパー"""

    def __init__(self, servers_config: Dict[str, Dict[str, Any]]):
        """Initialize MCPClient with raw dict config."""
        self._servers_config = servers_config
        self._fastmcp_client: Optional[Client] = None
        self._connected = False

    def _create_fastmcp_config(self) -> Dict[str, Any]:
        """生辞書形式のMCP設定をFastMCPConfig形式にラップ"""
        return {"mcpServers": self._servers_config}

    async def __aenter__(self) -> "MCPClient":
        """Context manager entry."""
        fastmcp_config = self._create_fastmcp_config()
        self._fastmcp_client = Client(fastmcp_config)
        await self._fastmcp_client.__aenter__()
        self._connected = True
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        if self._fastmcp_client:
            await self._fastmcp_client.__aexit__(exc_type, exc_val, exc_tb)
        self._connected = False

    async def execute_tool(
        self, server_name: str, tool_name: str, arguments: Dict[str, Any]
    ) -> List[Any]:
        """Execute tool with server name prefix."""
        if not self._connected or not self._fastmcp_client:
            raise MCPException("Client not connected")

        try:
            # プレフィックス付きツール名を作成
            prefixed_tool_name = f"{server_name}_{tool_name}"
            # FastMCPに委譲
            return await self._fastmcp_client.call_tool(prefixed_tool_name, arguments)
        except ClientError as e:
            raise MCPToolError.from_fastmcp_error(e) from e

    async def list_tools(self, server_name: Optional[str] = None) -> List[Any]:
        """List tools from all servers or specific server."""
        if not self._connected or not self._fastmcp_client:
            raise MCPException("Client not connected")

        all_tools = await self._fastmcp_client.list_tools()

        if server_name is None:
            return all_tools

        # 特定サーバーのツールのみフィルタリング
        prefix = f"{server_name}_"
        return [tool for tool in all_tools if tool.name.startswith(prefix)]

    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self._connected
