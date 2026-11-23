"""Konstanten für die Einkaufsliste-Integration."""

from __future__ import annotations

DOMAIN = "einkaufsliste"
VERSION = "1.1.1"

CONF_LIST_UUID = "list_uuid"
CONF_LIST_NAME = "list_name"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_STORES = "stores"
CONF_CUSTOM_STORES = "custom_stores"

DEFAULT_SCAN_INTERVAL = 60  # Sekunden
MIN_SCAN_INTERVAL = 15

FRONTEND_URL_BASE = "/einkaufsliste_static"
CARD_FILENAME = "einkaufsliste-card.js"

STORAGE_VERSION = 1

# id: (Anzeigename, Webseite für das Logo, Ersatz-Emoji)
STORE_CATALOG: dict[str, tuple[str, str | None, str]] = {
    "aldi_nord": ("ALDI Nord", "aldi-nord.de", "🛒"),
    "aldi_sued": ("ALDI SÜD", "aldi-sued.de", "🛒"),
    "lidl": ("Lidl", "lidl.de", "🛒"),
    "rewe": ("REWE", "rewe.de", "🛒"),
    "edeka": ("EDEKA", "edeka.de", "🛒"),
    "kaufland": ("Kaufland", "kaufland.de", "🛒"),
    "penny": ("PENNY", "penny.de", "🛒"),
    "netto": ("Netto Marken-Discount", "netto-online.de", "🛒"),
    "netto_scottie": ("Netto (Scottie)", "netto.de", "🛒"),
    "norma": ("NORMA", "norma-online.de", "🛒"),
    "globus": ("Globus", "globus.de", "🛒"),
    "marktkauf": ("Marktkauf", "marktkauf.de", "🛒"),
    "famila": ("famila", "famila.de", "🛒"),
    "tegut": ("tegut…", "tegut.com", "🛒"),
    "hit": ("HIT", "hit.de", "🛒"),
    "v_markt": ("V-Markt", "v-markt.de", "🛒"),
    "metro": ("METRO", "metro.de", "🛒"),
    "denns": ("denn's Biomarkt", "denns-biomarkt.de", "🌱"),
    "alnatura": ("Alnatura", "alnatura.de", "🌱"),
    "bio_company": ("BIO COMPANY", "biocompany.de", "🌱"),
    "dm": ("dm", "dm.de", "🧴"),
    "rossmann": ("Rossmann", "rossmann.de", "🧴"),
    "mueller": ("Müller", "mueller.de", "🧴"),
    "budni": ("Budni", "budni.de", "🧴"),
    "action": ("Action", "action.com", "🛍️"),
    "billa": ("BILLA (AT)", "billa.at", "🛒"),
    "spar_at": ("SPAR (AT)", "spar.at", "🛒"),
    "hofer": ("HOFER (AT)", "hofer.at", "🛒"),
    "migros": ("Migros (CH)", "migros.ch", "🛒"),
    "coop_ch": ("Coop (CH)", "coop.ch", "🛒"),
    "baeckerei": ("Bäckerei", None, "🥐"),
    "metzgerei": ("Metzgerei", None, "🥩"),
    "wochenmarkt": ("Wochenmarkt", None, "🧺"),
    "getraenkemarkt": ("Getränkemarkt", None, "🍺"),
    "apotheke": ("Apotheke", None, "💊"),
    "asia_markt": ("Asia-Markt", None, "🥢"),
    "baumarkt": ("Baumarkt", None, "🔨"),
    "tierbedarf": ("Tierbedarf", None, "🐾"),
}
