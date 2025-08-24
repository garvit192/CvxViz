from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.routes import router as v1_router
from app.core.logging import setup_logging
from app.core.errors import BadInput, bad_input_handler, timeout_handler

# Shared limiter (no circular import)
from app.core.limiting import (
    limiter,
    RateLimitExceeded,
    _rate_limit_exceeded_handler,
    HAVE_SLOWAPI,
)

# SlowAPI middleware may or may not exist
try:
    from slowapi.middleware import SlowAPIMiddleware
except Exception:
    SlowAPIMiddleware = None

app = FastAPI(title=settings.PROJECT_NAME)
setup_logging()

# Rate limiting wiring (only if slowapi is available)
if HAVE_SLOWAPI and SlowAPIMiddleware is not None:
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    # Use SlowAPI's own handler for 429 responses
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENV == "dev" else settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(v1_router, prefix=settings.API_V1_STR)

# Our custom handlers
app.add_exception_handler(BadInput, bad_input_handler)
app.add_exception_handler(TimeoutError, timeout_handler)
