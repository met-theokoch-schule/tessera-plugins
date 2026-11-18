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

## Resize-Fix 0.1.1

Die Mindestgröße `2x2` führte bei einer initialen `1x1`-Kachel zu fehlenden Zugpunkten: Tessera's `resizeChoices` verändert nur eine Achse und hält die andere konstant. Somit war weder `2x1` noch `1x2` zulässig. Plugin 0.1.1 erlaubt `min: 1x1`; die Firmware berücksichtigt die kurzen Zwischenformate mit einer kompakten Anordnung ohne Titelzeile.

Erfolgreich ausgeführt:

- `kidsplayer/tests/test_resize.mjs` lädt die tatsächlichen Funktionen `spanOf`, `dimensions`, `tileSizeChoices` und `resizeChoices` aus dem untersuchten Tessera-Checkout. Mit leeren Seiten-/Store-Fixtures reproduziert es fehlende Griffe mit dem alten Manifest und prüft beide Vergrößerungswege zu `2x2` sowie das Verkleinern mit dem neuen Manifest.
- Nativer Test des tatsächlichen Kachelcodes erweitert um die Geometrie in kleinen, breiten, hohen und quadratischen Kacheln, Öffnen und Zurück-Navigation in diesen Formaten; erfolgreich.
- Offizieller Tessera-Validator für Plugin 0.1.1 mit API 0.24 erfolgreich. New-music-Referenz unverändert.

Editor-Regressionsprüfung (Node.js mit `node:module.stripTypeScriptTypes` und PyYAML):

```sh
python3 -c 'import json,yaml; print(json.dumps(yaml.safe_load(open("kidsplayer/tessera-plugin.yaml"))["tiles"][0]["sizes"]))' \
  | node kidsplayer/tests/test_resize.mjs /path/to/core
```

Kein Test am echten Display und kein Firmwarebuild für diesen Fix. Der HA-Companion bleibt auf Version 0.1.0, da er nicht geändert wurde. Die Aktualisierung betrifft das Pluginmanifest und die Display-Firmware; Installationshinweise stehen am Ende der Kidsplayer-README.

## Coverwechsel 0.1.2

Direkter Vergleich mit der unveränderten Referenz: Kidsplayer hatte nur Tessera's Picture-/Slide-Primitive verwendet, aber Geometrie (kleine quadratische Nachbarn statt schmaler voller Höhe), Distanz, Dauer (220 statt 320 ms) und Spiegelung vereinfacht. Außerdem startete der Slide vor der Backendantwort. Das konnte bei langsamen Antworten zu verschoben wartenden alten Bildern führen. Derselbe Mittelcover-URL kann bei Folgen desselben Albums keinen neuen Atlas erzeugen; Tessera's Slide-Reset hängt jedoch von einem neuen Atlas ab.

Korrigiert: Proportionen und Pitch der Referenz, Spiegelung in nicht kompakten Kacheln, keine Platzhalterbalken, kein doppeltes Nachbarcover bei zwei Einträgen. Slide nur mit den neuen Adressen in der erfolgreichen Browseantwort, bei unterschiedlicher nicht leerer Mittelcoveradresse. Kein Slide bei Fehlern, identischen/fehlenden Mittelbildern oder deaktivierter Animation. Weiterhin drei statt bis zu sieben Bildplätze und `contain` für das unbeschnittene Mittelcover.

Der ausgeführte native C++-Test prüft nun zusätzlich die Bewegung erst nach einer um fünf Sekunden verzögerten Backendantwort, beide Richtungen, tatsächlichen Mittenabstand und 320 ms, gleiche Albumcover ohne Slide, deaktivierte Animation, Fehlerantwort ohne Slide, Spiegelungsflags und volle Nachbarhöhe sowie Ein-/Zwei-Eintrag-Ansichten. Geometrie- und Navigationstests für kleine Kacheln bestehen weiter. Tessera's offizieller Validator akzeptiert Version 0.1.2 für API 0.24.

Keine Hardware-/Pixelabnahme: Die Test-Doubles zeichnen keine Animationsframes. Ob der tatsächliche Atlaswechsel auf dem Guition angenehm wirkt, bleibt im realen Betrieb zu prüfen. Keine Änderung am Companion und keine neue Bibliothekskonfiguration erforderlich.

