# app/core/limiting.py
"""
Central place for SlowAPI limiter so main.py and routes.py can import
without causing circular imports.
"""

# Defaults so app still runs if slowapi isn't installed
HAVE_SLOWAPI = False
limiter = None

# Exported symbols (real or stubs)
def _rate_limit_exceeded_handler(*args, **kwargs): ...
class RateLimitExceeded(Exception): ...

def _key_from_request(request):
    """
    Prefer X-Forwarded-For (first IP), else fall back to request.client.host.
    This lets tests set a unique IP to avoid tripping shared buckets.
    """
    xf = request.headers.get("X-Forwarded-For") or request.headers.get("x-forwarded-for")
    if xf:
        return xf.split(",")[0].strip()
    client = getattr(request, "client", None)
    host = getattr(client, "host", None)
    return host or "testclient"

try:
    from slowapi import Limiter, _rate_limit_exceeded_handler as _rl_handler
    from slowapi.errors import RateLimitExceeded as _RLE

    # Real implementations available
    HAVE_SLOWAPI = True
    limiter = Limiter(key_func=_key_from_request)  # <-- use our header-aware key func
    _rate_limit_exceeded_handler = _rl_handler  # type: ignore
    RateLimitExceeded = _RLE  # type: ignore
except Exception:
    # keep the stubs above so imports elsewhere don't explode
    pass


def get_limit_decorator(rule: str):
    """
    Return a decorator usable on endpoints. If slowapi isn't present,
    return a no-op decorator so the app still runs.
    """
    if limiter:
        return limiter.limit(rule)

    def _noop(fn):
        return fn
    return _noop
