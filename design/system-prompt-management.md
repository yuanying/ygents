# システムプロンプト管理設計書

## 概要

Agentクラスに対してシステムプロンプトを指定できる機能を提供します。設定ファイルでプロンプトの種類を選択し、将来的にはReActエージェントなど異なるエージェントタイプを切り替えられるようにします。

## 設計目標

1. **システムプロンプトの注入**: Agent起動時にシステムプロンプトを指定可能
2. **プロンプトテンプレート管理**: 事前定義されたプロンプトテンプレートの管理
3. **設定による選択**: 設定ファイルでプロンプトタイプを選択
4. **早期検証**: 設定ファイル読み込み時にプロンプトタイプの妥当性を検証
5. **拡張性**: 新しいエージェントタイプの追加が容易
6. **後方互換性**: 既存のAgentクラスとの互換性維持

## アーキテクチャ

### 1. プロンプトテンプレート管理

```python
# src/ygents/prompts/templates.py
from enum import Enum
from typing import Dict, Protocol

class PromptTemplate(Protocol):
    """プロンプトテンプレートのインターフェース"""
    name: str
    description: str
    system_prompt: str

class PromptType(Enum):
    """利用可能なプロンプトタイプ"""
    DEFAULT = "default"
    REACT = "react"
    ANALYTICAL = "analytical"
    CREATIVE = "creative"

class DefaultPrompt:
    name = "default"
    description = "標準的な問題解決エージェント"
    system_prompt = """あなたは問題解決を支援するAIエージェントです。
ユーザーの要求を理解し、適切なツールを使用して問題を解決してください。"""

class ReActPrompt:
    name = "react"
    description = "ReActパターンを使用する推論エージェント"
    system_prompt = """あなたはReAct（Reasoning and Acting）パターンを使用するAIエージェントです。

以下の形式で思考と行動を交互に行ってください：

Thought: 現在の状況を分析し、次に何をすべきか考える
Action: 必要なツールを実行する
Observation: ツールの実行結果を観察する
Thought: 結果を分析し、次のステップを考える
...

最終的にFinal Answerで結論を提示してください。"""

# プロンプトテンプレートレジストリ
PROMPT_TEMPLATES: Dict[str, PromptTemplate] = {
    PromptType.DEFAULT.value: DefaultPrompt(),
    PromptType.REACT.value: ReActPrompt(),
    # 将来的に追加される他のプロンプトテンプレート
}
```

### 2. 設定モデルの拡張

```python
# src/ygents/config/models.py
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class YgentsConfig(BaseModel):
    """Main ygents configuration."""
    
    mcp_servers: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    litellm: Dict[str, Any] = Field(default_factory=dict)
    
    # システムプロンプト設定
    system_prompt: Optional[SystemPromptConfig] = Field(default=None)

class SystemPromptConfig(BaseModel):
    """システムプロンプト設定"""
    
    # プロンプトタイプの指定
    type: str = Field(default="default", description="プロンプトタイプ (default, react, analytical, etc.)")
    
    # カスタムプロンプト（typeより優先）
    custom_prompt: Optional[str] = Field(default=None, description="カスタムシステムプロンプト")
    
    # プロンプト変数（テンプレート内で使用）
    variables: Dict[str, str] = Field(default_factory=dict, description="プロンプトテンプレート内で使用される変数")
    
    # 解決済みプロンプト（ConfigLoaderで自動設定）
    resolved_prompt: Optional[str] = Field(default=None, description="テンプレートと変数を解決した最終的なシステムプロンプト")
```

### 3. 設定読み込み時の検証と解決

