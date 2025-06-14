"""Configuration loader."""

import os
from pathlib import Path
from typing import Any, Dict

import yaml
from pydantic import ValidationError

from .models import YgentsConfig


class ConfigLoader:
    """Configuration loader for ygents."""

    def load_from_file(self, config_path: str) -> YgentsConfig:
        """Load configuration from YAML file.

        Args:
            config_path: Path to the configuration file

        Returns:
            Parsed configuration

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid
        """
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                yaml_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML syntax: {e}") from e

        if yaml_data is None:
            yaml_data = {}

        return self.load_from_dict(yaml_data)

    def load_from_dict(self, config_dict: Dict[str, Any]) -> YgentsConfig:
        """Load configuration from dictionary.

        Args:
            config_dict: Configuration dictionary

        Returns:
            Parsed configuration

        Raises:
            ValueError: If config is invalid
        """
        # Convert to snake_case keys for pydantic
        normalized_dict = self._normalize_dict_keys(config_dict)

        # Apply environment variable overrides
        normalized_dict = self._apply_env_overrides(normalized_dict)

        try:
            return YgentsConfig(**normalized_dict)
        except ValidationError as e:
            raise ValueError(f"Configuration validation error: {e}") from e

    def _normalize_dict_keys(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert camelCase keys to snake_case for pydantic compatibility.

        Args:
            data: Original dictionary with potentially camelCase keys

        Returns:
            Dictionary with snake_case keys
        """
        normalized = {}

        for key, value in data.items():
            # Convert mcpServers to mcp_servers and keep as raw dict
            if key == "mcpServers":
                normalized["mcp_servers"] = value  # Keep as raw dict for FastMCP
            else:
                normalized[key] = value

        return normalized

    def _apply_env_overrides(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides to configuration.

        Args:
            config_dict: Original configuration dictionary

        Returns:
            Configuration dictionary with environment overrides applied
        """
        # Create a deep copy to avoid modifying the original
        config = dict(config_dict)

        # Handle OpenAI API key override
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            if "llm" not in config:
                config["llm"] = {}
            if "openai" not in config["llm"]:
                config["llm"]["openai"] = {}
            config["llm"]["openai"]["api_key"] = openai_key

        # Handle Claude API key override
        claude_key = os.getenv("ANTHROPIC_API_KEY")
        if claude_key:
            if "llm" not in config:
                config["llm"] = {}
            if "claude" not in config["llm"]:
                config["llm"]["claude"] = {}
            config["llm"]["claude"]["api_key"] = claude_key

        return config
