# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ygents** は LLM powered エージェントプロジェクトです。登録されたMCPサーバーを実行し、ユーザーの要求を解決するCLIを提供します。

## 開発の進め方

- **開発言語**: Python
- **開発方針**:
  - 新しい機能開発やバグ修正を行う際にはまず新しくブランチを作成する。
  - 設計ドキュメントを `design/` ディレクトリに配置。
  - テスト駆動開発（TDD）を実践。
  - 新しい作業を開始する前にブランチを作成し、適切な粒度でコミットを行ってください。

## Development Commands

### 環境セットアップ
```bash
# 仮想環境の作成・アクティベート
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 開発用インストール
pip install -e ".[dev]"
```

### テスト・品質チェック
```bash
# 仮想環境をアクティベートしてから実行
source .venv/bin/activate

# テスト実行
pytest tests/ -v

# コードフォーマット
black src tests
isort src tests

# 型チェック
mypy src

# リンティング
flake8 src tests
```

## Architecture

### Core Components
- **CLI Layer**: typer + rich によるコマンドラインインターフェース
- **Agent Layer**: LLMとMCPサーバーを調整する中核ロジック  
- **MCP Client Layer**: fastmcp を使用したMCPサーバーとの通信

### Key Technologies
- **typer**: コマンドライン引数解析
- **rich**: リッチなコンソール出力
- **litellm**: 複数LLMプロバイダーへの統一インターフェース
- **fastmcp**: MCPサーバーの実行と管理

## Configuration

設定は YAML ファイルと環境変数で管理されます：

### Configuration File Structure
```yaml
mcpServers:
  weather:
    url: "https://weather-api.example.com/mcp"
  assistant:
    command: "python"
    args: ["./assistant_server.py"]

litellm:
  model: "openai/gpt-4o"  # プロバイダー/モデル形式
  api_key: "your-api-key-here"
  temperature: 0.7
```

### Environment Variables
- `OPENAI_API_KEY`: OpenAI API キー
- `ANTHROPIC_API_KEY`: Anthropic API キー

## Development Notes

- **レイヤードアーキテクチャ**: CLI → Agent → MCP Client の構造を維持
- **設定駆動**: 環境変数とYAMLファイルによる設定管理
- **エージェントの独立性**: CLIとは分離されたエージェント実装でライブラリとしても利用可能

## Core Architecture Details

### Agent Layer (`src/ygents/agent/`)
- **core.py**: メインのAgentクラス。LLMとの対話ループとMCPツール実行を管理
- **models.py**: Agent内で使用するデータクラス（Message, AgentYieldItem等）
- **exceptions.py**: Agent固有の例外クラス

### Configuration Layer (`src/ygents/config/`)  
- **models.py**: Pydanticベースの設定データクラス（YgentsConfig）
- **loader.py**: YAML設定ファイルの読み込みと環境変数の適用

### Key Patterns
- **Streaming Response**: Agentは`AsyncGenerator[AgentYieldItem, None]`でリアルタイム応答
- **Tool Integration**: MCPサーバーとのツール実行は`fastmcp.Client`経由
- **LiteLLM Integration**: `**self.config.litellm`で設定を直接パススルー
- **Environment Override**: モデル名プレフィックス（openai/anthropic）で環境変数を選択

### Test Structure
- 各レイヤーごとに対應するテストディレクトリを配置
- `conftest.py`でテスト用設定とモックを提供
- 非同期テストは`pytest-asyncio`を使用
```