"""Einkaufsliste – zeigt deine Bring!-Liste schön in Home Assistant an."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .api import BringAuthError, BringClient, BringError
from .const import CARD_FILENAME, DOMAIN, FRONTEND_URL_BASE, VERSION
from .coordinator import EinkaufslisteCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.TODO]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type EinkaufslisteConfigEntry = ConfigEntry[EinkaufslisteCoordinator]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Karte (JavaScript) einmalig im Frontend registrieren."""
    frontend_dir = Path(__file__).parent / "frontend"
    await hass.http.async_register_static_paths(
        [StaticPathConfig(FRONTEND_URL_BASE, str(frontend_dir), False)]
    )
    add_extra_js_url(hass, f"{FRONTEND_URL_BASE}/{CARD_FILENAME}?v={VERSION}")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: EinkaufslisteConfigEntry) -> bool:
    """Eintrag einrichten."""
    client = BringClient(
        async_get_clientsession(hass), entry.data[CONF_EMAIL], entry.data[CONF_PASSWORD]
    )
    try:
        await client.login()
    except BringAuthError as err:
        raise ConfigEntryAuthFailed(str(err)) from err
    except BringError as err:
        raise ConfigEntryNotReady(str(err)) from err

    coordinator = EinkaufslisteCoordinator(hass, entry, client)
    await coordinator.async_load_assignments()
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Gespeicherte Geschäft-Zuordnungen löschen, wenn der Eintrag entfernt wird."""
    from homeassistant.helpers.storage import Store

    from .const import STORAGE_VERSION

    await Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}").async_remove()


async def async_unload_entry(hass: HomeAssistant, entry: EinkaufslisteConfigEntry) -> bool:
    """Eintrag entladen."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
