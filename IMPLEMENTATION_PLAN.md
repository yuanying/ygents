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
│   ├── mcp/
│   ├── llm/
│   ├── agent/
│   └── cli/
├── tests/
│   ├── conftest.py
│   ├── test_config/
│   ├── test_mcp/
│   ├── test_llm/
│   ├── test_agent/
│   └── test_cli/
```

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

### フェーズ2: MCPクライアント（TDD）

#### 2.1 MCP接続管理

**テスト作成:**
```python
# tests/test_mcp/test_client.py
def test_mcp_server_connection():
    """MCPサーバー接続テスト"""
    
def test_mcp_command_execution():
    """MCPコマンド実行テスト"""
    
def test_connection_error_handling():
    """接続エラーハンドリングテスト"""
    
def test_reconnection_logic():
    """再接続ロジックテスト"""
```

**実装順序:**
1. モックMCPサーバーの準備
2. 接続テスト作成・実行（失敗）
3. テストコミット
4. 接続機能実装
5. 実装コミット

### フェーズ3: LLMインターフェース（TDD）

#### 3.1 LLM統合

**テスト作成:**
```python
# tests/test_llm/test_interface.py
def test_openai_provider_integration():
    """OpenAIプロバイダー統合テスト"""
    
def test_claude_provider_integration():
    """Claudeプロバイダー統合テスト"""
    
def test_llm_response_processing():
    """LLMレスポンス処理テスト"""
    
def test_api_error_handling():
    """API エラーハンドリングテスト"""
```

**実装順序:**
1. LLMレスポンスモックの作成
2. 統合テスト作成・実行（失敗）
3. テストコミット
4. litellm統合実装
5. 実装コミット

### フェーズ4: エージェント中核ロジック（TDD）

#### 4.1 エージェント機能

**テスト作成:**
```python
# tests/test_agent/test_core.py
def test_user_request_interpretation():
    """ユーザー要求解釈テスト"""
    
def test_task_planning():
    """タスク計画生成テスト"""
    
def test_mcp_llm_coordination():
    """MCP-LLM協調テスト"""
    
def test_execution_flow():
    """実行フロー管理テスト"""
```

**実装順序:**
1. エージェント動作シナリオ定義
2. 統合テスト作成・実行（失敗）
3. テストコミット
4. エージェントロジック実装
5. 実装コミット

### フェーズ5: CLI（TDD）

#### 5.1 コマンドラインインターフェース

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

**週2-3: MCPテスト**
- MCP接続テスト作成・実装
- 通信エラーハンドリングテスト

**週4: LLMテスト**
- LLM統合テスト作成・実装
- レスポンス処理テスト

**週5-6: エージェントテスト**
- エージェントロジックテスト作成・実装
- 統合フローテスト

**週7: CLIテスト**
- CLIテスト作成・実装
- エンドツーエンドテスト

**週8: 最終テスト**
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