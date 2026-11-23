"""WebSocket-Befehle für die Einstellungen direkt in der Karte."""

from __future__ import annotations

import asyncio
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.config_entries import SOURCE_USER, ConfigEntry
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
    CONF_SOURCE,
    CONF_STORES,
    CONF_TARGET_ENTITY,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MIN_SCAN_INTERVAL,
    SOURCE_BRING,
    SOURCE_ENTITY,
    STORE_CATALOG,
)

# Integrationen, die die Alexa-Listen als To-do-Entitäten bereitstellen
ALEXA_PLATFORMS = {"alexa_devices", "alexa_media", "alexa_todo_lists", "alexa_shopping_list"}


@callback
def async_register(hass: HomeAssistant) -> None:
    websocket_api.async_register_command(hass, ws_get_settings)
    websocket_api.async_register_command(hass, ws_load_lists)
    websocket_api.async_register_command(hass, ws_create_list)
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


def _todo_lists(hass: HomeAssistant) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """(Alexa-Listen, sonstige Home-Assistant-Listen) – ohne die eigenen Einkaufslisten."""
    reg = er.async_get(hass)
    alexa: list[dict[str, str]] = []
    other: list[dict[str, str]] = []
    for state in sorted(hass.states.async_all("todo"), key=lambda s: s.name.lower()):
        ent = reg.async_get(state.entity_id)
        platform = ent.platform if ent else ""
        if platform == DOMAIN:
            continue
        item = {"entity_id": state.entity_id, "name": state.name, "platform": platform}
        (alexa if platform in ALEXA_PLATFORMS else other).append(item)
    return alexa, other


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
    email = entry.data.get(CONF_EMAIL, "")
    if email and entry.data.get(CONF_PASSWORD):
        try:
            lists = await _fetch_lists(hass, email, entry.data[CONF_PASSWORD])
        except BringError as err:
            lists_error = _err(err)
    alexa, other = _todo_lists(hass)
    connection.send_result(
        msg["id"],
        {
            "catalog": _catalog(),
            "stores": list(entry.options.get(CONF_STORES, [])),
            "custom_stores": entry.options.get(CONF_CUSTOM_STORES, ""),
            "scan_interval": entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            "source": entry.data.get(CONF_SOURCE, SOURCE_BRING),
            "target_entity": entry.data.get(CONF_TARGET_ENTITY, ""),
            "email": email,
            "has_password": bool(entry.data.get(CONF_PASSWORD)),
            "list_uuid": entry.data.get(CONF_LIST_UUID, ""),
            "lists": lists,
            "lists_error": lists_error,
            "alexa_configured": bool(hass.config_entries.async_entries("alexa_devices")),
            "alexa_lists": alexa,
            "ha_lists": other,
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
    """Mit (neuen) Bring-Zugangsdaten anmelden und Listen zurückgeben."""
    entry = _entry_for(hass, msg["entity_id"])
    if entry is None:
        connection.send_error(msg["id"], "not_found", "Einkaufsliste nicht gefunden")
        return
    password = msg.get("password") or entry.data.get(CONF_PASSWORD, "")
    if not password:
        connection.send_error(msg["id"], "login_failed", "Bitte das Bring!-Passwort eingeben.")
        return
    try:
        lists = await _fetch_lists(hass, msg["email"].strip(), password)
    except BringError as err:
        connection.send_error(msg["id"], "login_failed", _err(err))
        return
    connection.send_result(msg["id"], {"lists": lists})


@websocket_api.websocket_command(
    {
        vol.Required("type"): "einkaufsliste/settings/create_list",
        vol.Required("entity_id"): str,
        vol.Required("name"): vol.All(str, vol.Length(min=1, max=80)),
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_create_list(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """Neue lokale Liste („Local To-do“) in Home Assistant anlegen."""
    name = msg["name"].strip()
    try:
        result = await hass.config_entries.flow.async_init(
            "local_todo", context={"source": SOURCE_USER}, data={"todo_list_name": name}
        )
    except Exception as err:  # noqa: BLE001
        connection.send_error(msg["id"], "create_failed", f"Liste konnte nicht angelegt werden: {err}")
        return
    if result.get("type") != "create_entry" or not result.get("result"):
        reason = result.get("reason") or result.get("errors") or "unbekannt"
        connection.send_error(msg["id"], "create_failed", f"Liste konnte nicht angelegt werden ({reason}).")
        return
    new_entry_id = result["result"].entry_id
    reg = er.async_get(hass)
    entity_id = None
    for _ in range(50):  # bis zu 10 s warten, bis die Entität existiert
        ents = [e for e in er.async_entries_for_config_entry(reg, new_entry_id) if e.domain == "todo"]
        if ents and hass.states.get(ents[0].entity_id):
            entity_id = ents[0].entity_id
            break
        await asyncio.sleep(0.2)
    if entity_id is None:
        connection.send_error(msg["id"], "create_failed", "Liste wurde angelegt, ist aber noch nicht bereit.")
        return
    _, other = _todo_lists(hass)
    connection.send_result(msg["id"], {"entity_id": entity_id, "ha_lists": other})


@websocket_api.websocket_command(
    {
        vol.Required("type"): "einkaufsliste/settings/save",
        vol.Required("entity_id"): str,
        vol.Required("stores"): [str],
        vol.Optional("custom_stores", default=""): str,
        vol.Optional("source"): vol.In([SOURCE_BRING, SOURCE_ENTITY]),
        vol.Optional("target_entity"): str,
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
    old_source = data.get(CONF_SOURCE, SOURCE_BRING)
    source = msg.get("source") or old_source
    title = entry.title
    unique_id = entry.unique_id

    def _taken(uid: str) -> bool:
        return any(
            other.entry_id != entry.entry_id and other.unique_id == uid
            for other in hass.config_entries.async_entries(DOMAIN)
        )

    # Bring-Zugangsdaten werden immer übernommen (auch wenn gerade eine andere Liste aktiv ist)
    email = (msg.get("email") or data.get(CONF_EMAIL, "")).strip()
    password = msg.get("password") or data.get(CONF_PASSWORD, "")

    if source == SOURCE_BRING:
        list_uuid = msg.get("list_uuid") or data.get(CONF_LIST_UUID, "")
        changed = (
            old_source != SOURCE_BRING
            or email != data.get(CONF_EMAIL)
            or password != data.get(CONF_PASSWORD)
            or list_uuid != data.get(CONF_LIST_UUID)
        )
        if changed:
            if not email or not password:
                connection.send_error(msg["id"], "login_failed", "Bitte Bring!-E-Mail und Passwort eingeben.")
                return
            try:
                lists = await _fetch_lists(hass, email, password)
            except BringError as err:
                connection.send_error(msg["id"], "login_failed", _err(err))
                return
            match = next((lst for lst in lists if lst["uuid"] == list_uuid), None)
            if match is None:
                connection.send_error(msg["id"], "list_missing", "Bitte eine Bring!-Liste auswählen.")
                return
            if _taken(list_uuid):
                connection.send_error(
                    msg["id"], "already_configured", "Diese Liste ist bereits als eigener Eintrag eingerichtet."
                )
                return
            data.update({CONF_LIST_UUID: list_uuid, CONF_LIST_NAME: match["name"]})
            title = match["name"]
            unique_id = list_uuid
        data.update({CONF_SOURCE: SOURCE_BRING, CONF_EMAIL: email, CONF_PASSWORD: password})
    else:
        target = msg.get("target_entity") or data.get(CONF_TARGET_ENTITY, "")
        state = hass.states.get(target) if target else None
        if state is None or not target.startswith("todo."):
            connection.send_error(msg["id"], "list_missing", "Bitte eine Liste auswählen.")
            return
        ent = er.async_get(hass).async_get(target)
        if ent and ent.platform == DOMAIN:
            connection.send_error(msg["id"], "list_missing", "Diese Liste kann nicht gewählt werden.")
            return
        if target != data.get(CONF_TARGET_ENTITY) or old_source != SOURCE_ENTITY:
            if _taken(target):
                connection.send_error(
                    msg["id"], "already_configured", "Diese Liste ist bereits als eigener Eintrag eingerichtet."
                )
                return
        data.update({CONF_SOURCE: SOURCE_ENTITY, CONF_TARGET_ENTITY: target, CONF_LIST_NAME: state.name})
        if email:
            data[CONF_EMAIL] = email
        if password:
            data[CONF_PASSWORD] = password
        title = state.name
        unique_id = target

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
