# Unterrichtsmaterial

Materialsammlung für SuS als installierbare Web-App (GitHub Pages). Öffnen ohne Anmeldung, Bearbeiten direkt am iPad oder Handy.

## Einrichten (einmalig)

1. **Repository anlegen:** github.com → *New repository* → Name z. B. `unterricht` → **Public**.
2. **Dateien hochladen:** *Add file → Upload files* → den **Inhalt** dieses Ordners hineinziehen (nicht den Ordner selbst) → *Commit changes*.
3. **Pages einschalten:** *Settings → Pages → Source: Deploy from a branch* → Branch `main`, Ordner `/ (root)` → *Save*.
4. Nach 1–2 Minuten ist die Seite erreichbar unter
   `https://BENUTZERNAME.github.io/unterricht/`

## Bearbeiten vom Handy/iPad

1. **Token erstellen:** github.com → Profilbild → *Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token*
   - Repository access: **Only select repositories** → `unterricht`
   - Permissions → Repository → **Contents: Read and write**
   - Ablaufdatum setzen (z. B. 1 Jahr)
2. Seite öffnen → unten **Einstellungen** → Benutzername, Repository, Token eintragen → *Speichern und testen*.
3. Oben erscheint **Bearbeiten**. Damit Fächer, Jahrgänge, Themen, Unterrichtsvorhaben und Materialien anlegen, ändern, sortieren und löschen.
4. Änderungen sind nach ca. 1–2 Minuten für alle sichtbar.

Der Token bleibt nur auf deinem Gerät. Nie in eine Datei schreiben. Bei Verlust des Geräts den Token auf GitHub löschen.

## Als App installieren

- **iPad/iPhone (Safari):** Teilen → *Zum Home-Bildschirm*
- **Android (Chrome):** Menü → *App installieren* bzw. *Zum Startbildschirm hinzufügen*

## Aufbau

```
index.html            App (Ansicht + Bearbeiten)
data/inhalt.json      Alle Einträge (wird von der App gepflegt)
material/FACH/JAHRGANG/THEMA/   Hochgeladene Dateien
sw.js, manifest.webmanifest, icons/   App-Funktionen
```

## Dateigrößen

- Ziel: Dateien möglichst **unter 10 MB** (die App warnt darüber, blockiert über 50 MB).
- Präsentationen zusätzlich als **PDF** hochladen – öffnet auf jedem Gerät.
- Videos nicht hochladen, sondern **verlinken** (z. B. YouTube „nicht gelistet“).
- Gelöschte oder ersetzte Dateien bleiben im Git-Verlauf und zählen weiter zum Speicher.
- Grenzen von GitHub Pages: Seite höchstens 1 GB, ca. 100 GB Datenverkehr pro Monat.

## Wichtig

- Alles im Repository ist **öffentlich** – auch über direkte Links und im Verlauf.
- Keine Namen, Fotos oder Noten von SuS hochladen.
- Klassenarbeiten erst nach dem Schreiben hochladen.
- Fremde Bilder/Screenshots nur, wenn die Rechte geklärt sind (sonst verlinken oder eigene Bilder nutzen).
