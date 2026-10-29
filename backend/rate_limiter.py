# Plain-English description: Middleware that enforces in-memory rate limiting of 10 requests per minute per IP address.

import time
from collections import defaultdict
from threading import Lock
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

class IPRateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 10, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.request_history = defaultdict(list)
        self.lock = Lock()

    async def dispatch(self, request, call_next):
        # Determine client IP from headers or client object
        client_ip = request.headers.get("x-forwarded-for")
        if client_ip:
            client_ip = client_ip.split(",")[0].strip()
        elif request.client and request.client.host:
            client_ip = request.client.host
        else:
            client_ip = "127.0.0.1"

        now = time.time()

        with self.lock:
            # Purge timestamps older than the window
            timestamps = self.request_history[client_ip]
            self.request_history[client_ip] = [ts for ts in timestamps if now - ts < self.window_seconds]

            # Check if threshold is exceeded
            if len(self.request_history[client_ip]) >= self.max_requests:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too Many Requests: Rate limit of 10 requests per minute exceeded."}
                )

            # Record this request
            self.request_history[client_ip].append(now)

        return await call_next(request)

