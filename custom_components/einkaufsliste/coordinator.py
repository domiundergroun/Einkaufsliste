"""DataUpdateCoordinator für die Einkaufsliste."""

from __future__ import annotations

import logging
import time
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util, slugify

from .api import BringAuthError, BringClient, BringError, BringListData
from .const import (
    CONF_CUSTOM_STORES,
    CONF_LIST_UUID,
    CONF_SCAN_INTERVAL,
    CONF_STORES,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    STORAGE_VERSION,
    STORE_CATALOG,
)

_LOGGER = logging.getLogger(__name__)


class EinkaufslisteCoordinator(DataUpdateCoordinator[BringListData]):
    """Holt regelmäßig die Bring-Liste."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: BringClient) -> None:
        interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(seconds=int(interval)),
        )
        self.entry = entry
        self.client = client
        self._store: Store[dict] = Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}")
        self.assignments: dict[str, str] = {}
        # Heute abgehakte Artikel (uuid -> Zeitstempel); bleiben bis 0 Uhr durchgestrichen sichtbar
        self.checked: dict[str, float] = {}

    @staticmethod
    def item_key(name: str) -> str:
        return name.strip().lower()

    async def async_load_assignments(self) -> None:
        data = await self._store.async_load() or {}
        self.assignments = dict(data.get("assignments", {}))
        midnight = dt_util.start_of_local_day().timestamp()
        self.checked = {
            uid: float(ts) for uid, ts in (data.get("checked") or {}).items() if float(ts) >= midnight
        }

    async def _async_save(self) -> None:
        await self._store.async_save({"assignments": self.assignments, "checked": self.checked})

    async def async_midnight(self) -> None:
        """Um 0 Uhr: abgehakte Artikel endgültig ausblenden."""
        if self.checked:
            self.checked = {}
            await self._async_save()
            self.async_update_listeners()

    async def async_set_store(self, name: str, store_id: str | None) -> None:
        key = self.item_key(name)
        if store_id:
            self.assignments[key] = store_id
        else:
            self.assignments.pop(key, None)
        await self._async_save()
        self.async_update_listeners()

    async def async_rename_assignment(self, old: str, new: str) -> None:
        old_key, new_key = self.item_key(old), self.item_key(new)
        if old_key in self.assignments and old_key != new_key:
            self.assignments[new_key] = self.assignments.pop(old_key)
            await self._async_save()

    @property
    def stores(self) -> list[dict[str, str | None]]:
        """In den Einstellungen ausgewählte Geschäfte (Reihenfolge wie im Katalog)."""
        selected = set(self.entry.options.get(CONF_STORES, []))
        result: list[dict[str, str | None]] = [
            {"id": sid, "name": name, "domain": domain, "emoji": emoji}
            for sid, (name, domain, emoji) in STORE_CATALOG.items()
            if sid in selected
        ]
        custom = self.entry.options.get(CONF_CUSTOM_STORES, "") or ""
        for raw in custom.split(","):
            name = raw.strip()
            if name:
                result.append(
                    {"id": f"custom_{slugify(name)}", "name": name, "domain": None, "emoji": "🏪"}
                )
        return result

    @property
    def list_uuid(self) -> str:
        return self.entry.data[CONF_LIST_UUID]

    async def _async_update_data(self) -> BringListData:
        try:
            new = await self.client.get_items(self.list_uuid)
        except BringAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except BringError as err:
            raise UpdateFailed(f"Bring nicht erreichbar: {err}") from err

        # Übergang „kaufen“ → „zuletzt gekauft“ erkennen (egal ob in HA oder in der Bring-App abgehakt)
        changed = False
        old = self.data
        purchase_now = {i.uuid for i in new.purchase}
        recently_now = {i.uuid for i in new.recently}
        if old is not None:
            was_open = {i.uuid for i in old.purchase}
            now = time.time()
            for uid in recently_now & was_open:
                if uid not in self.checked:
                    self.checked[uid] = now
                    changed = True
        for uid in list(self.checked):
            if uid in purchase_now or uid not in recently_now:
                del self.checked[uid]
                changed = True
        if changed:
            await self._async_save()
        return new
