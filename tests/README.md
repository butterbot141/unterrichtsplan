# Tests

Automatische Prüfung der App im Browser – mit einem **simulierten GitHub** (keine echten Daten, kein Token, Testcode `1234`, Testpasswort `pruefung123`).

## Ausführen

```
pip install playwright
python -m playwright install chromium   # einmalig, falls kein Chrome vorhanden
python tests/run.py                     # prüft die App im übergeordneten Ordner
```

* Optional: `CHROME=/pfad/zu/chrome python tests/run.py`
* Ergebnis: `OK …` / `FAIL …` pro Prüfung, am Ende `n/n bestanden`.
* Screenshots und Testdateien landen in `tests/out/` (nicht im Repository).

## Was geprüft wird

* Ersteinrichtung, Migration alter Daten (Datenmodell v1 → v2)
* Upload SuS-/Lehrkraft-Material, Prüfungen mit Prüfungspasswort, Videos abgelehnt, Titelbild verkleinert
* Kursansicht (nur SuS-Sichtbares, Lehrkraft-Knopf, versteckter Rückweg), SuS-ZIP
* Sammel-Upload mit Ordnerstruktur `2526 M 6 / M 6 Brüche / …`, Abgleich (unverändert/geändert), Drag-and-drop, Mehrfachauswahl
* HTML-Seiten: Abschottung, `#zurueck`/`#weiter`, Sprunglinks, gespeicherter Fortschritt
* Freischalten ab Datum, Hinweis-Banner, Checkliste (auch aus Word), Suche, Vorlage
* Notizen pro Vorhaben (nur Lehrkraft), Niveau ★/★★/★★★ (auch Kursansicht)
* Export → Import („Ergänzen“) und Sicherung → „Alles ersetzen“ (verlustfrei)

## Erweitern

Neue Prüfungen vor dem Abschnitt „C: Sicherung“ in `run.py` einfügen (`check('Name', Bedingung, Info)`).
Echte Unterrichtsmaterialien nicht ins Repository legen – Testdateien im Skript erzeugen.
