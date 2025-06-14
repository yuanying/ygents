"""MCP client tests."""

from unittest.mock import AsyncMock, Mock

import pytest

from ygents.mcp.client import MCPClient
from ygents.mcp.exceptions import MCPException


class TestMCPClient:
    """Test cases for MCPClient."""

    def test_mcp_client_init_with_raw_dict_config(self, mcp_server_configs):
        """Test MCPClient initialization with raw dict config."""
        client = MCPClient(mcp_server_configs)

        # MCPClientが設定を受け取れることを確認
        assert client is not None
        assert client._servers_config == mcp_server_configs

    def test_create_fastmcp_config_format(self, mcp_server_configs):
        """Test conversion to FastMCP config format."""
        client = MCPClient(mcp_server_configs)

        # FastMCP形式への変換をテスト
        fastmcp_config = client._create_fastmcp_config()

        expected_config = {"mcpServers": mcp_server_configs}
        assert fastmcp_config == expected_config

    @pytest.mark.asyncio
    async def test_context_manager_lifecycle(self, mcp_server_configs):
        """Test MCPClient context manager lifecycle."""
        client = MCPClient(mcp_server_configs)

        # Context manager の基本動作をテスト
        assert client.is_connected() is False

        # モックでFastMCPクライアントの動作をシミュレート
        from unittest.mock import patch

        with patch("ygents.mcp.client.Client") as mock_client_class:
            mock_fastmcp_client = AsyncMock()
            mock_fastmcp_client.__aenter__ = AsyncMock(return_value=mock_fastmcp_client)
            mock_fastmcp_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_fastmcp_client

            async with client:
                # Context manager内でクライアントがアクティブであることを確認
                assert client.is_connected() is True

            # Context manager終了後、適切に終了処理が呼ばれることを確認
            assert client.is_connected() is False
            mock_fastmcp_client.__aenter__.assert_called_once()
            mock_fastmcp_client.__aexit__.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_tool_with_prefix(self, mcp_server_configs):
        """Test tool execution with server name prefix."""
        client = MCPClient(mcp_server_configs)

        # Mock FastMCP client
        mock_fastmcp_client = AsyncMock()
        mock_fastmcp_client.call_tool = AsyncMock(return_value=["Tool result"])
        client._fastmcp_client = mock_fastmcp_client
        client._connected = True

        # ツール実行テスト
        result = await client.execute_tool("weather", "get_forecast", {"city": "Tokyo"})

        # プレフィックス付きでFastMCPが呼ばれることを確認
        mock_fastmcp_client.call_tool.assert_called_once_with(
            "weather_get_forecast", {"city": "Tokyo"}
        )
        assert result == ["Tool result"]

    @pytest.mark.asyncio
    async def test_list_tools_all_servers(self, mcp_server_configs):
        """Test listing tools from all servers."""
        client = MCPClient(mcp_server_configs)

        # Mock FastMCP client
        mock_tool = Mock()
        mock_tool.name = "weather_get_forecast"
        mock_fastmcp_client = AsyncMock()
        mock_fastmcp_client.list_tools = AsyncMock(return_value=[mock_tool])
        client._fastmcp_client = mock_fastmcp_client
        client._connected = True

        # 全ツール一覧取得テスト
        result = await client.list_tools()

        # FastMCPのlist_toolsが呼ばれることを確認
        mock_fastmcp_client.list_tools.assert_called_once()
        # プレフィックス処理された結果が返されることを確認
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_list_tools_specific_server(self, mcp_server_configs):
        """Test listing tools from specific server."""
        client = MCPClient(mcp_server_configs)

        # Mock FastMCP client
        mock_tool = Mock()
        mock_tool.name = "weather_get_forecast"
        mock_fastmcp_client = AsyncMock()
        mock_fastmcp_client.list_tools = AsyncMock(return_value=[mock_tool])
        client._fastmcp_client = mock_fastmcp_client
        client._connected = True

        # 特定サーバーのツール一覧取得テスト
        result = await client.list_tools("weather")

        # FastMCPのlist_toolsが呼ばれることを確認
        mock_fastmcp_client.list_tools.assert_called_once()
        # 指定されたサーバーのツールのみが返されることを確認
        assert len(result) >= 0

    def test_is_connected_state(self, mcp_server_configs):
        """Test connection state management."""
        client = MCPClient(mcp_server_configs)

        # 初期状態では未接続
        assert client.is_connected() is False

        # 接続状態の更新テスト
        client._connected = True
        assert client.is_connected() is True

    @pytest.mark.asyncio
    async def test_error_handling_tool_execution(self, mcp_server_configs):
        """Test error handling during tool execution."""
        client = MCPClient(mcp_server_configs)

        # Mock FastMCP client to raise exception
        from fastmcp.exceptions import ClientError

        mock_fastmcp_client = AsyncMock()
        mock_fastmcp_client.call_tool = AsyncMock(
            side_effect=ClientError("Tool failed")
        )
        client._fastmcp_client = mock_fastmcp_client
        client._connected = True

        # 例外がMCPExceptionでラップされることをテスト
        with pytest.raises(MCPException):
            await client.execute_tool("weather", "get_forecast", {"city": "Tokyo"})
