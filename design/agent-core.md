# エージェント中核ロジック設計ドキュメント（Tiny Agent）

## 概要

ygentsプロジェクトのエージェント中核ロジックは、単純なcompletionループによりユーザーの問題を解決します。複雑なタスク計画・実行システムではなく、シンプルなメッセージベースの対話システムを採用します。TDD方式で実装し、LiteLLMとFastMCPを直接利用する簡素化された設計です。

## 設計方針

### Tiny Agent - 単純化されたアプローチ

- **複雑な計画システム不要**: ユーザー問題解決まで単純なcompletionループ
- **メッセージベース**: 会話履歴をmessages配列で管理
- **ツール呼び出し統合**: completion結果に基づく自動ツール実行
- **問題解決判定**: 単純な終了条件チェック

### アーキテクチャ（簡素化）

```
src/ygents/agent/
├── __init__.py         # パッケージ初期化
├── core.py             # Agent中核クラス（単純化）
└── exceptions.py       # エージェント専用例外
```

**削除されるモジュール**:
- `planner.py` - 複雑なタスク計画は不要
- `executor.py` - 単純なツール実行で十分

## コアクラス設計

### Agent クラス

```python
# src/ygents/agent/core.py
import asyncio
from typing import Optional, Dict, Any, List, AsyncGenerator
import fastmcp
import litellm
from ..config.models import YgentsConfig
from .exceptions import AgentError, AgentConnectionError

class Agent:
    """Tiny Agent - 単純なcompletionループによる問題解決エージェント
    
    複雑なタスク計画システムではなく、メッセージベースの単純な
    対話システムでユーザーの問題を解決します。
    """
    
    def __init__(self, config: YgentsConfig):
        self.config = config
        self._mcp_client: Optional[fastmcp.Client] = None
        self._mcp_client_connected = False
        self.messages: List[Dict[str, Any]] = []  # 会話履歴
    
    async def __aenter__(self) -> "Agent":
        """エージェント開始時にMCPクライアントを初期化・接続"""
        if self.config.mcp_servers:
            fastmcp_config = {"mcpServers": self.config.mcp_servers}
            self._mcp_client = fastmcp.Client(fastmcp_config)
            await self._mcp_client.__aenter__()
            self._mcp_client_connected = True
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """エージェント終了時にMCPクライアントを切断"""
        if self._mcp_client and self._mcp_client_connected:
            await self._mcp_client.__aexit__(exc_type, exc_val, exc_tb)
            self._mcp_client_connected = False
    
    @property
    def available_tools(self) -> List[Dict[str, Any]]:
        """利用可能なツール一覧を取得"""
        if self._mcp_client and self._mcp_client_connected:
            try:
                # 同期的にツール一覧を返すためのプロパティ
                # 実際の取得は非同期で事前に行う
                return getattr(self, '_cached_tools', [])
            except Exception:
                return []
        return []
    
    async def run(self, user_input: str, abort_event=None) -> AsyncGenerator[Any, None]:
        """ユーザー入力に対して問題解決まで単純なcompletionループを実行
        
        REQUIREMENTS.mdの疑似コードに基づく実装:
        1. user_inputをmessagesに追加
        2. 問題解決まで completion ループを回す
        3. 必要に応じてツール実行
        4. 問題解決判定で終了
        """
        # ユーザー入力をメッセージ履歴に追加
        self.messages.append({"role": "user", "content": user_input})
        
        while True:
            # 単一ターンでのツール付きcompletion処理
            loop_completed = False
            async for item in self.process_single_turn_with_tools(self.messages):
                yield item
                
                # 問題解決判定（簡単な実装）
                if self._is_problem_solved(item):
                    loop_completed = True
                    break
            
            if loop_completed:
                break
                
            # 中断イベントチェック
            if abort_event and abort_event.is_set():
                yield {"type": "status", "content": "処理が中断されました"}
                break
    
    async def process_single_turn_with_tools(self, messages: List[Dict[str, Any]]) -> AsyncGenerator[Any, None]:
        """単一ターンでのLLM completion + ツール実行
        
        1. LLM completionを実行
        2. レスポンスをyield（ストリーミング対応）
        3. ツール呼び出しがあれば実行
        4. ツール結果をmessagesに追加してyield
        """
        try:
            # LiteLLMでcompletion実行（ストリーミング）
            response = await litellm.acompletion(
                model=self._get_model_name(),
                messages=messages,
                tools=self._get_tools_schema() if self._mcp_client_connected else None,
                stream=True,
                **self._get_llm_params()
            )
            
            # ストリーミングレスポンスを処理
            assistant_message = {"role": "assistant", "content": "", "tool_calls": []}
            
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    assistant_message["content"] += content
                    yield {"type": "content", "content": content}
                
                if chunk.choices[0].delta.tool_calls:
                    for tool_call in chunk.choices[0].delta.tool_calls:
                        assistant_message["tool_calls"].append(tool_call)
            
            # アシスタントメッセージを履歴に追加
            self.messages.append(assistant_message)
            
            # ツール呼び出し実行
            if assistant_message.get("tool_calls"):
                async for tool_result in self._execute_tool_calls(assistant_message["tool_calls"]):
                    yield tool_result
                    
        except Exception as e:
            yield {"type": "error", "content": f"エラーが発生しました: {e}"}
            raise AgentError(f"Completion failed: {e}") from e
    
    async def _execute_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> AsyncGenerator[Any, None]:
        """ツール呼び出しを実行し、結果をyield"""
        for tool_call in tool_calls:
            tool_name = tool_call.get("function", {}).get("name")
            arguments = tool_call.get("function", {}).get("arguments", {})
            
            yield {"type": "tool_input", "tool_name": tool_name, "arguments": arguments}
            
            try:
                if self._mcp_client and self._mcp_client_connected:
                    result = await self._mcp_client.call_tool(tool_name, arguments)
                    
                    # ツール結果をmessagesに追加
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.get("id"),
                        "content": str(result)
                    })
                    
                    yield {"type": "tool_result", "tool_name": tool_name, "result": result}
                else:
                    yield {"type": "tool_error", "content": "MCPクライアントが利用できません"}
                    
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
        # TODO: より洗練された終了判定ロジック
        if item.get("type") == "content":
            content = item.get("content", "").lower()
            # 簡単な終了キーワード検出
            end_keywords = ["完了", "終了", "解決", "できました", "finished", "done"]
            return any(keyword in content for keyword in end_keywords)
        return False
    
    def _get_model_name(self) -> str:
        """設定からモデル名を取得"""
        provider = self.config.llm.provider
        
        if provider == "openai":
            return self.config.llm.openai.model
        elif provider == "claude":
            return self.config.llm.claude.model
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def _get_llm_params(self) -> Dict[str, Any]:
        """LiteLLM呼び出しパラメータを生成"""
        params = {
            "temperature": 0.7,
            "max_tokens": 1000,
        }
        
        provider = self.config.llm.provider
        
        if provider == "openai":
            params["api_key"] = self.config.llm.openai.api_key
        elif provider == "claude":
            params["api_key"] = self.config.llm.claude.api_key
        
        return params
    
    def _get_tools_schema(self) -> List[Dict[str, Any]]:
        """MCPツールをLiteLLM tools形式に変換"""
        if not self._mcp_client_connected:
            return []
        
        # 実装: MCPツール定義をOpenAI tools形式に変換
        # 詳細は実装時に調整
        return []
    
    async def _cache_available_tools(self):
        """ツール一覧をキャッシュ（初期化時に実行）"""
        if self._mcp_client and self._mcp_client_connected:
            try:
                tools = await self._mcp_client.list_tools()
                self._cached_tools = tools
            except Exception:
                self._cached_tools = []
```

