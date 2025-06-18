"""Prompt templates module."""

from enum import Enum
from typing import Dict, Protocol


class PromptTemplate(Protocol):
    """プロンプトテンプレートのインターフェース."""

    name: str
    description: str
    system_prompt: str


class PromptType(Enum):
    """利用可能なプロンプトタイプ."""

    DEFAULT = "default"


class DefaultPrompt:
    """標準的な問題解決エージェント用のプロンプトテンプレート."""

    name = "default"
    description = "標準的な問題解決エージェント"
    system_prompt = """あなたは問題解決を支援するAIエージェントです。
ユーザーの要求を理解し、適切なツールを使用して問題を解決してください。

以下の点に注意して行動してください：
- ユーザーの質問や依頼を正確に理解する
- 利用可能なツールを適切に選択して実行する
- 結果を分析してユーザーに有用な情報を提供する
- 不明な点があれば遠慮なく質問する"""


# プロンプトテンプレートレジストリ
PROMPT_TEMPLATES: Dict[str, PromptTemplate] = {
    PromptType.DEFAULT.value: DefaultPrompt(),
}
