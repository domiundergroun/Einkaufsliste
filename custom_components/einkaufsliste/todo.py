"""To-do-Entität der Einkaufsliste (Quelle: Bring! oder eine Home-Assistant-Liste)."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.todo import (
    TodoItem,
    TodoItemStatus,
    TodoListEntity,
    TodoListEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import BringItem
from .const import CONF_LIST_NAME, CONF_SOURCE, CONF_TARGET_ENTITY, DOMAIN, SOURCE_BRING, VERSION
from .coordinator import EinkaufslisteCoordinator


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([EinkaufslisteTodo(entry.runtime_data)])
    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        "set_store",
        {vol.Required("item"): cv.string, vol.Optional("store", default=""): vol.Any(None, cv.string)},
        "async_set_store",
    )


class EinkaufslisteTodo(CoordinatorEntity[EinkaufslisteCoordinator], TodoListEntity):
    """Einkaufsliste als To-do-Liste (offen = kaufen, erledigt = zuletzt gekauft)."""

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
        source = entry.data.get(CONF_SOURCE, SOURCE_BRING)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.data.get(CONF_LIST_NAME, entry.title),
            manufacturer="Bring!" if source == SOURCE_BRING else "Home Assistant",
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
        source = entry.data.get(CONF_SOURCE, SOURCE_BRING)
        name = entry.data.get(CONF_LIST_NAME, entry.title)
        if source != SOURCE_BRING:
            target = self.hass.states.get(entry.data.get(CONF_TARGET_ENTITY, ""))
            if target is not None:
                name = target.attributes.get("friendly_name", name)
        return {
            "list_name": name,
            "einkaufsliste": True,
            "source": source,
            "stores": self.coordinator.stores,
            "assignments": dict(self.coordinator.assignments),
            "checked": {uid: round(ts) for uid, ts in self.coordinator.checked.items()},
            # Für Widgets/Vorlagen (z. B. Android-Template-Widget): offene Artikel
            "anzahl": len(self.coordinator.data.purchase) if self.coordinator.data else 0,
            "artikel": [i.name for i in (self.coordinator.data.purchase if self.coordinator.data else [])][:30],
            **self._sync_attrs(),
        }

    def _sync_attrs(self) -> dict[str, Any]:
        sync = self.coordinator.sync
        if sync is None:
            return {"sync": []}
        partners = []
        for partner in sync.partners:
            partners.append({"entity_id": partner.id, "name": partner.name})
        return {
            "sync": partners,
            "sync_last": round(sync.last_sync) if sync.last_sync else None,
            "sync_error": sync.last_error,
        }

    async def async_set_store(self, item: str, store: str | None = "") -> None:
        """Artikel (per Name oder UID) einem Geschäft zuordnen; leer = allgemein."""
        current, _ = self._find(item)
        name = current.name if current else item
        await self.coordinator.async_set_store(name, store or None)

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

    async def _refresh(self) -> None:
        await self.coordinator.async_refresh()

    # ---------------------------------------------------------------- actions
    async def async_create_todo_item(self, item: TodoItem) -> None:
        name = (item.summary or "").strip()
        if not name:
            raise HomeAssistantError("Artikelname fehlt")
        try:
            await self.coordinator.backend.async_add(
                self.coordinator.data,
                name,
                item.description or "",
                item.status == TodoItemStatus.COMPLETED,
            )
        finally:
            await self._refresh()

    async def async_update_todo_item(self, item: TodoItem) -> None:
        current, _ = self._find(item.uid)
        if current is None:
            raise HomeAssistantError("Artikel nicht gefunden")
        new_name = (item.summary or current.name).strip()
        spec = item.description if item.description is not None else ""
        if new_name != current.name:
            await self.coordinator.async_rename_assignment(current.name, new_name)
        try:
            await self.coordinator.backend.async_update(
                current, new_name, spec, item.status == TodoItemStatus.COMPLETED
            )
        finally:
            await self._refresh()

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        items = [found for uid in uids if (found := self._find(uid)[0]) is not None]
        try:
            await self.coordinator.backend.async_delete(items)
        finally:
            await self._refresh()
