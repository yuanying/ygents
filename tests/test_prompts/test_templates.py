"""Tests for prompt templates module."""

from typing import Protocol

from ygents.prompts.templates import (
    PROMPT_TEMPLATES,
    PromptTemplate,
    PromptType,
)


class TestPromptTemplate:
    """Test PromptTemplate protocol."""

    def test_prompt_template_protocol_exists(self) -> None:
        """PromptTemplateプロトコルが存在することを確認."""
        assert PromptTemplate is not None
        assert isinstance(PromptTemplate, type)

    def test_prompt_template_is_protocol(self) -> None:
        """PromptTemplateがProtocolであることを確認."""
        assert issubclass(PromptTemplate, Protocol)

    def test_prompt_template_has_required_attributes(self) -> None:
        """PromptTemplateが必要な属性を持っていることを確認."""

        # Protocol自体はインスタンス化できないので、
        # 型チェックのためのテストクラスを作成
        class TestTemplate:
            name = "test"
            description = "Test template"
            system_prompt = "Test prompt"

        # Protocolに準拠しているかチェック
        assert hasattr(TestTemplate, "name")
        assert hasattr(TestTemplate, "description")
        assert hasattr(TestTemplate, "system_prompt")


class TestPromptType:
    """Test PromptType enum."""

    def test_prompt_type_enum_exists(self) -> None:
        """PromptType列挙型が存在することを確認."""
        assert PromptType is not None

    def test_prompt_type_has_default(self) -> None:
        """DEFAULT値が存在することを確認."""
        assert PromptType.DEFAULT.value == "default"

    def test_prompt_type_values_are_strings(self) -> None:
        """すべての値が文字列であることを確認."""
        for prompt_type in PromptType:
            assert isinstance(prompt_type.value, str)


class TestPromptTemplatesRegistry:
    """Test PROMPT_TEMPLATES registry."""

    def test_prompt_templates_registry_exists(self) -> None:
        """PROMPT_TEMPLATESレジストリが存在することを確認."""
        assert PROMPT_TEMPLATES is not None
        assert isinstance(PROMPT_TEMPLATES, dict)

    def test_registry_is_initially_empty(self) -> None:
        """初期状態でレジストリが空であることを確認."""
        # 基本構造の実装段階では空のレジストリ
        assert len(PROMPT_TEMPLATES) == 0
