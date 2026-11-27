"""Einkaufsliste – zeigt deine Bring!-, Alexa- oder Home-Assistant-Liste schön an."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.typing import ConfigType

from . import websocket
from .api import BringAuthError, BringClient, BringError
from .backends import BringBackend, EntityBackend, ListBackend
from .const import (
    CARD_FILENAME,
    CONF_LIST_UUID,
    CONF_SCAN_INTERVAL,
    CONF_SOURCE,
    CONF_SYNC_ENABLED,
    CONF_SYNC_TARGETS,
    CONF_TARGET_ENTITY,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    FRONTEND_URL_BASE,
    SOURCE_BRING,
    VERSION,
)
from .coordinator import EinkaufslisteCoordinator
from .sync import BRING_PREFIX, BringPartner, EntityPartner, ListSync

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.TODO, Platform.SENSOR]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type EinkaufslisteConfigEntry = ConfigEntry[EinkaufslisteCoordinator]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Karte (JavaScript) einmalig im Frontend registrieren."""
    frontend_dir = Path(__file__).parent / "frontend"
    await hass.http.async_register_static_paths(
        [StaticPathConfig(FRONTEND_URL_BASE, str(frontend_dir), False)]
    )
    add_extra_js_url(hass, f"{FRONTEND_URL_BASE}/{CARD_FILENAME}?v={VERSION}")
    websocket.async_register(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: EinkaufslisteConfigEntry) -> bool:
    """Eintrag einrichten."""
    backend: ListBackend
    if entry.data.get(CONF_SOURCE, SOURCE_BRING) == SOURCE_BRING:
        client = BringClient(
            async_get_clientsession(hass), entry.data[CONF_EMAIL], entry.data[CONF_PASSWORD]
        )
        try:
            await client.login()
        except BringAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except BringError as err:
            raise ConfigEntryNotReady(str(err)) from err
        backend = BringBackend(client, entry.data[CONF_LIST_UUID])
    else:
        backend = EntityBackend(hass, entry.data[CONF_TARGET_ENTITY])

    coordinator = EinkaufslisteCoordinator(hass, entry, backend)
    await coordinator.async_load_assignments()
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    @callback
    def _source_changed() -> None:
        hass.async_create_task(coordinator.async_refresh())

    await backend.async_start(_source_changed)
    entry.async_on_unload(backend.async_stop)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    # Synchronisierung mit weiteren Listen (z. B. Alexa ↔ Bring!)
    if entry.options.get(CONF_SYNC_ENABLED, True):
        partners = _build_partners(hass, entry, backend)
        if partners:
            sync = ListSync(hass, coordinator, partners)
            coordinator.sync = sync
            await sync.async_start()
            entry.async_on_unload(sync.async_stop)

    async def _midnight(_now) -> None:
        await coordinator.async_midnight()

    entry.async_on_unload(async_track_time_change(hass, _midnight, hour=0, minute=0, second=0))
    return True


def _build_partners(hass: HomeAssistant, entry: ConfigEntry, backend: ListBackend) -> list:
    """Partner-Listen aus den Optionen erzeugen (HA-Listen und Bring-Listen)."""
    main_id = (
        f"{BRING_PREFIX}{entry.data.get(CONF_LIST_UUID)}"
        if entry.data.get(CONF_SOURCE, SOURCE_BRING) == SOURCE_BRING
        else entry.data.get(CONF_TARGET_ENTITY)
    )
    interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    client = backend.client if isinstance(backend, BringBackend) else None
    partners: list = []
    for pid in entry.options.get(CONF_SYNC_TARGETS, []):
        if not pid or pid == main_id:
            continue
        if pid.startswith(BRING_PREFIX):
            if client is None:
                if not (entry.data.get(CONF_EMAIL) and entry.data.get(CONF_PASSWORD)):
                    _LOGGER.warning("Bring-Liste %s kann ohne Bring-Anmeldung nicht synchronisiert werden", pid)
                    continue
                client = BringClient(
                    async_get_clientsession(hass), entry.data[CONF_EMAIL], entry.data[CONF_PASSWORD]
                )
            partners.append(BringPartner(hass, client, pid[len(BRING_PREFIX):], interval))
        else:
            partners.append(EntityPartner(hass, pid))
    return partners


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Gespeicherte Geschäft-Zuordnungen löschen, wenn der Eintrag entfernt wird."""
    from homeassistant.helpers.storage import Store

    from .const import STORAGE_VERSION

    await Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}").async_remove()
    await Store(hass, STORAGE_VERSION, f"{DOMAIN}.sync.{entry.entry_id}").async_remove()


async def async_unload_entry(hass: HomeAssistant, entry: EinkaufslisteConfigEntry) -> bool:
    """Eintrag entladen."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
