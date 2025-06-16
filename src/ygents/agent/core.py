"""Agent core module."""

from typing import Any, AsyncGenerator, Dict, List, Optional

from ..config.models import YgentsConfig
from .exceptions import AgentConnectionError, AgentError
from .models import (
    AgentYieldItem,
    ContentChunk,
    ErrorMessage,
    Message,
    StatusUpdate,
    ToolError,
    ToolInput,
    ToolResult,
)


class Agent:
    """Tiny Agent - 単純なcompletionループによる問題解決エージェント

    複雑なタスク計画システムではなく、メッセージベースの単純な
    対話システムでユーザーの問題を解決します。
    """

    def __init__(self, config: YgentsConfig) -> None:
        self.config = config
        self._mcp_client: Optional[Any] = None
        self._mcp_client_connected = False
        self.messages: List[Message] = []

    async def __aenter__(self) -> "Agent":
        """エージェント開始時にMCPクライアントを初期化・接続"""
        if self.config.mcp_servers:
            try:
                import fastmcp

                fastmcp_config = {"mcpServers": self.config.mcp_servers}
                self._mcp_client = fastmcp.Client(fastmcp_config)
                await self._mcp_client.__aenter__()
                self._mcp_client_connected = True

                # ツール一覧をキャッシュ
                await self._cache_available_tools()
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
                return getattr(self, "_cached_tools", [])
            except Exception:
                return []
        return []

    async def run(
        self, user_input: str, abort_event: Optional[Any] = None
    ) -> AsyncGenerator[AgentYieldItem, None]:
        """ユーザー入力に対して問題解決まで単純なcompletionループを実行

        1. user_inputをmessagesに追加
        2. 問題解決まで completion ループを回す
        3. 必要に応じてツール実行
        4. 問題解決判定で終了
        """
        self.messages.append(Message(role="user", content=user_input))

        while True:
            problem_solved_items = []

            # process_single_turn_with_tools を完全に実行し、問題解決アイテムを記録
            async for item in self.process_single_turn_with_tools(self.messages):
                yield item
                if self._is_problem_solved(item):
                    problem_solved_items.append(item)

            # process_single_turn_with_tools実行後、問題解決アイテムがあった場合は終了
            if problem_solved_items:
                break

            # 最後のメッセージがassistantの応答でtool_callsがない場合はループ終了
            if (
                self.messages
                and self.messages[-1].role == "assistant"
                and not self.messages[-1].tool_calls
            ):
                break

            if abort_event and abort_event.is_set():
                yield StatusUpdate(content="処理が中断されました")
                break

    async def process_single_turn_with_tools(
        self, messages: List[Message]
    ) -> AsyncGenerator[AgentYieldItem, None]:
        """単一ターンでのLLM completion + ツール実行"""
        try:
            import litellm

            # MCPクライアントが接続されているがツールがキャッシュされていない場合、キャッシュする
            if self._mcp_client_connected and not hasattr(self, "_cached_tools"):
                await self._cache_available_tools()

            # MessageオブジェクトをAPI用のdict形式に変換
            messages_dict = [msg.to_dict() for msg in messages]

            tools_schema = (
                self._get_tools_schema() if self._mcp_client_connected else None
            )

            response = litellm.completion(
                messages=messages_dict,
                tools=tools_schema,
                stream=True,
                **self.config.litellm,
            )

            assistant_message = Message(role="assistant", content="", tool_calls=[])
            tool_calls_accumulator: Dict[str, Dict[str, Any]] = (
                {}
            )  # tool_call_id -> tool_call 辞書

            for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    assistant_message.content += content
                    yield ContentChunk(content=content)

                if chunk.choices[0].delta.tool_calls:
                    for chunk_tool_call in chunk.choices[0].delta.tool_calls:
                        tool_call_id = chunk_tool_call.id

                        # tool_call_idがNoneの場合は、最後のtool_callに累積
                        if tool_call_id is None:
                            # 最後のtool_callを取得して累積
                            if tool_calls_accumulator:
                                last_tool_call_id = list(tool_calls_accumulator.keys())[
                                    -1
                                ]

                                # function情報を累積
                                if (
                                    hasattr(chunk_tool_call, "function")
                                    and chunk_tool_call.function
                                ):
                                    if (
                                        hasattr(chunk_tool_call.function, "name")
                                        and chunk_tool_call.function.name
                                    ):
                                        tool_calls_accumulator[last_tool_call_id][
                                            "function"
                                        ]["name"] = chunk_tool_call.function.name

                                    if (
                                        hasattr(chunk_tool_call.function, "arguments")
                                        and chunk_tool_call.function.arguments
                                    ):
                                        tool_calls_accumulator[last_tool_call_id][
                                            "function"
                                        ][
                                            "arguments"
                                        ] += chunk_tool_call.function.arguments
                            continue

                        if tool_call_id not in tool_calls_accumulator:
                            # 新しいtool_callの開始
                            tool_calls_accumulator[tool_call_id] = {
                                "id": tool_call_id,
                                "type": getattr(chunk_tool_call, "type", "function"),
                                "function": {"name": "", "arguments": ""},
                            }

                        # function情報を累積
                        if (
                            hasattr(chunk_tool_call, "function")
                            and chunk_tool_call.function
                        ):
                            if (
                                hasattr(chunk_tool_call.function, "name")
                                and chunk_tool_call.function.name
                            ):
                                tool_calls_accumulator[tool_call_id]["function"][
                                    "name"
                                ] = chunk_tool_call.function.name

                            if (
                                hasattr(chunk_tool_call.function, "arguments")
                                and chunk_tool_call.function.arguments
                            ):
                                tool_calls_accumulator[tool_call_id]["function"][
                                    "arguments"
                                ] += chunk_tool_call.function.arguments

            # 累積されたtool_callsをメッセージに設定
            assistant_message.tool_calls = list(tool_calls_accumulator.values())

            # ストリーミング完了後、アシスタントメッセージを追加
            self.messages.append(assistant_message)

            if assistant_message.tool_calls:
                async for tool_result in self._execute_tool_calls(
                    assistant_message.tool_calls
                ):
                    yield tool_result

        except Exception as e:
            yield ErrorMessage(content=f"エラーが発生しました: {e}")
            raise AgentError(f"Completion failed: {e}") from e

    async def _execute_tool_calls(
        self, tool_calls: List[Dict[str, Any]]
    ) -> AsyncGenerator[AgentYieldItem, None]:
        """ツール呼び出しを実行し、結果をyield"""
        import json

        for tool_call in tool_calls:
            tool_name = tool_call.get("function", {}).get("name")
            arguments_str = tool_call.get("function", {}).get("arguments", "{}")

            # argumentsがJSON文字列の場合はパース
            try:
                if isinstance(arguments_str, str):
                    arguments = json.loads(arguments_str) if arguments_str else {}
                else:
                    arguments = arguments_str
            except json.JSONDecodeError:
                arguments = {}

            yield ToolInput(tool_name=tool_name, arguments=arguments)

            try:
                if self._mcp_client and self._mcp_client_connected:
                    result = await self._mcp_client.call_tool(tool_name, arguments)

                    self.messages.append(
                        Message(
                            role="tool",
                            tool_call_id=tool_call.get("id", ""),
                            content=str(result),
                        )
                    )

                    yield ToolResult(tool_name=tool_name, result=result)
                else:
                    yield ToolError(content="MCPクライアントが利用できません")

            except Exception as e:
                error_msg = f"ツール実行エラー ({tool_name}): {e}"
                self.messages.append(
                    Message(
                        role="tool",
                        tool_call_id=tool_call.get("id", ""),
                        content=error_msg,
                    )
                )
                yield ToolError(content=error_msg)

    def _is_problem_solved(self, item: AgentYieldItem) -> bool:
        """問題解決判定（簡単な実装）"""
        if isinstance(item, ContentChunk):
            content = item.content.lower()
            end_keywords = ["完了", "終了", "解決", "できました", "finished", "done"]
            return any(keyword in content for keyword in end_keywords)
        return False


    def _get_tools_schema(self) -> List[Dict[str, Any]]:
        """MCPツールをLiteLLM tools形式に変換"""
        if not self._mcp_client_connected or not hasattr(self, "_cached_tools"):
            return []

        tools_schema = []
        for tool in self._cached_tools:
            # MCPツール情報をOpenAI Function Calling形式に変換
            tool_schema = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or f"Execute {tool.name} tool",
                },
            }

            # パラメータスキーマがある場合は追加
            function_dict = tool_schema["function"]
            assert isinstance(function_dict, dict)
            if hasattr(tool, "input_schema") and tool.input_schema:
                function_dict["parameters"] = tool.input_schema
            else:
                # デフォルトのパラメータスキーマ
                function_dict["parameters"] = {
                    "type": "object",
                    "properties": {},
                    "required": [],
                }

            tools_schema.append(tool_schema)

        return tools_schema

    async def _cache_available_tools(self) -> None:
        """ツール一覧をキャッシュ（初期化時に実行）"""
        if self._mcp_client and self._mcp_client_connected:
            try:
                tools = await self._mcp_client.list_tools()
                self._cached_tools = tools
            except Exception:
                self._cached_tools = []
