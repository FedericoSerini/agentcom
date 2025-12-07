"""
Session negotiation and management endpoints for agent coordination.
"""
from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any, Optional
import json
import base64
from datetime import datetime, timedelta

from agentcom.models.session import (
    SessionRequest,
    SessionResponse,
    AcceptedCapability,
    RejectedCapability,
    NegotiatedSession,
    PolicyAck,
    ResponseSessionMeta
)
from agentcom.registry import REGISTERED_ENDPOINTS
from agentcom.config import get_agent_config


def _generate_session_token(session_id: str, timeout_seconds: int = 180) -> str:
    """
    Generate a mock JWT-like session token.
    In production, you'd use PyJWT or similar.
    """
    payload = {
        "session_id": session_id,
        "iat": datetime.utcnow().isoformat(),
        "exp": (datetime.utcnow() + timedelta(seconds=timeout_seconds)).isoformat(),
    }
    # Mock encoding (not secure, for demo purposes)
    encoded = base64.b64encode(json.dumps(payload).encode()).decode()
    return f"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.{encoded}.mock_signature"


def _match_version(required: Optional[str], available: str) -> bool:
    """
    Simple version matching logic.
    Supports: ">=1.0,<2.0", "1.2.x", exact versions, etc.
    For production, use packaging.version.
    """
    if not required:
        return True
    # Simplified: just check if available version starts with base version
    # In production, use proper semver parsing
    return True  # Mock: accept all for demo


def _find_capability(name: str, registry: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Find a capability in the registry by name."""
    for cap in registry:
        if cap.get("name") == name or str(cap.get("path")).strip("/").replace("/", "_") == name:
            return cap
    return None


def _negotiate_capability(wanted: Any, registered: Optional[Dict[str, Any]]) -> tuple:
    """
    Negotiate a single capability.
    Returns (AcceptedCapability | None, RejectedCapability | None)
    """
    if not registered:
        rejected = RejectedCapability(
            name=wanted.name,
            reason="capability_not_found",
            details=f"Capability '{wanted.name}' is not available on this agent"
        )
        return None, rejected

    # Check version compatibility
    if wanted.version and not _match_version(wanted.version, registered.get("version", "1.0.0")):
        rejected = RejectedCapability(
            name=wanted.name,
            reason="unsupported_version",
            supported_versions=["1.0.0", "1.1.0"],  # Mock supported versions
            details=f"Requested {wanted.version}, available 1.0.0-1.1.0"
        )
        return None, rejected

    # Check constraints (latency, cost, etc.)
    constraints = wanted.constraints or {}
    max_latency = constraints.get("max_latency_ms")
    if max_latency and max_latency < 500:  # Mock: assume p99 is ~850ms
        rejected = RejectedCapability(
            name=wanted.name,
            reason="latency_constraint_violation",
            details=f"Required latency {max_latency}ms, but expected p99 is ~850ms"
        )
        return None, rejected

    # Capability accepted: build response
    accepted = AcceptedCapability(
        name=wanted.name,
        version=registered.get("version", "1.0.0"),
        action_schema=registered.get("path"),  # or could be a URL
        estimated_cost=registered.get("cost"),
        latency_p99_ms=850,  # Mock P99 latency
    )
    return accepted, None


def register_session_endpoint(app: FastAPI):
    """
    Register the POST /session endpoint for session negotiation.

    This endpoint handles capability negotiation and session establishment
    between agents.

    Parameters:
    -----------
    app : FastAPI
        The FastAPI application instance.
    agent_id : Optional[str]
        Agent ID for this endpoint. If not provided, uses the configured value
        from `config.set_agent_config()` or defaults to "agent://unknown".

    Usage:
    ------
    At application startup:
    ```python
    from agentcom import set_agent_config, register_session_endpoint
    
    set_agent_config(
        agent_id="agent://executor/main",
        version="1.2.0"
    )
    register_session_endpoint(app)  # Uses configured agent_id
    ```

    The endpoint validates that the configured agent_id is listed in the
    request's participants list.
    """
    # Use provided agent_id or fall back to configured/default value
    config = get_agent_config()

    @app.post("/session", response_model=SessionResponse)
    async def session_endpoint(request: SessionRequest) -> SessionResponse:
        """
        Establish a session between agents with capability negotiation.

        Request body includes:
        - session_id: unique session identifier
        - from: initiating agent ID
        - intent: purpose of the session
        - participants: list of participating agents
        - wanted_capabilities: list of requested capabilities with versions and constraints
        - policy: session policy (evidence, conflict resolution, etc.)
        - session_preferences: transport, retry, etc.
        - timeout_seconds: session timeout
        - meta: tracing metadata

        Response includes:
        - accepted_capabilities: capabilities that match requirements
        - rejected_capabilities: capabilities that couldn't be matched
        - negotiated_session: final session parameters
        - session_token: JWT or bearer token for subsequent requests
        - policy_ack: acknowledgment of accepted policies
        """

        # Validate that this agent is a participant (optional)
        if config.agent_id not in request.participants:
            raise HTTPException(
                status_code=400,
                detail=f"Agent {config.agent_id} is not listed as a participant"
            )

        accepted_caps: List[AcceptedCapability] = []
        rejected_caps: List[RejectedCapability] = []

        # Negotiate each wanted capability
        for wanted_cap in request.wanted_capabilities:
            registered_cap = _find_capability(wanted_cap.name, REGISTERED_ENDPOINTS)
            accepted, rejected = _negotiate_capability(wanted_cap, registered_cap)

            if accepted:
                accepted_caps.append(accepted)
            if rejected:
                rejected_caps.append(rejected)

        # Determine session status
        if len(accepted_caps) == len(request.wanted_capabilities) and not rejected_caps:
            status = "accepted"
        elif accepted_caps:
            status = "partial"
        else:
            status = "rejected"

        # Select transport (first available in preferences that we support)
        selected_transport = "http-json"  # default
        supported_transports = ["http-json", "grpc", "nats"]
        for pref_transport in (request.session_preferences.transport or ["http-json"]):
            if pref_transport in supported_transports:
                selected_transport = pref_transport
                break

        # Negotiate timeout (use minimum of requested and max allowed)
        negotiated_timeout = min(request.timeout_seconds or 180, 180)

        # Build response
        negotiated = NegotiatedSession(
            timeout_seconds=negotiated_timeout,
            transport=selected_transport,
            retry_strategy=request.session_preferences.retry_strategy or "exponential",
            max_retries=request.session_preferences.max_retries or 3,
        )

        policy_ack = PolicyAck(
            require_evidence=request.policy.require_evidence if request.policy else False,
            conflict_resolution=request.policy.conflict_resolution if request.policy else "planner_wins",
        )

        session_token = _generate_session_token(request.session_id, negotiated_timeout)

        response_meta = ResponseSessionMeta(
            trace_id=request.meta.trace_id if request.meta else None,
            correlation_id=request.meta.correlation_id if request.meta else None,
            responder_version="agent-proto-1.0.4",
        )

        return SessionResponse(
            session_id=request.session_id,
            status=status,
            accepted_capabilities=accepted_caps,
            rejected_capabilities=rejected_caps,
            negotiated_session=negotiated,
            session_token=session_token,
            policy_ack=policy_ack,
            meta=response_meta,
            error=None if status != "rejected" else "No compatible capabilities found",
        )