## Original-Coverplätze 0.1.3

Die manuell eingeführte Begrenzung auf drei Plätze wurde entfernt. Die Bildplatz-Schleife (`spread`, `stepx`, `k=SIDE..1`, `inner`, beide `frames.push_back`) ist jetzt unverändert aus dem festgelegten New-music-Code übernommen. Ein automatischer Textvergleich gegen die unveränderte Referenz prüft genau diesen Block. Mittenplatz, Pitch und Duplikatregel folgen ebenfalls der Referenz. Die Höhenberechnung normaler Kacheln verwendet die Referenzformel im Bereich unter der Zurück-Zeile; kompakte Zwischenformate und `contain` bleiben Anpassungen an Kidsplayer.

Erfolgreich ausgeführt:

- 23 Python-Tests, darunter alle bisherigen Wiedergabe-/Konfigurationstests sowie Vergleich des unveränderten Originalblocks, tatsächliche Backend-Browsefunktion mit sieben Einträgen, zyklisches Fenster und Auflösung jedes Bildes nur einmal bei kleinen Bibliotheken.
- Sieben Objekte mit maximal langen Darstellungstexten/IDs und den echten kurzen Coveradressen passen unter Tessera's 3200-Byte-Antwortbudget. Keine Playback-URIs in der Antwort.
- Nativer C++-Test der tatsächlichen Kachel zeigt sieben angelegte Coverplätze in einer breiten/niedrigen Kachel, Außen-nach-innen-Reihenfolge und keine Duplikate für ein bis acht Bibliotheksobjekte. Vorhandene Tests für kompakte Kacheln, getrennte Instanzen, Animation und Fehler bestehen weiter.
- Offizieller Tessera-Validator für 0.1.3 / API 0.24 erfolgreich; Companion-Bytecode kompiliert; Referenzordner unverändert.

Wie im Original werden nicht vollständig passende äußere Cover weggelassen. Eine quadratische Kachel kann deshalb trotz sieben erlaubter Plätze drei sichtbare Cover haben. Es gibt weiterhin keinen Hardware-/Firmwarebuildnachweis; die nativen Tests ersetzen keine Pixel- oder Speicherprüfung auf dem Guition. Beide Teile müssen aktualisiert werden: Companion 0.1.3 plus Display-Firmware 0.1.3. Bibliotheks-YAML bleibt kompatibel.

## Wiedergabe-Kompatibilität 0.1.4

Im verbundenen System **nur lesend** ermittelt: HA 2026.11.1, Tessera 0.4.97, MA-Server 2.10.12. Das Core-Protokoll meldet `Kidsplayer-Wiedergabe fehlgeschlagen`; der MCP-Logzugriff liefert dabei keinen Traceback. Der offizielle HA-Tag 2026.11.1 pinnt MA-Client 1.6.0. Dessen `music.get_item_by_uri`, `get_album_tracks`, `get_active_queue` und `repeat` akzeptieren kein `user`; `autoplay` fehlt und `play_media` akzeptiert kein `shuffle`. Die vorherige Implementierung war damit inkompatibel, unabhängig davon, ob in YAML ein Benutzer gesetzt war. Der offizielle MA-Server-Tag 2.10.12 bietet Schema 65 mit `play_media(shuffle=...)` und dem Alias `dont_stop_the_music`.

32 Python-Tests erfolgreich ausgeführt, einschließlich eines Tests, der die tatsächlichen Methoden aus dem offiziellen Client-Tag v1.6.0 ausführt (externe Modellparser und Netzwerktransport gemockt). Dieser prüft Metadaten ohne nicht unterstützte Parameter und einen einzigen geordneten Play-Protokollaufruf mit explizitem Shuffle aus, Queue-Ersetzung und Wiedergabebenutzer. Weitere Tests prüfen Client 1.8 auf Server-Schema 65, fehlende URI/Providerfehler ohne Wiederholung und die sichere Fehlerbehandlung beider Firmwareprotokolle. Die bisherigen Wiedergabetests A–G bleiben erfolgreich.

```sh
MA_CLIENT_16_SOURCE=/path/to/music-assistant-client-v1.6.0 \
python3 -m unittest discover -s kidsplayer/tests -v
```

