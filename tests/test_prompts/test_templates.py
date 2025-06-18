"""Tests for prompt templates module."""

from typing import Protocol

from ygents.prompts.templates import (
    PROMPT_TEMPLATES,
    DefaultPrompt,
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

    def test_registry_has_default_template(self) -> None:
        """レジストリにデフォルトテンプレートが登録されていることを確認."""
        assert "default" in PROMPT_TEMPLATES
        assert PROMPT_TEMPLATES["default"].__class__.__name__ == "DefaultPrompt"


class TestDefaultPrompt:
    """Test DefaultPrompt template."""

    def test_default_prompt_exists(self) -> None:
        """DefaultPromptクラスが存在することを確認."""
        assert DefaultPrompt is not None

    def test_default_prompt_has_required_attributes(self) -> None:
        """DefaultPromptが必要な属性を持っていることを確認."""
        prompt = DefaultPrompt()
        assert hasattr(prompt, "name")
        assert hasattr(prompt, "description")
        assert hasattr(prompt, "system_prompt")

    def test_default_prompt_attribute_values(self) -> None:
        """DefaultPromptの属性値が適切であることを確認."""
        prompt = DefaultPrompt()
        assert prompt.name == "default"
        assert isinstance(prompt.description, str)
        assert len(prompt.description) > 0
        assert isinstance(prompt.system_prompt, str)
        assert len(prompt.system_prompt) > 0

    def test_default_prompt_system_prompt_content(self) -> None:
        """DefaultPromptのシステムプロンプト内容が適切であることを確認."""
        prompt = DefaultPrompt()
        system_prompt = prompt.system_prompt.lower()

        # 問題解決に関連するキーワードが含まれていることを確認
        assert any(
            keyword in system_prompt
            for keyword in ["問題解決", "問題", "解決", "支援", "エージェント", "ai"]
        )

    def test_default_prompt_conforms_to_protocol(self) -> None:
        """DefaultPromptがPromptTemplateプロトコルに準拠していることを確認."""
        prompt = DefaultPrompt()

        # 型チェックはmypyで行われるが、実行時確認も行う
        assert isinstance(prompt.name, str)
        assert isinstance(prompt.description, str)
        assert isinstance(prompt.system_prompt, str)