```python
# src/ygents/config/loader.py
from ..prompts.templates import PROMPT_TEMPLATES

class ConfigLoader:
    def load_from_dict(self, config_dict: Dict[str, Any]) -> YgentsConfig:
        """設定辞書から設定を読み込み、検証・解決を行う"""
        # キー正規化
        normalized_dict = self._normalize_dict_keys(config_dict)
        
        # 環境変数適用
        normalized_dict = self._apply_env_overrides(normalized_dict)
        
        # システムプロンプト設定の検証と解決
        self._validate_system_prompt_config(normalized_dict)
        normalized_dict = self._resolve_system_prompt(normalized_dict)
        
        # Pydanticモデルに変換
        return YgentsConfig(**normalized_dict)
    
    def _validate_system_prompt_config(self, config_dict: Dict[str, Any]) -> None:
        """システムプロンプト設定の検証"""
        if "system_prompt" not in config_dict:
            return
            
        system_prompt = config_dict["system_prompt"]
        if not isinstance(system_prompt, dict):
            return
            
        # プロンプトタイプの検証
        prompt_type = system_prompt.get("type", "default")
        if prompt_type not in PROMPT_TEMPLATES:
            available_types = list(PROMPT_TEMPLATES.keys())
            raise ValueError(
                f"Invalid prompt type '{prompt_type}'. "
                f"Available types: {available_types}"
            )
    
    def _resolve_system_prompt(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """システムプロンプトテンプレートと変数を解決"""
        if "system_prompt" not in config_dict:
            return config_dict
            
        system_prompt = config_dict["system_prompt"]
        if not isinstance(system_prompt, dict):
            return config_dict
            
        # コピーを作成して元を変更しない
        config = dict(config_dict)
        resolved_prompt = dict(system_prompt)
        
        # カスタムプロンプトが指定されている場合は優先
        if "custom_prompt" in resolved_prompt and resolved_prompt["custom_prompt"]:
            prompt_text = resolved_prompt["custom_prompt"]
            variables = resolved_prompt.get("variables", {})
            resolved_prompt["resolved_prompt"] = self._apply_template_variables(
                prompt_text, variables
            )
        else:
            # テンプレートベースのプロンプト
            prompt_type = resolved_prompt.get("type", "default")
            if prompt_type in PROMPT_TEMPLATES:
                template = PROMPT_TEMPLATES[prompt_type]
                variables = resolved_prompt.get("variables", {})
                resolved_prompt["resolved_prompt"] = self._apply_template_variables(
                    template.system_prompt, variables
                )
        
        config["system_prompt"] = resolved_prompt
        return config
    
    def _apply_template_variables(self, template: str, variables: Dict[str, str]) -> str:
        """テンプレート変数を適用"""
        result = template
        for key, value in variables.items():
            result = result.replace(f"{{{key}}}", value)
        return result
```

### 4. Agentクラスの拡張

```python
# src/ygents/agent/core.py
from ..config.models import YgentsConfig

class Agent:
    def __init__(self, config: YgentsConfig) -> None:
        self.config = config
        self._mcp_client: Optional[Any] = None
        self._mcp_client_connected = False
        self.messages: List[Message] = []
        
        # システムプロンプトの設定
        self._setup_system_prompt()
    
    def _setup_system_prompt(self) -> None:
        """システムプロンプトをセットアップ"""
        if not self.config.system_prompt:
            return
            
        # ConfigLoaderで解決済みのプロンプトを使用
        resolved_prompt = self.config.system_prompt.resolved_prompt
        if resolved_prompt:
            # システムメッセージをメッセージリストの最初に追加
            self.messages.insert(0, Message(role="system", content=resolved_prompt))
```

### 5. 設定ファイル例

```yaml
# config.yaml
mcpServers:
  weather:
    url: "https://weather-api.example.com/mcp"

litellm:
  model: "openai/gpt-4o"
  api_key: "${OPENAI_API_KEY}"
  temperature: 0.7

# システムプロンプト設定
system_prompt:
  type: "react"  # default, react, analytical, creative
  variables:
    domain: "ソフトウェア開発"
    expertise_level: "上級"

# カスタムプロンプトの例
# system_prompt:
#   custom_prompt: |
#     あなたは{domain}の専門家です。
#     {expertise_level}レベルの知識を持ち、
#     常に最新のベストプラクティスに従って回答してください。
#   variables:
#     domain: "機械学習"
#     expertise_level: "エキスパート"
```

