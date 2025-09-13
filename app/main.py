from fastapi import FastAPI
from app.db.session import engine, Base
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.routes import router as v1_router
from app.core.logging import setup_logging
from app.core.errors import BadInput, bad_input_handler, timeout_handler

from app.core.limiting import (
    limiter,
    RateLimitExceeded,
    _rate_limit_exceeded_handler,
    HAVE_SLOWAPI,
)

try:
    from slowapi.middleware import SlowAPIMiddleware
except Exception:
    SlowAPIMiddleware = None

app = FastAPI(title=settings.PROJECT_NAME)
setup_logging()

if HAVE_SLOWAPI and SlowAPIMiddleware is not None:
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENV == "dev" else settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.add_exception_handler(BadInput, bad_input_handler)
app.add_exception_handler(TimeoutError, timeout_handler)

@app.on_event("startup")
def on_startup():
    try:
        from app.services.persistence import create_tables
        create_tables()
    except Exception as e:
        import logging
        logging.getLogger(__name__).exception("DB init failed: %s", e)

app.include_router(v1_router, prefix=settings.API_V1_STR)