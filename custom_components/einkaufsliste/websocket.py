"""WebSocket-Befehle für die Einstellungen direkt in der Karte."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import BringAuthError, BringClient, BringError
from .const import (
    CONF_CUSTOM_STORES,
    CONF_LIST_NAME,
    CONF_LIST_UUID,
    CONF_SCAN_INTERVAL,
    CONF_STORES,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MIN_SCAN_INTERVAL,
    STORE_CATALOG,
)


@callback
def async_register(hass: HomeAssistant) -> None:
    websocket_api.async_register_command(hass, ws_get_settings)
    websocket_api.async_register_command(hass, ws_load_lists)
    websocket_api.async_register_command(hass, ws_save_settings)


def _entry_for(hass: HomeAssistant, entity_id: str) -> ConfigEntry | None:
    ent = er.async_get(hass).async_get(entity_id)
    if not ent or not ent.config_entry_id:
        return None
    entry = hass.config_entries.async_get_entry(ent.config_entry_id)
    return entry if entry and entry.domain == DOMAIN else None


async def _fetch_lists(hass: HomeAssistant, email: str, password: str) -> list[dict[str, str]]:
    client = BringClient(async_get_clientsession(hass), email, password)
    await client.login()
    return await client.get_lists()


def _catalog() -> list[dict[str, Any]]:
    return [
        {"id": sid, "name": name, "domain": domain, "emoji": emoji}
        for sid, (name, domain, emoji) in STORE_CATALOG.items()
    ]


def _err(err: Exception) -> str:
    if isinstance(err, BringAuthError):
        return "E-Mail oder Passwort ist falsch."
    return "Bring! ist gerade nicht erreichbar."


@websocket_api.websocket_command(
    {vol.Required("type"): "einkaufsliste/settings/get", vol.Required("entity_id"): str}
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_get_settings(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    entry = _entry_for(hass, msg["entity_id"])
    if entry is None:
        connection.send_error(msg["id"], "not_found", "Einkaufsliste nicht gefunden")
        return
    lists: list[dict[str, str]] = []
    lists_error = None
    try:
        lists = await _fetch_lists(hass, entry.data[CONF_EMAIL], entry.data[CONF_PASSWORD])
    except BringError as err:
        lists_error = _err(err)
    connection.send_result(
        msg["id"],
        {
            "catalog": _catalog(),
            "stores": list(entry.options.get(CONF_STORES, [])),
            "custom_stores": entry.options.get(CONF_CUSTOM_STORES, ""),
            "scan_interval": entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            "email": entry.data[CONF_EMAIL],
            "list_uuid": entry.data[CONF_LIST_UUID],
            "lists": lists,
            "lists_error": lists_error,
        },
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): "einkaufsliste/settings/lists",
        vol.Required("entity_id"): str,
        vol.Required("email"): str,
        vol.Optional("password"): str,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_load_lists(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """Mit (neuen) Zugangsdaten anmelden und Listen zurückgeben."""
    entry = _entry_for(hass, msg["entity_id"])
    if entry is None:
        connection.send_error(msg["id"], "not_found", "Einkaufsliste nicht gefunden")
        return
    password = msg.get("password") or entry.data[CONF_PASSWORD]
    try:
        lists = await _fetch_lists(hass, msg["email"].strip(), password)
    except BringError as err:
        connection.send_error(msg["id"], "login_failed", _err(err))
        return
    connection.send_result(msg["id"], {"lists": lists})


@websocket_api.websocket_command(
    {
        vol.Required("type"): "einkaufsliste/settings/save",
        vol.Required("entity_id"): str,
        vol.Required("stores"): [str],
        vol.Optional("custom_stores", default=""): str,
        vol.Optional("email"): str,
        vol.Optional("password"): str,
        vol.Optional("list_uuid"): str,
        vol.Optional("scan_interval"): vol.All(vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL, max=3600)),
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_save_settings(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    entry = _entry_for(hass, msg["entity_id"])
    if entry is None:
        connection.send_error(msg["id"], "not_found", "Einkaufsliste nicht gefunden")
        return

    data = dict(entry.data)
    email = (msg.get("email") or data[CONF_EMAIL]).strip()
    password = msg.get("password") or data[CONF_PASSWORD]
    list_uuid = msg.get("list_uuid") or data[CONF_LIST_UUID]
    title = entry.title
    unique_id = entry.unique_id

    account_changed = email != data[CONF_EMAIL] or password != data[CONF_PASSWORD]
    if account_changed or list_uuid != data[CONF_LIST_UUID]:
        try:
            lists = await _fetch_lists(hass, email, password)
        except BringError as err:
            connection.send_error(msg["id"], "login_failed", _err(err))
            return
        match = next((lst for lst in lists if lst["uuid"] == list_uuid), None)
        if match is None:
            connection.send_error(msg["id"], "list_missing", "Bitte eine Liste auswählen.")
            return
        for other in hass.config_entries.async_entries(DOMAIN):
            if other.entry_id != entry.entry_id and other.unique_id == list_uuid:
                connection.send_error(
                    msg["id"], "already_configured", "Diese Liste ist bereits als eigener Eintrag eingerichtet."
                )
                return
        data.update(
            {CONF_EMAIL: email, CONF_PASSWORD: password, CONF_LIST_UUID: list_uuid, CONF_LIST_NAME: match["name"]}
        )
        title = match["name"]
        unique_id = list_uuid

    known = set(STORE_CATALOG)
    options = dict(entry.options)
    options[CONF_STORES] = [sid for sid in msg["stores"] if sid in known]
    options[CONF_CUSTOM_STORES] = msg.get("custom_stores", "").strip()
    if "scan_interval" in msg:
        options[CONF_SCAN_INTERVAL] = msg["scan_interval"]

    hass.config_entries.async_update_entry(
        entry, data=data, options=options, title=title, unique_id=unique_id
    )
    connection.send_result(msg["id"], {"reloading": True})
