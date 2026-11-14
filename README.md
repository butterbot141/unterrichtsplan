# Unterrichtsmaterial

Materialsammlung als Web-App (GitHub Pages). Schülerinnen, Schüler und Lehrkräfte öffnen sie mit einem Zugangscode – ohne Konto. Bearbeitet wird direkt vom iPad oder Handy.

## Einrichten (einmalig, am Computer)

1. **Neues Repository** auf github.com anlegen, z. B. `unterricht`, **Public**.
   Wichtig: ein *neues* Repository verwenden. Alte, unverschlüsselte Dateien bleiben sonst im Verlauf sichtbar.
2. **Inhalt dieses Ordners hochladen** (*Add file → Upload files*, den Inhalt hineinziehen, nicht den Ordner selbst) → *Commit changes*.
3. **Pages einschalten:** *Settings → Pages → Deploy from a branch → main / (root) → Save*.
   Nach 1–2 Minuten: `https://BENUTZERNAME.github.io/unterricht/`
4. **Token erstellen:** Profilbild → *Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token*
   - *Only select repositories* → `unterricht`
   - *Repository permissions → Contents: Read and write*
   - Ablaufdatum setzen (z. B. 1 Jahr)
5. Seite öffnen → **Einstellungen** → Benutzername, Repository, Token → *Speichern und testen* → **Ersteinrichtung**:
   Zugangscode (z. B. 4 Ziffern), Prüfungspasswort (mind. 8 Zeichen), Schulform, Jahrgänge.
6. Über **+ Material** die ersten Dateien hochladen.

## Bedienung

- **+ Material** (oben): Datei oder Link hochladen, dabei Fach, Jahrgang, Reihe und Unterrichtsvorhaben wählen – auch neue anlegen.
  - *Für SuS*: am besten PDF oder HTML. *Für Lehrkräfte*: die bearbeitbare Word-/PowerPoint-Datei.
  - *Klassenarbeit / Test / Klausur* wird zusätzlich mit dem Prüfungspasswort verschlüsselt und nur im Lehrkraft-Bereich gezeigt.
- **Bearbeiten**: Reihen und Vorhaben anlegen, umbenennen, sortieren, löschen; Reihenübersicht hinterlegen; Reihen aus dem Kernlehrplan ergänzen.
- **Herunterladen**: Jahrgang oder alles als ZIP mit `Übersicht.html` – zum Weiterverwenden ohne diese Seite.
- **Einstellungen → Verwaltung**: Schulform für die Lehrplan-Vorlagen, Zugangscode oder Prüfungspasswort ändern.

## Mit dem Kurs teilen

- In einer Reihe auf **Mit Kurs teilen** tippen: Link und QR-Code.
- Über den Link sehen SuS nur diese Reihe – ohne Hauptmenü, ohne ausgeblendete Stunden, ohne Lehrkraft-Material.
- Ganz unten führt ein kleiner Link „Ganze Sammlung öffnen“ trotzdem zurück. Nichts ist geheim, es lenkt nur nicht ab.

## Überblick einer Reihe

- Concept-Map mit Karten (Thema, Begriff, Frage, Notiz), Verbindungen und optionalem Titelbild.
- Bearbeiten: **Bearbeiten → Überblick bearbeiten**. Karten ziehen, antippen zum Ändern, „Verbinden“ für Linien.

## Stunden ausblenden

- **Bearbeiten → Augen-Symbol** in der Zeile. Ausgeblendete Stunden sind in der Kursansicht nicht sichtbar.

## Planung importieren

- **Einstellungen → Verwaltung → Planung importieren**: ZIP mit `import.json` und Dateien (oder auf dem iPad: `import.json` und Dateien gemeinsam auswählen).
- Jeder Export enthält eine `import.json` – so lässt sich eine Sammlung in eine andere übernehmen.

## Mehrere Geräte

- Zum Ansehen: auf jedem Gerät einmal den Zugangscode eingeben.
- Zum Bearbeiten: auf jedem Gerät einmal in den Einstellungen GitHub-Name, Repository und Token eintragen.

## Als App installieren

- **iPad/iPhone (Safari):** Teilen → *Zum Home-Bildschirm*
- **Android (Chrome):** Menü → *App installieren*

## Was geschützt ist – und was nicht

- Alle Dateien und die Übersicht liegen **verschlüsselt** (AES-256) im Repository. Ohne Code sieht man nur Datensalat.
- Der Zugangscode ist eine **Zugangshürde** für einen abgegrenzten Personenkreis, kein Tresor: Ein vierstelliger Code lässt sich von technisch Versierten durchprobieren.
- Klassenarbeiten deshalb mit einem **langen** Prüfungspasswort schützen.
- Ein geänderter Code gilt für neue Anmeldungen. Alte Versionen der Zugangsdatei bleiben im Git-Verlauf.
- Keine Namen, Fotos oder Noten von SuS hochladen.

## Dateigrößen

- Möglichst **unter 15 MB** pro Datei (Warnung), höchstens 50 MB.
- Videos nicht hochladen, sondern verlinken.
- GitHub Pages: Seite bis 1 GB, ca. 100 GB Datenverkehr pro Monat. Ersetzte Dateien bleiben im Verlauf und zählen mit.

## Technik

```
index.html             App
data/zugang.json       Verschlüsselte Schlüssel (wird bei der Einrichtung erstellt)
data/inhalt.enc        Verschlüsselte Übersicht aller Einträge
material/…/*.enc       Verschlüsselte Dateien
lib/pdfjs/             PDF-Anzeige (pdf.js, Apache-2.0)
sw.js, manifest.webmanifest, icons/   App-Funktionen
```
