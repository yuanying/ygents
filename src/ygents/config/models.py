"""Configuration data models."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class SystemPromptConfig(BaseModel):
    """システムプロンプト設定."""

    # プロンプトタイプの指定
    type: str = Field(
        default="default",
        description="プロンプトタイプ (default, react, analytical, etc.)",
    )

    # カスタムプロンプト（typeより優先）
    custom_prompt: Optional[str] = Field(
        default=None, description="カスタムシステムプロンプト"
    )

    # プロンプト変数（テンプレート内で使用）
    variables: Dict[str, str] = Field(
        default_factory=dict, description="プロンプトテンプレート内で使用される変数"
    )

    # 解決済みプロンプト（ConfigLoaderで自動設定）
    resolved_prompt: Optional[str] = Field(
        default=None,
        description="テンプレートと変数を解決した最終的なシステムプロンプト",
    )


class YgentsConfig(BaseModel):
    """Main ygents configuration."""

    mcp_servers: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    litellm: Dict[str, Any] = Field(default_factory=dict)

    # システムプロンプト設定
    system_prompt: Optional[SystemPromptConfig] = Field(
        default=None, description="システムプロンプトの設定"
    )
