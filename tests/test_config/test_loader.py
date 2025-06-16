"""Configuration loader tests."""

import os

import pytest

from ygents.config.loader import ConfigLoader
from ygents.config.models import YgentsConfig


class TestConfigLoader:
    """Test cases for ConfigLoader."""

    def test_load_yaml_config_basic(self, temp_dir, clean_env):
        """Test basic YAML config file loading."""
        config_file = temp_dir / "config.yaml"
        config_content = """
mcpServers:
  weather:
    url: "https://weather-api.example.com/mcp"
  assistant:
    command: "python"
    args: ["./assistant_server.py"]

litellm:
  model: "openai/gpt-3.5-turbo"
  api_key: "test-openai-key"
"""
        config_file.write_text(config_content)

        loader = ConfigLoader()
        config = loader.load_from_file(str(config_file))

        assert isinstance(config, YgentsConfig)
        assert len(config.mcp_servers) == 2
        assert (
            config.mcp_servers["weather"]["url"]
            == "https://weather-api.example.com/mcp"
        )
        assert config.mcp_servers["assistant"]["command"] == "python"
        assert config.litellm["model"] == "openai/gpt-3.5-turbo"
        assert config.litellm["api_key"] == "test-openai-key"

    def test_load_yaml_config_with_environment_override(self, temp_dir):
        """Test YAML config with environment variable override."""
        config_file = temp_dir / "config.yaml"
        config_content = """
litellm:
  model: "openai/gpt-3.5-turbo"
  api_key: "placeholder"
"""
        config_file.write_text(config_content)

        # Set environment variable
        os.environ["OPENAI_API_KEY"] = "env-openai-key"

        try:
            loader = ConfigLoader()
            config = loader.load_from_file(str(config_file))

            # Environment variable should override YAML value
            assert config.litellm["api_key"] == "env-openai-key"
        finally:
            # Clean up environment variable
            os.environ.pop("OPENAI_API_KEY", None)

    def test_load_yaml_config_claude_provider(self, temp_dir, clean_env):
        """Test YAML config with Claude provider."""
        config_file = temp_dir / "config.yaml"
        config_content = """
litellm:
  model: "anthropic/claude-3-sonnet-20240229"
  api_key: "test-claude-key"
"""
        config_file.write_text(config_content)

        loader = ConfigLoader()
        config = loader.load_from_file(str(config_file))

        assert config.litellm["model"] == "anthropic/claude-3-sonnet-20240229"
        assert config.litellm["api_key"] == "test-claude-key"

    def test_config_validation_empty_config(self, temp_dir):
        """Test config validation with empty config (should not fail)."""
        config_file = temp_dir / "config.yaml"
        config_content = """
mcpServers:
  weather:
    url: "https://weather-api.example.com/mcp"
# litellm is optional now
"""
        config_file.write_text(config_content)

        loader = ConfigLoader()
        config = loader.load_from_file(str(config_file))
        # Environment variables may be applied, so just check it's not None
        assert isinstance(config.litellm, dict)

    def test_config_validation_invalid_litellm_config(self, temp_dir):
        """Test config validation with invalid litellm config."""
        config_file = temp_dir / "config.yaml"
        config_content = """
litellm:
  invalid_field: "invalid_value"
"""
        config_file.write_text(config_content)

        loader = ConfigLoader()
        # Should not fail - litellm accepts any dict
        config = loader.load_from_file(str(config_file))
        assert config.litellm["invalid_field"] == "invalid_value"

    def test_load_nonexistent_config_file(self):
        """Test loading non-existent config file raises appropriate error."""
        loader = ConfigLoader()
        with pytest.raises(FileNotFoundError):
            loader.load_from_file("/nonexistent/config.yaml")

    def test_load_invalid_yaml_syntax(self, temp_dir):
        """Test loading config file with invalid YAML syntax."""
        config_file = temp_dir / "config.yaml"
        config_content = """
invalid: yaml: content:
  - missing
    proper: indentation
"""
        config_file.write_text(config_content)

        loader = ConfigLoader()
        with pytest.raises(ValueError, match="Invalid YAML"):
            loader.load_from_file(str(config_file))

    def test_default_values_applied(self, temp_dir, clean_env):
        """Test that default values are properly applied."""
        config_file = temp_dir / "config.yaml"
        config_content = """
litellm:
  api_key: "test-key"
  # model not specified - should be handled by litellm
"""
        config_file.write_text(config_content)

        loader = ConfigLoader()
        config = loader.load_from_file(str(config_file))

        # Only api_key should be present
        assert config.litellm["api_key"] == "test-key"
        assert "model" not in config.litellm

    def test_load_from_dict(self, clean_env):
        """Test loading config from dictionary."""
        config_dict = {
            "mcpServers": {"test": {"command": "python", "args": ["test.py"]}},
            "litellm": {
                "model": "openai/gpt-4",
                "api_key": "test-key",
            },
        }

        loader = ConfigLoader()
        config = loader.load_from_dict(config_dict)

        assert isinstance(config, YgentsConfig)
        assert config.mcp_servers["test"]["command"] == "python"
        assert config.litellm["model"] == "openai/gpt-4"
