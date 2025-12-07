from functools import wraps, partial
from typing import List, Dict, Any, Optional
import inspect
import asyncio

from agentcom.registry import REGISTERED_ENDPOINTS


def capability(
    path: str,
    method: str = "GET",
    name: Optional[str] = None,
    auth_required: Optional[List[str]] = None,
    cost: Optional[Dict[str, Any]] = None,
    rate_limit: Optional[str] = None,
):
    """
    Decorator che registra l'endpoint come capability con introspezione dei parametri.

    Parametri opzionali per arricchire la capability:
    - `name`: nome logico della capability (es. `create_ticket`).
    - `auth_required`: lista di scope o permessi richiesti.
    - `cost`: dict con stima dei costi (es. `{"units": "tokens", "estimate": 5}`).
    - `rate_limit`: stringa con limite (es. `"10/s"`).
    """

    def decorator(func):
        sig = inspect.signature(func)
        parameters: List[Dict[str, Any]] = []
        for param_name, param in sig.parameters.items():
            # Ignora self e request
            if param_name in ("self", "request"):
                continue
            parameters.append({
                "name": param_name,
                "default": None if param.default is inspect.Parameter.empty else param.default,
                "annotation": (
                    str(param.annotation)
                    if param.annotation is not inspect.Parameter.empty
                    else "Any"
                ),
            })

        default_name = None
        if not name and path:
            default_name = path.strip("/").replace("/", "_") or path

        REGISTERED_ENDPOINTS.append({
            "path": path,
            "method": method,
            "name": name or default_name,
            "description": func.__doc__ or "",
            "parameters": parameters,
            "auth_required": auth_required or [],
            "cost": cost or {},
            "rate_limit": rate_limit,
        })

        # Support both async and sync functions. If the original function is
        # synchronous, run it in the default thread executor to avoid
        # blocking the event loop.
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
        else:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                loop = asyncio.get_running_loop()
                func_call = partial(func, *args, **kwargs)
                return await loop.run_in_executor(None, func_call)
        return wrapper

    return decorator

