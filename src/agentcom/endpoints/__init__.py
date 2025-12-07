"""
Endpoints for agentcom library.
"""
from .capabality_endpoint import register_capability_endpoint
from .session_endpoint import register_session_endpoint

__all__ = [
    "register_capability_endpoint",
    "register_session_endpoint",
]
