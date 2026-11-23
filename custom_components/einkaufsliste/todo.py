"""To-do-Entität für die Bring-Liste."""

from __future__ import annotations

import uuid as uuidlib
from typing import Any

from homeassistant.components.todo import (
    TodoItem,
    TodoItemStatus,
    TodoListEntity,
    TodoListEntityFeature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import OP_PURCHASE, OP_RECENTLY, OP_REMOVE, BringError, BringItem
from .const import CONF_LIST_NAME, DOMAIN, VERSION
from .coordinator import EinkaufslisteCoordinator


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([EinkaufslisteTodo(entry.runtime_data)])


class EinkaufslisteTodo(CoordinatorEntity[EinkaufslisteCoordinator], TodoListEntity):
    """Bring-Liste als To-do-Liste (offen = kaufen, erledigt = zuletzt gekauft)."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_icon = "mdi:cart-variant"
    _attr_supported_features = (
        TodoListEntityFeature.CREATE_TODO_ITEM
        | TodoListEntityFeature.UPDATE_TODO_ITEM
        | TodoListEntityFeature.DELETE_TODO_ITEM
        | TodoListEntityFeature.SET_DESCRIPTION_ON_ITEM
    )

    def __init__(self, coordinator: EinkaufslisteCoordinator) -> None:
        super().__init__(coordinator)
        entry = coordinator.entry
        self._attr_unique_id = f"{entry.entry_id}_list"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.data.get(CONF_LIST_NAME, entry.title),
            manufacturer="Bring!",
            model="Einkaufsliste",
            sw_version=VERSION,
            entry_type=DeviceEntryType.SERVICE,
        )

    # ------------------------------------------------------------------ state
    @property
    def todo_items(self) -> list[TodoItem] | None:
        data = self.coordinator.data
        if data is None:
            return None
        items = [
            TodoItem(
                uid=item.uuid,
                summary=item.name,
                description=item.specification or None,
                status=TodoItemStatus.NEEDS_ACTION,
            )
            for item in data.purchase
        ]
        items += [
            TodoItem(
                uid=item.uuid,
                summary=item.name,
                description=item.specification or None,
                status=TodoItemStatus.COMPLETED,
            )
            for item in data.recently
        ]
        return items

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        entry = self.coordinator.entry
        return {
            "list_name": entry.data.get(CONF_LIST_NAME, entry.title),
            "einkaufsliste": True,
        }

    # ---------------------------------------------------------------- helpers
    def _find(self, uid: str) -> tuple[BringItem | None, bool]:
        data = self.coordinator.data
        for item in data.purchase:
            if item.uuid == uid:
                return item, True
        for item in data.recently:
            if item.uuid == uid:
                return item, False
        return None, False

    async def _send(self, changes: list[dict[str, str]]) -> None:
        try:
            await self.coordinator.client.batch_update(self.coordinator.list_uuid, changes)
        except BringError as err:
            raise HomeAssistantError(f"Bring-Liste konnte nicht geändert werden: {err}") from err
        finally:
            await self.coordinator.async_refresh()

    # ---------------------------------------------------------------- actions
    async def async_create_todo_item(self, item: TodoItem) -> None:
        name = (item.summary or "").strip()
        if not name:
            raise HomeAssistantError("Artikelname fehlt")
        op = OP_RECENTLY if item.status == TodoItemStatus.COMPLETED else OP_PURCHASE
        # Gibt es den Artikel schon (z. B. unter „Zuletzt gekauft“)? Dann wiederverwenden.
        existing = next(
            (
                i
                for i in (self.coordinator.data.purchase + self.coordinator.data.recently)
                if i.name.casefold() == name.casefold()
            ),
            None,
        )
        await self._send(
            [
                {
                    "itemId": existing.name if existing else name,
                    "spec": item.description or "",
                    "uuid": existing.uuid if existing else str(uuidlib.uuid4()),
                    "operation": op,
                }
            ]
        )

    async def async_update_todo_item(self, item: TodoItem) -> None:
        current, _ = self._find(item.uid)
        if current is None:
            raise HomeAssistantError("Artikel nicht gefunden")
        op = OP_RECENTLY if item.status == TodoItemStatus.COMPLETED else OP_PURCHASE
        new_name = (item.summary or current.name).strip()
        spec = item.description if item.description is not None else ""
        changes: list[dict[str, str]] = []
        if new_name != current.name:
            changes.append(
                {"itemId": current.name, "spec": "", "uuid": current.uuid, "operation": OP_REMOVE}
            )
        changes.append({"itemId": new_name, "spec": spec, "uuid": current.uuid, "operation": op})
        await self._send(changes)

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        changes = []
        for uid in uids:
            current, _ = self._find(uid)
            if current is not None:
                changes.append(
                    {"itemId": current.name, "spec": "", "uuid": current.uuid, "operation": OP_REMOVE}
                )
        if changes:
            await self._send(changes)

    @callback
    def _handle_coordinator_update(self) -> None:
        super()._handle_coordinator_update()
