"""Schlanker, asynchroner Client für die (inoffizielle) Bring!-API."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

API_BASE = "https://api.getbring.com/rest/"
API_KEY = "cof4Nc6D8saplXjE3h3HXqHH8m7VU2i1Gs0g85Sp"
TIMEOUT = aiohttp.ClientTimeout(total=20)

OP_PURCHASE = "TO_PURCHASE"
OP_RECENTLY = "TO_RECENTLY"
OP_REMOVE = "REMOVE"


class BringError(Exception):
    """Allgemeiner Fehler bei der Kommunikation mit Bring."""


class BringAuthError(BringError):
    """Login fehlgeschlagen (falsche Zugangsdaten)."""


class BringConnectionError(BringError):
    """Bring ist nicht erreichbar."""


@dataclass
class BringItem:
    """Ein Artikel auf der Liste."""

    uuid: str
    name: str
    specification: str = ""


@dataclass
class BringListData:
    """Inhalt einer Liste."""

    purchase: list[BringItem] = field(default_factory=list)
    recently: list[BringItem] = field(default_factory=list)


class BringClient:
    """Minimaler Bring!-Client."""

    def __init__(self, session: aiohttp.ClientSession, email: str, password: str) -> None:
        self._session = session
        self._email = email
        self._password = password
        self._user_uuid: str | None = None
        self._public_uuid: str | None = None
        self._token: str | None = None
        self._token_expires: float = 0
        self.user_name: str | None = None
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------ helpers
    def _headers(self) -> dict[str, str]:
        headers = {
            "X-BRING-API-KEY": API_KEY,
            "X-BRING-CLIENT": "android",
            "X-BRING-APPLICATION": "bring",
            "X-BRING-COUNTRY": "DE",
        }
        if self._user_uuid:
            headers["X-BRING-USER-UUID"] = self._user_uuid
        if self._public_uuid:
            headers["X-BRING-PUBLIC-USER-UUID"] = self._public_uuid
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    async def login(self) -> None:
        """Bei Bring anmelden."""
        headers = self._headers()
        headers.pop("Authorization", None)
        try:
            async with self._session.post(
                f"{API_BASE}v2/bringauth",
                data={"email": self._email, "password": self._password},
                headers=headers,
                timeout=TIMEOUT,
            ) as resp:
                if resp.status in (400, 401, 404):
                    raise BringAuthError("E-Mail oder Passwort falsch")
                if resp.status >= 400:
                    raise BringError(f"Login fehlgeschlagen (HTTP {resp.status})")
                data = await resp.json(content_type=None)
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise BringConnectionError(str(err)) from err

        self._user_uuid = data.get("uuid")
        self._public_uuid = data.get("publicUuid")
        self._token = data.get("access_token")
        self.user_name = data.get("name")
        expires_in = int(data.get("expires_in") or 3600)
        self._token_expires = time.monotonic() + expires_in - 120
        if not self._token or not self._user_uuid:
            raise BringAuthError("Unerwartete Antwort von Bring")

    async def _ensure_login(self) -> None:
        async with self._lock:
            if not self._token or time.monotonic() >= self._token_expires:
                await self.login()

    async def _request(self, method: str, path: str, *, retry: bool = True, **kwargs: Any) -> Any:
        await self._ensure_login()
        try:
            async with self._session.request(
                method, f"{API_BASE}{path}", headers=self._headers(), timeout=TIMEOUT, **kwargs
            ) as resp:
                if resp.status == 401 and retry:
                    self._token = None
                    return await self._request(method, path, retry=False, **kwargs)
                if resp.status == 401:
                    raise BringAuthError("Sitzung abgelaufen")
                if resp.status >= 400:
                    raise BringError(f"HTTP {resp.status} bei {path}")
                text = await resp.text()
                if not text:
                    return None
                return await resp.json(content_type=None)
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise BringConnectionError(str(err)) from err

    # ---------------------------------------------------------------------- API
    async def get_lists(self) -> list[dict[str, str]]:
        """Alle Listen des Nutzers: [{'uuid':…, 'name':…}]."""
        await self._ensure_login()
        data = await self._request("GET", f"bringusers/{self._user_uuid}/lists")
        lists = (data or {}).get("lists", [])
        return [
            {"uuid": lst.get("listUuid"), "name": lst.get("name") or "Liste"}
            for lst in lists
            if lst.get("listUuid")
        ]

    async def get_items(self, list_uuid: str) -> BringListData:
        """Artikel einer Liste laden."""
        data = await self._request("GET", f"v2/bringlists/{list_uuid}") or {}
        items = data.get("items", data)

        def parse(raw: list[dict[str, Any]]) -> list[BringItem]:
            result = []
            for entry in raw or []:
                name = entry.get("itemId") or entry.get("name")
                if not name:
                    continue
                result.append(
                    BringItem(
                        uuid=entry.get("uuid") or f"{name}",
                        name=name,
                        specification=entry.get("specification") or "",
                    )
                )
            return result

        return BringListData(
            purchase=parse(items.get("purchase", [])),
            recently=parse(items.get("recently", [])),
        )

    async def batch_update(self, list_uuid: str, changes: list[dict[str, str]]) -> None:
        """Mehrere Änderungen auf einmal senden.

        Jede Änderung: {"itemId", "spec", "uuid", "operation"}.
        """
        payload = {
            "changes": [
                {
                    "accuracy": "0.0",
                    "altitude": "0.0",
                    "latitude": "0.0",
                    "longitude": "0.0",
                    "itemId": change["itemId"],
                    "spec": change.get("spec", ""),
                    "uuid": change.get("uuid", ""),
                    "operation": change["operation"],
                }
                for change in changes
            ],
            "sender": "",
        }
        await self._request("PUT", f"v2/bringlists/{list_uuid}/items", json=payload)
