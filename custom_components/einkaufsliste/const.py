"""Konstanten für die Einkaufsliste-Integration."""

from __future__ import annotations

DOMAIN = "einkaufsliste"
VERSION = "1.0.0"

CONF_LIST_UUID = "list_uuid"
CONF_LIST_NAME = "list_name"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_SCAN_INTERVAL = 60  # Sekunden
MIN_SCAN_INTERVAL = 15

FRONTEND_URL_BASE = "/einkaufsliste_static"
CARD_FILENAME = "einkaufsliste-card.js"
