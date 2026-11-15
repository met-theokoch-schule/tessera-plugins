# Prüfstand 0.1.0

Ausgeführt in dieser Entwicklungsumgebung:

- 20 erfolgreiche Python-`unittest`-Tests: YAML-Validierung, Schlüssel-/ID-Duplikate, leere/fehlerhafte Listen, unbekannte Felder, URIs, Pfadausbruch, große Bibliotheken, Fensterauswahl; Wiedergabeszenarien A–G mit asynchronen MA-Mocks, Disc-Reihenfolge, fehlende Tracks, leere Alben und Auflösungsfehler.
- Nativer Test des **tatsächlichen Kachel-C++-Codes**, kompiliert mit Clang gegen Tessera's aktuelle originale Plugin-Header, ArduinoJson 7.x und LVGL 9.3: vertauschte Antwortreihenfolge, Öffnen, Blättern, Abspielen, Zurück, zwei unabhängige Instanzen, kein Play-Retry nach Timeout, sicheres Entfernen gelöschter Tiles. UI und Transport sind Fakes; dies ist kein Renderingtest.
- C++-Syntaxprüfung des Plugins gegen dieselben Originalheader. Nur der kleine ESPHome-`Component`-Basistyp und `millis()` sind im nativen Test ersetzt; keine erfundene Tessera-API.
- Offizieller unveränderter `tools/check.py` aus dem Referenzrepository, mit aktuellem `plugin_manifest.py` und `boards.json`: **Kidsplayer ok, needs ok, Plugin API 0.24**. Hinweis: kein `store.png`; das betrifft nur die Storevorschau.
- Python-Bytecodekompilierung des Companions erfolgreich.
- Vollständiger rekursiver Dateivergleich von `examples/new_music/` mit `plugins/new_music/` am geforderten Commit ohne Unterschiede, einschließlich Binärbildern.

Nicht ausgeführt bzw. nicht nachgewiesen:

- ESPHome-Konfigurationsprüfung und vollständiger Guition-ESP32-S3-Firmwarebuild: ESPHome, ESP-IDF-Toolchain und SDL-Umgebung stehen hier nicht bereit. Der native Header-/Navigationstest ersetzt diesen Build nicht.
- Import/Start der Custom Integration in einem real laufenden Home Assistant, deren Bildroute im echten HA-Router sowie Websocket-Kommunikation mit einem laufenden Tessera. Die vorhandene Installation wurde ausdrücklich nicht verändert.
- Apple-Music-/lokale Audiowiedergabe, echte Queue-Trackfortsetzung und Ende nach Track 8, Anbieter-Fallbacks, Gruppenplayer, MA-Benutzerrechte und Coverdarstellung auf dem 480 × 480-Panel. Dafür gilt der Abnahmeplan in `kidsplayer/README.md`.
- Pixeldarstellung, Bildatlas-RAMverbrauch, Animationstiming und Touch-Ergonomie auf echter Hardware.

## Reproduktion

```sh
python3 -m pip install -r requirements-dev.txt
python3 -m unittest discover -s kidsplayer/tests -v
TESSERA_MANIFEST=/path/to/core/screen_manager/app/plugin_manifest.py \
TESSERA_BOARDS=/path/to/core/screen_manager/app/boards.json \
python3 tools/check.py kidsplayer
sh tools/test-native.sh /path/to/core /path/to/ArduinoJson /path/to/lvgl
PYTHONPYCACHEPREFIX=/tmp/kidsplayer-pycache python3 -m compileall -q kidsplayer/backend
```

Der native Test nutzt `tests/support/esphome/core/component.h`, ausdrücklich einen Teststub. Ein echter Firmwarebau erfolgt nach lokaler Plugininstallation durch Tessera für das ausgewählte Guition. Wer ihn extern reproduziert, verwendet die durch Tessera für **dieses** Display erzeugte vollständige ESPHome-Konfiguration; hier wurde keine Boardkonfiguration erfunden.

## Git-Umgebung

Das Zielrepository war leer (kein Remote-Branch `main`). Der aktuelle Arbeitsordner erlaubt Projektdateien, sperrt jedoch `.git`-Schreibzugriffe. Git-Metadaten liegen während dieser Arbeit in `/private/tmp/kidsplayer-target.git`, mit dem Arbeitsbaum `/Users/moritz/Tessera`, Branch `main` und dem vom Auftrag vorgegebenen `origin`. Status/Commit werden daher mit `git --git-dir=/private/tmp/kidsplayer-target.git ...` ausgeführt. Ein normaler erneuter Clone aus GitHub erzeugt außerhalb dieser Einschränkung einen regulären Checkout. Keine zusätzlichen Verzeichnisebenen wurden im Projekt angelegt.

Der erste Implementierungscommit wurde lokal auf `main` erstellt. Pushversuche über HTTPS und SSH scheiterten an fehlenden Zugangsdaten (`could not read Username` beziehungsweise `Permission denied (publickey)`), nicht an einem Code- oder Mergekonflikt. Es wurde kein Force-Push verwendet. Ein ignoriertes `kidsplayer-0.1.0.bundle` im Projektordner sichert den vollständigen lokalen Branch unabhängig vom temporären Git-Verzeichnis.

Nach GitHub-Anmeldung kann aus dem aktuellen Arbeitsbaum mit den vorhandenen Metadaten gepusht werden:

```sh
git --git-dir=/private/tmp/kidsplayer-target.git push -u origin main
```

Falls diese temporären Metadaten nicht mehr existieren, in ein neues Verzeichnis wiederherstellen:

```sh
git clone /Users/moritz/Tessera/kidsplayer-0.1.0.bundle tessera-plugins
git -C tessera-plugins remote set-url origin https://github.com/met-theokoch-schule/tessera-plugins.git
git -C tessera-plugins push -u origin main
```
