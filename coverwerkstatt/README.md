# Coverwerkstatt

Eine eigenständige Webseite zum schnellen quadratischen Zuschneiden von Hörspielcovern. Sie läuft vollständig im Browser, ohne Installation, Bibliotheken oder Bild-Upload.

## Verwenden

1. [Fertige HTML-Datei herunterladen](https://github.com/met-theokoch-schule/tessera-plugins/raw/refs/heads/main/downloads/coverwerkstatt.html) und per Doppelklick im Browser öffnen. Alternativ direkt `dist/index.html` aus diesem Ordner öffnen.
2. Bild in die Dropzone ziehen oder über **Bild auswählen** öffnen.
3. Den quadratischen Rahmen ziehen. Seine Kantenlänge entspricht immer der kürzeren Originalseite. Bei Hochformatbildern bewegt er sich vertikal, bei Querformatbildern horizontal.
4. Rechts den ausgewählten Ausschnitt prüfen und **Cover herunterladen** wählen. Das Ergebnis ist ein JPG in der Originalauflösung des ausgewählten Quadrats, beispielsweise `conni-cover.jpg`.

Die Position lässt sich auch mit dem Schieberegler ändern. **Zentrieren** setzt den Ausschnitt zurück in die Mitte. Bei fokussiertem Rahmen funktionieren die passenden Pfeiltasten, **Umschalt + Pfeiltaste** für größere Schritte sowie **Pos1/Ende** für beide Ränder. Maus, Stift und Touch verwenden denselben Pointer-Ereignispfad. Ein bereits quadratisches Bild benötigt keine Bewegung.

JPG, PNG, WebP und andere vom jeweiligen Browser unterstützte Bildformate lassen sich öffnen. Nicht lesbare Dateien werden verständlich gemeldet. Transparente Bildbereiche werden beim JPG-Export weiß. Die Quelldatei wird nicht verändert. Dateiname und Bildinhalt werden weder gespeichert noch übertragen; nach dem Schließen des Tabs ist kein Bildzustand abgelegt.

## Dateien und Prüfung

`dist/index.html` enthält die komplette Seite einschließlich CSS und JavaScript. Sie funktioniert auch über `file://`, ohne Webserver. `downloads/coverwerkstatt.html` im Repository ist die identische Downloadkopie. Nach Änderungen aktualisieren:

```sh
cp coverwerkstatt/dist/index.html downloads/coverwerkstatt.html
node --test coverwerkstatt/tests/*.test.mjs
```

Die Tests verwenden nur Node.js-Bordmittel; keine Paketinstallation nötig. Sie prüfen Zuschneidegeometrie, Grenzen, Skalierung, Tastaturbedienung sowie den tatsächlichen Seitencontroller mit DOM-/Bild-/Canvas-Doubles einschließlich Downloadkoordinaten und gleichzeitiger Ladevorgänge. Details und Grenzen stehen in `VALIDATION.md`.

Die `.openai/hosting.json` ist für eine private Sites-Veröffentlichung vorbereitet. Die Registrierung besteht, aber die Veröffentlichung wurde wegen des hier nicht erreichbaren Git-Hosts noch nicht ausgeführt. Die HTML-Datei ist davon unabhängig lokal nutzbar.
