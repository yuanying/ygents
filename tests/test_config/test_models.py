"""Configuration models tests."""

from ygents.config.models import SystemPromptConfig, YgentsConfig


class TestYgentsConfig:
    """Test cases for YgentsConfig."""

    def test_ygents_config_minimal(self):
        """Test minimal Ygents config."""
        config = YgentsConfig()
        assert config.mcp_servers == {}
        assert config.litellm == {}
        assert config.system_prompt is None

    def test_ygents_config_with_litellm(self):
        """Test Ygents config with litellm configuration."""
        config = YgentsConfig(
            litellm={
                "model": "gpt-3.5-turbo",
                "api_key": "test-key",
                "temperature": 0.7,
            }
        )
        assert config.litellm["model"] == "gpt-3.5-turbo"
        assert config.litellm["api_key"] == "test-key"
        assert config.litellm["temperature"] == 0.7

    def test_ygents_config_with_mcp_servers(self):
        """Test Ygents config with MCP servers (raw dict format)."""
        config = YgentsConfig(
            mcp_servers={
                "weather": {"url": "https://weather.example.com"},
                "assistant": {"command": "python", "args": ["server.py"]},
            },
            litellm={"model": "claude-3-sonnet-20240229", "api_key": "test-key"},
        )
        assert len(config.mcp_servers) == 2
        assert config.mcp_servers["weather"]["url"] == "https://weather.example.com"
        assert config.mcp_servers["assistant"]["command"] == "python"
        assert config.litellm["model"] == "claude-3-sonnet-20240229"

    def test_ygents_config_with_system_prompt(self):
        """Test YgentsConfig with system prompt configuration."""
        system_prompt_config = SystemPromptConfig(type="react")
        config = YgentsConfig(
            litellm={"model": "openai/gpt-4o", "api_key": "test-key"},
            system_prompt=system_prompt_config,
        )
        assert config.system_prompt is not None
        assert config.system_prompt.type == "react"
        assert config.system_prompt.custom_prompt is None
        assert config.system_prompt.variables == {}

    def test_ygents_config_with_system_prompt_dict(self):
        """Test YgentsConfig with system prompt as dict."""
        config = YgentsConfig(
            system_prompt={
                "type": "custom",
                "custom_prompt": "あなたは{role}です。",
                "variables": {"role": "エンジニア"},
            }
        )
        assert config.system_prompt is not None
        assert config.system_prompt.type == "custom"
        assert config.system_prompt.custom_prompt == "あなたは{role}です。"
        assert config.system_prompt.variables == {"role": "エンジニア"}

    def test_ygents_config_full_configuration(self):
        """Test YgentsConfig with all fields including system_prompt."""
        config = YgentsConfig(
            mcp_servers={"weather": {"url": "https://weather.example.com"}},
            litellm={"model": "openai/gpt-4o", "api_key": "test-key"},
            system_prompt={"type": "react", "variables": {"domain": "データ分析"}},
        )
        assert len(config.mcp_servers) == 1
        assert config.litellm["model"] == "openai/gpt-4o"
        assert config.system_prompt is not None
        assert config.system_prompt.type == "react"
        assert config.system_prompt.variables == {"domain": "データ分析"}

    def test_ygents_config_backward_compatibility(self):
        """Test that existing configurations without system_prompt still work."""
        config = YgentsConfig(
            mcp_servers={"test": {"url": "https://test.example.com"}},
            litellm={"model": "openai/gpt-3.5-turbo"},
        )
        assert config.mcp_servers["test"]["url"] == "https://test.example.com"
        assert config.litellm["model"] == "openai/gpt-3.5-turbo"
        assert config.system_prompt is None  # デフォルトはNone


class TestSystemPromptConfig:
    """Test cases for SystemPromptConfig."""

    def test_system_prompt_config_minimal(self):
        """Test minimal SystemPromptConfig with defaults."""
        config = SystemPromptConfig()
        assert config.type == "default"
        assert config.custom_prompt is None
        assert config.variables == {}
        assert config.resolved_prompt is None

    def test_system_prompt_config_with_type(self):
        """Test SystemPromptConfig with specific type."""
        config = SystemPromptConfig(type="react")
        assert config.type == "react"
        assert config.custom_prompt is None
        assert config.variables == {}
        assert config.resolved_prompt is None

    def test_system_prompt_config_with_custom_prompt(self):
        """Test SystemPromptConfig with custom prompt."""
        custom_prompt = "あなたは{role}として、{task}を実行してください。"
        config = SystemPromptConfig(custom_prompt=custom_prompt)
        assert config.type == "default"  # デフォルト値
        assert config.custom_prompt == custom_prompt
        assert config.variables == {}

    def test_system_prompt_config_with_variables(self):
        """Test SystemPromptConfig with template variables."""
        variables = {"domain": "データ分析", "expertise_level": "上級"}
        config = SystemPromptConfig(type="react", variables=variables)
        assert config.type == "react"
        assert config.custom_prompt is None
        assert config.variables == variables

    def test_system_prompt_config_full(self):
        """Test SystemPromptConfig with all fields."""
        custom_prompt = "あなたは{role}として、{task}を実行してください。"
        variables = {"role": "データサイエンティスト", "task": "統計分析"}
        config = SystemPromptConfig(
            type="custom", custom_prompt=custom_prompt, variables=variables
        )
        assert config.type == "custom"
        assert config.custom_prompt == custom_prompt
        assert config.variables == variables

    def test_system_prompt_config_empty_variables(self):
        """Test SystemPromptConfig with explicitly empty variables."""
        config = SystemPromptConfig(type="react", variables={})
        assert config.type == "react"
        assert config.variables == {}

    def test_system_prompt_config_field_types(self):
        """Test SystemPromptConfig field types."""
        config = SystemPromptConfig(
            type="test", custom_prompt="test prompt", variables={"key": "value"}
        )
        assert isinstance(config.type, str)
        assert isinstance(config.custom_prompt, str)
        assert isinstance(config.variables, dict)
        assert isinstance(config.variables["key"], str)

    def test_system_prompt_config_with_resolved_prompt(self):
        """Test SystemPromptConfig with resolved prompt."""
        config = SystemPromptConfig(
            type="custom",
            custom_prompt="あなたは{role}です。",
            resolved_prompt="あなたはエンジニアです。",
        )
        assert config.type == "custom"
        assert config.custom_prompt == "あなたは{role}です。"
        assert config.resolved_prompt == "あなたはエンジニアです。"
