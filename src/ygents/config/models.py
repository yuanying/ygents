"""Configuration data models."""

from typing import Any, Dict

from pydantic import BaseModel, Field


class YgentsConfig(BaseModel):
    """Main ygents configuration."""

    mcp_servers: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    litellm: Dict[str, Any] = Field(default_factory=dict)
