"""DataUpdateCoordinator für die Einkaufsliste."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import BringAuthError, BringClient, BringError, BringListData
from .const import CONF_LIST_UUID, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN

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

    @property
    def list_uuid(self) -> str:
        return self.entry.data[CONF_LIST_UUID]

    async def _async_update_data(self) -> BringListData:
        try:
            return await self.client.get_items(self.list_uuid)
        except BringAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except BringError as err:
            raise UpdateFailed(f"Bring nicht erreichbar: {err}") from err