Ohne diesen zusätzlichen Checkout wird genau der Original-Clientmethoden-Test übersprungen; alle anderen Tests bleiben lokal ausführbar. Nativer C++-Test erweitert: strukturierter Anwendungsfehler wird vor dem Wiedergabe-Erfolgszweig geprüft und nicht automatisch wiederholt. Offizieller Tessera-Validator und Python-Bytecodekompilierung erfolgreich.

Die Live-Installation wurde nicht verändert, kein echter Play-Aufruf durch den Agenten ausgelöst und keine erfolgreiche Audiowiedergabe behauptet. Der Audiofix erfordert Companion 0.1.4 plus HA-Neustart; die neue Fehleranzeige zusätzlich Firmware 0.1.4. Im alten Firmwareprotokoll kann Tessera den Fehler weiter pauschalisieren; ab Companion 0.1.4 enthält schon die erste HA-Logzeile den Fehlertext.

## Live-Diagnose: Companion nicht gefunden

Die Browserdiagnose lieferte bei beiden Bibliotheks-Protokollvarianten `unknown_command`. Anschließend ergab die HA-Konfigurationsprüfung die konkrete Warnung `Integration error: kidsplayer - Integration 'kidsplayer' not found.`; der YAML-Block war vorhanden. Dies belegt eine aktuell nicht auffindbare Custom Integration und erklärt den fehlenden Bibliotheks-/Coverabruf unabhängig von der Animation. Die vorherige Kompatibilitätskorrektur allein konnte diese Installation nicht reparieren.

`tools/package-companion.py` erzeugt ein ZIP mit den fünf benötigten Companiondateien und Lizenz direkt unter `custom_components/kidsplayer/`. Das erzeugte ZIP wurde auf beschädigte Einträge und seinen Inhalt geprüft. Keine neue Plugin-/Companionversion, kein Firmwarebau und keine Änderung der laufenden Installation durch den Agenten. Das Wiederherstellen der Dateien und der HA-Neustart stehen als nächster Schritt aus.

## Stiller statischer Coverwechsel 0.1.5

Firmwareänderung ohne Backend-/YAML-Migration. Initiale und spätere Browseanfragen setzen keine Ladeanzeige mehr. Die alte Beschriftung bleibt bis zur Bildrückmeldung stehen. Bei gleichen Bildadressen erfolgt die Beschriftung sofort, weil Tessera dafür keinen neuen Atlas und keine erneute Rückmeldung liefern muss. Der Slideaufruf entfällt vollständig; Wiedergabestart und echte Fehler bleiben sichtbar. Während auf die Bilder einer neuen Auswahl gewartet wird, startet ein Tipp kein unsichtbares neues Medium.

Der native Test des tatsächlichen C++-Codes prüft eine um fünf Sekunden verzögerte Backendantwort und eine getrennt simulierte, verspätete Bildrückmeldung: kein einziger „Laden …“-Text, keine vorzeitige Titel-/Headeränderung und keine Bewegung. Zusätzlich geprüft: identische Albumcover, Auswahl während des Bildwechsels, beibehaltene Wiedergabemeldungen, Bildfehler, Bildtimeout und verspäteter Bilderfolg. Bestehende Instanz-/Navigations- und Sieben-Cover-Tests bestehen weiter. Python-Regressionstests und offizieller Tessera-Validator ebenfalls erfolgreich.

Kein Guition-Renderingtest und kein Firmwarebau in dieser Umgebung. Die Tests simulieren den Atlas-Callback, sie prüfen keine vollständige Tessera-Bildpipeline. Die Kernfunktion `set_picture` behält alte Bilder bei nicht leeren Ersatzadressen. Nicht mehr benötigte Plätze werden beim Wechsel zu weniger Einträgen weiterhin sofort vom Kern entfernt; eine garantiert vollständig atomare Umschaltung auch dieser Sichtbarkeitsänderungen würde weitere Kern-/Pufferunterstützung erfordern und wird nicht behauptet.

## Fotoabgleich: Hintergrund und Covergröße 0.1.6

Das bereitgestellte Foto zeigt eine helle Kachel mit kleinem mittleren Cover, Nachbar und viel vertikalem Freiraum. Im Kerncode ist der Effekt nachvollziehbar: `runtime_tiles` setzt den Hintergrund der gedrückten Hostkachel auf `theme::pressed(...)`, während der Bildatlas die normale Grundfarbe verwendet. Die API bietet kein Pluginflag zum Abschalten dieses Hostzustands.

