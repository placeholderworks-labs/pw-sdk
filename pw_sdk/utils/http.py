import asyncio
import logging
from collections.abc import Iterable

import httpx

logger = logging.getLogger(__name__)

RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})
_clients: dict[float, httpx.AsyncClient] = {}


def client(timeout: float = 15.0) -> httpx.AsyncClient:
    existing = _clients.get(timeout)
    if existing is None or existing.is_closed:
        existing = httpx.AsyncClient(timeout=timeout, limits=httpx.Limits(max_connections=100, max_keepalive_connections=20))
        _clients[timeout] = existing
    return existing


async def close_all() -> None:
    for item in list(_clients.values()):
        await item.aclose()
    _clients.clear()


async def request(
    method: str,
    url: str,
    *,
    retries: int = 2,
    backoff: float = 0.5,
    timeout: float = 15.0,
    retry_on: Iterable[int] = RETRY_STATUSES,
    **kwargs,
) -> httpx.Response:
    statuses = frozenset(retry_on)
    attempt = 0
    while True:
        try:
            response = await client(timeout).request(method, url, **kwargs)
            if response.status_code not in statuses or attempt >= retries:
                return response
            logger.warning(f"[http] {method} {url} -> {response.status_code}, retrying")
        except (httpx.TransportError, httpx.TimeoutException) as error:
            if attempt >= retries:
                raise
            logger.warning(f"[http] {method} {url} failed ({type(error).__name__}), retrying")
        attempt += 1
        await asyncio.sleep(backoff * (2 ** (attempt - 1)))


def base_url(url: str) -> str:
    return url.rsplit("/", 1)[0] if url else url
