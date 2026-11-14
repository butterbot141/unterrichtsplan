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

- **Bearbeiten** → pro Unterrichtsvorhaben zwei Knöpfe:
  - **+ Unterrichtsmaterial** (für SuS): PDF, interaktive Seite (HTML), Link, Video-Link. Mit dem **Auge** daneben ein- und ausblenden.
  - **+ Lehrkraft-Material**: Word-/PowerPoint-Dateien, Lösungen, Klassenarbeiten. Für SuS **nie** sichtbar.
  - Art und Titel werden aus dem Dateinamen vorgeschlagen („Lösung“ → Lösung, „Klausur/Test/KA“ → Prüfung, `.html` → interaktive Seite).
  - *Klassenarbeit / Test / Klausur* landet immer im Lehrkraft-Bereich und wird zusätzlich mit dem Prüfungspasswort verschlüsselt.
- **+ Material** (oben): wie oben, mit Auswahl von Fach, Jahrgang, Reihe und Vorhaben – auch neue anlegen.
- **Bearbeiten**: außerdem Reihen und Vorhaben anlegen, umbenennen, sortieren, löschen; Titelbild hinterlegen; Reihen aus dem Kernlehrplan ergänzen.
- **Herunterladen**: Jahrgang oder alles als ZIP mit `Übersicht.html` – zum Weiterverwenden ohne diese Seite.
- **Einstellungen → Verwaltung**: Schulform für die Lehrplan-Vorlagen, Zugangscode oder Prüfungspasswort ändern.

## Mit dem Kurs teilen

- In einer Reihe auf **Mit Kurs teilen** tippen: Link und QR-Code.
- Über den Link sehen SuS nur diese Reihe – ohne Hauptmenü, ohne Ausgeblendetes, ohne Lehrkraft-Material. Das Gerät merkt sich die Reihe.
- Ganz unten: **Alle Materialien herunterladen** – ein ZIP mit allem, was SuS sehen (z. B. zur Vorbereitung auf einen Test).
- **Zurück zur ganzen Sammlung (Lehrkraft):**
  - Auf Geräten mit eingetragenem Token gibt es oben den Knopf **Lehrkraft-Ansicht**; diese Geräte bleiben nie im Kursmodus hängen.
  - Auf anderen Geräten: **5× schnell auf das Fach-Schild** (z. B. „Physik 8“) tippen oder die Adresse mit `#/einstellungen` aufrufen → **Kursansicht auf diesem Gerät beenden**.

## Titelbild einer Reihe

- Ein Bild pro Reihe, z. B. Foto oder Export der Concept-Map oder Fragensammlung (außerhalb der App erstellt).
- **Bearbeiten → Titelbild hinzufügen/ändern**. Große Bilder werden beim Hochladen verkleinert.
- Wird oben in der Reihe ganz angezeigt (nicht abgeschnitten); antippen öffnet es groß.

## Interaktive HTML-Seiten

- HTML-Dateien öffnen sich in der App. Oben gibt es **Zurück** und, wenn es in der Reihe weitergeht, **Weiter**.
- Damit eine Seite selbst zur Oberfläche zurückführt, reichen normale Links:
  - `<a href="#zurueck">Zurück zur Übersicht</a>` – schließt die Seite und zeigt wieder die Reihe
  - `<a href="#weiter">Weiter</a>` – öffnet das nächste Material der Reihe
  - `<a href="um:material:Nachricht an Lena">AB öffnen</a>` – öffnet ein Material der Reihe mit genau diesem Titel
  - in JavaScript: `Plattform.zurueck()`, `Plattform.weiter()`, `Plattform.oeffne('Titel')`
- Speichert die Seite etwas mit `localStorage` (z. B. Fortschritt oder Antworten), bleibt das auf dem Gerät erhalten – getrennt für jede Seite.
- Externe Links öffnen sich in einem neuen Tab.
- Sicherheit: Die Seiten laufen abgeschottet. Sie kommen nicht an Zugangscode, Token oder andere Daten der App.

## Ausblenden

- **Stunden:** Bearbeiten → Augen-Symbol rechts in der Zeile.
- **Einzelne Materialien:** Bearbeiten → Augen-Symbol neben dem Material.
- In der Kursansicht ist Ausgeblendetes unsichtbar, in der Lehrkraft-Ansicht abgedimmt.

## Ordner vom Laptop hochladen (Sammel-Upload)

