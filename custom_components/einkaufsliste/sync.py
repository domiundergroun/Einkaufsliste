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
from dataclasses import dataclass
from typing import Any

from homeassistant.components.todo import TodoItemStatus, TodoListEntityFeature
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.helpers.event import async_call_later, async_track_state_change_event
from homeassistant.helpers.storage import Store

from .backends import todo_entity_object
from .const import DOMAIN, STORAGE_VERSION

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


# --------------------------------------------------------------------------- Ausführung
class ListSync:
    """Hält die Hauptliste (Coordinator) mit einer oder mehreren Partner-Listen synchron."""

    def __init__(self, hass: HomeAssistant, coordinator, partners: list[str]) -> None:
        self.hass = hass
        self.coordinator = coordinator
        self.partners = [p for p in partners if p]
        self._store: Store[dict] = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}.sync.{coordinator.entry.entry_id}"
        )
        self._base: dict[str, dict[str, list]] = {}
        # Erwartete, noch nicht bestätigte Schreibvorgänge: (seite, partner, key) -> (alter Zustand, Zeit)
        self._expect: dict[tuple[str, str, str], tuple[tuple | None, float]] = {}
        self._unsubs: list[CALLBACK_TYPE] = []
        self._item_unsubs: dict[str, CALLBACK_TYPE] = {}
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
        self._base = {p: data.get(p, {}) for p in self.partners}

        @callback
        def _main_updated() -> None:
            if not self._notifying:
                self._schedule()

        self._unsubs.append(self.coordinator.async_add_listener(_main_updated))

        @callback
        def _state_changed(event: Event) -> None:
            self._subscribe_items()
            self._schedule()

        self._unsubs.append(async_track_state_change_event(self.hass, self.partners, _state_changed))
        self._subscribe_items()
        self._schedule(delay=5)

    @callback
    def async_stop(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()
        for unsub in self._item_unsubs.values():
            try:
                unsub()
            except Exception:  # noqa: BLE001
                pass
        self._item_unsubs.clear()
        if self._scheduled:
            self._scheduled()
            self._scheduled = None

    @callback
    def _subscribe_items(self) -> None:
        for eid in self.partners:
            if eid in self._item_unsubs:
                continue
            ent = todo_entity_object(self.hass, eid)
            if ent is not None and hasattr(ent, "async_subscribe_updates"):
                try:
                    self._item_unsubs[eid] = ent.async_subscribe_updates(lambda *_: self._schedule())
                except Exception:  # noqa: BLE001
                    pass

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

    # ------------------------------------------------------------------ Snapshots
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

    def _partner_supports_description(self, eid: str) -> bool:
        ent = todo_entity_object(self.hass, eid)
        feats = getattr(ent, "supported_features", 0) or 0
        return bool(feats & TodoListEntityFeature.SET_DESCRIPTION_ON_ITEM)

    def _partner_snapshot(self, eid: str) -> dict[str, Entry] | None:
        ent = todo_entity_object(self.hass, eid)
        if ent is None or ent.todo_items is None:
            return None
        use_desc = self._partner_supports_description(eid)
        result: dict[str, Entry] = {}
        # offene zuerst, damit sie bei Doppelungen gewinnen
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

    def _partner_summary(self, eid: str, name: str, spec: str) -> tuple[str, str | None]:
        """Name/Beschreibung für den Partner (ohne Beschreibungsfeld: „Milch (2 Liter)“)."""
        if self._partner_supports_description(eid):
            return name, spec
        return (f"{name} ({spec})" if spec else name), None

    # ------------------------------------------------------------------ Abgleich
    def _skip_keys(self, eid: str, main: dict[str, Entry], partner: dict[str, Entry]) -> set[str]:
        """Schlüssel, deren eigener Schreibvorgang noch nicht sichtbar ist."""
        skip: set[str] = set()
        now = time.time()
        for (side, pid, key), (old, ts) in list(self._expect.items()):
            if pid != eid:
                continue
            snap = main if side == "main" else partner
            current = snap[key].state if key in snap else None
            if now - ts > GRACE_SECONDS or current != old:
                del self._expect[(side, pid, key)]  # bestätigt (oder zu alt)
            else:
                skip.add(key)
        return skip

    async def async_sync(self) -> None:
        if self._lock.locked():
            self._schedule(delay=3)
            return
        async with self._lock:
            try:
                for eid in self.partners:
                    await self._sync_partner(eid)
                self.last_error = None
            except Exception as err:  # noqa: BLE001
                _LOGGER.warning("Synchronisierung fehlgeschlagen: %s", err)
                self.last_error = str(err)
            self.last_sync = time.time()
            await self._store.async_save(self._base)
            # Anzeige (letzter Abgleich) aktualisieren, ohne erneut einen Abgleich auszulösen
            self._notifying = True
            try:
                self.coordinator.async_update_listeners()
            finally:
                self._notifying = False

    async def _sync_partner(self, eid: str) -> None:
        partner = self._partner_snapshot(eid)
        main = self._main_snapshot()
        if partner is None or self.coordinator.data is None:
            return
        base = {k: tuple(v) for k, v in self._base.get(eid, {}).items()}
        skip = self._skip_keys(eid, main, partner)
        actions, new_base = plan(main, partner, base, skip)
        self._base[eid] = {k: list(v) for k, v in new_base.items()}
        if not actions:
            return
        _LOGGER.debug("Sync %s: %s", eid, actions)

        backend = self.coordinator.backend
        main_changed = False
        now = time.time()
        for action in actions:
            kind = action[0]
            try:
                if kind == "main_add":
                    _, name, spec = action
                    key = norm_key(name)
                    self._expect[("main", eid, key)] = (main[key].state if key in main else None, now)
                    await backend.async_add(self.coordinator.data, name, spec, False)
                    main_changed = True
                elif kind == "main_update":
                    _, key, status, spec = action
                    m = main[key]
                    self._expect[("main", eid, key)] = (m.state, now)
                    await backend.async_update(m.ref, m.ref.name, spec, status == DONE)
                    main_changed = True
                elif kind == "main_delete":
                    _, key = action
                    self._expect[("main", eid, key)] = (main[key].state, now)
                    await backend.async_delete([main[key].ref])
                    main_changed = True
                elif kind == "partner_add":
                    _, name, spec = action
                    key = norm_key(name)
                    self._expect[("partner", eid, key)] = (partner[key].state if key in partner else None, now)
                    summary, desc = self._partner_summary(eid, name, spec)
                    data: dict[str, Any] = {"item": summary}
                    if desc:
                        data["description"] = desc
                    await self._todo(eid, "add_item", data)
                elif kind == "partner_update":
                    _, key, status, spec = action
                    p = partner[key]
                    self._expect[("partner", eid, key)] = (p.state, now)
                    summary, desc = self._partner_summary(eid, p.name, spec)
                    data = {"item": p.ref, "status": "completed" if status == DONE else "needs_action"}
                    if desc is not None:
                        data["description"] = desc
                    elif summary != (f"{p.name} ({p.spec})" if p.spec else p.name):
                        data["rename"] = summary
                    await self._todo(eid, "update_item", data)
                elif kind == "partner_delete":
                    _, key = action
                    self._expect[("partner", eid, key)] = (partner[key].state, now)
                    await self._todo(eid, "remove_item", {"item": [partner[key].ref]})
            except Exception as err:  # noqa: BLE001
                _LOGGER.warning("Sync-Aktion %s für %s fehlgeschlagen: %s", action, eid, err)
                # Basis für diesen Artikel verwerfen → beim nächsten Lauf neu bewerten
                key = action[1] if kind.endswith(("update", "delete")) else norm_key(action[1])
                self._base[eid].pop(key, None)
                self._expect.pop(("main" if kind.startswith("main") else "partner", eid, key), None)

        if main_changed:
            await self.coordinator.async_refresh()

    async def _todo(self, eid: str, service: str, data: dict[str, Any]) -> None:
        await self.hass.services.async_call("todo", service, {"entity_id": eid, **data}, blocking=True)