Umgesetzt wurde eine nicht interaktive, pluginlokale Hintergrundfläche. Sie liest die normale lokale BG-Farbe bzw. Transparenz des Hostobjekts, schreibt aber ausschließlich auf ihr eigenes Objekt. Native Tests prüfen Größe/Position der Fläche, ausschließlich normale Style-Abfragen, keine Schreibzugriffe auf den Host, Palette-/Seitenfarbe und Themeaufruf. Der äußere Kernrahmen/dessen Polsterung bleibt ausdrücklich außerhalb dieses Workarounds.

Die Coverberechnung reserviert eine kürzere Kopfzeile und nur eine gemeinsame Titel-/Statuszeile. Die Breitenkappe erlaubt weiter mindestens einen Viertel-Cover-Platz je Nachbar und erreicht im 400×380-Test 253 statt zuvor 200 Pixel. Die Gruppe wird vertikal zentriert. Native Tests prüfen die größere Abbildung, Platzierung des Hauptmotivs oberhalb des Textes sowie abwechselnde Titel-/Statussichtbarkeit. Kompakte Größen, Sieben-Cover-Regeln, stiller Bildwechsel und Fehlerpfade bestehen weiter.

Offizieller Pluginvalidator und Python-Regressionstests erfolgreich. Kein Firmwarebuild, kein vollständiger LVGL-Renderingtest und keine erfolgte Hardwareabnahme. Die Fotoaufnahme wurde nur zur Analyse herangezogen; keine Bilddatei oder privaten Bildinhalte ins Repository aufgenommen. Keine Änderung am HA-Companion oder an der laufenden Installation.

## Automatische Cover: Companion 0.1.7

Nur lesend im Live-System ermittelt: Tessera empfängt für die Folge eine HA-Coveradresse, deren Abruf wiederholt mit HTTP 500 scheitert; die bestehenden lokalen Reihenbilder werden erfolgreich abgerufen. Das passt zu einem Fehler im Bildauslieferungsweg und belegt nicht allein einen konkreten Decoder-Traceback, den der MCP-Protokollauszug nicht liefert.

Im Code gefunden und reproduziert: Ein einzelnes `aiohttp.StreamReader.read(n)` kann nur das erste verfügbare Teilstück zurückgeben. Der bisherige Cover-View übergab dieses Teilstück direkt an Pillow. Der neue Reader iteriert bis EOF und hält das Größenlimit von 2 MiB auch bei fragmentierten Antworten ein. Die Coveradressen erhalten einen neuen Cache-Namensraum, um frühere Fehlversuche zu umgehen. Die Metadaten-/URI- und Wiedergabeauflösung bleibt unverändert.

39 Python-Tests erfolgreich, einschließlich sieben neuer Cover-Tests: vollständiges kleines PNG aus mehreren asynchron gelieferten Teilstücken, alter verkürzter Einzel-Read, inkrementelles Größenlimit, Ablehnung angekündigter Übergröße vor dem Download, exakte Grenzgröße, HTTP-Fehler/Redirect/leere Antwort, Streamabbruch sowie Ausführung des tatsächlichen CoverView-Downloadpfads mit getrennt simuliertem Codec. Der Codec-Test prüft, dass alle PNG-Bytes vorliegen; er ist kein Test eines realen Pillow-Decoders. Neue Fehlerdiagnostik im HTTP-View gibt keine Quell-URLs mit möglichen Signaturen aus.

Companion-ZIP 0.1.7 erstellt und geprüft: `__init__.py`, `manifest.json`, `library.py`, `playback.py`, `compat.py`, `images.py` und Lizenz liegen korrekt unter `custom_components/kidsplayer/`. Display-Plugin bleibt 0.1.6; offizieller Validator und Bytecodeprüfung erfolgreich. Keine Installation oder HA-Neustart durch den Agenten, kein Nachweis eines erfolgreichen Live-Coverabrufs nach dem Fix. Die reale Prüfung folgt nach dem Companionupdate.

## Verteilung des Companion-ZIP