## 使用例

### 基本的な使用パターン（REQUIREMENTS.mdの疑似コードに基づく）

```python
async def main():
    config = load_config("config.yaml")
    
    async with Agent(config) as agent:
        # 利用可能なツール一覧表示
        for tool in agent.available_tools:
            print(f"Tool: {tool.get('name', 'Unknown')}")
        
        while True:
            user_input = await async_prompt(exit_event=exit_event)
            
            # user_inputを元に問題解決まで単純なcompletionループ
            async for chunk in agent.run(user_input, abort_event=abort_event):
                display_chunk(chunk)

def display_chunk(chunk):
    """チャンク表示ヘルパー"""
    if chunk.get("type") == "content":
        print(chunk["content"], end="", flush=True)
    elif chunk.get("type") == "tool_input":
        print(f"\n🔧 ツール実行: {chunk['tool_name']}")
        print(f"   引数: {chunk['arguments']}")
    elif chunk.get("type") == "tool_result":
        print(f"✅ 結果: {chunk['result']}")
    elif chunk.get("type") == "error":
        print(f"❌ エラー: {chunk['content']}")
```

## ライフサイクル管理

### 永続接続とメッセージ履歴

```python
# Tiny Agentのライフサイクル管理
async def interactive_session():
    config = load_config("config.yaml")
    
    async with Agent(config) as agent:
        # エージェント開始時に一度だけMCPサーバーに接続
        await agent._cache_available_tools()  # ツール一覧を事前にキャッシュ
        
        print("利用可能なツール:")
        for tool in agent.available_tools:
            print(f"  - {tool.get('name', 'Unknown')}")
        
        # インタラクティブセッション
        while True:
            user_input = input("\n質問: ")
            if user_input.lower() in ['quit', 'exit']:
                break
            
            print("回答:")
            # 単純なcompletionループで問題解決
            async for chunk in agent.run(user_input):
                if chunk.get("type") == "content":
                    print(chunk["content"], end="", flush=True)
                elif chunk.get("type") == "tool_input":
                    print(f"\n🔧 {chunk['tool_name']} を実行中...")
                elif chunk.get("type") == "tool_result":
                    print(f"✅ 完了")
            print()  # 改行
    
    # エージェント終了時に全MCP接続が自動的に閉じられる
```

