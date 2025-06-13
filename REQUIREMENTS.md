# Requirements

## プロジェクト概要

**プロジェクト名**: ygents
**目的**: LLM powered エージェント。登録されたMCPを実行し、ユーザーの要求を解決するCLIを提供する。
**開発言語**: Python 
**開発方針**: テスト駆動開発（TDD）

## 機能要件

- ユーザーはコマンドラインからエージェントを起動できる。
- 設定ファイルを読み込み、MCP serverを登録できる。
- エージェントは他のプロジェクトでも利用できるようCLIとは分離する。

## 技術アーキテクチャ

### プロジェクト構造

```
TBD
```

### 使用ライブラリ

- `rich`: コマンドラインインターフェースの構築
- `typer`: コマンドライン引数の解析
- `litellm`: LLMとのインターフェース
- `fastmcp`: MCPの実行と管理

### アーキテクチャパターン
- **レイヤードアーキテクチャ**: CLI → Agent → MCP Client
- **設定駆動**: 環境変数とYAMLファイル

## 設定

### 設定ファイル

```yaml
mcpServers:
  weather:
    url: "https://weather-api.example.com/mcp"
  assistant:
    command: "python"
    args: ["./assistant_server.py"]}

llm:
  provider: "openai"  # openai または claude
  openai:
    api_key: "your-openai-api-key-here"
    model: "gpt-3.5-turbo"
  claude:
    api_key: "your-claude-api-key-here"
    model: "claude-3-sonnet-20240229"
```

### 環境変数

- `OPENAI_API_KEY`: OpenAI APIキー
- `ANTHROPIC_API_KEY`: Anthropic APIキー

---

**ドキュメントバージョン**: 1.0  
**最終更新**: 2025年6月13日  
**ステータス**: アクティブ開発中
