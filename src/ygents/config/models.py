"""Configuration data models."""

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


class MCPServerConfig(BaseModel):
    """MCP server configuration."""

    url: Optional[str] = None
    command: Optional[str] = None
    args: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_url_or_command(self) -> "MCPServerConfig":
        """Validate that either URL or command is specified, but not both."""
        if self.url is not None and self.command is not None:
            raise ValueError("Either url or command must be specified")
        if self.url is None and self.command is None:
            raise ValueError("Either url or command must be specified")
        return self


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

    mcp_servers: Dict[str, MCPServerConfig] = Field(default_factory=dict)
    llm: LLMConfig
