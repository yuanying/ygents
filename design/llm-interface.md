# LLMインターフェース設計ドキュメント（簡素化方針）

## 概要

ygentsプロジェクトのLLMインターフェースは、独自のラッパーモジュールを実装せず、LiteLLMライブラリを直接利用する簡素化された設計を採用します。この方針により、実装の複雑性を大幅に削減し、LiteLLMの豊富な機能とプロバイダーサポートを直接享受します。

## 設計方針の変更

### 従来の設計（実装中止）
- 独自のLLMインターフェースモジュール（`src/ygents/llm/`）
- プロバイダー固有のクラス（OpenAIConfig、ClaudeConfig等）
- レスポンス処理の抽象化レイヤー
- 独自のエラーハンドリングシステム

### 新設計（LiteLLM直接利用）
- `src/ygents/llm/` モジュールは作成しない
- LiteLLMの `completion()` 関数を直接呼び出し
- 設定からプロバイダー情報をLiteLLMに直接渡す
- LiteLLMの例外処理をそのまま利用

## アーキテクチャ

### モジュール構成

```
src/ygents/
├── config/             # 設定管理（LLM設定含む）
├── mcp/               # MCPクライアント
├── agent/             # エージェント中核ロジック（LiteLLM直接利用）
└── cli/               # CLIインターフェース
```

**注意**: `src/ygents/llm/` モジュールは作成しません。

### データフロー

```mermaid
graph TD
    A[エージェント] --> B[litellm.completion]
    B --> C[OpenAI API]
    B --> D[Anthropic Claude API]
    B --> E[Other LLM Providers]
    
    F[YgentsConfig] --> G[LLMConfig]
    G --> H[litellm params]
    H --> B
```

## 実装方針

### 設定管理

既存の設定モジュールを活用してLiteLLM設定を管理：

```python
# src/ygents/config/models.py（現在の実装）
class YgentsConfig(BaseModel):
    mcp_servers: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    litellm: Dict[str, Any] = Field(default_factory=dict)
```

### エージェントでの直接利用

```python
# src/ygents/agent/core.py（現在の実装）
import litellm
from ..config.models import YgentsConfig

class Agent:
    def __init__(self, config: YgentsConfig):
        self.config = config
    
    async def process_single_turn_with_tools(self, messages: List[Message]) -> AsyncGenerator[AgentYieldItem, None]:
        """LiteLLMを直接利用してレスポンス生成"""
        # MessageオブジェクトをAPI用のdict形式に変換
        messages_dict = [msg.to_dict() for msg in messages]
        
        tools_schema = self._get_tools_schema() if self._mcp_client_connected else None
        
        # LiteLLM設定を直接パススルー
        response = litellm.completion(
            messages=messages_dict,
            tools=tools_schema,
            stream=True,
            **self.config.litellm,  # 設定をそのままパススルー
        )
        
        # ストリーミングレスポンスの処理...
```

### エラーハンドリング

LiteLLMの例外をそのまま利用：

```python
import litellm
from litellm.exceptions import AuthenticationError, RateLimitError, APIError

try:
    response = await litellm.acompletion(
        model=model,
        messages=messages,
        api_key=api_key
    )
except AuthenticationError as e:
    # API key関連のエラー
    raise e
except RateLimitError as e:
    # レート制限エラー
    raise e
except APIError as e:
    # その他のAPIエラー
    raise e
```

## 利点

### 1. 実装の大幅簡素化

**削減される実装:**
- LLMインターフェースモジュール全体（~200行）
- プロバイダー固有のクライアントクラス
- レスポンス処理の抽象化レイヤー
- 独自のエラーハンドリングシステム
- 対応するテストスイート（~30テストケース）

### 2. LiteLLMの豊富な機能を直接享受

**利用可能な機能:**
- 100+ LLMプロバイダーサポート
- 自動リトライとエラーハンドリング
- レスポンスキャッシュ
- 使用量トラッキング
- ストリーミング対応
- 関数呼び出し（Function Calling）

### 3. 保守性の向上

**メリット:**
- LiteLLMのアップデートを直接享受
- 新しいプロバイダー対応の自動追従
- バグ修正とパフォーマンス改善の自動適用
- ドキュメント・サポートの充実

### 4. 設定の一貫性

既存の設定管理システムを活用して一貫性を保持：

```yaml
# config.yaml
llm:
  provider: "openai"
  openai:
    api_key: "${OPENAI_API_KEY}"
    model: "gpt-4"

# または
llm:
  provider: "claude"
  claude:
    api_key: "${ANTHROPIC_API_KEY}"
    model: "claude-3-sonnet-20240229"
```

## 実装例

### 基本的な利用パターン

