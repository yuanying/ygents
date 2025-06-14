# ygents プロジェクト要件定義

## プロジェクト概要

**プロジェクト名**: ygents  
**目的**: Model Context Protocol (MCP) サーバーと連携してタスクを実行するLLM駆動のCLIエージェント  
**開発言語**: Python 3.10+  
**開発方針**: テスト駆動開発（TDD）

## 基本機能要件

### 1. 設定管理
- **YAML設定ファイル**: MCPサーバー・LLMプロバイダー設定
- **環境変数サポート**: APIキー管理と設定上書き
- **設定検証**: Pydanticによる構造化検証

### 2. MCP クライアント機能  
- **マルチサーバー接続**: 複数MCPサーバーとの同時接続
- **ツール実行**: 統一インターフェースでのツール呼び出し
- **FastMCP活用**: Multi-Server Clients機能による効率的実装

### 3. LLM 統合（簡素化方針）
- **LiteLLM直接利用**: 独自ラッパーなし、100+プロバイダーサポート
- **設定連携**: config.yamlからLiteLLMパラメータを自動生成
- **エラーハンドリング**: LiteLLM例外をそのまま活用

### 4. エージェント中核ロジック
- **要求解釈**: 自然言語から実行可能タスクへの変換
- **MCP-LLM協調**: ツール実行結果をLLMコンテキストに統合
- **実行フロー管理**: 複雑なタスクの段階的実行

### 5. CLI インターフェース
- **Typer**: 直感的なコマンドライン引数処理
- **Rich**: 美しいコンソール出力とプログレス表示
- **インタラクティブモード**: 継続対話での連続タスク実行

## 技術アーキテクチャ

### プロジェクト構造

```
ygents/
├── src/ygents/
│   ├── config/          # 設定管理（YAML、環境変数）
│   ├── mcp/            # MCPクライアント（FastMCP活用）
│   ├── agent/          # エージェント中核ロジック（LiteLLM直接利用）
│   └── cli/            # CLIインターフェース（Typer + Rich）
├── tests/              # 包括的テストスイート
└── design/             # 設計ドキュメント
```

**注意**: `src/ygents/llm/` モジュールは作成しません（LiteLLM直接利用）

### 使用ライブラリ

**コア依存関係:**
- `litellm`: LLM統合（OpenAI、Claude、その他100+プロバイダー）
- `fastmcp`: MCPクライアント実装（Multi-Server Clients活用）
- `typer`: CLIフレームワーク
- `rich`: 美しいコンソール出力
- `pydantic`: 設定・データ検証
- `pyyaml`: YAML設定ファイル処理

**開発・テスト:**
- `pytest`: テストフレームワーク（asyncio対応）
- `black`, `isort`, `flake8`, `mypy`: コード品質管理

### アーキテクチャパターン
- **レイヤードアーキテクチャ**: CLI → Agent → MCP Client ← LiteLLM
- **設定駆動**: YAML + 環境変数による柔軟な設定管理
- **依存性注入**: 外部ライブラリ機能の直接活用

## 設定例

### 設定ファイル（config.yaml）

```yaml
# MCP サーバー設定（生辞書形式、FastMCPに直接委譲）
mcp_servers:
  weather:
    url: "https://weather-api.example.com/mcp"
  assistant:
    command: "python"
    args: ["./assistant_server.py"]

# LLM プロバイダー設定（LiteLLM直接利用）
llm:
  provider: "openai"  # "openai" または "claude"
  openai:
    api_key: "${OPENAI_API_KEY}"  # 環境変数展開
    model: "gpt-4"
  claude:
    api_key: "${ANTHROPIC_API_KEY}"
    model: "claude-3-sonnet-20240229"
```

### 環境変数

- `OPENAI_API_KEY`: OpenAI APIキー
- `ANTHROPIC_API_KEY`: Anthropic APIキー（Claude用）

## 実装方針

### 1. テスト駆動開発（TDD）
- **RED-GREEN-REFACTOR**: 厳格なTDDサイクル適用
- **テストカバレッジ**: 90%以上を目標
- **テスト先行コミット**: 仕様確定としてテストを先にコミット

### 2. 外部ライブラリ活用
- **LiteLLM直接利用**: 独自LLMラッパーを実装せず
- **FastMCP委譲**: MCP機能の大部分をFastMCPライブラリに委譲
- **依存性最小化**: 必要最小限の独自実装

### 3. コード品質管理
- **自動整形**: black、isort による統一フォーマット
- **静的解析**: flake8、mypy による品質チェック
- **CI/CD**: GitHub Actions による自動テスト・品質チェック

## 成功基準

### 機能達成
- [ ] YAML設定ファイルからの MCP サーバー接続
- [ ] LiteLLM による複数 LLM プロバイダー利用
- [ ] 自然言語による MCP ツール実行
- [ ] Rich による美しいコンソール出力
- [ ] インタラクティブモードでの継続対話

### 品質達成
- [ ] テストカバレッジ 90% 以上
- [ ] 全コード品質チェックツールの通過
- [ ] TDD 手法による完全実装
- [ ] 包括的エラーハンドリング

---

**ドキュメントバージョン**: 2.0（LiteLLM直接利用方針）  
**最終更新**: 2025年6月14日  
**ステータス**: アクティブ開発中（Issue #3完了、Issue #4簡素化完了）
