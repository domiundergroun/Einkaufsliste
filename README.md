# 🛒 Einkaufsliste für Home Assistant

Zeigt deine **Einkaufsliste aus Bring!, Alexa oder Home Assistant** als schöne Karte in Home Assistant – mit großen Kacheln, Bildern/Emojis, „Zuletzt gekauft“ und Bearbeiten per langem Drücken.

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
1. **Einstellungen → Geräte & Dienste → Integration hinzufügen → „Einkaufsliste“**
2. Quelle wählen:
   - **Bring!** – E-Mail und Passwort eingeben (wer sich bei Bring mit Google/Apple anmeldet, legt zuerst in der Bring-App ein Passwort fest) und Liste auswählen.
   - **Alexa- oder Home-Assistant-Liste** – eine vorhandene To-do-Liste wählen.
3. Fertig. Die Quelle lässt sich jederzeit in der Karte über ⚙️ → Listen wechseln.

### Alexa
Die Anmeldung bei Amazon läuft über die offizielle Home-Assistant-Integration **„Alexa Devices“** (ab Home Assistant 2026.7 mit Einkaufs- und To-do-Listen). In der Karte unter ⚙️ → Listen → Alexa → „Bei Alexa anmelden“ geht es direkt dorthin; danach erscheinen die Alexa-Listen zur Auswahl.

### Home Assistant
Unter ⚙️ → Listen → Home Assistant kannst du jede vorhandene Liste (z. B. „Einkaufsliste“ oder lokale To-do-Listen) wählen oder direkt eine neue lokale Liste anlegen.

Alle Einstellungen (Geschäfte, Listen-Quelle, Bring-Zugang, Aktualisierung) findest du auch direkt in der Karte über das **Zahnrad ⚙️** oben rechts – oder unter **Konfigurieren** bei der Integration. Ändern dürfen das nur Administratoren.

## Synchronisieren (z. B. Alexa ↔ Bring!)
Unter ⚙️ → Listen → **Synchronisieren** wählst du weitere Listen, die in **beide Richtungen** mit deiner Hauptliste abgeglichen werden: Hinzufügen, Ändern, Abhaken und Löschen.

- Zuordnung über den Artikelnamen (Groß-/Kleinschreibung egal).
- Listen ohne Beschreibungsfeld (z. B. Alexa) bekommen die Menge in Klammern: „Milch (2 Liter)“.
- Beim ersten Abgleich werden beide Listen zusammengeführt; bereits erledigte Artikel (z. B. Bring „Zuletzt gekauft“) werden nicht kopiert.
- Ändern beide Seiten denselben Artikel gleichzeitig, gewinnt die Hauptliste.
- Verzögerung: so lange, wie die Listen zum Aktualisieren brauchen (Bring: dein Intervall, Alexa: je nach Integration).

## Geschäfte
1. **Einstellungen → Geräte & Dienste → Einkaufsliste (Bring!) → Konfigurieren** → unter „Deine Geschäfte“ auswählen (eigene Geschäfte mit Komma getrennt ergänzen).
2. In der Karte lange auf einen Artikel drücken → Geschäft wählen.
3. Sobald einem Geschäft Artikel zugeordnet sind, erscheint oben ein Reiter dafür:
   - **Allgemein** zeigt alle Artikel ohne Geschäft.
   - **Geschäfts-Reiter** erscheinen als Logo (mit Anzahl) – ohne Logo als farbiger Name – und zeigen „Nur bei …“ plus alle allgemeinen Artikel.
4. Beim Hinzufügen gibt es keine automatische Vorauswahl: Sind Geschäfts-Reiter eingeblendet, fragt ein Fenster „Wo kaufst du das?“ mit „Überall“ und den gerade sichtbaren Geschäften. Ohne Reiter landet der Artikel unter „Überall“.

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
