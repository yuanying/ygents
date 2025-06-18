# システムプロンプト管理設計書

## 概要

Agentクラスに対してシステムプロンプトを指定できる機能を提供します。設定ファイルでプロンプトの種類を選択し、将来的にはReActエージェントなど異なるエージェントタイプを切り替えられるようにします。

## 設計目標

1. **システムプロンプトの注入**: Agent起動時にシステムプロンプトを指定可能
2. **プロンプトテンプレート管理**: 事前定義されたプロンプトテンプレートの管理
3. **設定による選択**: 設定ファイルでプロンプトタイプを選択
4. **拡張性**: 新しいエージェントタイプの追加が容易
5. **後方互換性**: 既存のAgentクラスとの互換性維持

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
```

### 3. Agentクラスの拡張

```python
# src/ygents/agent/core.py
from ..prompts.templates import PROMPT_TEMPLATES
from ..config.models import YgentsConfig, SystemPromptConfig

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
            
        system_prompt = self._get_system_prompt()
        if system_prompt:
            # システムメッセージをメッセージリストの最初に追加
            self.messages.insert(0, Message(role="system", content=system_prompt))
    
    def _get_system_prompt(self) -> Optional[str]:
        """設定からシステムプロンプトを取得"""
        if not self.config.system_prompt:
            return None
            
        # カスタムプロンプトが指定されている場合はそれを使用
        if self.config.system_prompt.custom_prompt:
            return self._apply_template_variables(
                self.config.system_prompt.custom_prompt,
                self.config.system_prompt.variables
            )
        
        # プロンプトタイプから取得
        prompt_type = self.config.system_prompt.type
        if prompt_type in PROMPT_TEMPLATES:
            template = PROMPT_TEMPLATES[prompt_type]
            return self._apply_template_variables(
                template.system_prompt,
                self.config.system_prompt.variables
            )
        
        return None
    
    def _apply_template_variables(self, template: str, variables: Dict[str, str]) -> str:
        """テンプレート変数を適用"""
        result = template
        for key, value in variables.items():
            result = result.replace(f"{{{key}}}", value)
        return result
```

### 4. 設定ファイル例

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

## 実装フェーズ

### Phase 1: 基本機能
- [ ] プロンプトテンプレートシステムの実装
- [ ] YgentsConfigへのsystem_prompt設定追加
- [ ] Agentクラスでのシステムプロンプト注入機能
- [ ] 基本的なテンプレート（default, react）の実装

### Phase 2: 拡張機能
- [ ] テンプレート変数システムの実装
- [ ] 設定ファイルでの変数指定機能
- [ ] カスタムプロンプト機能
- [ ] プロンプトテンプレートの動的読み込み

### Phase 3: 高度な機能
- [ ] 外部ファイルからのプロンプトテンプレート読み込み
- [ ] プロンプトテンプレートの検証機能
- [ ] 複数のプロンプトテンプレートの組み合わせ
- [ ] プロンプトテンプレートのバージョン管理

## テスト戦略

### 1. 単体テスト
- プロンプトテンプレートの正常な読み込み
- システムプロンプトの正しい注入
- テンプレート変数の正しい置換
- 設定ファイルの正しい解析

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