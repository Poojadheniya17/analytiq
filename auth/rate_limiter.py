# auth/rate_limiter.py
# Analytiq — Simple in-memory rate limiter

import time
from collections import defaultdict
from fastapi import HTTPException, Request

# Stores: { ip: [timestamp, timestamp, ...] }
_request_log: dict[str, list] = defaultdict(list)

# Rules per route prefix
RATE_RULES = {
    "/api/auth":      (10,  60),   # 10 requests per 60 seconds
    "/api/analysis":  (20, 120),   # 20 requests per 2 minutes
    "/api/export":    (5,   60),   # 5 requests per 60 seconds
    "/api/ai":        (15, 120),   # 15 requests per 2 minutes
    "default":        (60,  60),   # 60 requests per 60 seconds
}


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def check_rate_limit(request: Request):
    ip   = get_client_ip(request)
    path = request.url.path
    now  = time.time()

    # Find matching rule
    limit, window = RATE_RULES["default"]
    for prefix, rule in RATE_RULES.items():
        if prefix != "default" and path.startswith(prefix):
            limit, window = rule
            break

    key = f"{ip}:{path}"

    # Clean old timestamps
    _request_log[key] = [t for t in _request_log[key] if now - t < window]

    if len(_request_log[key]) >= limit:
        retry_after = int(window - (now - _request_log[key][0]))
        raise HTTPException(
            status_code=429,
            detail=f"Too many requests. Please wait {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)}
        )

    _request_log[key].append(now)
