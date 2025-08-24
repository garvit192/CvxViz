from fastapi import Request
from fastapi.responses import JSONResponse
from starlette import status
from slowapi.errors import RateLimitExceeded

class BadInput(Exception):
    def __init__(self, detail: str): self.detail = detail

async def bad_input_handler(request: Request, exc: BadInput):
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        content={"detail": exc.detail})

async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={"detail": "Rate limit exceeded"})

async def timeout_handler(request: Request, exc: TimeoutError):
    return JSONResponse(status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                        content={"detail": "Request timed out"})
