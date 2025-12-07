# Import dai moduli interni per esporre direttamente i decorator e endpoint
from .decorators.capability_decorator import capability
from .decorators.logger import log_request
from .endpoints.capabality_endpoint import register_capability_endpoint
from .endpoints.session_endpoint import register_session_endpoint
from .registry import REGISTERED_ENDPOINTS
from .config import set_agent_config, get_agent_config, reset_agent_config
from .models import (
    SessionRequest,
    SessionResponse,
    AcceptedCapability,
    RejectedCapability,
)

# Puoi anche aggiungere altri decorator qui in futuro
__all__ = [
    "capability",
    "register_capability_endpoint",
    "register_session_endpoint",
    "log_request",
    "REGISTERED_ENDPOINTS",
    "set_agent_config",
    "get_agent_config",
    "reset_agent_config",
    "SessionRequest",
    "SessionResponse",
    "AcceptedCapability",
    "RejectedCapability",
]
