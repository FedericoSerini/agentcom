"""
Capability endpoint that exposes agent metadata and capabilities.

This module provides the /capability endpoint which returns agent information
including registered capabilities with their action schemas from OpenAPI.
"""
from fastapi import FastAPI
from typing import List, Dict, Any, Optional

from agentcom.registry import REGISTERED_ENDPOINTS


def register_capability_endpoint(
    app: FastAPI,
    agent_id: str = "agent://unknown",
    version: str = "0.0.0",
    health: str = "unknown",
    supported_transports: Optional[List[str]] = None,
):
    """
    Automatically mount the `/capability` endpoint on the FastAPI app and return
    agent metadata along with capabilities.

    Parameters:
    -----------
    app : FastAPI
        The FastAPI application instance.
    agent_id : str
        Unique identifier for the agent (e.g., "agent://inventory/worker-1").
    version : str
        Agent version (e.g., "1.2.0").
    health : str
        Health status of the agent (e.g., "ok", "degraded").
    supported_transports : Optional[List[str]]
        List of supported transport protocols (default: ["http-json"]).

    Usage:
    ------
    - `GET /capability?raw=true` : returns the full OpenAPI schema (equivalent to `/openapi.json`).
    - `GET /capability` : returns an object with `agent_id`, `version`, `capabilities`,
                         `health` and `supported_transports`. Each capability includes
                         `action_schema` extracted from the corresponding OpenAPI operation.

    Example response (with `raw=false`):
    ```json
    {
        "agent_id": "agent://inventory/worker-1",
        "version": "1.2.0",
        "health": "ok",
        "supported_transports": ["http-json", "grpc"],
        "capabilities": [
            {
                "name": "create_ticket",
                "path": "/ticket",
                "method": "POST",
                "description": "Create a new ticket",
                "parameters": [...],
                "auth_required": ["scope:ticket:create"],
                "cost": {"units": "tokens", "estimate": 5},
                "rate_limit": "10/s",
                "action_schema": {...}  // OpenAPI operation object
            }
        ]
    }
    ```
    """
    if supported_transports is None:
        supported_transports = ["http-json"]

    @app.get("/capability")
    async def capability_endpoint(raw: bool = False):
        openapi_schema = app.openapi()
        if raw:
            return openapi_schema

        paths = openapi_schema.get("paths", {})

        capabilities_out: List[Dict[str, Any]] = []
        for cap in REGISTERED_ENDPOINTS:
            path = cap.get("path")
            method = (cap.get("method") or "GET").lower()

            action_schema = None
            if path and path in paths:
                path_item = paths.get(path, {})
                action_schema = path_item.get(method)

            capabilities_out.append({
                "name": cap.get("name") or path,
                "path": path,
                "method": cap.get("method"),
                "description": cap.get("description"),
                "parameters": cap.get("parameters"),
                "auth_required": cap.get("auth_required", []),
                "cost": cap.get("cost", {}),
                "rate_limit": cap.get("rate_limit"),
                "action_schema": action_schema,
            })

        return {
            "agent_id": agent_id,
            "version": version,
            "capabilities": capabilities_out,
            "health": health,
            "supported_transports": supported_transports,
        }
