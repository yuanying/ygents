"""Configuration loader."""

import os
from pathlib import Path
from typing import Any, Dict

import yaml
from pydantic import ValidationError

from ..prompts.templates import PROMPT_TEMPLATES
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

        # Validate and resolve system prompt configuration
        self._validate_system_prompt_config(normalized_dict)
        normalized_dict = self._resolve_system_prompt(normalized_dict)

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
                normalized["mcp_servers"] = value  # Keep as raw dict
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

        # Handle API key override based on model name
        if "litellm" in config and "model" in config["litellm"]:
            model_name = config["litellm"]["model"]

            if model_name.startswith("openai"):
                openai_key = os.getenv("OPENAI_API_KEY")
                if openai_key:
                    config["litellm"]["api_key"] = openai_key
            elif model_name.startswith("anthropic"):
                claude_key = os.getenv("ANTHROPIC_API_KEY")
                if claude_key:
                    config["litellm"]["api_key"] = claude_key
        else:
            # Fallback: try both keys if no model specified
            openai_key = os.getenv("OPENAI_API_KEY")
            claude_key = os.getenv("ANTHROPIC_API_KEY")

            if openai_key:
                if "litellm" not in config:
                    config["litellm"] = {}
                config["litellm"]["api_key"] = openai_key
            elif claude_key:
                if "litellm" not in config:
                    config["litellm"] = {}
                config["litellm"]["api_key"] = claude_key

        return config

    def _validate_system_prompt_config(self, config_dict: Dict[str, Any]) -> None:
        """Validate system prompt configuration.

        Args:
            config_dict: Configuration dictionary

        Raises:
            ValueError: If system prompt configuration is invalid
        """
        if "system_prompt" not in config_dict:
            return

        system_prompt = config_dict["system_prompt"]
        if not isinstance(system_prompt, dict):
            return

        # Validate prompt type
        prompt_type = system_prompt.get("type", "default")
        if prompt_type not in PROMPT_TEMPLATES:
            available_types = list(PROMPT_TEMPLATES.keys())
            raise ValueError(
                f"Invalid prompt type '{prompt_type}'. "
                f"Available types: {available_types}"
            )

    def _resolve_system_prompt(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve system prompt template and variables.

        Args:
            config_dict: Configuration dictionary

        Returns:
            Configuration dictionary with resolved system prompt
        """
        if "system_prompt" not in config_dict:
            return config_dict

        system_prompt = config_dict["system_prompt"]
        if not isinstance(system_prompt, dict):
            return config_dict

        # Create a copy to avoid modifying the original
        config = dict(config_dict)
        resolved_prompt = dict(system_prompt)

        # If custom_prompt is specified, use it with variable substitution
        if "custom_prompt" in resolved_prompt and resolved_prompt["custom_prompt"]:
            prompt_text = resolved_prompt["custom_prompt"]
            variables = resolved_prompt.get("variables", {})
            resolved_prompt["resolved_prompt"] = self._apply_template_variables(
                prompt_text, variables
            )
        else:
            # Use template-based prompt
            prompt_type = resolved_prompt.get("type", "default")
            if prompt_type in PROMPT_TEMPLATES:
                template = PROMPT_TEMPLATES[prompt_type]
                variables = resolved_prompt.get("variables", {})
                resolved_prompt["resolved_prompt"] = self._apply_template_variables(
                    template.system_prompt, variables
                )

        config["system_prompt"] = resolved_prompt
        return config

    def _apply_template_variables(
        self, template: str, variables: Dict[str, str]
    ) -> str:
        """Apply template variables to a prompt template.

        Args:
            template: Template string with {variable} placeholders
            variables: Dictionary of variable name to value mappings

        Returns:
            Template with variables substituted
        """
        result = template
        for key, value in variables.items():
            result = result.replace(f"{{{key}}}", value)
        return result
