# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ygents** は LLM powered エージェントプロジェクトです。登録されたMCPサーバーを実行し、ユーザーの要求を解決するCLIを提供します。

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

llm:
  provider: "openai"  # openai または claude
  openai:
    api_key: "your-openai-api-key-here"
    model: "gpt-3.5-turbo"
  claude:
    api_key: "your-claude-api-key-here"
    model: "claude-3-sonnet-20240229"
```

### Environment Variables
- `OPENAI_API_KEY`: OpenAI API キー
- `ANTHROPIC_API_KEY`: Anthropic API キー

## Development Notes

- **レイヤードアーキテクチャ**: CLI → Agent → MCP Client の構造を維持
- **設定駆動**: 環境変数とYAMLファイルによる設定管理
- **エージェントの独立性**: CLIとは分離されたエージェント実装でライブラリとしても利用可能