## 実装計画

### Phase 1: 基本機能（Issues #25-#31）

#### 1. プロンプトテンプレートの基本構造を実装 [#25](https://github.com/yuanying/ygents/issues/25)
- `src/ygents/prompts/__init__.py`
- `src/ygents/prompts/templates.py`
- `PromptTemplate`プロトコルと`PromptType`列挙型の定義

#### 2. デフォルトプロンプトテンプレートを実装 [#26](https://github.com/yuanying/ygents/issues/26)
- `DefaultPrompt`クラスの実装
- `PROMPT_TEMPLATES`レジストリの基本構造

#### 3. ReActプロンプトテンプレートを実装 [#27](https://github.com/yuanying/ygents/issues/27)
- `ReActPrompt`クラスの実装
- `PROMPT_TEMPLATES`への追加

#### 4. SystemPromptConfig設定モデルを実装 [#28](https://github.com/yuanying/ygents/issues/28)
- `src/ygents/config/models.py`の`SystemPromptConfig`クラス追加
- Pydanticバリデーションの実装

#### 5. YgentsConfigにsystem_promptフィールドを追加 [#29](https://github.com/yuanying/ygents/issues/29)
- `YgentsConfig`クラスの`system_prompt`フィールド追加
- 既存設定との互換性確保

#### 5.5. ConfigLoaderでの設定検証・解決機能を実装 [#43](https://github.com/yuanying/ygents/issues/43) ✅ **完了**
- `ConfigLoader`での`_validate_system_prompt_config`メソッド実装
- `ConfigLoader`での`_resolve_system_prompt`メソッド実装  
- `_apply_template_variables`メソッドでの変数置換機能
- 設定ファイル読み込み時のプロンプトタイプ検証
- 存在しないプロンプトタイプの早期エラー検出
- SystemPromptConfigに`resolved_prompt`フィールド追加

#### 6. Agentクラスにシステムプロンプト注入機能を実装 [#30](https://github.com/yuanying/ygents/issues/30)
- `Agent.__init__`での`_setup_system_prompt`メソッド呼び出し
- `_setup_system_prompt`メソッドの実装（ConfigLoaderで解決済みプロンプトを使用）
- Issue #31, #32の機能をConfigLoaderに統合したため、Agentクラス側は簡素化

### Phase 2: 拡張機能（Issues #32-#34）

#### 8. テンプレート変数システムを実装 [#32](https://github.com/yuanying/ygents/issues/32) ✅ **ConfigLoaderに統合済み**
- `_apply_template_variables`メソッドの実装（ConfigLoader内）
- 変数置換機能の実装

#### 9. カスタムプロンプト機能を実装 [#33](https://github.com/yuanying/ygents/issues/33) ✅ **ConfigLoaderに統合済み**
- `custom_prompt`設定の処理ロジック（`_resolve_system_prompt`内）
- プロンプトタイプより優先されるロジック

#### 10. システムプロンプト機能のテストを実装 [#34](https://github.com/yuanying/ygents/issues/34)
- `tests/test_prompts/test_templates.py`
- `tests/test_config/test_models.py`の拡張
- `tests/test_agent/test_core.py`の拡張

### Phase 3: 完成・文書化（Issues #35-#36）

#### 11. 利用例とサンプル設定を追加 [#35](https://github.com/yuanying/ygents/issues/35)
- `examples/`にプロンプト使用例を追加
- 設定ファイル例の更新

#### 12. システムプロンプト機能のドキュメントを更新 [#36](https://github.com/yuanying/ygents/issues/36)
- `README.md`の機能説明更新
- `CLAUDE.md`の設定例更新

