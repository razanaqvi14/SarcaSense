from slowapi import Limiter
from slowapi.util import get_remote_address

from .config import get_settings

# Keyed on the client IP. uvicorn runs with --proxy-headers and nginx overwrites
# X-Forwarded-For, so this is the real client address, not the proxy's.
# State is in-process: run a single worker, or move to a Redis storage_uri to scale out.
limiter = Limiter(
    key_func=get_remote_address,
    enabled=get_settings().rate_limit_enabled,
)
