# 実装計画（テスト駆動開発）

## プロジェクト概要
**ygents** - LLM powered エージェント CLI

## TDD原則の厳格な適用

### 開発サイクル
1. **RED**: テストを書く → 実行して失敗確認
2. **GREEN**: テストをパスする最小限の実装
3. **REFACTOR**: コード品質向上
4. **テストのみコミット** → **実装コミット**

## 実装フェーズ（テスト駆動）

### フェーズ1: プロジェクト基盤

#### 1.1 プロジェクト構造セットアップ
**テスト先行アプローチ:**
- テスト環境の構築
- `pytest`設定とテストランナーの準備
- モジュールインポートテストの作成

**実装内容:**
```
ygents/
├── pyproject.toml
├── src/ygents/
│   ├── __init__.py
│   ├── config/
│   ├── agent/        # LiteLLM + FastMCPを直接利用
│   └── cli/
├── tests/
│   ├── conftest.py
│   ├── test_config/
│   ├── test_agent/   # LiteLLM + FastMCP統合テスト含む
│   └── test_cli/
```

**注意**: 以下のモジュールは作成しません
- `src/ygents/llm/` および `tests/test_llm/`（LiteLLM直接利用）
- `src/ygents/mcp/` および `tests/test_mcp/`（FastMCP直接利用）

#### 1.2 設定管理モジュール（TDD）

**テスト作成:**
```python
# tests/test_config/test_config_loader.py
def test_load_yaml_config():
    """YAML設定ファイルの読み込みテスト"""
    
def test_environment_variable_override():
    """環境変数による設定上書きテスト"""
    
def test_config_validation():
    """設定値検証テスト"""
    
def test_default_values():
    """デフォルト値適用テスト"""
```

**実装順序:**
1. テスト作成・実行（失敗確認）
2. テストのみコミット
3. 最小限実装
4. 実装コミット

### フェーズ2: MCP統合（簡素化）

#### 2.1 FastMCP直接利用

**アプローチ変更:**
- 独自のMCPクライアントモジュールは実装せず
- FastMCPを直接利用してシンプルな設計に変更
- エージェントロジック内でfastmcp.Client()を直接呼び出し

**実装内容:**
- `src/ygents/mcp/` モジュールは作成しない
- 設定で指定されたMCPサーバー情報をFastMCPに直接渡す
- エラーハンドリングはFastMCPの例外をそのまま利用

### フェーズ3: LLMインターフェース（簡素化）

#### 3.1 LiteLLM直接利用

**アプローチ変更:**
- 独自のLLMインターフェースモジュールは実装せず
- LiteLLMを直接利用してシンプルな設計に変更
- エージェントロジック内でlitellm.completion()を直接呼び出し

**実装内容:**
- `src/ygents/llm/` モジュールは作成しない
- 設定で指定されたプロバイダー情報をlitellmに直接渡す
- エラーハンドリングはlitellmの例外をそのまま利用

### フェーズ3: エージェント中核ロジック（TDD）

#### 3.1 エージェント機能

**テスト作成:**
```python
# tests/test_agent/test_core.py
def test_user_request_interpretation():
    """ユーザー要求解釈テスト"""
    
def test_task_planning():
    """タスク計画生成テスト"""
    
def test_mcp_llm_coordination():
    """MCP-LLM協調テスト（LiteLLM + FastMCP直接利用）"""
    
def test_execution_flow():
    """実行フロー管理テスト"""
```

**実装順序:**
1. エージェント動作シナリオ定義
2. 統合テスト作成・実行（失敗）
3. テストコミット
4. エージェントロジック実装（LiteLLM + FastMCP統合）
5. 実装コミット

### フェーズ4: CLI（TDD）

#### 4.1 コマンドラインインターフェース

**テスト作成:**
```python
# tests/test_cli/test_commands.py
def test_cli_argument_parsing():
    """CLI引数解析テスト"""
    
def test_interactive_mode():
    """インタラクティブモードテスト"""
    
def test_output_formatting():
    """出力フォーマットテスト"""
    
def test_error_display():
    """エラー表示テスト"""
```

**実装順序:**
1. CLI動作シナリオ定義
2. CLIテスト作成・実行（失敗）
3. テストコミット
4. typer + rich実装
5. 実装コミット

## TDDマイルストーン

### 週次目標（テスト駆動）

**週1: 基盤テスト**
- プロジェクト構造テスト
- 設定管理テスト作成・実装

**週2: 外部ライブラリ統合**
- LiteLLM + FastMCP直接統合確認
- エージェントアーキテクチャ設計

**週3-4: エージェントテスト**
- エージェントロジックテスト作成・実装
- LiteLLM + FastMCP統合テスト
- MCP-LLM協調フローテスト

**週5: CLIテスト**
- CLIテスト作成・実装
- エンドツーエンドテスト

**週6: 最終テスト**
- パフォーマンステスト
- エラーケーステスト完成

## テスト品質管理

### カバレッジ目標
- **ユニットテスト**: 90%以上
- **統合テスト**: 主要フロー100%
- **エラーハンドリング**: 全パターン

### テストの種類
1. **ユニットテスト**: 各機能単体
2. **統合テスト**: モジュール間連携
3. **エンドツーエンドテスト**: 完全なワークフロー
4. **エラーテスト**: 異常系の全パターン

## 実装ルール

### 厳格なTDD適用
- **実装前にテスト**: 一行のコードも書かない
- **テストコミット分離**: 仕様確定として記録
- **最小実装**: テストを通す最小限のコード
- **リファクタリング**: テスト通過後の品質向上