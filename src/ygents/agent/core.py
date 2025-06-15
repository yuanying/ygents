"""Agent core module."""

from typing import Optional, Dict, Any, List, AsyncGenerator
from ..config.models import YgentsConfig
from .exceptions import AgentError, AgentConnectionError


class Agent:
    """Tiny Agent - 単純なcompletionループによる問題解決エージェント

    複雑なタスク計画システムではなく、メッセージベースの単純な
    対話システムでユーザーの問題を解決します。
    """

    def __init__(self, config: YgentsConfig) -> None:
        self.config = config
        self._mcp_client: Optional[Any] = None
        self._mcp_client_connected = False
        self.messages: List[Dict[str, Any]] = []

    async def __aenter__(self) -> "Agent":
        """エージェント開始時にMCPクライアントを初期化・接続"""
        if self.config.mcp_servers:
            try:
                import fastmcp
                fastmcp_config = {"mcpServers": self.config.mcp_servers}
                self._mcp_client = fastmcp.Client(fastmcp_config)
                await self._mcp_client.__aenter__()
                self._mcp_client_connected = True
            except ImportError:
                raise AgentConnectionError("fastmcp is not available")
            except Exception as e:
                msg = f"Failed to connect to MCP server: {e}"
                raise AgentConnectionError(msg)
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """エージェント終了時にMCPクライアントを切断"""
        if self._mcp_client and self._mcp_client_connected:
            await self._mcp_client.__aexit__(exc_type, exc_val, exc_tb)
            self._mcp_client_connected = False

    @property
    def available_tools(self) -> List[Dict[str, Any]]:
        """利用可能なツール一覧を取得"""
        if self._mcp_client and self._mcp_client_connected:
            try:
                return getattr(self, '_cached_tools', [])
            except Exception:
                return []
        return []

    async def run(
        self,
        user_input: str,
        abort_event: Optional[Any] = None
    ) -> AsyncGenerator[Any, None]:
        """ユーザー入力に対して問題解決まで単純なcompletionループを実行

        1. user_inputをmessagesに追加
        2. 問題解決まで completion ループを回す
        3. 必要に応じてツール実行
        4. 問題解決判定で終了
        """
        self.messages.append({"role": "user", "content": user_input})

        while True:
            loop_completed = False
            async for item in self.process_single_turn_with_tools(
                self.messages
            ):
                yield item

                if self._is_problem_solved(item):
                    loop_completed = True
                    break

            if loop_completed:
                break

            if abort_event and abort_event.is_set():
                yield {"type": "status", "content": "処理が中断されました"}
                break

    async def process_single_turn_with_tools(
        self, messages: List[Dict[str, Any]]
    ) -> AsyncGenerator[Any, None]:
        """単一ターンでのLLM completion + ツール実行"""
        try:
            import litellm

            response = litellm.completion(
                model=self._get_model_name(),
                messages=messages,
                tools=(self._get_tools_schema()
                       if self._mcp_client_connected else None),
                stream=True,
                **self._get_llm_params()
            )

            assistant_message: Dict[str, Any] = {
                "role": "assistant",
                "content": "",
                "tool_calls": []
            }

            for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    assistant_message["content"] += content
                    yield {"type": "content", "content": content}

                if chunk.choices[0].delta.tool_calls:
                    for tool_call in chunk.choices[0].delta.tool_calls:
                        assistant_message["tool_calls"].append(tool_call)

            self.messages.append(assistant_message)

            if assistant_message.get("tool_calls"):
                async for tool_result in self._execute_tool_calls(
                    assistant_message["tool_calls"]
                ):
                    yield tool_result

        except Exception as e:
            yield {"type": "error", "content": f"エラーが発生しました: {e}"}
            raise AgentError(f"Completion failed: {e}") from e

    async def _execute_tool_calls(
        self, tool_calls: List[Dict[str, Any]]
    ) -> AsyncGenerator[Any, None]:
        """ツール呼び出しを実行し、結果をyield"""
        for tool_call in tool_calls:
            tool_name = tool_call.get("function", {}).get("name")
            arguments = tool_call.get("function", {}).get("arguments", {})

            yield {
                "type": "tool_input",
                "tool_name": tool_name,
                "arguments": arguments
            }

            try:
                if self._mcp_client and self._mcp_client_connected:
                    result = await self._mcp_client.call_tool(
                        tool_name, arguments
                    )

                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.get("id"),
                        "content": str(result)
                    })

                    yield {
                        "type": "tool_result",
                        "tool_name": tool_name,
                        "result": result
                    }
                else:
                    yield {
                        "type": "tool_error",
                        "content": "MCPクライアントが利用できません"
                    }

            except Exception as e:
                error_msg = f"ツール実行エラー ({tool_name}): {e}"
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.get("id"),
                    "content": error_msg
                })
                yield {"type": "tool_error", "content": error_msg}

    def _is_problem_solved(self, item: Dict[str, Any]) -> bool:
        """問題解決判定（簡単な実装）"""
        if item.get("type") == "content":
            content = item.get("content", "").lower()
            end_keywords = [
                "完了", "終了", "解決", "できました", "finished", "done"
            ]
            return any(keyword in content for keyword in end_keywords)
        return False

    def _get_model_name(self) -> str:
        """設定からモデル名を取得"""
        provider = self.config.llm.provider

        if provider == "openai" and self.config.llm.openai:
            return self.config.llm.openai.model
        elif provider == "claude" and self.config.llm.claude:
            return self.config.llm.claude.model
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def _get_llm_params(self) -> Dict[str, Any]:
        """LiteLLM呼び出しパラメータを生成"""
        params: Dict[str, Any] = {
            "temperature": 0.7,
            "max_tokens": 1000,
        }

        provider = self.config.llm.provider

        if provider == "openai" and self.config.llm.openai:
            params["api_key"] = self.config.llm.openai.api_key
        elif provider == "claude" and self.config.llm.claude:
            params["api_key"] = self.config.llm.claude.api_key

        return params

    def _get_tools_schema(self) -> List[Dict[str, Any]]:
        """MCPツールをLiteLLM tools形式に変換"""
        if not self._mcp_client_connected:
            return []
        return []

    async def _cache_available_tools(self) -> None:
        """ツール一覧をキャッシュ（初期化時に実行）"""
        if self._mcp_client and self._mcp_client_connected:
            try:
                tools = await self._mcp_client.list_tools()
                self._cached_tools = tools
            except Exception:
                self._cached_tools = []
