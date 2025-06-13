# ygents

LLM powered エージェント。登録されたMCPを実行し、ユーザーの要求を解決するCLIを提供する。

## 概要

**ygents** は、大規模言語モデル（LLM）を活用したエージェントシステムです。Model Context Protocol（MCP）サーバーと連携し、ユーザーの要求を理解して実行するコマンドラインインターフェースを提供します。

## 特徴

- **LLM統合**: OpenAI、Claude等の複数のLLMプロバイダーをサポート
- **MCP対応**: MCPサーバーとの統合によるツール実行
- **設定駆動**: YAMLファイルと環境変数による柔軟な設定
- **CLI提供**: typerとrichによるユーザーフレンドリーなインターフェース

## 開発状況

現在開発中のプロジェクトです。

## 開発環境

Python 3.10以上が必要です。

```bash
# 仮想環境の作成
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 開発用インストール
pip install -e ".[dev]"

# テスト実行
pytest

# コードフォーマット
black src tests
isort src tests

# 型チェック
mypy src
```

## ライセンス

MIT License