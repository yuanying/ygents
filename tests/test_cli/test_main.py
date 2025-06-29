"""CLI main tests."""

import tempfile
from pathlib import Path

from typer.testing import CliRunner

from ygents.cli.main import app


class TestCLIMain:
    """Test cases for CLI main application."""

    def setup_method(self):
        """Setup test fixtures."""
        self.runner = CliRunner()

    def test_app_exists(self):
        """Test that the main CLI app exists."""
        assert app is not None

    def test_help_command(self):
        """Test CLI help command."""
        result = self.runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "ygents" in result.output.lower()
        assert "Usage:" in result.output

    def test_version_command(self):
        """Test version command."""
        result = self.runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert any(char.isdigit() for char in result.output)

    def test_run_command_help(self):
        """Test run command help."""
        result = self.runner.invoke(app, ["run", "--help"])
        assert result.exit_code == 0
        assert "query" in result.output.lower()

    def test_interactive_command_help(self):
        """Test interactive command help."""
        result = self.runner.invoke(app, ["interactive", "--help"])
        assert result.exit_code == 0
        assert "interactive" in result.output.lower()

    def test_config_info_command_help(self):
        """Test config-info command help."""
        result = self.runner.invoke(app, ["config-info", "--help"])
        assert result.exit_code == 0
        assert "configuration" in result.output.lower()

    def test_config_info_with_default_config(self):
        """Test config-info command with default configuration."""
        result = self.runner.invoke(app, ["config-info"])
        assert result.exit_code == 0
        assert "Configuration Info" in result.output
        assert "openai/gpt-3.5-turbo" in result.output

    def test_config_info_with_yaml_config(self):
        """Test config-info command with YAML configuration."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(
                """
litellm:
  model: "openai/gpt-4"
  api_key: "test-key"
system_prompt:
  type: "default"
  variables:
    domain: "テスト"
"""
            )
            config_path = f.name

        try:
            result = self.runner.invoke(app, ["config-info", "--config", config_path])
            assert result.exit_code == 0
            assert "Configuration Info" in result.output
            assert "openai/gpt-4" in result.output
            assert "Configured" in result.output
        finally:
            Path(config_path).unlink()

    def test_run_command_without_query_starts_interactive(self):
        """Test run command without query starts interactive mode."""
        # Use Ctrl+C to exit immediately
        result = self.runner.invoke(app, ["run"], input="\x03")
        # Should exit with code 0 (successful interactive mode exit)
        assert result.exit_code == 0
        assert "Interactive Mode" in result.output
        assert "Welcome" in result.output

    def test_run_command_with_query_parameter(self):
        """Test run command with query parameter works normally."""
        # This test will fail due to missing API keys, but should show the query is processed
        result = self.runner.invoke(app, ["run", "--query", "test query"])
        # The command should attempt to process the query (though it may fail due to missing API keys)
        # We're just checking that it doesn't start interactive mode
        assert "Interactive Mode" not in result.output
        assert "Welcome" not in result.output

    def test_config_info_with_nonexistent_config(self):
        """Test config-info command with non-existent config file."""
        result = self.runner.invoke(
            app, ["config-info", "--config", "/nonexistent/config.yaml"]
        )
        assert result.exit_code == 1
        assert "not found" in result.output.lower() or "error" in result.output.lower()

    def test_config_info_with_invalid_yaml(self):
        """Test config-info command with invalid YAML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content:")
            config_path = f.name

        try:
            result = self.runner.invoke(app, ["config-info", "--config", config_path])
            assert result.exit_code == 1
            assert "error" in result.output.lower() or "failed" in result.output.lower()
        finally:
            Path(config_path).unlink()
