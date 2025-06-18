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


# プロンプトテンプレートレジストリ
PROMPT_TEMPLATES: Dict[str, PromptTemplate] = {}
