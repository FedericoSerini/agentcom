from functools import wraps
from fastapi import Request
import logging

logger = logging.getLogger("my_decorators")

def log_request(func):
    @wraps(func)
    async def wrapper(*args, request: Request, **kwargs):
        logger.info(f"Request {request.method} {request.url}")
        return await func(*args, request=request, **kwargs)
    return wrapper