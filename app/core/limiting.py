# app/core/limiting.py
HAVE_SLOWAPI = False
limiter = None

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

    HAVE_SLOWAPI = True
    limiter = Limiter(key_func=_key_from_request)
    _rate_limit_exceeded_handler = _rl_handler
    RateLimitExceeded = _RLE
except Exception:
    pass


def get_limit_decorator(rule: str):
    if limiter:
        return limiter.limit(rule)

    def _noop(fn):
        return fn
    return _noop
