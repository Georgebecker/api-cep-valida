"""Rate limiting simples em memória para as rotas de validação."""

import hashlib
import os
import time
from collections import deque
from threading import Lock

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

PROTECTED_PREFIX = "/validate/"
MAX_TRACKED_CLIENTS = 10_000

_HITS: dict[str, deque[float]] = {}
_LOCK = Lock()


def _env_float(name: str, default: float, minimum: float) -> float:
    try:
        return max(minimum, float(os.getenv(name, str(default))))
    except ValueError:
        return default


def _enabled() -> bool:
    value = os.getenv("RATE_LIMIT_ENABLED", "1").strip().lower()
    return value not in {"0", "false", "off", "no"}


def reset() -> None:
    """Esvazia o histórico de requisições (usado pelos testes)."""
    with _LOCK:
        _HITS.clear()


def _client_key(request: Request) -> str:
    host = request.client.host if request.client else "desconhecido"
    return hashlib.sha256(host.encode("utf-8")).hexdigest()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Aplica janela deslizante por cliente (hash do IP) nas rotas `/validate/*`."""

    async def dispatch(self, request: Request, call_next):
        if not _enabled() or not request.url.path.startswith(PROTECTED_PREFIX):
            return await call_next(request)

        limit = int(_env_float("RATE_LIMIT_REQUESTS", 60, 1))
        window = _env_float("RATE_LIMIT_WINDOW", 60.0, 0.1)
        client = _client_key(request)
        now = time.monotonic()

        with _LOCK:
            hits = _HITS.setdefault(client, deque())
            while hits and now - hits[0] >= window:
                hits.popleft()
            if len(hits) >= limit:
                retry_after = max(1, int(window - (now - hits[0])))
                return JSONResponse(
                    status_code=429,
                    content={"detail": "limite de requisições excedido"},
                    headers={"Retry-After": str(retry_after)},
                )
            hits.append(now)
            if len(_HITS) > MAX_TRACKED_CLIENTS:
                for key in [key for key, values in _HITS.items() if not values]:
                    del _HITS[key]

        return await call_next(request)