## テスト戦略

### 1. 単体テスト
- プロンプトテンプレートの正常な読み込み ✅ **実装済み**
- システムプロンプト設定の検証と解決 ✅ **実装済み**
- テンプレート変数の正しい置換 ✅ **実装済み**
- カスタムプロンプトの変数置換 ✅ **実装済み**
- 設定ファイルの正しい解析 ✅ **実装済み**
- 設定読み込み時のプロンプトタイプ検証 ✅ **実装済み**
- resolved_promptフィールドの動作 ✅ **実装済み**

### 2. 統合テスト
- Agentクラスでのシステムプロンプト動作
- 異なるプロンプトタイプでの動作確認
- MCPツールとの連携動作

### 3. E2Eテスト
- 設定ファイルからエージェント実行まで
- ReActパターンでの問題解決フロー
- カスタムプロンプトでの動作確認

## 利用例

### 1. ReActエージェントとして使用

```python
config = YgentsConfig(
    litellm={"model": "openai/gpt-4o", "api_key": "your-key"},
    system_prompt={
        "type": "react",
        "variables": {
            "domain": "データ分析"
        }
    }
)

async with Agent(config) as agent:
    async for item in agent.run("売上データを分析してください"):
        print(item)
```

### 2. カスタムプロンプトの使用

```python
config = YgentsConfig(
    litellm={"model": "openai/gpt-4o", "api_key": "your-key"},
    system_prompt={
        "custom_prompt": "あなたは{role}として、{task}を実行してください。",
        "variables": {
            "role": "データサイエンティスト",
            "task": "統計分析とレポート作成"
        }
    }
)
```

## 設計変更履歴

### 2024-12-19: ConfigLoaderでの統合実装 (Issue #43)

**変更概要:**
- システムプロンプトの解決処理をAgentクラスからConfigLoaderに移動
- ConfigLoaderで設定ファイル読み込み時に検証と解決を実行
- SystemPromptConfigに`resolved_prompt`フィールドを追加

**利点:**
1. **早期検証**: 設定ファイル読み込み時に無効なプロンプトタイプを検出
2. **パフォーマンス向上**: プロンプト解決を1回だけ実行
3. **責任の分離**: 設定の処理はConfigLoader、利用はAgentクラス
4. **テスタビリティ**: ConfigLoader単体でのテストが容易

**影響範囲:**
- Issue #31, #32の機能がConfigLoaderに統合
- Agentクラスの実装が大幅に簡素化
- resolved_promptフィールドによる解決済み状態の明確化

## 拡張性の考慮

### 1. 新しいプロンプトタイプの追加
- `src/ygents/prompts/templates.py`に新しいクラスを追加
- `PROMPT_TEMPLATES`に登録
- 必要に応じてテンプレート変数を定義

### 2. 外部プロンプトテンプレート
- プラグインシステムでの外部テンプレート読み込み
- GitHubなどからのテンプレート取得機能
- コミュニティベースのテンプレート共有

### 3. 動的プロンプト調整
- 実行時のプロンプト調整機能
- 対話履歴に基づくプロンプト最適化
- A/Bテストによるプロンプト効果測定

## セキュリティ考慮事項

1. **テンプレート変数の検証**: 悪意のある変数値の注入を防ぐ
2. **プロンプトサイズ制限**: 過度に大きなプロンプトによるリソース消費を防ぐ
3. **外部テンプレートの検証**: 外部からのテンプレート読み込み時の安全性確保
4. **設定ファイルの検証**: 不正な設定値による動作異常を防ぐ

## 今後の発展

1. **Multi-Modal対応**: 画像や音声を含むプロンプトテンプレート
2. **動的スキーマ**: プロンプトに応じたツールスキーマの自動調整
3. **学習機能**: 利用パターンに基づくプロンプト最適化
4. **プロンプトエンジニアリング支援**: 効果的なプロンプト作成支援ツール