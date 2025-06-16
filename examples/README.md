# Ygents Examples

このディレクトリには、ygentsのAgentクラスを使用した実例が含まれています。

## 前提条件

### 1. 依存関係のインストール

```bash
# 基本インストール
pip install -e ".[dev]"

# MCP例を実行する場合（オプション）
pip install fastmcp
```

### 2. API キーの設定

OpenAI APIキーを環境変数に設定してください：

```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

Claude APIを使用する場合：

```bash
export ANTHROPIC_API_KEY="your-claude-api-key-here"
```

## 実行例

### 1. 基本的なAgent使用例

```bash
python examples/simple_agent.py
```

**内容:**
- Agentクラスの基本的な使用方法
- シンプルなチャット機能
- インタラクティブな対話例

**特徴:**
- MCPサーバーなしで動作
- LiteLLMによるOpenAI API統合
- ストリーミング応答の表示

### 2. MCPサーバー連携例

```bash
python examples/agent_with_mcp.py
```

**内容:**
- InMemory MCPサーバーとの連携
- ツール呼び出し機能のデモ
- 天気取得、計算、時刻取得ツール

**利用可能なツール:**
- `get_weather(city)`: 都市の天気取得
- `calculate(operation, a, b)`: 基本計算
- `get_time()`: 現在時刻取得

### 3. 設定管理例

```bash
python examples/config_example.py
```

**内容:**
- 設定ファイルの作成と読み込み
- 直接設定とファイル設定の比較
- 設定バリデーション例

## ファイル説明

| ファイル | 説明 |
|---------|------|
| `simple_agent.py` | 基本的なAgent使用例 |
| `agent_with_mcp.py` | MCPサーバー連携例 |
| `config_example.py` | 設定管理の例 |
| `README.md` | このドキュメント |

## 設定ファイル例

```yaml
# config.yaml
llm:
  provider: "openai"
  openai:
    api_key: "${OPENAI_API_KEY}"
    model: "gpt-3.5-turbo"

mcpServers: {}
```

## トラブルシューティング

### よくあるエラー

1. **APIキー未設定**
   ```
   ❌ エラー: OPENAI_API_KEYが設定されていません
   ```
   **解決方法:** 環境変数を設定してください
   ```bash
   export OPENAI_API_KEY="your-api-key"
   ```

2. **fastmcp未インストール**
   ```
   ❌ fastmcpがインストールされていません
   ```
   **解決方法:** fastmcpをインストールしてください
   ```bash
   pip install fastmcp
   ```

3. **モジュールが見つからない**
   ```
   ModuleNotFoundError: No module named 'ygents'
   ```
   **解決方法:** プロジェクトルートから実行してください
   ```bash
   # プロジェクトルートに移動
   cd /path/to/ygents
   
   # 開発モードでインストール
   pip install -e ".[dev]"
   ```

## カスタマイズ

### 独自のMCPサーバー追加

`agent_with_mcp.py`を参考に、独自のツールを追加できます：

```python
@server.tool()
def my_custom_tool(param: str) -> str:
    """カスタムツールの説明"""
    # ツールの実装
    return f"結果: {param}"
```

### 異なるLLMプロバイダー使用

設定で`provider`を変更することで、異なるLLMを使用できます：

```python
config = YgentsConfig(
    llm=LLMConfig(
        provider="claude",  # "openai" から "claude" に変更
        claude=ClaudeConfig(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            model="claude-3-sonnet-20240229"
        )
    ),
    mcp_servers={}
)
```

## 次のステップ

- [設計ドキュメント](../design/agent-core.md)でAgentの詳細仕様を確認
- [テストファイル](../tests/test_agent/)で実装の詳細を学習
- 独自のMCPサーバーやツールを開発

## サポート

問題や質問がある場合は、GitHubのIssuesでお知らせください。