Nach erneuter Live-Warnung `Integration 'kidsplayer' not found` und Rückmeldung, im heruntergeladenen ZIP fehle `manifest.json`, wird das fertige Companion-Paket zusätzlich direkt im GitHub-Repository unter `downloads/kidsplayer-ha-companion-0.1.7.zip` angeboten. Die genaue Struktur des zuvor vom Benutzer heruntergeladenen Archivs wurde nicht eingesehen; es wird keine Behauptung über dessen konkreten Inhalt gemacht.

Das neue öffentliche Installationsarchiv wurde neu aus den Companionquellen erstellt. Integrität, korrekter Installationspräfix und bytegleicher Inhalt aller sechs erforderlichen Dateien einschließlich des JSON-Manifests mit Version 0.1.7 wurden geprüft. Die Downloadanleitung unterscheidet nun ausdrücklich zwischen dem ganzen GitHub-Quellarchiv, dem Tessera-Plugin und dem HA-Companion. Kein neuer Runtimecode und keine neue Versionsnummer; keine weitere Firmwarekompilierung erforderlich.

## Überschrift, runde Navigation und Medienknöpfe 0.1.7

Erfolgreich: **40 Python-Tests**, nativer C++-Test der echten Kidsplayer-Kachel gegen Tessera API 0.24/ArduinoJson/LVGL sowie offizieller Tessera-Manifest-/Codevalidator. Die bisherigen Wiedergabe- und Konfigurationstests bestehen weiter; der New-music-Referenzblock ist unverändert.

Neue native Prüfungen: konfigurierbare Überschrift, Back-Sichtbarkeit erst nach Atlaswechsel und Wiederherstellung beim Zurückgehen, kein versteckter Header-Touchbereich, zwei runde Footer-Knöpfe nur bei ausreichender Größe und Inspector-Player, Player-Zustandswechsel/Icons, Pause/Fortsetzen ohne `kidsplayer/play`, Unterdrückung schneller Doppeltipps, fehlende Medienkachel, nicht verfügbarer Player und Sendefehler. Player-Steuerung funktioniert auch bei ausstehender Browseantwort. Ein weiterer Test kompiliert das **tatsächliche Codegen-Lambda** mit dem echten `native_media.h` und einem Kernmodel-Double: exakte Player-Zuordnung, erste passende Kachel, fehlende/falsche Entity, deaktivierter Kern und kein Seitenwechsel.

**Grenze der Prüfung:** Das Model-Double rendert keine native Medienkarte. Der Aufruf `runtime_tiles::hold_card(unsigned)` wurde im untersuchten echten Kern geprüft; dieser Kern und seine native Detaildarstellung werden im Test nicht vollständig gebaut. ESPHome ist in der lokalen Python-Umgebung nicht installiert, daher kein kompletter Guition-Firmwarebuild. Native Overlay-Öffnung, Touchgefühl, tatsächliches Pausieren/Fortsetzen und Grafikabnahme müssen mit der neu gebauten Firmware am Gerät geprüft werden. Die bestehende Home-Assistant-/Tessera-Installation wurde nicht verändert. HA-Companion und dessen ZIP bleiben unverändert auf 0.1.7.

## Knöpfe oben rechts und Titelzentrierung 0.1.8

40 Python-Tests, nativer Test der tatsächlichen C++-Kachel gegen die vorhandenen Tessera API 0.24-/ArduinoJson-/LVGL-Header sowie offizieller Tessera-Validator erfolgreich. Zusätzlich geprüft: Back-/Playerknöpfe auf gleichem y-Wert mit gleichen Maßen, Abstand des Headers und der Cover zu den Knöpfen, volle Titel-/Meldungsbreite und explizite mittige Textausrichtung. Die Player-Hitbereiche öffnen weiterhin den Opener bzw. pausieren/setzen fort, ohne eine Folge erneut einzureihen. Fehlende normale Medienkachel wird verständlicher gemeldet. Native Opener-Prüfung und Wiedergabetests bleiben erfolgreich; unveränderte New-music-Referenz.

Der Benutzer bestätigte, dass bislang keine normale Medienkachel für den Player im Layout vorhanden ist; damit ist die Ursache der Opener-Meldung geklärt. Per lesendem MCP-Zugriff waren die aktuellen Tessera-Add-on-Logs zugänglich; es wurde kein Layout und keine Home-Assistant-Konfiguration verändert. Keine vollständige Firmwarekompilierung oder Grafikabnahme am Guition; die Prüfung mit UI-Doubles ersetzt diese nicht. Nur das Plugin benötigt einen Firmwarebau; HA-Companion 0.1.7 bleibt unverändert.

