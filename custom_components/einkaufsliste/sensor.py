"""Sensor „Offene Artikel“ – Anzahl für Android-Widgets, Automationen und Badges."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import CONF_LIST_NAME, DOMAIN
from .coordinator import EinkaufslisteCoordinator
from .widget import emoji_for, widget_html, widget_small_html


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([OffeneArtikelSensor(entry.runtime_data)])


class OffeneArtikelSensor(CoordinatorEntity[EinkaufslisteCoordinator], SensorEntity):
    """Anzahl offener Artikel – plus fertig gestalteter Widget-Text."""

    _attr_has_entity_name = True
    _attr_name = "Offene Artikel"
    _attr_icon = "mdi:cart"
    _attr_native_unit_of_measurement = "Artikel"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: EinkaufslisteCoordinator) -> None:
        super().__init__(coordinator)
        entry = coordinator.entry
        self._attr_unique_id = f"{entry.entry_id}_offene_artikel"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)})

    def _items(self) -> list[str]:
        data = self.coordinator.data
        return [i.name for i in data.purchase] if data else []

    @property
    def native_value(self) -> int:
        return len(self._items())

    @property
    def icon(self) -> str:
        return "mdi:cart-check" if not self._items() else "mdi:cart"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        items = self._items()
        entry = self.coordinator.entry
        list_name = entry.data.get(CONF_LIST_NAME, entry.title)
        # Anzeigename wie in der Karte (bei Alexa-/HA-Listen deren Name)
        reg = er.async_get(self.hass)
        for ent in er.async_entries_for_config_entry(reg, entry.entry_id):
            if ent.domain == "todo":
                state = self.hass.states.get(ent.entity_id)
                if state is not None:
                    list_name = state.attributes.get("list_name", list_name)
                break
        midnight = dt_util.start_of_local_day().timestamp()
        done_today = sum(1 for ts in self.coordinator.checked.values() if ts >= midnight)
        return {
            "artikel": items[:30],
            "artikel_mit_bild": [f"{emoji_for(n)} {n}" for n in items[:30]],
            "heute_erledigt": done_today,
            "liste": list_name,
            "widget": widget_html(list_name, items, done_today),
            "widget_klein": widget_small_html(items),
        }