## エラーハンドリング

### 例外階層（簡素化）

```python
# src/ygents/agent/exceptions.py
class AgentError(Exception):
    """エージェント基底例外"""
    pass

class AgentConnectionError(AgentError):
    """エージェント接続エラー"""
    pass
```

### エラー処理戦略（簡素化）

Tiny Agentでは、エラーは`run`メソッド内で`yield {"type": "error", "content": "..."}` 形式で報告されます。複雑なエラー分類や進捗報告は不要で、シンプルなエラーメッセージ表示を行います。

```python
class Agent:
    async def run(self, user_input: str, abort_event=None) -> AsyncGenerator[Any, None]:
        try:
            # 正常処理（単純なcompletionループ）
            # ... (実装は上記の通り)
            
        except fastmcp.exceptions.ConnectionError as e:
            yield {"type": "error", "content": f"ツールサーバー接続エラー: {e}"}
            
        except litellm.exceptions.APIError as e:
            yield {"type": "error", "content": f"LLM API エラー: {e}"}
            
        except AgentError as e:
            yield {"type": "error", "content": f"エージェントエラー: {e}"}
            
        except Exception as e:
            yield {"type": "error", "content": f"予期しないエラー: {e}"}
```

## TDD実装計画（Tiny Agent）

### Phase 1: テスト作成（RED）

```python
# tests/test_agent/test_core.py
@pytest.mark.asyncio
async def test_agent_initialization():
    """エージェント初期化テスト"""
    pass

@pytest.mark.asyncio
async def test_agent_context_manager():
    """エージェントコンテキストマネージャーテスト"""
    pass

@pytest.mark.asyncio
async def test_available_tools_property():
    """available_toolsプロパティテスト"""
    pass

@pytest.mark.asyncio
async def test_run_simple_completion():
    """単純なcompletionループテスト"""
    pass

@pytest.mark.asyncio
async def test_run_with_tool_calls():
    """ツール呼び出しありのrunテスト"""
    pass

@pytest.mark.asyncio
async def test_process_single_turn_streaming():
    """単一ターンストリーミング処理テスト"""
    pass

@pytest.mark.asyncio
async def test_execute_tool_calls():
    """ツール実行テスト"""
    pass

@pytest.mark.asyncio
async def test_problem_solved_detection():
    """問題解決判定テスト"""
    pass

@pytest.mark.asyncio
async def test_error_handling():
    """エラーハンドリングテスト"""
    pass

@pytest.mark.asyncio
async def test_abort_event():
    """中断イベント処理テスト"""
    pass
```

