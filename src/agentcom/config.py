"""
Agent configuration management.

This module provides a centralized configuration context for agent metadata
that must be set by the application using the agentcom library.
"""
from typing import Optional, List
from dataclasses import dataclass, field


@dataclass
class AgentConfig:
    """
    Configuration for the agent.
    
    This class holds agent-level metadata that must be set by the application
    using the agentcom library. These values serve as defaults for endpoints
    and can be overridden per-endpoint if needed.
    
    Example:
    --------
    ```python
    from agentcom import config
    
    # Set configuration at application startup
    config.set_agent_config(
        agent_id="agent://inventory/worker-1",
        version="1.2.0",
        supported_transports=["http-json", "grpc"]
    )
    
    # Now endpoints will use these values as defaults
    register_capability_endpoint(app)
    register_session_endpoint(app)
    ```
    """
    agent_id: str = "agent://unknown"
    version: str = "0.0.0"
    supported_transports: List[str] = field(default_factory=lambda: ["http-json"])


# Global instance
_agent_config = AgentConfig()


def set_agent_config(
    agent_id: Optional[str] = None,
    version: Optional[str] = None,
    supported_transports: Optional[List[str]] = None,
) -> None:
    """
    Set the global agent configuration.
    
    Call this function at application startup to configure agent metadata.
    
    Parameters:
    -----------
    agent_id : Optional[str]
        Unique identifier for the agent (e.g., "agent://inventory/worker-1").
    version : Optional[str]
        Agent version (e.g., "1.2.0").
    supported_transports : Optional[List[str]]
        List of supported transport protocols (e.g., ["http-json", "grpc"]).
    
    Example:
    --------
    ```python
    from agentcom.config import set_agent_config
    
    set_agent_config(
        agent_id="agent://planner/main",
        version="2.1.0",
        supported_transports=["http-json", "grpc", "nats"]
    )
    ```
    """
    global _agent_config
    if agent_id is not None:
        _agent_config.agent_id = agent_id
    if version is not None:
        _agent_config.version = version
    if supported_transports is not None:
        _agent_config.supported_transports = supported_transports


def get_agent_config() -> AgentConfig:
    """
    Get the current global agent configuration.
    
    Returns:
    --------
    AgentConfig
        The current agent configuration.
    
    Example:
    --------
    ```python
    from agentcom.config import get_agent_config
    
    config = get_agent_config()
    print(f"Agent: {config.agent_id}, Version: {config.version}")
    ```
    """
    return _agent_config


def reset_agent_config() -> None:
    """
    Reset the agent configuration to default values.
    Useful for testing.
    """
    global _agent_config
    _agent_config = AgentConfig()
