"""Agent exceptions."""


class AgentError(Exception):
    """Base agent exception."""
    pass


class AgentConnectionError(AgentError):
    """Agent connection error."""
    pass
