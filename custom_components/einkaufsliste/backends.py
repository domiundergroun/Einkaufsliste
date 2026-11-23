"""Listen-Quellen: Bring! direkt oder eine beliebige To-do-Liste aus Home Assistant
(z. B. Alexa-Einkaufsliste aus „Alexa Devices“ oder eine lokale Liste)."""

from __future__ import annotations

import logging
import uuid as uuidlib
from collections.abc import Callable
from typing import Any

from homeassistant.components.todo import TodoItemStatus, TodoListEntityFeature
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import UpdateFailed

from .api import (
    OP_PURCHASE,
    OP_RECENTLY,
    OP_REMOVE,
    BringAuthError,
    BringClient,
    BringError,
    BringItem,
    BringListData,
)

_LOGGER = logging.getLogger(__name__)


class ListBackend:
    """Gemeinsame Schnittstelle."""

    source: str = ""

    async def async_start(self, on_change: Callable[[], None]) -> None:
        """Optional: auf Änderungen der Quelle lauschen."""

    def async_stop(self) -> None:
        """Lauschen beenden."""

    async def async_fetch(self) -> BringListData:
        raise NotImplementedError

    async def async_add(self, data: BringListData, name: str, spec: str, completed: bool) -> None:
        raise NotImplementedError

    async def async_update(self, item: BringItem, name: str, spec: str, completed: bool) -> None:
        raise NotImplementedError

    async def async_delete(self, items: list[BringItem]) -> None:
        raise NotImplementedError


# --------------------------------------------------------------------------- Bring
class BringBackend(ListBackend):
    source = "bring"

    def __init__(self, client: BringClient, list_uuid: str) -> None:
        self.client = client
        self.list_uuid = list_uuid

    async def async_fetch(self) -> BringListData:
        try:
            return await self.client.get_items(self.list_uuid)
        except BringAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except BringError as err:
            raise UpdateFailed(f"Bring nicht erreichbar: {err}") from err

    async def _send(self, changes: list[dict[str, str]]) -> None:
        try:
            await self.client.batch_update(self.list_uuid, changes)
        except BringError as err:
            raise HomeAssistantError(f"Bring-Liste konnte nicht geändert werden: {err}") from err

    async def async_add(self, data: BringListData, name: str, spec: str, completed: bool) -> None:
        # Gibt es den Artikel schon (z. B. unter „Zuletzt gekauft“)? Dann wiederverwenden.
        existing = next(
            (i for i in (data.purchase + data.recently) if i.name.casefold() == name.casefold()), None
        )
        await self._send(
            [
                {
                    "itemId": existing.name if existing else name,
                    "spec": spec,
                    "uuid": existing.uuid if existing else str(uuidlib.uuid4()),
                    "operation": OP_RECENTLY if completed else OP_PURCHASE,
                }
            ]
        )

    async def async_update(self, item: BringItem, name: str, spec: str, completed: bool) -> None:
        changes: list[dict[str, str]] = []
        if name != item.name:
            changes.append({"itemId": item.name, "spec": "", "uuid": item.uuid, "operation": OP_REMOVE})
        changes.append(
            {
                "itemId": name,
                "spec": spec,
                "uuid": item.uuid,
                "operation": OP_RECENTLY if completed else OP_PURCHASE,
            }
        )
        await self._send(changes)

    async def async_delete(self, items: list[BringItem]) -> None:
        if items:
            await self._send(
                [{"itemId": i.name, "spec": "", "uuid": i.uuid, "operation": OP_REMOVE} for i in items]
            )


# ------------------------------------------------------------- Home-Assistant-Liste
def todo_entity_object(hass: HomeAssistant, entity_id: str) -> Any | None:
    """Das Entitäts-Objekt einer To-do-Liste holen."""
    component = None
    try:
        from homeassistant.components.todo.const import DATA_COMPONENT  # noqa: PLC0415

        component = hass.data.get(DATA_COMPONENT)
    except ImportError:
        pass
    if component is None:
        component = hass.data.get("todo")
    return component.get_entity(entity_id) if component else None


