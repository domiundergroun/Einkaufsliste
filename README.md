# 🛒 Einkaufsliste (Bring!) für Home Assistant

Zeigt deine **Bring!-Einkaufsliste** als schöne Karte in Home Assistant – mit großen Kacheln, Bildern/Emojis, „Zuletzt gekauft“ und Bearbeiten per langem Drücken.

- Anmeldung bei Bring! und Listenauswahl direkt in den Home-Assistant-Einstellungen
- Eigene Lovelace-Karte `einkaufsliste-card` (wird automatisch geladen – keine Ressource nötig)
- Antippen = abhaken: der Artikel rutscht grau und durchgestrichen ans Ende der Liste. Nochmal antippen macht es rückgängig, um 0 Uhr verschwindet er.
- „Zuletzt gekauft“ antippen = wieder auf die Liste
- Hinzufügen mit Beschreibung: `Milch, 2 Liter`
- Langes Drücken / Rechtsklick = Name & Beschreibung bearbeiten oder löschen
- Kachel- oder Listenansicht, mehrere Farben, Hell- & Dunkelmodus
- Über 1.300 Stichwörter für Lebensmittel & Haushalt mit passendem Bild (auch zusammengesetzte Wörter wie „Vollkornbrot“ oder „Bergkäse“)
- **Reiter für Geschäfte**: Artikel lassen sich ALDI, Lidl, REWE, dm & Co. zuordnen – mit Logo
- Die Liste ist zusätzlich als normale To-do-Entität nutzbar (Automationen, Sprachassistent, To-do-Ansicht)

## Installation

### HACS (empfohlen)
1. HACS → ⋮ → **Benutzerdefinierte Repositories** → `https://github.com/domiundergroun/Einkaufsliste`, Typ **Integration**.
2. „Einkaufsliste (Bring!)“ herunterladen und Home Assistant neu starten.

### Manuell
Ordner `custom_components/einkaufsliste` nach `config/custom_components/` kopieren (oder die ZIP aus dem Release entpacken) und neu starten.

## Einrichtung
1. **Einstellungen → Geräte & Dienste → Integration hinzufügen → „Einkaufsliste (Bring!)“**
2. Bring!-E-Mail und Passwort eingeben (wer sich bei Bring mit Google/Apple anmeldet, legt zuerst in der Bring-App ein Passwort fest).
3. Liste auswählen – fertig.

Über **Konfigurieren** kannst du später eine andere Liste wählen und das Aktualisierungsintervall ändern.

## Geschäfte
1. **Einstellungen → Geräte & Dienste → Einkaufsliste (Bring!) → Konfigurieren** → unter „Deine Geschäfte“ auswählen (eigene Geschäfte mit Komma getrennt ergänzen).
2. In der Karte lange auf einen Artikel drücken → Geschäft wählen.
3. Sobald einem Geschäft Artikel zugeordnet sind, erscheint oben ein Reiter dafür:
   - **Allgemein** zeigt alle Artikel ohne Geschäft.
   - **Geschäfts-Reiter** erscheinen als Logo (mit Anzahl) – ohne Logo als farbiger Name – und zeigen „Nur bei …“ plus alle allgemeinen Artikel.
4. Die Zuordnung wird pro Artikelname gemerkt – kommt „Gouda“ wieder auf die Liste, landet er automatisch bei seinem Geschäft. Wer in einem Geschäfts-Reiter etwas hinzufügt, ordnet es direkt diesem Geschäft zu.

Die Logos werden in der Karte direkt über die Webseite des Geschäfts geladen. Ohne Internet erscheint ein farbiger Anfangsbuchstabe.

## Karte
Dashboard bearbeiten → Karte hinzufügen → **Einkaufsliste (Bring!)**. Alles ist im visuellen Editor einstellbar, oder per YAML:

```yaml
type: custom:einkaufsliste-card
entity: todo.zuhause
title: Einkaufen        # optional
layout: grid            # grid | list
accent: bring           # bring | smaragd | ozean | violett | orange | graphit | theme
sort: bring             # bring | alpha
show_recent: true
recent_limit: 24
show_tabs: true         # Reiter für Geschäfte
show_icons: false       # true = Bring-Bilder statt Emojis
```

Das Integrations-Logo wird ab Home Assistant 2026.3 angezeigt.

> Hinweis: Bring! bietet keine offizielle API. Die Integration nutzt dieselbe Schnittstelle wie die Bring-Apps.
