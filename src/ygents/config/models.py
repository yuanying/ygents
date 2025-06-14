"""Configuration data models."""

from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field, model_validator


class OpenAIConfig(BaseModel):
    """OpenAI configuration."""

    api_key: str
    model: str = "gpt-3.5-turbo"


class ClaudeConfig(BaseModel):
    """Claude configuration."""

    api_key: str
    model: str = "claude-3-sonnet-20240229"


class LLMConfig(BaseModel):
    """LLM configuration."""

    provider: Literal["openai", "claude"]
    openai: Optional[OpenAIConfig] = None
    claude: Optional[ClaudeConfig] = None

    @model_validator(mode="after")
    def validate_provider_config(self) -> "LLMConfig":
        """Validate that provider configuration is present."""
        if self.provider == "openai" and self.openai is None:
            raise ValueError("Provider configuration is required for OpenAI")
        if self.provider == "claude" and self.claude is None:
            raise ValueError("Provider configuration is required for Claude")
        return self


class YgentsConfig(BaseModel):
    """Main ygents configuration."""

    mcp_servers: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    llm: LLMConfig
