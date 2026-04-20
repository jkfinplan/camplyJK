"""
HTTP session and auth for api.reserveamerica.com JSON endpoints.
"""

from __future__ import annotations

import logging
import urllib.parse
from typing import Any, Dict, Optional

import requests
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)

HTTP_UNAUTHORIZED = 401

SIGNIN_URL = "https://www.reserveamerica.com/signin"
HOME_URL = "https://www.reserveamerica.com/"
API_BASE = "https://api.reserveamerica.com"


class ReserveAmericaAuthError(RuntimeError):
    """Raised when sign-in does not yield required cookies."""


class ReserveAmericaClient:
    """
    Minimal client: browser-like User-Agent is required or /signin may return 403.
    """

    def __init__(self) -> None:
        self._session = requests.Session()
        ua = UserAgent(browsers=["chrome"]).random
        self._session.headers.update({"User-Agent": ua})
        self._api_headers: Optional[Dict[str, str]] = None

    def refresh_auth(self) -> None:
        """
        Load www.reserveamerica.com then /signin and set Authorization + A1Data headers.
        """
        self._session.get(HOME_URL, timeout=60)
        r = self._session.get(SIGNIN_URL, timeout=60)
        r.raise_for_status()
        id_token = r.cookies.get("idToken")
        a1 = r.cookies.get("a1Data")
        if not id_token or not a1:
            raise ReserveAmericaAuthError(
                "Reserve America sign-in did not return idToken/a1Data cookies"
            )
        self._api_headers = {
            "Authorization": id_token,
            "A1Data": urllib.parse.unquote(a1),
            "Referer": "https://www.reserveamerica.com",
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json",
        }

    def _ensure_auth(self) -> Dict[str, str]:
        if self._api_headers is None:
            self.refresh_auth()
        assert self._api_headers is not None
        return self._api_headers

    def get_json(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        GET JSON relative to API_BASE or absolute URL.
        """
        url = path if path.startswith("http") else f"{API_BASE}{path}"
        headers = self._ensure_auth()
        r = self._session.get(url, headers=headers, params=params or {}, timeout=120)
        if r.status_code == HTTP_UNAUTHORIZED:
            logger.info("Reserve America auth expired; refreshing")
            self.refresh_auth()
            headers = self._ensure_auth()
            r = self._session.get(
                url, headers=headers, params=params or {}, timeout=120
            )
        r.raise_for_status()
        return r.json()
