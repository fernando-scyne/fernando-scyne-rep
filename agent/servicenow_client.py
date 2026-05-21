"""ServiceNow REST API client with Basic Auth."""

import logging
import time
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

_RETRY_TOTAL = 3
_RETRY_BACKOFF = 1.0
_RETRY_ON = {429, 500, 502, 503, 504}
_TIMEOUT = 30


class ServiceNowClient:
    def __init__(self, instance_url: str, username: str, password: str) -> None:
        self.base_url = instance_url.rstrip("/")
        self._session = requests.Session()
        self._session.auth = (username, password)
        self._session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
        })
        retry = Retry(
            total=_RETRY_TOTAL,
            backoff_factor=_RETRY_BACKOFF,
            status_forcelist=_RETRY_ON,
            allowed_methods=["GET", "POST"],
        )
        adapter = HTTPAdapter(max_retries=retry)
        self._session.mount("https://", adapter)
        self._session.mount("http://", adapter)

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict:
        resp = self._session.get(self._url(path), params=params, timeout=_TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    def post(self, path: str, payload: dict) -> dict:
        resp = self._session.post(self._url(path), json=payload, timeout=_TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    def verify_auth(self) -> str:
        """Return the display name of the authenticated user."""
        data = self.get("/api/now/table/sys_user", params={
            "sysparm_query": "user_name=" + self._session.auth[0],
            "sysparm_fields": "name,user_name",
            "sysparm_limit": "1",
        })
        records = data.get("result", [])
        if not records:
            raise RuntimeError("Auth succeeded but no user record returned")
        return records[0].get("name", self._session.auth[0])
