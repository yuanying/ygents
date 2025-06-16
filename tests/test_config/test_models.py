"""Configuration models tests."""

from ygents.config.models import YgentsConfig


class TestYgentsConfig:
    """Test cases for YgentsConfig."""

    def test_ygents_config_minimal(self):
        """Test minimal Ygents config."""
        config = YgentsConfig()
        assert config.mcp_servers == {}
        assert config.litellm == {}

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