### Phase 2: 最小実装（GREEN）

1. 例外クラス実装（`AgentError`, `AgentConnectionError`）
2. Agent基本クラス実装
   - `__init__`, `__aenter__`, `__aexit__`
   - `available_tools` プロパティ
   - `run` メソッド（基本ループ）
   - `process_single_turn_with_tools` メソッド
   - ヘルパーメソッド群

### Phase 3: リファクタリング

1. コード品質向上
2. エラーハンドリング強化
3. 問題解決判定ロジック改善

## テスト戦略（InMemory MCP Server使用）

### モックとFixture

```python
# tests/test_agent/conftest.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastmcp import FastMCP, Client
from ygents.config.models import YgentsConfig, LLMConfig, OpenAIConfig

@pytest.fixture
def mock_agent_config():
    """テスト用エージェント設定"""
    return YgentsConfig(
        llm=LLMConfig(
            provider="openai",
            openai=OpenAIConfig(api_key="test-key", model="gpt-4")
        ),
        mcp_servers={}
    )

@pytest.fixture
def mock_agent_config_with_mcp():
    """MCP付きテスト用エージェント設定"""
    return YgentsConfig(
        llm=LLMConfig(
            provider="openai",
            openai=OpenAIConfig(api_key="test-key", model="gpt-4")
        ),
        mcp_servers={
            "test_server": {}  # InMemory serverは設定不要
        }
    )

@pytest.fixture
def inmemory_mcp_server():
    """InMemory MCP Server（FastMCPインスタンス）"""
    server = FastMCP(name="TestServer")
    
    @server.tool()
    def get_weather(city: str) -> str:
        """Get weather for a city"""
        return f"Weather in {city}: Sunny, 25°C"
    
    @server.tool()
    def calculate(operation: str, a: float, b: float) -> float:
        """Perform basic math operations"""
        if operation == "add":
            return a + b
        elif operation == "subtract":
            return a - b
        elif operation == "multiply":
            return a * b
        elif operation == "divide":
            if b == 0:
                raise ValueError("Division by zero")
            return a / b
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    @server.resource("file://test/data")
    def get_test_data() -> str:
        """Test data resource"""
        return "This is test data"
    
    return server

@pytest.fixture
async def inmemory_mcp_client(inmemory_mcp_server):
    """InMemory MCP Client（実際のFastMCP Client）"""
    # FastMCPインスタンスから直接Clientを作成
    client = Client(inmemory_mcp_server)
    return client

@pytest.fixture
def mock_litellm_streaming():
    """LiteLLMストリーミング応答モック"""
    async def mock_acompletion(*args, **kwargs):
        # ストリーミングレスポンスのモック
        chunks = [
            MagicMock(choices=[MagicMock(delta=MagicMock(content="Hello", tool_calls=None))]),
            MagicMock(choices=[MagicMock(delta=MagicMock(content=" world", tool_calls=None))]),
            MagicMock(choices=[MagicMock(delta=MagicMock(content="!", tool_calls=None))]),
        ]
        for chunk in chunks:
            yield chunk
    
    with patch("litellm.acompletion", side_effect=mock_acompletion):
        yield

@pytest.fixture
def mock_litellm_with_tools():
    """ツール呼び出し付きLiteLLM応答モック"""
    async def mock_acompletion(*args, **kwargs):
        # ツール呼び出しを含むストリーミングレスポンス
        chunks = [
            MagicMock(choices=[MagicMock(delta=MagicMock(content="I'll check the weather", tool_calls=None))]),
            MagicMock(choices=[MagicMock(delta=MagicMock(
                content=None,
                tool_calls=[{
                    "id": "tool_call_1",
                    "function": {
                        "name": "get_weather",
                        "arguments": {"city": "Tokyo"}
                    }
                }]
            ))]),
        ]
        for chunk in chunks:
            yield chunk
    
    with patch("litellm.acompletion", side_effect=mock_acompletion):
        yield
```

### 統合テスト

