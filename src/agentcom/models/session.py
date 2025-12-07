"""
Pydantic models for agent session negotiation and management.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


# ===================== Request Models =====================

class WantedCapability(BaseModel):
    """Represents a capability that a client wants to use in the session."""
    name: str = Field(..., description="Name of the capability")
    version: Optional[str] = Field(default=None, description="Version constraint (e.g., '>=1.0,<2.0')")
    constraints: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional constraints (e.g., max_latency_ms)"
    )


class SessionPreferences(BaseModel):
    """Preferences for session negotiation."""
    transport: List[str] = Field(
        default=["http-json"],
        description="Preferred transport protocols"
    )
    retry_strategy: str = Field(default="exponential", description="Retry strategy")
    max_retries: Optional[int] = Field(default=3, description="Maximum number of retries")


class SessionPolicy(BaseModel):
    """Policy constraints for the session."""
    require_evidence: bool = Field(default=False, description="Require evidence of execution")
    conflict_resolution: str = Field(default="planner_wins", description="Conflict resolution strategy")


class SessionMeta(BaseModel):
    """Metadata for tracing and correlation."""
    trace_id: Optional[str] = Field(default=None, description="Trace ID for logging")
    correlation_id: Optional[str] = Field(default=None, description="Correlation ID")


class SessionRequest(BaseModel):
    """Request to establish a session between agents."""
    session_id: str = Field(..., description="Unique session identifier")
    from_agent: str = Field(..., alias="from", description="Agent ID initiating the session")
    intent: str = Field(..., description="Intent or purpose of the session")
    participants: List[str] = Field(..., description="List of participating agent IDs")
    wanted_capabilities: List[WantedCapability] = Field(
        default_factory=list,
        description="Capabilities requested for this session"
    )
    policy: Optional[SessionPolicy] = Field(default_factory=SessionPolicy, description="Session policy")
    session_preferences: SessionPreferences = Field(
        default_factory=SessionPreferences,
        description="Preferences for session negotiation"
    )
    timeout_seconds: Optional[int] = Field(default=180, description="Session timeout in seconds")
    meta: Optional[SessionMeta] = Field(default_factory=SessionMeta, description="Metadata")

    class Config:
        populate_by_name = True  # Allow 'from' field despite it being a reserved keyword


# ===================== Response Models =====================

class AcceptedCapability(BaseModel):
    """Details of a capability that was accepted for the session."""
    name: str = Field(..., description="Capability name")
    version: str = Field(..., description="Accepted version")
    action_schema: Optional[str] = Field(default=None, description="URL to the action schema or embedded schema")
    estimated_cost: Optional[Dict[str, Any]] = Field(default=None, description="Estimated cost of execution")
    latency_p99_ms: Optional[int] = Field(default=None, description="P99 latency in milliseconds")


class RejectedCapability(BaseModel):
    """Details of a capability that was rejected."""
    name: str = Field(..., description="Capability name")
    reason: str = Field(..., description="Reason for rejection (e.g., 'unsupported_version', 'auth_required')")
    supported_versions: Optional[List[str]] = Field(default=None, description="Supported versions if applicable")
    details: Optional[str] = Field(default=None, description="Additional details")


class NegotiatedSession(BaseModel):
    """Negotiated session parameters."""
    timeout_seconds: int = Field(..., description="Agreed timeout")
    transport: str = Field(..., description="Selected transport protocol")
    retry_strategy: str = Field(..., description="Agreed retry strategy")
    max_retries: int = Field(..., description="Agreed max retries")


class PolicyAck(BaseModel):
    """Acknowledgment of session policy."""
    require_evidence: bool = Field(default=False)
    conflict_resolution: str = Field(default="planner_wins")


class ResponseSessionMeta(BaseModel):
    """Response metadata."""
    trace_id: Optional[str] = Field(default=None)
    correlation_id: Optional[str] = Field(default=None)
    responder_version: Optional[str] = Field(default=None)


class SessionResponse(BaseModel):
    """Response to a session establishment request."""
    session_id: str = Field(..., description="Session identifier")
    status: str = Field(..., description="Session status (e.g., 'accepted', 'rejected', 'partial')")
    accepted_capabilities: List[AcceptedCapability] = Field(
        default_factory=list,
        description="Capabilities that were accepted"
    )
    rejected_capabilities: List[RejectedCapability] = Field(
        default_factory=list,
        description="Capabilities that were rejected"
    )
    negotiated_session: Optional[NegotiatedSession] = Field(
        default=None,
        description="Negotiated session parameters"
    )
    session_token: Optional[str] = Field(
        default=None,
        description="JWT or bearer token for subsequent calls"
    )
    policy_ack: Optional[PolicyAck] = Field(
        default=None,
        description="Acknowledgment of accepted policies"
    )
    meta: Optional[ResponseSessionMeta] = Field(
        default_factory=ResponseSessionMeta,
        description="Response metadata"
    )
    error: Optional[str] = Field(default=None, description="Error message if status is 'rejected'")
