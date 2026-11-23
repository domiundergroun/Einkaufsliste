"""Synchronisierung der Hauptliste mit weiteren To-do-Listen (z. B. Alexa ↔ Bring!).

Prinzip: Dreiwege-Abgleich über den Artikelnamen.
Für jedes Partner-Paar wird der zuletzt abgeglichene Stand („Basis“) gespeichert.
Weicht nur eine Seite von der Basis ab, wird ihre Änderung auf die andere übertragen.
Weichen beide ab, gewinnt die Hauptliste. So entstehen keine Endlosschleifen.
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from homeassistant.components.todo import TodoItemStatus, TodoListEntityFeature
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.helpers.event import (
    async_call_later,
    async_track_state_change_event,
    async_track_time_interval,
)
from homeassistant.helpers.storage import Store

from .api import BringClient
from .backends import BringBackend, todo_entity_object
from .const import DOMAIN, STORAGE_VERSION

BRING_PREFIX = "bring:"

_LOGGER = logging.getLogger(__name__)

OPEN = "open"
DONE = "done"
GRACE_SECONDS = 180  # so lange auf die Bestätigung eigener Schreibvorgänge warten
SPEC_RE = re.compile(r"^(.*?)\s*\(([^()]*)\)\s*$")


def norm_key(name: str) -> str:
    return " ".join(name.strip().lower().split())


@dataclass
class Entry:
    name: str
    status: str
    spec: str
    ref: Any = None  # BringItem (Hauptliste) bzw. uid (Partner)

    @property
    def state(self) -> tuple[str, str]:
        return (self.status, self.spec)


# --------------------------------------------------------------------------- Planung
def plan(
    main: dict[str, Entry],
    partner: dict[str, Entry],
    base: dict[str, tuple[str, str]],
    skip: set[str] | None = None,
) -> tuple[list[tuple], dict[str, tuple[str, str]]]:
    """Aktionen berechnen. Gibt (Aktionen, neue Basis) zurück.

    Aktionen: ("main_add", name, spec) · ("main_update", key, status, spec) · ("main_delete", key)
              ("partner_add", name, spec) · ("partner_update", key, status, spec) · ("partner_delete", key)
    """
    skip = skip or set()
    actions: list[tuple] = []
    new_base: dict[str, tuple[str, str]] = {}

    for key in set(main) | set(partner) | set(base):
        m, p, b = main.get(key), partner.get(key), base.get(key)
        if key in skip:
            if b is not None:
                new_base[key] = b
            continue

        if m and p:
            if m.state == p.state:
                new_base[key] = m.state
            elif b is None:
                # Erster Abgleich: offen gewinnt, Beschreibung der Hauptliste bevorzugen
                status = OPEN if OPEN in (m.status, p.status) else DONE
                spec = m.spec or p.spec
                if m.state != (status, spec):
                    actions.append(("main_update", key, status, spec))
                if p.state != (status, spec):
                    actions.append(("partner_update", key, status, spec))
                new_base[key] = (status, spec)
            elif p.state == b:  # nur Hauptliste geändert
                actions.append(("partner_update", key, m.status, m.spec))
                new_base[key] = m.state
            elif m.state == b:  # nur Partner geändert
                actions.append(("main_update", key, p.status, p.spec))
                new_base[key] = p.state
            else:  # beide geändert → Hauptliste gewinnt
                actions.append(("partner_update", key, m.status, m.spec))
                new_base[key] = m.state

        elif m and not p:
            if b is None:
                if m.status == OPEN:  # neu in der Hauptliste
                    actions.append(("partner_add", m.name, m.spec))
                    new_base[key] = m.state
                # erledigte Altlasten (z. B. Bring „Zuletzt gekauft“) nicht übertragen
            elif m.state == b:  # im Partner gelöscht
                if m.status == OPEN:
                    actions.append(("main_delete", key))
                # erledigt: Hauptliste behalten (Partner räumt Erledigtes oft selbst auf)
            elif m.status == OPEN:  # in der Hauptliste wieder geöffnet → im Partner neu anlegen
                actions.append(("partner_add", m.name, m.spec))
                new_base[key] = m.state

        elif p and not m:
            if b is None:
                if p.status == OPEN:  # neu im Partner (z. B. per Alexa)
                    actions.append(("main_add", p.name, p.spec))
                    new_base[key] = p.state
            elif p.state == b:  # in der Hauptliste gelöscht
                if p.status == OPEN:
                    actions.append(("partner_delete", key))
            elif p.status == OPEN:  # im Partner wieder geöffnet
                actions.append(("main_add", p.name, p.spec))
                new_base[key] = p.state
        # weder noch: Basis-Eintrag verfällt

    return actions, new_base


# --------------------------------------------------------------------------- Partner
class EntityPartner:
    """Partner: beliebige To-do-Liste in Home Assistant (z. B. Alexa-Einkaufsliste)."""

    def __init__(self, hass: HomeAssistant, entity_id: str) -> None:
        self.hass = hass
        self.id = entity_id
        self._item_unsub: CALLBACK_TYPE | None = None
        self._unsubs: list[CALLBACK_TYPE] = []

    @property
    def name(self) -> str:
        state = self.hass.states.get(self.id)
        return state.name if state else self.id

    def start(self, on_change: Callable[[], None]) -> None:
        @callback
        def _state_changed(event: Event) -> None:
            self._subscribe(on_change)
            on_change()

        self._unsubs.append(async_track_state_change_event(self.hass, [self.id], _state_changed))
        self._subscribe(on_change)

    @callback
    def _subscribe(self, on_change: Callable[[], None]) -> None:
        if self._item_unsub is not None:
            return
        ent = todo_entity_object(self.hass, self.id)
        if ent is not None and hasattr(ent, "async_subscribe_updates"):
            try:
                self._item_unsub = ent.async_subscribe_updates(lambda *_: on_change())
            except Exception:  # noqa: BLE001
                self._item_unsub = None

    def stop(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()
        if self._item_unsub:
            try:
                self._item_unsub()
            except Exception:  # noqa: BLE001
                pass
            self._item_unsub = None

    def _supports_description(self) -> bool:
        ent = todo_entity_object(self.hass, self.id)
        feats = getattr(ent, "supported_features", 0) or 0
        return bool(feats & TodoListEntityFeature.SET_DESCRIPTION_ON_ITEM)

    def _summary(self, name: str, spec: str) -> tuple[str, str | None]:
        """Ohne Beschreibungsfeld steht die Menge in Klammern: „Milch (2 Liter)“."""
        if self._supports_description():
            return name, spec
        return (f"{name} ({spec})" if spec else name), None

    async def snapshot(self) -> dict[str, Entry] | None:
        ent = todo_entity_object(self.hass, self.id)
        if ent is None or ent.todo_items is None:
            return None
        use_desc = self._supports_description()
        result: dict[str, Entry] = {}
        items = sorted(ent.todo_items, key=lambda i: i.status == TodoItemStatus.COMPLETED)
        for item in items:
            summary = (item.summary or "").strip()
            if not summary:
                continue
            spec = (item.description or "").strip() if use_desc else ""
            name = summary
            if not use_desc:
                match = SPEC_RE.match(summary)
                if match and match.group(1).strip():
                    name, spec = match.group(1).strip(), match.group(2).strip()
            key = norm_key(name)
            if key in result:
                continue
            status = DONE if item.status == TodoItemStatus.COMPLETED else OPEN
            result[key] = Entry(name, status, spec, item.uid or summary)
        return result

    async def _todo(self, service: str, data: dict[str, Any]) -> None:
        await self.hass.services.async_call("todo", service, {"entity_id": self.id, **data}, blocking=True)

    async def add(self, name: str, spec: str) -> None:
        summary, desc = self._summary(name, spec)
        data: dict[str, Any] = {"item": summary}
        if desc:
            data["description"] = desc
        await self._todo("add_item", data)

    async def update(self, entry: Entry, status: str, spec: str) -> None:
        summary, desc = self._summary(entry.name, spec)
        data: dict[str, Any] = {"item": entry.ref, "status": "completed" if status == DONE else "needs_action"}
        if desc is not None:
            data["description"] = desc
        elif summary != (f"{entry.name} ({entry.spec})" if entry.spec else entry.name):
            data["rename"] = summary
        await self._todo("update_item", data)

    async def delete(self, entry: Entry) -> None:
        await self._todo("remove_item", {"item": [entry.ref]})


class BringPartner:
    """Partner: eine weitere Bring!-Liste (mit den gespeicherten Bring-Zugangsdaten)."""

    def __init__(self, hass: HomeAssistant, client: BringClient, list_uuid: str, interval: int) -> None:
        self.hass = hass
        self.id = f"{BRING_PREFIX}{list_uuid}"
        self.backend = BringBackend(client, list_uuid)
        self.interval = max(15, int(interval))
        self.name = "Bring!"
        self._unsub: CALLBACK_TYPE | None = None
        self._data = None

    def start(self, on_change: Callable[[], None]) -> None:
        self._unsub = async_track_time_interval(
            self.hass, lambda _now: on_change(), timedelta(seconds=self.interval)
        )

    def stop(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None

    async def snapshot(self) -> dict[str, Entry] | None:
        if self.name == "Bring!":
            try:
                lists = await self.backend.client.get_lists()
                match = next((l for l in lists if l["uuid"] == self.backend.list_uuid), None)
                if match:
                    self.name = f"Bring! · {match['name']}"
            except Exception:  # noqa: BLE001
                pass
        self._data = await self.backend.async_fetch()
        result: dict[str, Entry] = {}
        for status, items in ((OPEN, self._data.purchase), (DONE, self._data.recently)):
            for item in items:
                key = norm_key(item.name)
                if key and key not in result:
                    result[key] = Entry(item.name, status, item.specification or "", item)
        return result

    async def add(self, name: str, spec: str) -> None:
        await self.backend.async_add(self._data, name, spec, False)

    async def update(self, entry: Entry, status: str, spec: str) -> None:
        await self.backend.async_update(entry.ref, entry.ref.name, spec, status == DONE)

    async def delete(self, entry: Entry) -> None:
        await self.backend.async_delete([entry.ref])


# --------------------------------------------------------------------------- Ausführung
class ListSync:
    """Hält die Hauptliste (Coordinator) mit einer oder mehreren Partner-Listen synchron."""

    def __init__(self, hass: HomeAssistant, coordinator, partners: list) -> None:
        self.hass = hass
        self.coordinator = coordinator
        self.partners = partners  # EntityPartner | BringPartner
        self._store: Store[dict] = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}.sync.{coordinator.entry.entry_id}"
        )
        self._base: dict[str, dict[str, list]] = {}
        # Erwartete, noch nicht bestätigte Schreibvorgänge: (seite, partner, key) -> (alter Zustand, Zeit)
        self._expect: dict[tuple[str, str, str], tuple[tuple | None, float]] = {}
        self._unsubs: list[CALLBACK_TYPE] = []
        self._lock = asyncio.Lock()
        self._scheduled: CALLBACK_TYPE | None = None
        self.last_sync: float | None = None
        self.last_error: str | None = None
        self._notifying = False

    # ------------------------------------------------------------------ Start/Stopp
    async def async_start(self) -> None:
        if not self.partners:
            return
        data = await self._store.async_load() or {}
        self._base = {p.id: data.get(p.id, {}) for p in self.partners}

        @callback
        def _main_updated() -> None:
            if not self._notifying:
                self._schedule()

        self._unsubs.append(self.coordinator.async_add_listener(_main_updated))
        for partner in self.partners:
            partner.start(self._schedule)
        self._schedule(delay=5)

    @callback
    def async_stop(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()
        for partner in self.partners:
            partner.stop()
        if self._scheduled:
            self._scheduled()
            self._scheduled = None

    @callback
    def _schedule(self, delay: float = 2) -> None:
        """Mehrere Änderungen kurz sammeln und dann einmal abgleichen."""
        if self._scheduled:
            self._scheduled()

        @callback
        def _run(_now) -> None:
            self._scheduled = None
            self.hass.async_create_task(self.async_sync())

        self._scheduled = async_call_later(self.hass, delay, _run)

    # ------------------------------------------------------------------ Abgleich
    def _main_snapshot(self) -> dict[str, Entry]:
        data = self.coordinator.data
        result: dict[str, Entry] = {}
        if data is None:
            return result
        for status, items in ((OPEN, data.purchase), (DONE, data.recently)):
            for item in items:
                key = norm_key(item.name)
                if key and key not in result:
                    result[key] = Entry(item.name, status, item.specification or "", item)
        return result

    def _skip_keys(self, pid: str, main: dict[str, Entry], partner: dict[str, Entry]) -> set[str]:
        """Schlüssel, deren eigener Schreibvorgang noch nicht sichtbar ist."""
        skip: set[str] = set()
        now = time.time()
        for (side, p, key), (old, ts) in list(self._expect.items()):
            if p != pid:
                continue
            snap = main if side == "main" else partner
            current = snap[key].state if key in snap else None
            if now - ts > GRACE_SECONDS or current != old:
                del self._expect[(side, p, key)]  # bestätigt (oder zu alt)
            else:
                skip.add(key)
        return skip

    async def async_sync(self) -> None:
        if self._lock.locked():
            self._schedule(delay=3)
            return
        async with self._lock:
            errors = []
            for partner in self.partners:
                try:
                    await self._sync_partner(partner)
                except Exception as err:  # noqa: BLE001
                    _LOGGER.warning("Synchronisierung mit %s fehlgeschlagen: %s", partner.id, err)
                    errors.append(f"{partner.name}: {err}")
            self.last_error = "; ".join(errors) or None
            self.last_sync = time.time()
            await self._store.async_save(self._base)
            # Anzeige (letzter Abgleich) aktualisieren, ohne erneut einen Abgleich auszulösen
            self._notifying = True
            try:
                self.coordinator.async_update_listeners()
            finally:
                self._notifying = False

    async def _sync_partner(self, partner) -> None:
        pid = partner.id
        snap = await partner.snapshot()
        main = self._main_snapshot()
        if snap is None or self.coordinator.data is None:
            return
        base = {k: tuple(v) for k, v in self._base.get(pid, {}).items()}
        skip = self._skip_keys(pid, main, snap)
        actions, new_base = plan(main, snap, base, skip)
        self._base[pid] = {k: list(v) for k, v in new_base.items()}
        if not actions:
            return
        _LOGGER.debug("Sync %s: %s", pid, actions)

        backend = self.coordinator.backend
        main_changed = False
        now = time.time()
        for action in actions:
            kind = action[0]
            key = action[1] if kind.endswith(("update", "delete")) else norm_key(action[1])
            side = "main" if kind.startswith("main") else "partner"
            current = (main if side == "main" else snap).get(key)
            self._expect[(side, pid, key)] = (current.state if current else None, now)
            try:
                if kind == "main_add":
                    await backend.async_add(self.coordinator.data, action[1], action[2], False)
                    main_changed = True
                elif kind == "main_update":
                    m = main[key]
                    await backend.async_update(m.ref, m.ref.name, action[3], action[2] == DONE)
                    main_changed = True
                elif kind == "main_delete":
                    await backend.async_delete([main[key].ref])
                    main_changed = True
                elif kind == "partner_add":
                    await partner.add(action[1], action[2])
                elif kind == "partner_update":
                    await partner.update(snap[key], action[2], action[3])
                elif kind == "partner_delete":
                    await partner.delete(snap[key])
            except Exception as err:  # noqa: BLE001
                _LOGGER.warning("Sync-Aktion %s für %s fehlgeschlagen: %s", action, pid, err)
                # Basis für diesen Artikel verwerfen → beim nächsten Lauf neu bewerten
                self._base[pid].pop(key, None)
                self._expect.pop((side, pid, key), None)

        if main_changed:
            await self.coordinator.async_refresh()
