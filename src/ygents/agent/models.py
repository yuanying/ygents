"""Agent models."""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Message:
    """Simplified message representation."""

    role: str
    content: str = ""
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    tool_call_id: str = ""
    name: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API calls."""
        result: Dict[str, Any] = {"role": self.role}
        # Always include content for assistant/user/system roles
        if self.role in ["assistant", "user", "system"]:
            result["content"] = self.content if self.content else ""
        elif self.content:  # For tool role, only include if not empty
            result["content"] = self.content
        if self.tool_calls:
            result["tool_calls"] = self.tool_calls
        if self.tool_call_id:
            result["tool_call_id"] = self.tool_call_id
        if self.name:
            result["name"] = self.name
        return result
