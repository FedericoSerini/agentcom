import aiohttp
from aiomisc.circuit_breaker import CircuitBreaker


# Istanza del circuit breaker
cb = CircuitBreaker(
    error_ratio=0.5,
    response_time=5,
)


async def get_capability():
    # Il circuit breaker va chiamato come funzione wrapper
    async def _wrapped_call():
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8080/capability") as response:
                print("Status:", response.status)
                print("Content-Type:", response.headers.get("content-type"))

                body = await response.text()
                print("Body:", body)
                return body

    return await cb.call(_wrapped_call)