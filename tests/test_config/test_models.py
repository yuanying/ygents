"""Configuration models tests."""

import pytest
from pydantic import ValidationError

from ygents.config.models import (
    ClaudeConfig,
    LLMConfig,
    MCPServerConfig,
    OpenAIConfig,
    YgentsConfig,
)


class TestMCPServerConfig:
    """Test cases for MCPServerConfig."""

    def test_mcp_server_config_with_url(self):
        """Test MCP server config with URL."""
        config = MCPServerConfig(url="https://example.com/mcp")
        assert config.url == "https://example.com/mcp"
        assert config.command is None
        assert config.args == []

    def test_mcp_server_config_with_command(self):
        """Test MCP server config with command."""
        config = MCPServerConfig(command="python", args=["server.py", "--port", "8080"])
        assert config.command == "python"
        assert config.args == ["server.py", "--port", "8080"]
        assert config.url is None

    def test_mcp_server_config_validation_both_url_and_command(self):
        """Test validation error when both URL and command are provided."""
        with pytest.raises(
            ValidationError, match="Either url or command must be specified"
        ):
            MCPServerConfig(url="https://example.com/mcp", command="python")

    def test_mcp_server_config_validation_neither_url_nor_command(self):
        """Test validation error when neither URL nor command are provided."""
        with pytest.raises(
            ValidationError, match="Either url or command must be specified"
        ):
            MCPServerConfig()


class TestOpenAIConfig:
    """Test cases for OpenAIConfig."""

    def test_openai_config_basic(self):
        """Test basic OpenAI config."""
        config = OpenAIConfig(api_key="test-key")
        assert config.api_key == "test-key"
        assert config.model == "gpt-3.5-turbo"  # default value

    def test_openai_config_with_custom_model(self):
        """Test OpenAI config with custom model."""
        config = OpenAIConfig(api_key="test-key", model="gpt-4")
        assert config.api_key == "test-key"
        assert config.model == "gpt-4"

    def test_openai_config_validation_missing_api_key(self):
        """Test validation error when API key is missing."""
        with pytest.raises(ValidationError, match="api_key"):
            OpenAIConfig()


class TestClaudeConfig:
    """Test cases for ClaudeConfig."""

    def test_claude_config_basic(self):
        """Test basic Claude config."""
        config = ClaudeConfig(api_key="test-key")
        assert config.api_key == "test-key"
        assert config.model == "claude-3-sonnet-20240229"  # default value

    def test_claude_config_with_custom_model(self):
        """Test Claude config with custom model."""
        config = ClaudeConfig(api_key="test-key", model="claude-3-opus-20240229")
        assert config.api_key == "test-key"
        assert config.model == "claude-3-opus-20240229"

    def test_claude_config_validation_missing_api_key(self):
        """Test validation error when API key is missing."""
        with pytest.raises(ValidationError, match="api_key"):
            ClaudeConfig()


class TestLLMConfig:
    """Test cases for LLMConfig."""

    def test_llm_config_openai(self):
        """Test LLM config with OpenAI provider."""
        config = LLMConfig(provider="openai", openai=OpenAIConfig(api_key="test-key"))
        assert config.provider == "openai"
        assert config.openai.api_key == "test-key"
        assert config.claude is None

    def test_llm_config_claude(self):
        """Test LLM config with Claude provider."""
        config = LLMConfig(provider="claude", claude=ClaudeConfig(api_key="test-key"))
        assert config.provider == "claude"
        assert config.claude.api_key == "test-key"
        assert config.openai is None

    def test_llm_config_validation_invalid_provider(self):
        """Test validation error with invalid provider."""
        with pytest.raises(
            ValidationError, match="Input should be 'openai' or 'claude'"
        ):
            LLMConfig(provider="invalid")

    def test_llm_config_validation_missing_provider_config(self):
        """Test validation error when provider config is missing."""
        with pytest.raises(ValidationError, match="Provider configuration is required"):
            LLMConfig(provider="openai")


class TestYgentsConfig:
    """Test cases for YgentsConfig."""

    def test_ygents_config_minimal(self):
        """Test minimal Ygents config."""
        config = YgentsConfig(
            llm=LLMConfig(provider="openai", openai=OpenAIConfig(api_key="test-key"))
        )
        assert config.mcp_servers == {}
        assert config.llm.provider == "openai"

    def test_ygents_config_with_mcp_servers(self):
        """Test Ygents config with MCP servers."""
        config = YgentsConfig(
            mcp_servers={
                "weather": MCPServerConfig(url="https://weather.example.com"),
                "assistant": MCPServerConfig(command="python", args=["server.py"]),
            },
            llm=LLMConfig(provider="claude", claude=ClaudeConfig(api_key="test-key")),
        )
        assert len(config.mcp_servers) == 2
        assert config.mcp_servers["weather"].url == "https://weather.example.com"
        assert config.mcp_servers["assistant"].command == "python"
        assert config.llm.provider == "claude"

    def test_ygents_config_validation_missing_llm(self):
        """Test validation error when LLM config is missing."""
        with pytest.raises(ValidationError, match="llm"):
            YgentsConfig()