```python
# tests/test_agent/test_integration.py
@pytest.mark.asyncio
async def test_simple_completion_flow(mock_agent_config, mock_litellm_streaming):
    """単純なcompletionフローテスト"""
    from ygents.agent.core import Agent
    
    async with Agent(mock_agent_config) as agent:
        results = []
        async for chunk in agent.run("Hello"):
            results.append(chunk)
        
        # ストリーミングコンテンツが正しくyieldされることを確認
        content_chunks = [c for c in results if c.get("type") == "content"]
        assert len(content_chunks) > 0
        
        # 全コンテンツを結合
        full_content = "".join(c["content"] for c in content_chunks)
        assert "Hello world!" in full_content

@pytest.mark.asyncio
async def test_tool_execution_flow(inmemory_mcp_client, mock_litellm_with_tools):
    """InMemory MCP Serverを使ったツール実行フローテスト"""
    from ygents.agent.core import Agent
    from ygents.config.models import YgentsConfig, LLMConfig, OpenAIConfig
    
    # AgentにInMemory MCP Clientを注入
    config = YgentsConfig(
        llm=LLMConfig(
            provider="openai",
            openai=OpenAIConfig(api_key="test-key", model="gpt-4")
        ),
        mcp_servers={"test_server": {}}
    )
    
    async with Agent(config) as agent:
        # InMemory clientを直接注入（テスト用）
        agent._mcp_client = inmemory_mcp_client
        agent._mcp_client_connected = True
        
        async with inmemory_mcp_client:
            results = []
            async for chunk in agent.run("What's the weather in Tokyo?"):
                results.append(chunk)
            
            # ツール入力・結果が正しくyieldされることを確認
            tool_inputs = [c for c in results if c.get("type") == "tool_input"]
            tool_results = [c for c in results if c.get("type") == "tool_result"]
            
            assert len(tool_inputs) > 0
            assert len(tool_results) > 0
            
            # 天気ツールが呼び出されることを確認
            weather_calls = [t for t in tool_inputs if t.get("tool_name") == "get_weather"]
            assert len(weather_calls) > 0
            assert weather_calls[0]["arguments"]["city"] == "Tokyo"

@pytest.mark.asyncio
async def test_inmemory_server_tools(inmemory_mcp_client):
    """InMemory MCP Serverのツールが正しく動作することを確認"""
    async with inmemory_mcp_client:
        # ツール一覧取得
        tools = await inmemory_mcp_client.list_tools()
        tool_names = [tool.name for tool in tools]
        
        assert "get_weather" in tool_names
        assert "calculate" in tool_names
        
        # 天気ツール実行
        weather_result = await inmemory_mcp_client.call_tool("get_weather", {"city": "Tokyo"})
        assert "Tokyo" in str(weather_result)
        assert "Sunny" in str(weather_result)
        
        # 計算ツール実行
        calc_result = await inmemory_mcp_client.call_tool("calculate", {
            "operation": "add",
            "a": 5,
            "b": 3
        })
        assert calc_result[0].text == "8"  # TextContentを想定
```

## 関連ドキュメント

- [MCP統合設計](./mcp-client.md)
- [設定管理設計](./config-management.md)
- [実装計画](../IMPLEMENTATION_PLAN.md)
- [REQUIREMENTS.md](../REQUIREMENTS.md)
- [FastMCP Documentation](https://docs.fastmcp.ai/)
- [LiteLLM Documentation](https://docs.litellm.ai/)

## まとめ

Tiny Agentは以下の特徴を持つ簡素化されたエージェントシステムです：

1. **単純なcompletionループ**: 複雑なタスク計画・実行システム不要
2. **メッセージベース対話**: 会話履歴を`messages`配列で管理
3. **ストリーミング対応**: LiteLLMのストリーミングAPIを活用
4. **ツール統合**: completion結果に基づく自動ツール実行
5. **永続MCP接続**: エージェントライフサイクルと同期した効率的接続管理
6. **TDD実装**: テスト先行による品質確保

この設計により、REQUIREMENTS.mdで定義された「単純なcompletionループでユーザーの問題を解決する」という要件を満たす、シンプルで保守性の高いエージェントシステムを実現します。