## Größere Cover und angepasste Spiegelung 0.1.9

Der native Test der tatsächlichen Kachel ist um die Formate 400 × 250, 400 × 300, 400 × 380 und 400 × 500 erweitert. Geprüft werden eine größere Motivkante, Bild-/Spiegelungsgrenzen innerhalb der Kachel, freie Header-/Titelzeile, zentriertes Mittelcover und zwei sichtbare innere Nachbarn. Die ersten drei Formate verzichten zugunsten des Motivs auf die Spiegelung; im letzten bleibt sie erhalten. Gemessene Mittelcover im Test: 168, 218, 285 und 285 Pixel, beim letzten zusätzlich 30% Spiegelung. Die Font-Fixture verwendet 20 Pixel Zeilenhöhe; reale Displaywerte können abweichen. Vorhandene Navigation, Instanztrennung und Touch-/Playersteuerung bestehen weiter.

40 Python-Tests inklusive unverändertem New-music-Referenzblock und Wiedergabefällen sowie offizieller Tessera-Validator erfolgreich. Kein vollständiger Firmwarebau und keine Grafikabnahme auf dem Guition. Die Änderung betrifft nur Plugin 0.1.9; HA-Companion 0.1.7 bleibt unverändert. Das Benutzerfoto zeigt noch die Knöpfe unten; 0.1.9 enthält die bereits in 0.1.8 umgesetzte obere Position und mittigen Titel.

## Abgerundete Hintergrundfläche 0.1.10

Die Änderung entfernt ausschließlich den Radius-Override auf null von der pluginlokalen Hintergrundfläche. Der untersuchte Tessera-Kern setzt für `ui::block` bereits einen zur Ansicht passenden Radius (`ui::px(large ? 12 : 8)`). Es werden keine Host-Styles verändert; die native Rand-Rückmeldung bleibt erhalten.

Bestehender nativer C++-Test und offizieller Tessera-Validator erfolgreich. Die Hintergrundtests prüfen weiterhin das unveränderte Host-Objekt, stabile normale Farben beim Drücken und Theme-Wechsel. Die Test-Doubles rendern keine Rundungen; Form und Randwirkung sind am Display abzunehmen. Kein vollständiger Firmwarebau. Keine Änderungen am HA-Companion oder an der laufenden Installation.

## HomePod-mini-Symbol 0.1.11

Das bereitgestellte SVG wurde mit dem eingecheckten optionalen AppKit-Werkzeug in eine 32 × 32 A8-Maske umgewandelt. Die erzeugte PNG-Vorschau wurde betrachtet; eine erneute Erzeugung liefert bytegleich denselben Header (`cmp`). SVG-Quelle und MIT-Lizenzhinweise sind im Repository enthalten. Firmwarebuilds benötigen diesen Generationsschritt nicht.

Erfolgreich: 40 Python-Tests, nativer C++-Test mit den echten Tessera API 0.24-/ArduinoJson-/LVGL-Headern und offizieller Tessera-Validator. Der native Test prüft zusätzlich den lokalen A8-Bilddeskriptor (32 × 32, 1024 Bytes), Zentrierung und Skalierung im Knopf, vollständige Farbübernahme und Wechsel zwischen hellem/dunklem `INK`. Der bestehende Hitbereich öffnet weiterhin die originale Medienansicht. Zusätzlich wurde die tatsächliche Kachel mit `LV_USE_IMAGE=0` gegen die realen Header kompiliert; sie verwendet dann einen vorhandenen Lautsprecherglyph.

Die Test-Doubles rendern kein LVGL-Bild auf einem ESP32. Keine vollständige Firmwarekompilierung oder Sichtprüfung auf dem Guition; das ist nach dem Firmwareupdate nötig. Keine Änderung an Home Assistant, dem Companion oder der nativen Tessera-Medienseite.

## Höhere Cover, Spiegelung und Headerfläche 0.1.12

