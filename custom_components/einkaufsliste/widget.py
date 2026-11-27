"""Fertig gestalteter Text für das Android-Vorlagen-Widget (Home-Assistant-App).

Das Vorlagen-Widget zeigt einfaches HTML an (fett, Farben, groß/klein, Zeilenumbrüche, Emojis).
Die Bilder (Emojis) kommen aus demselben Katalog wie in der Karte.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from html import escape
from pathlib import Path

ACCENT = "#E5534B"
GREY = "#9AA0A6"
GREEN = "#2EB82E"


def fold_key(text: str) -> str:
    text = str(text or "").lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss"), ("é", "e"), ("è", "e"), ("ê", "e"),
                 ("á", "a"), ("à", "a"), ("â", "a"), ("ç", "c")):
        text = text.replace(a, b)
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


@lru_cache(maxsize=1)
def _index() -> dict[str, str]:
    path = Path(__file__).parent / "emoji_catalog.json"
    try:
        catalog = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    index: dict[str, str] = {}
    for emoji, words in catalog:
        for word in words.split(","):
            key = fold_key(word)
            if key and key not in index:
                index[key] = emoji
    return index


@lru_cache(maxsize=512)
def emoji_for(name: str) -> str:
    """Gleiche Logik wie in der Karte: exakt → Wort → Wortende → enthalten."""
    index = _index()
    key = fold_key(name)
    if key in index:
        return index[key]
    words = [w for w in key.split(" ") if w]
    for word in words:
        if word in index:
            return index[word]
    best = ""
    for k in index:
        if len(k) >= 4 and len(k) > len(best) and (key.endswith(k) or any(w.endswith(k) for w in words)):
            best = k
    if not best:
        for k in index:
            if len(k) >= 5 and len(k) > len(best) and k in key:
                best = k
    if best:
        return index[best]
    if words and words[-1].endswith("tee"):
        return "🍵"
    return "🛒"


def widget_html(list_name: str, items: list[str], done_today: int = 0, max_items: int = 6) -> str:
    """Großes Widget: Anzahl, Listenname und die ersten Artikel mit Bild."""
    count = len(items)
    title = escape(list_name or "Einkaufsliste")
    if count == 0:
        done = f"<br><small><font color='{GREY}'>✔️ heute {done_today} erledigt</font></small>" if done_today else ""
        return (
            "<p style='text-align:center'>"
            f"<big><big><big><big>🛒</big></big></big></big> <font color='{GREEN}'><big><big><big><b>✓</b></big></big></big></font><br>"
            f"<b>Alles eingekauft!</b><br><small><font color='{GREY}'>{title}</font></small>{done}</p>"
        )
    shown = [f"{emoji_for(n)} {escape(n)}" for n in items[:max_items]]
    lines = []
    for i in range(0, len(shown), 2):
        lines.append(" · ".join(shown[i:i + 2]))
    more = count - len(shown)
    if more > 0:
        lines.append(f"<font color='{ACCENT}'><b>+ {more} weitere</b></font>")
    done = f" · ✔️ {done_today}" if done_today else ""
    return (
        "<p style='text-align:center'>"
        f"<big><big><big><big>🛒</big></big></big></big> "
        f"<font color='{ACCENT}'><big><big><big><b>{count}</b></big></big></big></font><br>"
        f"<b>{title}</b><small><font color='{GREY}'>{done}</font></small><br>"
        f"<small><font color='{GREY}'>{'<br>'.join(lines)}</font></small></p>"
    )


def widget_small_html(items: list[str]) -> str:
    """Kleines Widget (1×1 / 2×1): nur Einkaufswagen und Anzahl."""
    count = len(items)
    if count == 0:
        return (
            "<p style='text-align:center'><big><big><big><big>🛒</big></big></big></big><br>"
            f"<font color='{GREEN}'><big><b>✓ erledigt</b></big></font></p>"
        )
    word = "Artikel"
    return (
        "<p style='text-align:center'>"
        f"<big><big><big><big>🛒</big></big></big></big><br>"
        f"<font color='{ACCENT}'><big><big><b>{count}</b></big></big></font> <small>{word}</small></p>"
    )