- **Einstellungen → Verwaltung → Ordner oder Dateien hochladen**, im Bearbeiten-Modus auch in Jahrgang und Reihe. Am Laptop: Ordner wählen oder einfach auf die Seite bzw. auf eine Zeile ziehen. Auf dem iPad: Ordner in der Dateien-App komprimieren und die ZIP wählen, oder mehrere Dateien auf einmal auswählen.
- Erwartete Ablage (wie bisher): `… / 2526 M 6 / M 6 Brüche / M 6 Brüche - 2 Bruchrechnung Fehler.pdf`
  - **Fach und Jahrgang** aus Ordnernamen wie „2526 M 6“, „M 6 Brüche“ oder „Ph Q2“ (M/Ma/Mathe, P/Ph/Physik; 5–10, EF, Q1, Q2).
  - **Reihe** = Ordner, in dem die Dateien liegen („M 6 Brüche“ → Reihe „Brüche“).
  - **Unterrichtsvorhaben** = Nummer am Anfang des Dateinamens (einstellbar: Unterordner oder alles in ein Vorhaben).
  - **Art** aus Dateiname und Endung („Lösung“, „Klausur/Test/KA“, `.html`, `.pptx` …), **Titel** aus dem Dateinamen.
  - **PDF und Word/PowerPoint mit gleichem Namen**: PDF für SuS, Original im Lehrkraft-Bereich. Word/PowerPoint ohne PDF landet im Lehrkraft-Bereich.
  - Ignoriert werden versteckte Dateien und Word-Sperrdateien (`~$…`). Videos werden nicht hochgeladen. `.url`-Verknüpfungen werden zu Links.
- **Vorschau** vor dem Hochladen: Ziel (Fach, Jahrgang, Reihe, Vorhaben), Art, Titel und Bereich pro Datei prüfen und ändern; Dateien abwählen.
- **Erneut ausführen = Abgleich**: Unveränderte Dateien werden übersprungen, geänderte ersetzt. Auf dem Laptop gelöschte Dateien bleiben in der Sammlung.
- Das passt zur Arbeitsweise: Am Laptop liegt die vollständige Sicherung aller Jahre, in der Sammlung nur, was für den aktuellen Durchgang gebraucht wird.

## Planung importieren und Sicherung wiederherstellen

- **Einstellungen → Verwaltung → Planung importieren / Sicherung wiederherstellen**: ZIP mit `import.json` und Dateien (oder auf dem iPad: `import.json` und Dateien gemeinsam auswählen).
  - **Ergänzen**: Vorhandene Reihen und Vorhaben mit gleichem Namen werden ergänzt, nichts wird überschrieben.
  - **Alles ersetzen**: stellt eine Sicherung („Alles herunterladen“) vollständig wieder her – Fächer mit Farben, Reihenfolge, Ausgeblendetes, Titelbilder, Datei zur Reihe, Lehrkraft-Dateien, Kurs-Links. Prüfungen nur mit Prüfungspasswort (beim Sichern und beim Wiederherstellen).
- Tipp: Ab und zu **Einstellungen → Alles herunterladen** mit eingegebenem Prüfungspasswort und die ZIP am Laptop ablegen.

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

- Möglichst **unter 15 MB** pro Datei (Warnung), höchstens 50 MB. Bei großen PowerPoints für SuS lieber ein PDF hochladen.
- Videos werden nicht hochgeladen, sondern verlinkt. Bilder werden automatisch verkleinert.
- **Einstellungen → Speicherplatz** zeigt den belegten Platz gesamt und pro Fach/Jahrgang, dazu die Größe des Repositorys inkl. Verlauf. Warnung ab ca. 800 MB.
- GitHub Pages: Seite bis 1 GB, ca. 100 GB Datenverkehr pro Monat. Ersetzte Dateien bleiben im Verlauf und zählen mit.
- **Wird es eng:** ein Fach in ein eigenes Repository (eigene Sammlung) auslagern und hier unter *Fach bearbeiten → Adresse* verlinken. Die Startseite zeigt dann einen Knopf zur anderen Sammlung.

## Technik

```
index.html             App
data/zugang.json       Verschlüsselte Schlüssel (wird bei der Einrichtung erstellt)
data/inhalt.enc        Verschlüsselte Übersicht aller Einträge
material/…/*.enc       Verschlüsselte Dateien
lib/pdfjs/             PDF-Anzeige (pdf.js, Apache-2.0)
sw.js, manifest.webmanifest, icons/   App-Funktionen
```
