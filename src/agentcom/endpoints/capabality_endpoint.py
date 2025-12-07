"""
Capability endpoint that exposes agent metadata and capabilities.

This module provides the /capability endpoint which returns agent information
including registered capabilities with their action schemas from OpenAPI.
"""
from fastapi import FastAPI
from typing import List, Dict, Any

from agentcom.registry import REGISTERED_ENDPOINTS
from agentcom.config import get_agent_config


def register_capability_endpoint(
    app: FastAPI,
):
    """
    Automatically mount the `/capability` endpoint on the FastAPI app and return
    agent metadata along with capabilities.

    Parameters:
    -----------
    app : FastAPI
        The FastAPI application instance.
    agent_id : Optional[str]
        Unique identifier for the agent. If not provided, uses the configured value
        from `config.set_agent_config()` or defaults to "agent://unknown".
    version : Optional[str]
        Agent version. If not provided, uses the configured value from `config.set_agent_config()`
        or defaults to "0.0.0".
    supported_transports : Optional[List[str]]
        List of supported transport protocols. If not provided, uses the configured value
        from `config.set_agent_config()` or defaults to ["http-json"].

    Usage:
    ------
    At application startup:
    ```python
    from agentcom import set_agent_config, register_capability_endpoint
    
    set_agent_config(
        agent_id="agent://inventory/worker-1",
        version="1.2.0",
    )
    register_capability_endpoint(app)  # Uses configured values
    ```

    Or override per-endpoint:
    ```python
    register_capability_endpoint(
        app,
        agent_id="agent://custom",
        version="2.0.0"
    )
    ```

    Endpoint behavior:
    - `GET /capability?raw=true` : returns the full OpenAPI schema (equivalent to `/openapi.json`).
    - `GET /capability` : returns an object with `agent_id`, `version`, `capabilities`
                          and `supported_transports`. Each capability includes
                         `action_schema` extracted from the corresponding OpenAPI operation.

    Example response (with `raw=false`):
    ```json
    {
        "agent_id": "agent://inventory/worker-1",
        "version": "1.2.0",
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
    # Use provided values or fall back to configured/default values
    config = get_agent_config()

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
            "agent_id": config.agent_id,
            "version": config.version,
            "capabilities": capabilities_out,
            "supported_transports": config.supported_transports,
        }