class EntityBackend(ListBackend):
    """Spiegelt eine vorhandene To-do-Entität (Alexa, lokale Liste, Einkaufsliste …)."""

    source = "entity"

    def __init__(self, hass: HomeAssistant, entity_id: str) -> None:
        self.hass = hass
        self.entity_id = entity_id
        self._unsubs: list[CALLBACK_TYPE] = []
        self._item_unsub: CALLBACK_TYPE | None = None
        self._on_change: Callable[[], None] | None = None

    def _entity(self) -> Any:
        ent = todo_entity_object(self.hass, self.entity_id)
        if ent is None:
            raise UpdateFailed(f"Liste {self.entity_id} ist (noch) nicht verfügbar")
        return ent

    @callback
    def _subscribe_items(self) -> None:
        if self._item_unsub is not None:
            return
        ent = todo_entity_object(self.hass, self.entity_id)
        if ent is not None and hasattr(ent, "async_subscribe_updates"):
            try:
                self._item_unsub = ent.async_subscribe_updates(lambda *_: self._fire())
            except Exception:  # noqa: BLE001 – ältere HA-Versionen
                self._item_unsub = None

    @callback
    def _fire(self) -> None:
        if self._on_change:
            self._on_change()

    async def async_start(self, on_change: Callable[[], None]) -> None:
        self._on_change = on_change

        @callback
        def _state_changed(event: Event) -> None:
            # Entität wurde (neu) geladen → Abo erneuern
            if self._item_unsub is not None and todo_entity_object(self.hass, self.entity_id) is None:
                self._item_unsub = None
            self._subscribe_items()
            self._fire()

        self._unsubs.append(async_track_state_change_event(self.hass, [self.entity_id], _state_changed))
        self._subscribe_items()

    def async_stop(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()
        if self._item_unsub:
            try:
                self._item_unsub()
            except Exception:  # noqa: BLE001
                pass
            self._item_unsub = None

    async def async_fetch(self) -> BringListData:
        ent = self._entity()
        self._subscribe_items()
        data = BringListData()
        for item in ent.todo_items or []:
            entry = BringItem(
                uuid=item.uid or item.summary or "",
                name=item.summary or "",
                specification=item.description or "",
            )
            if not entry.name:
                continue
            if item.status == TodoItemStatus.COMPLETED:
                data.recently.append(entry)
            else:
                data.purchase.append(entry)
        return data

    def _supports_description(self) -> bool:
        ent = todo_entity_object(self.hass, self.entity_id)
        feats = getattr(ent, "supported_features", 0) or 0
        return bool(feats & TodoListEntityFeature.SET_DESCRIPTION_ON_ITEM)

    async def _call(self, service: str, data: dict[str, Any]) -> None:
        await self.hass.services.async_call(
            "todo", service, {"entity_id": self.entity_id, **data}, blocking=True
        )

    async def async_add(self, data: BringListData, name: str, spec: str, completed: bool) -> None:
        existing = next((i for i in data.recently if i.name.casefold() == name.casefold()), None)
        if existing and not completed:
            await self.async_update(existing, existing.name, spec or existing.specification, False)
            return
        payload: dict[str, Any] = {"item": name}
        if spec and self._supports_description():
            payload["description"] = spec
        await self._call("add_item", payload)
        if completed:
            await self._call("update_item", {"item": name, "status": "completed"})

    async def async_update(self, item: BringItem, name: str, spec: str, completed: bool) -> None:
        payload: dict[str, Any] = {
            "item": item.uuid,
            "status": "completed" if completed else "needs_action",
        }
        if name != item.name:
            payload["rename"] = name
        if self._supports_description() and spec != item.specification:
            payload["description"] = spec
        await self._call("update_item", payload)

    async def async_delete(self, items: list[BringItem]) -> None:
        if items:
            await self._call("remove_item", {"item": [i.uuid for i in items]})
