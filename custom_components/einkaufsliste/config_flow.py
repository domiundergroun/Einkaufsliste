"""Einrichtungsdialog: Bring-Login und Listenauswahl."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import BringAuthError, BringClient, BringConnectionError, BringError
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

STORE_SELECTOR = SelectSelector(
    SelectSelectorConfig(
        options=[
            SelectOptionDict(value=sid, label=f"{emoji} {name}" if not domain else name)
            for sid, (name, domain, emoji) in STORE_CATALOG.items()
        ],
        multiple=True,
        mode=SelectSelectorMode.DROPDOWN,
    )
)

_LOGGER = logging.getLogger(__name__)

LOGIN_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): TextSelector(
            TextSelectorConfig(type=TextSelectorType.EMAIL, autocomplete="email")
        ),
        vol.Required(CONF_PASSWORD): TextSelector(
            TextSelectorConfig(type=TextSelectorType.PASSWORD, autocomplete="current-password")
        ),
    }
)


def _list_selector(lists: list[dict[str, str]]) -> SelectSelector:
    return SelectSelector(
        SelectSelectorConfig(
            options=[SelectOptionDict(value=lst["uuid"], label=lst["name"]) for lst in lists],
            mode=SelectSelectorMode.LIST,
        )
    )


async def _login_and_fetch(hass, email: str, password: str) -> list[dict[str, str]]:
    client = BringClient(async_get_clientsession(hass), email, password)
    await client.login()
    return await client.get_lists()


class EinkaufslisteConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config Flow."""

    VERSION = 1

    def __init__(self) -> None:
        self._email: str | None = None
        self._password: str | None = None
        self._lists: list[dict[str, str]] = []

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Quelle wählen: Bring! oder eine vorhandene Liste (Alexa / Home Assistant)."""
        return self.async_show_menu(step_id="user", menu_options=["bring", "ha_list"])

    async def async_step_ha_list(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Vorhandene To-do-Liste aus Home Assistant verwenden (z. B. Alexa-Einkaufsliste)."""
        if user_input is not None:
            target = user_input[CONF_TARGET_ENTITY]
            await self.async_set_unique_id(target)
            self._abort_if_unique_id_configured()
            state = self.hass.states.get(target)
            name = state.attributes.get("friendly_name", target) if state else target
            return self.async_create_entry(
                title=name,
                data={CONF_SOURCE: SOURCE_ENTITY, CONF_TARGET_ENTITY: target, CONF_LIST_NAME: name},
                options={CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL},
            )
        own = [
            e.entity_id
            for e in er.async_get(self.hass).entities.values()
            if e.platform == DOMAIN
        ]
        return self.async_show_form(
            step_id="ha_list",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_TARGET_ENTITY): EntitySelector(
                        EntitySelectorConfig(domain="todo", exclude_entities=own)
                    )
                }
            ),
        )

    async def async_step_bring(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Bei Bring anmelden."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                self._lists = await _login_and_fetch(
                    self.hass, user_input[CONF_EMAIL], user_input[CONF_PASSWORD]
                )
            except BringAuthError:
                errors["base"] = "invalid_auth"
            except BringConnectionError:
                errors["base"] = "cannot_connect"
            except BringError:
                _LOGGER.exception("Unerwarteter Fehler beim Bring-Login")
                errors["base"] = "unknown"
            else:
                if not self._lists:
                    errors["base"] = "no_lists"
                else:
                    self._email = user_input[CONF_EMAIL]
                    self._password = user_input[CONF_PASSWORD]
                    return await self.async_step_list()

        return self.async_show_form(
            step_id="bring",
            data_schema=self.add_suggested_values_to_schema(LOGIN_SCHEMA, user_input),
            errors=errors,
        )

    async def async_step_list(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Schritt 2: Liste auswählen."""
        if user_input is not None:
            list_uuid = user_input[CONF_LIST_UUID]
            name = next((lst["name"] for lst in self._lists if lst["uuid"] == list_uuid), "Einkaufsliste")
            await self.async_set_unique_id(list_uuid)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=name,
                data={
                    CONF_SOURCE: SOURCE_BRING,
                    CONF_EMAIL: self._email,
                    CONF_PASSWORD: self._password,
                    CONF_LIST_UUID: list_uuid,
                    CONF_LIST_NAME: name,
                },
                options={CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL},
            )

        return self.async_show_form(
            step_id="list",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_LIST_UUID, default=self._lists[0]["uuid"]): _list_selector(
                        self._lists
                    )
                }
            ),
        )

    # ------------------------------------------------------------------ reauth
    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        self._email = entry_data[CONF_EMAIL]
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()
        if user_input is not None:
            try:
                await _login_and_fetch(self.hass, entry.data[CONF_EMAIL], user_input[CONF_PASSWORD])
            except BringAuthError:
                errors["base"] = "invalid_auth"
            except BringError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_reload_and_abort(
                    entry, data_updates={CONF_PASSWORD: user_input[CONF_PASSWORD]}
                )
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PASSWORD): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.PASSWORD)
                    )
                }
            ),
            description_placeholders={"email": entry.data[CONF_EMAIL]},
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return EinkaufslisteOptionsFlow()


class EinkaufslisteOptionsFlow(OptionsFlow):
    """Einstellungen: andere Liste wählen, Aktualisierungsintervall."""

    def __init__(self) -> None:
        self._lists: list[dict[str, str]] = []

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        entry = self.config_entry
        errors: dict[str, str] = {}
        is_bring = entry.data.get(CONF_SOURCE, SOURCE_BRING) == SOURCE_BRING

        if is_bring and not self._lists:
            try:
                self._lists = await _login_and_fetch(
                    self.hass, entry.data[CONF_EMAIL], entry.data[CONF_PASSWORD]
                )
            except BringAuthError:
                errors["base"] = "invalid_auth"
            except BringError:
                errors["base"] = "cannot_connect"

        if user_input is not None and not errors and not is_bring:
            return self.async_create_entry(
                data={
                    CONF_SCAN_INTERVAL: int(user_input[CONF_SCAN_INTERVAL]),
                    CONF_STORES: list(user_input.get(CONF_STORES, [])),
                    CONF_CUSTOM_STORES: (user_input.get(CONF_CUSTOM_STORES) or "").strip(),
                }
            )

        if user_input is not None and not errors:
            list_uuid = user_input[CONF_LIST_UUID]
            if list_uuid != entry.data[CONF_LIST_UUID]:
                for other in self.hass.config_entries.async_entries(DOMAIN):
                    if other.entry_id != entry.entry_id and other.unique_id == list_uuid:
                        errors["base"] = "already_configured"
                        break
            if not errors:
                name = next(
                    (lst["name"] for lst in self._lists if lst["uuid"] == list_uuid),
                    entry.data.get(CONF_LIST_NAME, "Einkaufsliste"),
                )
                if list_uuid != entry.data[CONF_LIST_UUID]:
                    self.hass.config_entries.async_update_entry(
                        entry,
                        unique_id=list_uuid,
                        title=name,
                        data={**entry.data, CONF_LIST_UUID: list_uuid, CONF_LIST_NAME: name},
                    )
                return self.async_create_entry(
                    data={
                        CONF_SCAN_INTERVAL: int(user_input[CONF_SCAN_INTERVAL]),
                        CONF_STORES: list(user_input.get(CONF_STORES, [])),
                        CONF_CUSTOM_STORES: (user_input.get(CONF_CUSTOM_STORES) or "").strip(),
                    }
                )

        if is_bring and errors and not self._lists:
            return self.async_show_form(step_id="init", data_schema=vol.Schema({}), errors=errors)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    **(
                        {
                            vol.Required(
                                CONF_LIST_UUID, default=entry.data[CONF_LIST_UUID]
                            ): _list_selector(self._lists)
                        }
                        if is_bring
                        else {}
                    ),
                    vol.Optional(
                        CONF_STORES, default=entry.options.get(CONF_STORES, [])
                    ): STORE_SELECTOR,
                    vol.Optional(
                        CONF_CUSTOM_STORES,
                        description={"suggested_value": entry.options.get(CONF_CUSTOM_STORES, "")},
                    ): TextSelector(TextSelectorConfig()),
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=MIN_SCAN_INTERVAL,
                            max=3600,
                            step=5,
                            unit_of_measurement="s",
                            mode=NumberSelectorMode.BOX,
                        )
                    ),
                }
            ),
            errors=errors,
        )