```python
# エージェント内でのLiteLLM直接利用（現在の実装）
class Agent:
    async def process_single_turn_with_tools(self, messages: List[Message]) -> AsyncGenerator[AgentYieldItem, None]:
        """単一ターンでのLLM completion + ツール実行"""
        try:
            import litellm
            
            # MessageオブジェクトをAPI用のdict形式に変換
            messages_dict = [msg.to_dict() for msg in messages]
            
            tools_schema = self._get_tools_schema() if self._mcp_client_connected else None
            
            # 設定を直接パススルー - プロバイダー固有の処理不要
            response = litellm.completion(
                messages=messages_dict,
                tools=tools_schema,
                stream=True,
                **self.config.litellm,  # 全設定を直接渡す
            )
            
            # ストリーミングレスポンスとツール実行の処理
            assistant_message = Message(role="assistant", content="", tool_calls=[])
            # ... (詳細な実装は省略)
            
        except Exception as e:
            yield ErrorMessage(content=f"エラーが発生しました: {e}")
            raise AgentError(f"Completion failed: {e}") from e
```

### MCP連携での利用

```python
# MCPツール結果をLLMに渡す
class Agent:
    async def execute_with_mcp(self, user_request: str) -> str:
        # 1. ユーザーリクエストを分析
        analysis = await self._analyze_request(user_request)
        
        # 2. 必要なMCPツールを実行
        mcp_results = []
        for tool_call in analysis.tool_calls:
            result = await self.mcp_client.execute_tool(
                tool_call.server, tool_call.tool, tool_call.arguments
            )
            mcp_results.append(result)
        
        # 3. MCP結果を含めてLLMで最終応答生成
        messages = [
            {"role": "system", "content": "You are a helpful assistant with access to tools."},
            {"role": "user", "content": user_request},
            {"role": "assistant", "content": f"Tool results: {mcp_results}"},
            {"role": "user", "content": "Please provide a comprehensive response based on the tool results."}
        ]
        
        response = await litellm.acompletion(
            model=self._get_model_string(),
            messages=messages,
            api_key=self._get_api_key()
        )
        
        return response.choices[0].message.content
```

## テスト戦略

### 削減されるテスト

独自のLLMインターフェースモジュールを実装しないため、以下のテストは不要：

- LLMクライアント単体テスト
- プロバイダー固有のテスト
- レスポンス処理テスト
- エラーハンドリングテスト

### 必要なテスト

エージェントロジック内でのLiteLLM統合テスト：

```python
# tests/test_agent/test_llm_integration.py
@pytest.mark.asyncio
async def test_llm_integration_openai(mock_openai_response):
    """OpenAI統合テスト（LiteLLMモック使用）"""
    
@pytest.mark.asyncio  
async def test_llm_integration_claude(mock_claude_response):
    """Claude統合テスト（LiteLLMモック使用）"""

@pytest.mark.asyncio
async def test_llm_error_handling():
    """LiteLLMエラーハンドリングテスト"""
```

## 今後の拡張

### 1. 設定拡張

LiteLLMの高度な機能を活用する設定オプション：

```yaml
litellm:
  model: "openai/gpt-4"
  api_key: "${OPENAI_API_KEY}"
  temperature: 0.7
  max_tokens: 2000
  timeout: 30
  # LiteLLMの任意のパラメータが利用可能
  stream: true
  functions: []
  logit_bias: {}
```

### 2. 高度なLiteLLM機能

将来的に活用可能な機能：

- ストリーミングレスポンス
- 関数呼び出し（Function Calling）
- レスポンスキャッシュ
- 複数プロバイダーの負荷分散

### 3. 監視・ロギング

LiteLLMの統計情報を活用：

```python
import litellm
from litellm import success_callback, failure_callback

# 使用量トラッキング
@success_callback
def log_success(kwargs, response_obj, start_time, end_time):
    print(f"LLM call successful: {response_obj.usage}")

@failure_callback  
def log_failure(kwargs, response_obj, start_time, end_time):
    print(f"LLM call failed: {response_obj}")
```

## 関連ドキュメント

- [LiteLLM Documentation](https://docs.litellm.ai/)
- [設定管理モジュール設計](./config-management.md)
- [エージェント中核ロジック設計](./agent-core.md)（作成予定）
- [実装計画書](../IMPLEMENTATION_PLAN.md)

## まとめ

LiteLLMを直接利用する設計が完全に実装されました：

1. **実装完了**: YgentsConfig.litellmによる柔軟な設定管理
2. **機能豊富性**: LiteLLMの全機能を直接享受
3. **保守性向上**: プロバイダー固有コードの削除による簡素化
4. **拡張性確保**: 100+プロバイダーへの自動対応

**実装成果:**
- コード行数: 358行削除、155行追加（大幅な簡素化）
- テスト削減: 20→12テストケース
- 設定柔軟性: 任意のLiteLLMパラメータ対応

この設計により、エージェントの中核ロジックとユーザーエクスペリエンスの向上により多くのリソースを集中できるようになりました。