Erfolgreich: nativer C++-Test gegen die echten API-/ArduinoJson-/LVGL-Header, 40 Python-Tests und offizieller Tessera-Validator. Die Geometriefixtures 400 × 250, 400 × 300, 400 × 380 und 400 × 500 prüfen die wieder aktivierte Spiegelung, ausreichend große Cover, vollständige Motivhöhe oberhalb des Titels, Grenzen innerhalb der Kachel und weiterhin sichtbare Nachbarn. Bei den ersten drei Formaten reicht die Coverzeile jetzt absichtlich hinter die Knöpfe; deren höhere Zeichenreihenfolge und weiterhin korrekte Hitbereiche werden geprüft.

Zusätzlich geprüft: Headerfläche in Tessera-Tastenfarbe mit abgerundeten Ecken und Innenabständen, Breite passend zum Text, Zeichenreihenfolge oberhalb der Bilder, gemeinsame Sichtbarkeit von Text/Fläche erst nach Atlaswechsel, versteckte Fläche auf Folgenebene bzw. bei leerem Text, keine Navigation beim Antippen der Überschrift sowie kein Überdecken der Playerknöpfe bei 64 Zeichen langem Text. Bisherige Wiedergabe-, Instanz-, Farbwechsel- und Fehlerprüfungen bestehen weiter.

Keine Pixel-/Hardwareabnahme oder vollständige Firmwarekompilierung; die Tests verwenden UI-Doubles. Die tatsächliche Überlagerung von Bildatlas und LVGL-Elementen sowie die Spiegelung müssen nach dem Firmwareupdate am Guition geprüft werden. Keine Änderung an der laufenden Home-Assistant-/Tessera-Installation oder am Companion 0.1.7.

## Reale Pixelprüfung des Icons 0.1.13

Die bisherigen UI-Doubles prüften Bilddeskriptor, Platzierung und Farbe, zeichneten das Icon aber nicht. Das Benutzerfoto zeigt die Grenze dieser Prüfung. Im Code fehlte die explizite Anforderung des A8-Software-Renderers, den ESPHome für dieses ausschließlich in C++ erzeugte Bild nicht automatisch auswählt.

Neu: `tools/test-icon-render.py` baut den tatsächlichen LVGL-Quellbaum und führt `kidsplayer/tests/test_icon_render.cpp` mit dem unveränderten eingebetteten HomePod-Bild aus. Ausgeführt mit dem offiziellen Tag **v9.5.0**, passend zum LVGL-Pin des offiziellen ESPHome-Tags **2026.10.2**. RGB565-Ausgabe, 32-Byte-Pufferausrichtung und 28-Pixel-Skalierung entsprechen den relevanten Darstellungsbedingungen. Der Test vergleicht Innen- und Hintergrundpixel mit der Alphamaske und überspringt interpolierte Randpixel.

- Helles Design: 460 geprüfte Pixel, 0 Abweichungen.
- Dunkles Design: 460 geprüfte Pixel, 0 Abweichungen.
- Negative Kontrolle ohne A8-Transformation: 272 von 460 Pixeln falsch; der Fehler wird erkannt. Dafür wird nur das reale Transformationsmodul mit deaktiviertem A8-Fall ersetzt.
- Die tatsächlich gerenderte PNG-Vorschau wurde zusätzlich betrachtet; sie zeigt die HomePod-Silhouette mit heller oberer Öffnung.
- 41 Python-Tests erfolgreich, einschließlich Ausführung des tatsächlichen Plugin-`to_code` mit gemocktem ESPHome zur Prüfung der A8-Anforderung. Bestehender nativer Kacheltest gegen API 0.24/LVGL 9.3 und offizieller Tessera-Validator bestehen weiter.

Reproduzieren (clang/clang++, ar; der Buildordner enthält nur wiederverwendbare Testartefakte):

```sh
python3 tools/test-icon-render.py /path/to/lvgl-v9.5.0 /tmp/kidsplayer-icon-render
```

Die vollständige Guition-Firmware wurde nicht gebaut oder installiert. Der reale Host-Renderer ist eine zusätzliche Prüfung, kein ESP32-Hardwaretest. Der tatsächliche Compilerstand des Displays wurde nicht erneut ausgelesen; der untersuchte ESPHome-Tag entspricht dem zuletzt bekannten installierten Builder. Das Symbol muss nach dem Update am Gerät bestätigt werden. Kein neues Bildformat vom Benutzer nötig; SVG, Maske und HA-Companion bleiben unverändert.
