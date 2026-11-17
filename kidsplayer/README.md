# Kidsplayer 0.1.7

Aktueller Home-Assistant-Companion: **0.1.7**. [Fertiges HA-Installationsarchiv](https://github.com/met-theokoch-schule/tessera-plugins/raw/refs/heads/main/downloads/kidsplayer-ha-companion-0.1.7.zip). Plugin- und Companionversion werden getrennt geführt; diese Korrektur ändert nur den Companion.

Kidsplayer zeigt Hörspielreihen und deren Folgen innerhalb derselben Tessera-Kachel. Seitlich tippen blättert; das mittlere Cover öffnet eine Reihe oder startet eine Folge. Oben führt ein runder Pfeil nach links zur Reihenebene. Die Überschrift der Reihenebene lässt sich pro Kachel unter **Überschrift** ändern (Standard: `Reihen`, maximal 64 Zeichen). Die Tessera-Seite bleibt erhalten. Bis zu sieben Coverplätze verwenden New music's Anordnungsschleife unverändert, mit Perspektive und überlappenden äußeren Nachbarn. Ab 0.1.5 wechseln sie ohne Slide direkt in den neuen Endzustand. Größere Kacheln zeigen eine auslaufende Spiegelung unter den vollständig sichtbaren Covern; niedrige Kacheln sparen diese aus. Bildübertragung und Cache übernimmt Tessera.

**Status:** Beta-Implementierung mit Mocktests und ausgeführten nativen C++-Navigationstests. Home Assistant und Hardware wurden nicht gestartet. Die Installationsschritte sind für einen anschließenden Test beschrieben, nicht bereits auf deinem Display ausgeführt.

## Set up

Voraussetzungen und Installation auf dem Guition

1. Home Assistant mit der **offiziellen** Integration `music_assistant`, einem eingerichteten MA-Server, Apple-Music-/Dateianbieter und einem erreichbaren MA-Lautsprecher. Die alte benutzerdefinierte Integration `mass` wird nicht unterstützt.
2. Tessera mit Plugin-API **0.24** oder kompatibler neuerer API. Ab 0.1.4 unterstützt der Companion die Schnittstellen von **HA 2026.11.1 / music-assistant-client 1.6.0 / MA-Server 2.10.12 (Schema 65)** sowie die zuvor untersuchte Client-1.8-/Schema-101-Schnittstelle. Die installierten Versionen wurden im konkreten Fehlerfall aus HA gelesen, die Kompatibilitätsaufrufe gegen offizielle Quellstände und Mocks geprüft. Dies ersetzt keine erfolgreiche Live-Wiedergabe. Der Companion verwendet den von HA installierten Client und installiert keinen eigenen. MA-Berechtigungen müssen die gewünschte Benutzerzuordnung erlauben.
3. Kopiere **nur** `backend/custom_components/kidsplayer/` nach `/config/custom_components/kidsplayer/` in Home Assistant. Das ist eine zusätzlich notwendige Custom Integration, kein Tessera-Kernpatch. Sichere deine Konfiguration vor eigener Installation.
4. Lege `/config/kidsplayer.yaml` nach dem Beispiel unter `examples/libraries.yaml` an. Ersetze alle `PLACEHOLDER`-URIs und Player; entferne `music_assistant_user`, wenn du noch kein entsprechendes MA-Konto eingerichtet hast.
5. Ergänze einmalig in Home Assistant `configuration.yaml`:

   ```yaml
   kidsplayer:
     libraries_file: kidsplayer.yaml
     cover_root: /media/hoerspielcover
   ```

6. Home-Assistant-Konfiguration prüfen und Home Assistant neu starten. PyYAML und Pillow werden bereits von Home Assistant bereitgestellt; der Companion installiert keinen eigenen MA-Client.
7. Kopiere den **gesamten Pluginordner `kidsplayer/`** nach `/config/tessera-plugins/kidsplayer/`, neben `/config/esphome/`. Bei abweichendem Tessera-ESPHome-Verzeichnis ist der Ordner `tessera-plugins/` dessen Geschwisterordner. Keine Symlinks verwenden. Das ist Tessera's offizieller lokaler Testplugin-Weg. Ein GitHub-Push allein trägt Kidsplayer noch nicht in den offiziellen Store ein.
8. In Tessera unter **Plugins** Kidsplayer auswählen, nur das Guition-Testdisplay wählen und installieren. Tessera baut und überträgt dessen Firmware einmal. Diese Entwicklung hat das nicht für dich ausgeführt.
9. Im Layout eine **Kidsplayer**-Kachel hinzufügen. Sie beginnt bei **1 × 1** und lässt sich an den Zugpunkten rechts/unten über **2 × 1** oder **1 × 2** auf **2 × 2** vergrößern. Die angrenzenden Rasterfelder müssen frei sein. Für den ersten Guition-Test möglichst den Großteil der 480 × 480-Seite verwenden. Als Player den MA-Mediaplayer auswählen; unter **Bibliotheks-ID** `kinderzimmer_1` eintragen. Speichern und senden.
10. Bei Verbindungsfehlern prüfen, ob Tessera seine normale administrative HA-Websocket-Verbindung verwendet. `kidsplayer/play` erfordert eine Adminverbindung; die Firmware bekommt weder HA- noch MA-Zugangsdaten.

Plugin-Codeänderungen benötigen einen erneuten Tessera-Build. Änderungen am Companion-Code benötigen einen HA-Neustart. **Änderungen an der Bibliotheksdatei benötigen beides nicht**: Der Companion liest sie beim nächsten Browse/Play erneut und validiert bei geändertem Inhalt atomar. Sichtbare Kacheln aktualisieren etwa alle 30 Sekunden. Ein Tipp bei geändertem Dateistand wird zunächst abgewiesen; Auswahl neu laden und erneut antippen. YAML niemals nur teilweise speichern; möglichst Datei atomar ersetzen.

## Eine erste Reihe konfigurieren

Das vollständige Schema ist in [examples/libraries.yaml](examples/libraries.yaml) gezeigt. Für den ersten Versuch genügt:

```yaml
libraries:
  kinderzimmer_1:
    version: 1
    player: media_player.kinderzimmer_1
    display:
      show_titles: true
      cover_style: contain
      animation: false
    categories:
      - id: robin_hood
        title: Robin Hood
        cover: robin_hood.jpg
        episodes:
          - id: folge_1
            title: Folge 1
            cover: auto
            playback:
              items:
                - uri: "apple_music://track/PLACEHOLDER_TRACK_01"
                - uri: "apple_music://track/PLACEHOLDER_TRACK_02"
          - id: folge_2
            title: Folge 2
            cover: auto
            playback:
              items:
                - uri: "apple_music://track/PLACEHOLDER_TRACK_03"
                - uri: "apple_music://track/PLACEHOLDER_TRACK_04"
```

Die IDs und URIs hier sind **ausdrücklich Platzhalter**; der Parser verweigert `PLACEHOLDER` absichtlich. Übernimm echte URIs aus deinem MA. Kategorie-IDs müssen innerhalb einer Bibliothek, Folgen-IDs innerhalb einer Reihe eindeutig sein. IDs: 1–32 Kleinbuchstaben/Ziffern/Unterstriche, erster Buchstabe ein Buchstabe. Unbekannte Felder, doppelte YAML-Schlüssel, leere Reihen/Folgen und ungültige URIs werden abgewiesen.

Unter `libraries:` sind bis zu 32 Bibliotheken möglich; pro Bibliothek 128 Reihen, pro Reihe 512 Folgen, pro Folge 256 konfigurierte Medienobjekte. Eine Datei darf maximal 512 KiB groß sein; die expandierte Wiedergabe einer Folge ist auf 2048 Tracks begrenzt. Das sind Backendgrenzen, keine Übertragung der gesamten Bibliothek an den ESP32. Titel dürfen 160 UTF-8-Bytes enthalten; Tessera kürzt die Darstellung auf 48 Bytes.

## Music-Assistant-URIs ermitteln

Öffne das konkrete Medium in der MA-Weboberfläche. Wenn dessen Menü „URI kopieren“ anbietet, kopiere die **MA-URI**, nicht die Apple-Webseite oder den Titel. Je nach MA-Version kann die Menübezeichnung abweichen. Alternativ liefert die MA-API `music/item_by_uri` ein Medienobjekt mit `uri`; `music/albums/album_tracks` liefert die einzelnen Albumtracks mit `uri`, `disc_number` und `track_number`. Diese Antworten lassen sich in den Browser-Netzwerkwerkzeugen der MA-Oberfläche beim Öffnen eines Albums nachvollziehen. Details und Parameter stehen in der [offiziellen Clientimplementierung](https://github.com/music-assistant/client/blob/v1.8.0/music_assistant_client/music.py).

URI-Aufbau: `<provider-domain-oder-instanz>://album/<item-id>` beziehungsweise `...://track/<item-id>`. `library://album/<id>` und `library://track/<id>` sind die internen MA-Bibliotheks-URIs. Verwende den **vollständigen zurückgegebenen Wert**, insbesondere die richtige Anbieterinstanz und vorhandene URL-Kodierung. Die Beispielpräfixe `apple_music` und `filesystem_local` allein belegen keine gültige Anbieterinstanz in deinem Server.

Keine Titel, keine numerischen IDs ohne Präfix und keine Apple-Sharing-URLs eintragen. Lokale Dateien zuerst vom MA-Dateianbieter indizieren lassen und dessen Track-URIs verwenden. `/media/hoerspiele/conni/01.mp3` ist keine Kidsplayer-URI. Kidsplayer hostet keine Audiodateien.

## Alben und Folgen aus ausgewählten Tracks

Ein komplettes Album steht als einzelnes `playback.items`-Objekt mit seiner Album-URI. Der Companion expandiert es vor dem Start über MA und sortiert nach Disc- und Tracknummer. Leere Alben, fehlende/mehrdeutige Tracknummern und als nicht verfügbar gemeldete Tracks führen zum Fehler. Ein vom Anbieter überhaupt nicht mehr gelisteter Track lässt sich ohne Soll-Trackliste nicht erkennen; für kritische Fälle explizite Track-URIs verwenden.

Für ein Album mit zwölf Tracks legst du drei eigenständige Folgen an: Folge 1 mit den vier Track-URIs 1–4, Folge 2 mit 5–8, Folge 3 mit 9–12. Die Reihenfolge in YAML ist die Wiedergabereihenfolge; explizite Tracklisten werden niemals nach Tracknummer umsortiert. **Keine Album-URI zusätzlich in die Trackgruppe aufnehmen**, sonst gehört das gesamte Album zur Folge.

Eine Liste kann einzelne Tracks unterschiedlicher Anbieter und Album-URIs enthalten. Die Albumtracks werden an der jeweiligen Listenposition eingesetzt. Apple Music und lokale Medien funktionieren über denselben MA-Player, sofern MA beide Anbieter abspielen kann.

Kidsplayer prüft alle Einträge vor einer Queueänderung. Danach schaltet es Repeat und Autoplay aus und übergibt alle aufgelösten Tracks mit `replace`, `shuffle=false`, `radio_mode=false` in **einem** Wiedergabeaufruf. Der Start einer neuen Folge ersetzt die vorherige Queue. Danach übernimmt MA die normale Trackfortsetzung. Es gibt weder Track-Ende-Callbacks noch automatisches Fortsetzen nach Pause/Stop durch Kidsplayer. Ein Wiedergabetimeout wird nicht automatisch wiederholt.

Die offizielle HA-Aktion `music_assistant.play_media` unterstützt Listen. Ihr untersuchter Code enthält jedoch bei fehlgeschlagener URI-Verifikation einen Titelsuch-Rückfall. Deshalb verwendet Kidsplayer als begründete Alternative den bereits in HA vorhandenen MA-Client direkt. Es führt selbst keinerlei Titelsuche aus. **MA-eigene Providerzuordnungen und Fehler während des eigentlichen Streamings bleiben Verantwortung des MA-Servers**; Kidsplayer kann nicht garantieren, dass ein von MA als verfügbar gemeldeter Track später decodiert wird. Der reale Abnahmeplan muss insbesondere ungewünschte Provider-Fallbacks ausschließen.

## Cover

`cover: auto` nimmt die MA-Grafik des ersten Medienobjekts der Folge; eine Reihe ohne eigenes Bild verwendet das erste Objekt ihrer ersten Folge. Folgen aus demselben Album dürfen dasselbe Bild verwenden. Wenn der Track keine Grafik meldet, bleibt ein Platzhalter.

`cover: robin_hood.jpg` liest `/media/hoerspielcover/robin_hood.jpg`. Relative Unterordner sind erlaubt. Ein ursprünglich gewünschtes `covers/robin_hood.jpg` bedeutet entsprechend `/media/hoerspielcover/covers/robin_hood.jpg`. Absolute Pfade und Verzeichnisausbruch sind gesperrt; auch aufgelöste Symlinks müssen im Coververzeichnis bleiben. Keine öffentlichen `/local/`-Freigaben notwendig.

Der Companion stellt die Grafik unter einer kurzen, **authentifizierten** HA-Bildadresse bereit. Tessera lädt sie mit seinen vorhandenen Zugangsdaten, skaliert sie in bis zu sieben Coverplätze und cached das Ergebnis. Das Bild behält sein Seitenverhältnis (`contain`), ohne Abdunklung oder Text über dem Motiv. Download maximal 2 MiB, Ausgangsbild höchstens 360 × 360 Pixel. Der Originalcoverinhalt verlässt nur den bestehenden HA/Tessera-Bildweg; keine Schlüssel gehen an das Display. Ein bestehendes lokales Bild nach Austausch durch eine kleine YAML-Änderung invalidieren; ansonsten kann Tessera es bis zu sechs Stunden cachen.

## Mehrere Kacheln, Player und Benutzer

Kachel A wählt `kinderzimmer_1`, Kachel B `kinderzimmer_2`; beide können auf derselben Seite stehen. Jede Tile-Instanz hält ihre Kategorie, Auswahlindizes und ausstehenden Anfragekennungen selbst. Nach Neuanlage/Neustart beginnt sie auf der Reihenebene. Ein Player im Inspector überschreibt `player:` der Bibliothek. Fehlt er, wird YAML verwendet.

Mit unterschiedlichen Playern spielen beide unabhängig. Wählen zwei Kacheln denselben Player, teilen sie dessen MA-Queue: Die zuletzt gestartete Folge ersetzt die vorherige. Das ist beabsichtigt. Parallel gestartete Aktionen desselben Players werden im Backend serialisiert.

Optional wird `music_assistant_user: kind1` als `user` für die Wiedergabe an MA weitergereicht. Auf Schema 65 erfolgen Metadatenabfragen und Queueeinstellungen im Kontext der HA-Systemverbindung, weil diese Methoden dort keine Benutzerzuordnung akzeptieren; der eigentliche Play-Aufruf trägt den gewünschten Benutzer. Auf der untersuchten Schema-101-Schnittstelle wird auch bei den unterstützten Metadaten-/Queuemethoden der Benutzer übergeben. Der Name muss in MA existieren; MA muss Impersonation erlauben. Dies bereitet spätere kontogebundene Medien vor. Audiobookshelf-Integration, Hörfortschritt, Fortsetzen von Hörbüchern und echte Inhaltssperren gehören noch nicht zu 0.1.0. Die Auswahl in Kidsplayer ist keine Zugriffskontrolle für MA.

## Wiedergabe auf dem Testdisplay abnehmen

1. Prüfe denselben MA-Player zuerst in der MA-Oberfläche mit dem gewünschten Anbieter.
2. Beginne mit einer Folge aus zwei oder drei bekannten, kurzen Tracks. In der MA-Queue müssen exakt diese Tracks in YAML-Reihenfolge erscheinen; Shuffle, Repeat und Autoplay müssen aus sein.
3. Prüfe ein komplettes Album, einschließlich Discwechsel. Die Queue muss Disc 1 vor Disc 2 zeigen.
4. Prüfe die drei Folgen eines zwölfteiligen Apple-Albums separat. Bei Folge 2 müssen ausschließlich Tracks 5–8 erscheinen, Track 5 zuerst. Bis zum Ende laufen lassen: Track 9 darf nicht starten.
5. Starte während einer laufenden Folge eine andere: Die Queue muss ersetzt werden und bei deren erstem Track beginnen. Pause/Stop anschließend beobachten: Kidsplayer darf nicht neu starten.
6. Prüfe fünf lokale Tracks und eine gemischte Liste über denselben Player.
7. Trage testweise eine nicht verfügbare URI ein: Fehlermeldung muss erscheinen; kein Ersatzalbum darf gesucht werden. Beachte: Der tatsächliche Player kann bei erst während des Streamings erkannten Fehlern anders reagieren als der Metadaten-Preflight.
8. Setze zwei Kacheln auf dieselbe Seite und navigiere unabhängig. Ändere YAML ohne Firmwarebau und prüfe die Aktualisierung.
9. Entferne ein Cover, prüfe Platzhalter und Fehlerrückmeldung; teste lange Titel und Kachelgrößen 1 × 1, 2 × 1 und 2 × 2.

## Fehleranalyse und Grenzen

- „Bibliotheks-ID fehlt“: Inspector ergänzen. Unbekannte ID/ungültige YAML: HA-Protokoll nach `custom_components.kidsplayer` filtern.
- „Tessera nicht verbunden“ oder Timeout: Verbindung zu Tessera/HA und Companion-Installation prüfen. Bei einem Wiedergabetimeout zuerst die MA-Queue prüfen, da die Aktion bereits angekommen sein kann.
- Kein Player: offizielle MA-Entity auswählen; ein gewöhnlicher Cast-/Sonos-Player außerhalb der MA-Integration genügt nicht.
- Benutzerfehler: Namen und MA-Berechtigung prüfen; ohne gewünschte Benutzerzuordnung das YAML-Feld entfernen.
- Kein Cover: Leserechte, Größe, Bildformat und relativen Pfad prüfen. Bei Netzwerkcovern folgt der Companion keinen HTTP-Redirects.
- Änderungen werden nicht übernommen: Datei vollständig speichern, 30 Sekunden warten oder nach einem Fehler erneut tippen. Gelöschte Kategorie mit „Zurueck“ verlassen.
- Fehler nach Start, Provider-Fallback, Gruppen-/Syncplayer, echte Streamverfügbarkeit und Benutzerfortschritt sind bislang nicht am echten Server geprüft. Keine Aussage über eine bereits erfolgte Hardwareabnahme.
- Keine vollständige grafische Vorschau der verschachtelten Bibliothek im Tessera-Editor, keine Swipe-Gesten, kein persistenter Navigationszustand und keine Bibliotheks-YAML im Inspector. Firmwaretexte sind momentan deutsch in ASCII-Schreibweise.
- Album-Tracknummern (`album_uri`, `tracks`, `track_range`) sind **noch nicht implementiert** und werden als unbekannte Felder abgewiesen. Die MA-Albumtrack-API liefert die notwendigen URIs und Disc-/Tracknummern; eine spätere Erweiterung muss Disc explizit behandeln, fehlende Nummern verweigern und Metadatenänderungen berücksichtigen.

## Privacy

Bibliotheken bleiben in Home Assistant; das Display erhält nur die sichtbaren Titel, IDs und Coveradressen. Music Assistant kontaktiert die konfigurierten Medienanbieter. Automatische Cover werden vom durch MA angegebenen Host über HA geladen; dieser Host sieht die IP von Home Assistant. Keine Telemetrie in Kidsplayer.

## Update auf 0.1.1: Zugpunkte

Die bisherige Mindestgröße 2 × 2 blockierte Tessera's achsenweise Vergrößerung einer neu angelegten 1 × 1-Kachel. Ab 0.1.1 ist die Mindestgröße 1 × 1; damit sind auch die Zwischenstufen 2 × 1 und 1 × 2 zulässig. Für eine niedrige Kachel wird die Titelzeile ausgeblendet, damit Cover, Zurück-Navigation und Status Platz haben. Für die komfortable Coverauswahl bleibt 2 × 2 oder größer empfohlen.

Den Pluginordner in `/config/tessera-plugins/kidsplayer/` durch den neuen Stand ersetzen beziehungsweise die verwendete GitHub-Pluginquelle auf den neuen Commit aktualisieren. Danach die Pluginliste im Tessera-Editor neu laden; falls nötig Tessera neu starten, damit das neue Manifest eingelesen wird. Für die angepasste Darstellung Kidsplayer auf dem Testdisplay aktualisieren/neu bauen. Der HA-Companion wurde hierfür nicht geändert.

Die ausgewählte Kachel braucht freien Platz rechts/unten; nach unten vergrößern setzt außerdem Tessera's Unterstützung für höhere Kacheln voraus. Sollte ein Zugpunkt trotz neuer Mindestgröße fehlen, zunächst die Kachel auf eine leere Seite oder in einen freien Bereich setzen.

## Update auf 0.1.2: Coverwechsel

Der ursprüngliche Kidsplayer-Flow war eine vereinfachte Anpassung von New music, keine unveränderte Übernahme. Er verschob kleinere Nachbarcover um eine pauschale halbe Coverbreite in 220 ms und startete bereits vor der asynchronen Backendantwort. 0.1.2 übernimmt die Proportionen der Referenz: Mittelcover maximal halbe Kachelbreite, Nachbarn bis zu 55 % dieser Breite bei voller Höhe, Abstand `ui::px(10)`, Bewegung um den tatsächlichen Mittenabstand in 320 ms und Spiegelung auf höheren Kacheln. Bis einschließlich 0.1.2 blieben drei sichtbare Plätze erhalten; diese Beschränkung ist ab 0.1.3 aufgehoben. Das Mittelcover verwendet weiterhin `contain`, damit keine Motive abgeschnitten werden. In 0.1.2 standen die Titel unterhalb der Reflexion; ab 0.1.3 verwendet die normale Kachel die Höhenberechnung der Referenz und lässt die Reflexion unter den Textzeilen auslaufen.

Während einer Backendanfrage bleiben die bisherigen Cover an ihrem Platz. Erst mit den neuen Adressen werden Slide und Bildwechsel zusammen ausgelöst. Bei gleichem Mittelcover – insbesondere mehreren Folgen desselben Apple-Albums –, fehlendem Bild, Fehlerantwort oder `display.animation: false` entfällt die Bewegung. Tessera setzt einen Slide erst beim Eintreffen eines neuen Bildatlas zurück; ohne geänderte Bildquelle würde ein Slide sonst dauerhaft verschoben bleiben können. Zwei Einträge zeigen nur einen Nachbarn, ein Eintrag keinen.

Das bleibt Tessera's bestehender Slide eines Bildatlas mit anschließendem Wechsel, keine kontinuierliche 3D-Drehung einzelner Covers. Den tatsächlichen Eindruck bei Cachetreffern, langsamen Downloads und auf dem Guition muss der Hardwaretest bestätigen. Die nativen Tests prüfen Aufrufreihenfolge, Geometrie und Parameter, keine gerenderten Animationsframes.

Zum Anwenden das Plugin auf 0.1.2 aktualisieren und die Display-Firmware neu bauen. Der HA-Companion bleibt unverändert; Bibliotheksdateien müssen nicht angepasst werden.

## Update auf 0.1.3: Originalanordnung mit bis zu sieben Covern

Die Beschränkung auf drei Bildplätze war eine Vereinfachung in Kidsplayer, keine Tessera-Grenze. 0.1.3 übernimmt die Bildplatz-Schleife aus dem festgelegten New-music-Commit unverändert: bis zu drei Nachbarn je Seite, außen zuerst gezeichnet, nach innen überlappend, und nur vollständig in die Kachel passende Nachbarn. Ein automatischer Quellvergleich schützt diesen übernommenen Block vor versehentlichen Abweichungen. Die normale Kachel verwendet auch die Höhenberechnung der Referenz, innerhalb der Fläche unter Kidsplayer's Zurück-Zeile. `contain`, kompakte Zwischenformate und die hierarchische Bedienung bleiben Kidsplayer-Anpassungen.

**Sieben Plätze bedeuten nicht immer sieben sichtbare Cover.** Wie im Original können bei einem großen Mittelcover in einer quadratischen Kachel nur die ersten Nachbarn passen, also drei Cover. Eine breite, niedrigere Kachel kann alle sieben darstellen. Weniger Bibliothekseinträge werden nicht dupliziert. Es wird keine zusätzliche Verkleinerung erzwungen, um immer sieben zu zeigen; das würde erneut vom Original abweichen.

Das Backend liefert das Zentrum und die drei Nachbarn je Seite als kleines Fenster. Es überträgt weiterhin keine Tracklisten oder gesamte Bibliothek an den ESP32. Mehrfach auftretende Fensterobjekte in einer kleinen Bibliothek werden pro Browse nur einmal für das Cover aufgelöst. Die Manifestdeklaration umfasst jetzt sieben Bildplätze und 5600 Bytes Tile-Memory; Bildatlas-Speicher zählt Tessera zusätzlich. Der echte RAMverbrauch muss auf dem Display geprüft werden.

**Für 0.1.3 beide Teile aktualisieren:**

1. `backend/custom_components/kidsplayer/` erneut nach `/config/custom_components/kidsplayer/` kopieren und Home Assistant neu starten.
2. Plugin auf 0.1.3 aktualisieren und die Display-Firmware neu bauen.
3. YAML unverändert lassen. Die vorhandenen Reihen/Folgen erscheinen automatisch im größeren Fenster.

Nur das Firmwareupdate genügt für die äußeren Nachbarn nicht, weil der bisherige Companion lediglich drei Objekte lieferte. Die bisherige Mitte-/Links-/Rechts-Antwort bleibt für ältere Kacheln erhalten. Die neue Firmware lässt fehlende äußere Antwortfelder leer.

## Update auf 0.1.4: „Home Assistant refused the command.“

Tessera verdeckt den HA-Fehlertext in dieser allgemeinen Meldung. Im untersuchten Fall läuft HA 2026.11.1 mit dem von HA festgelegten MA-Client 1.6.0 und MA-Server 2.10.12/Schema 65. Kidsplayer hatte fälschlich die neueren Client-1.8-Methoden vorausgesetzt: `get_item_by_uri(..., user=...)`, Benutzerparameter bei Album-/Queueabfragen, `autoplay(...)` und `play_media(..., shuffle=False)` passen nicht zu Client 1.6.0. Schon die erste Metadatenauflösung kann deshalb mit `TypeError` abbrechen. Das Entfernen des YAML-Benutzers hätte diesen Programmfehler nicht behoben, da vorher sogar `user=None` übergeben wurde.

0.1.4 verwendet die passende Kombination von Client- und Serverschnittstelle. Für Schema 65 wird Autoplay über `dont_stop_the_music(..., False)` abgeschaltet; die gesamte Trackliste wird in einem direkten offiziellen `player_queues/play_media`-Protokollaufruf mit `replace`, `shuffle=false`, `radio_mode=false` und optionalem Wiedergabebenutzer übergeben. Das umgeht ausschließlich die fehlenden Parameter des alten Python-Wrappers; es ist keine Titelsuche, neue Audioengine oder Lockerung der Benutzerberechtigung. Für diesen direkten Pfad wird mindestens Schema 65 verlangt. Bei unterstütztem neuerem Client/Server wird weiterhin der typisierte Aufruf verwendet.

**Für den Wiedergabefix genügt zunächst:**

1. Den **gesamten** Ordner `kidsplayer/backend/custom_components/kidsplayer/` nach `/config/custom_components/kidsplayer/` aktualisieren, einschließlich der neuen Datei `compat.py`.
2. Home Assistant neu starten.
3. Dieselbe Folge erneut antippen; YAML und Playerzuordnung bleiben unverändert. In der MA-Queue Reihenfolge und vollständige Liste prüfen.

Die vorhandene Display-Firmware 0.1.3 kann mit diesem Companion weiterarbeiten. Optional danach Plugin-Firmware 0.1.4 bauen: Sie fordert mit `protocol: 1` strukturierte Fehler an und zeigt die konkrete Fehlermeldung statt des pauschalen Tessera-Texts. **Companion zuerst aktualisieren**, bevor die neue Firmware verwendet wird. Alte Firmware erhält bei Fehlern weiterhin eine echte Fehlerantwort und meldet keine falsche erfolgreiche Wiedergabe.

Die erste HA-Protokollzeile enthält ab jetzt Fehlerklasse und Meldung; der vollständige Traceback bleibt ebenfalls im HA-Protokoll. Bei verbleibendem Fehler bitte den neuen Eintrag `Kidsplayer-Wiedergabe fehlgeschlagen (...)` prüfen. Die Reparatur wurde gegen Original-Clientmethoden und Mocks getestet; eine erfolgreiche Audioausgabe auf dem echten Player ist erst nach diesem Update bestätigt.

## Fehler: `unknown_command` / `Integration 'kidsplayer' not found`

Wenn die HA-Konfigurationsprüfung `Integration error: kidsplayer - Integration 'kidsplayer' not found.` meldet, ist der YAML-Eintrag zwar vorhanden, HA findet aber kein installierbares Companion-Paket. Dann sind weder `kidsplayer/browse` noch `kidsplayer/play` registriert; Bibliothek, Cover und Wiedergabe können nicht funktionieren. Eine Firmwareänderung behebt diesen Installationsfehler nicht.

Diese Dateien müssen direkt in **Home Assistant's** `/config/custom_components/kidsplayer/` liegen:

```text
/config/custom_components/kidsplayer/
├── __init__.py
├── manifest.json
├── library.py
├── playback.py
├── compat.py
└── images.py
```

Der Tessera-Pluginordner `/config/tessera-plugins/kidsplayer/` allein genügt nicht. Ebenso falsch wäre eine zusätzliche Ebene wie `/config/custom_components/kidsplayer/backend/custom_components/kidsplayer/`.

Ein passendes Installationsarchiv lässt sich auf dem Entwicklungsrechner mit `python3 tools/package-companion.py /tmp/kidsplayer-ha-companion-0.1.7.zip` erzeugen. Es enthält ausschließlich den Companion und seine Lizenz mit dem Wurzelordner `custom_components/`, keine Audioinhalte, Zugangsdaten oder Firmware.

ZIP auf den HA-Rechner nach `/config/kidsplayer-ha-companion-0.1.7.zip` kopieren und im HA-Terminal ausführen:

```sh
unzip -o /config/kidsplayer-ha-companion-0.1.7.zip -d /config
ls -l /config/custom_components/kidsplayer/
ha core check
```

Anschließend Home Assistant neu starten und zuerst nur die Bibliothek öffnen. Nach dem Neustart darf die Konfigurationsprüfung `Integration 'kidsplayer' not found` nicht mehr melden. Falls stattdessen ein Ladefehler erscheint, genau diesen Protokolleintrag prüfen. Bestehende Bibliotheks-YAML und Display-Firmware bleiben für die Wiederherstellung unverändert.

## Update auf 0.1.5: Unauffälliger Coverwechsel

Beim Öffnen, Blättern und automatischen Bibliotheksabgleich erscheint kein „Laden …“ mehr. Während der Backendabfrage bleibt die vorherige Darstellung stehen. Die statische Anordnung wechselt über Tessera's vorhandenen Bildatlas, sobald das Ersatzbild verfügbar ist. Titel und Zurück-Zeile werden bis zur Bildrückmeldung zurückgehalten, damit kein neuer Titel über einem noch alten Cover steht. Bei unverändertem Albumcover kann der Titel sofort wechseln; dafür ist kein neuer Download nötig. Fehlende Bilder und echte Verbindungs-/Konfigurationsfehler bleiben sichtbar. Der bewusste Wiedergabestart zeigt weiterhin „Starte …“ und sein Ergebnis.

Die Slide-Bewegung wird in dieser Firmware nicht verwendet. Das bestehende YAML-Feld `display.animation` bleibt für die Kompatibilität erlaubt, hat in 0.1.5 aber keine Wirkung. Die Wartezeit wird nicht künstlich verlängert; während eines ausstehenden Bildwechsels ist die Auswahl gesperrt, damit ein Tipp auf das noch alte Cover keine unsichtbare neue Folge startet. Ein Bildfehler oder 20 Sekunden ohne Bildrückmeldung lösen diesen Zustand auf und zeigen den Fehler.

**Nur das Tessera-Plugin auf 0.1.5 aktualisieren und die Display-Firmware neu bauen.** Der HA-Companion 0.1.4 und die Bibliotheksdatei benötigen für diese Änderung kein Update.

Der statische Bildtausch verwendet die vorhandene API, keine zweite komplette Bildpufferung: Bei einem Ebenenwechsel mit weniger Nachbarn entfernt Tessera nicht mehr benötigte Plätze weiterhin sofort. Der native Test prüft die unterdrückten Ladehinweise und die Reihenfolge der Titel-/Bildrückmeldung, keine gerenderten Frames. Der tatsächliche Eindruck auf dem Display bleibt vor Ort zu prüfen.

## Update auf 0.1.6: Größere Cover und ruhiger Hintergrund

Das bei Berührung kurz dunklere Feld stammt aus Tessera's gedrücktem Kachelzustand, während die Cover samt Spiegelung bereits im normalen Hintergrund gerendert sind. Kidsplayer legt jetzt eine eigene undurchsichtige, nicht anklickbare Fläche unter seine Inhalte. Sie übernimmt die normale Kachelfarbe; ein transparenter Kachelhintergrund verwendet die Seitenfarbe. Die normale Farbe wird unabhängig vom aktuellen Druckzustand gelesen. Kein fremdes Objekt und keine andere Kachel werden verändert.

Diese Lösung deckt den **Inhaltsbereich des Plugins** ab. Den schmalen äußeren Rahmen bzw. die Polsterung der Tessera-Kachel zeichnet weiterhin der Kern; dessen Druckeffekt kann die derzeitige Plugin-API nicht vollständig abschalten. Ein vollständiger Ausschalter für diesen äußeren Bereich würde eine Kern-/API-Erweiterung erfordern.

Das Mittelcover darf jetzt statt 50 % ungefähr 63 % der Inhaltsbreite einnehmen; die genaue Obergrenze lässt links und rechts weiterhin Platz für perspektivische Nachbarn. Eine kürzere Kopfzeile und eine gemeinsame Fußzeile schaffen zusätzlich Höhe. Die Covergruppe wird in der restlichen Höhe mittig platziert. In einer breiten, hohen Testkachel mit 400 × 380 Inhaltspixeln wächst die Coverbreite von 200 auf 253 Pixel; bei anderen Größen entscheidet weiterhin der verfügbare Platz.

Titel und Status verwenden einzeilige Labels und dieselbe Fußzeile: Ohne Meldung erscheint der Titel, bei Wiedergabestart oder Fehler stattdessen die Meldung. Keine zwei Texte überlagern sich. Die Referenz-Schleife für Nachbarn bleibt unverändert; die Begrenzung der Hauptcovergröße wurde auf den ausdrücklichen Wunsch nach größeren Covern angepasst. Bei größeren Mittelcovern passen entsprechend weniger äußere Nachbarn vollständig in die Kachel.

**Nur Plugin 0.1.6 installieren und die Display-Firmware neu bauen.** Companion 0.1.4 und Bibliotheks-YAML bleiben unverändert. Die Änderungen sind nativ gegen die echten API-Header geprüft; Größe und Druckwirkung müssen auf dem Guition visuell abgenommen werden.

## Companion 0.1.7: Automatische Cover / HTTP 500

Im untersuchten Fehlerfall wurden die Bibliothek und eine automatische Coveradresse geliefert, der anschließende HA-Bildabruf antwortete aber mit HTTP 500; lokale Reihenbilder funktionierten weiter. Dabei wurde ein Fehler im bisherigen HTTP-Leser gefunden: `response.content.read(n)` liefert bei aiohttp nicht zwingend das vollständige Bild, sondern gegebenenfalls nur den bereits verfügbaren Anfang. Ein anschließend abgeschnittenes JPEG/PNG kann beim Decodieren fehlschlagen. Die [aiohttp-Dokumentation](https://docs.aiohttp.org/en/stable/streams.html#reading-attributes-and-methods) beschreibt dieses Verhalten ausdrücklich. Der über MCP verfügbare Sammelprotokolleintrag enthält keinen vollständigen Decoder-Traceback; deshalb wird nicht behauptet, dass jede denkbare Ursache für HTTP 500 damit ausgeschlossen ist.

Der neue Leser verarbeitet alle Netzwerkstücke bis zum Dateiende und prüft nach jedem Stück das bestehende 2-MiB-Limit. HTTP-Fehler, Redirects und leere Antworten werden eindeutig erkannt; Redirects werden weiterhin nicht verfolgt. Fehler im HA-Cover-View landen mit Grund bzw. Decoderklasse im Protokoll, ohne die möglicherweise signierte Bild-URL auszugeben. Ein neuer Cache-Schlüssel fordert die Bilder nach dem Update frisch an.

**Nur den HA-Companion aktualisieren:** Den gesamten aktuellen Ordner `backend/custom_components/kidsplayer/` nach `/config/custom_components/kidsplayer/` kopieren, **einschließlich `images.py`**, oder das mit `tools/package-companion.py` erzeugte Companion-0.1.7-Archiv nach `/config` entpacken. Danach Home Assistant neu starten und die betroffene Folge öffnen. Die Bibliothek lädt innerhalb etwa 30 Sekunden ihre neuen Coveradressen. YAML und Display-Firmware bleiben unverändert.

`cover: auto` gilt immer für genau den betreffenden Eintrag. Eine Reihe mit `cover: conni.jpg` bleibt ein lokales Bild, auch wenn ihre Folgen `cover: auto` verwenden. Für ein automatisches Reihenbild dort ebenfalls `auto` setzen. Ganze Album-URIs und vollständig provider-spezifische URIs werden für die Metadatenauflösung verwendet; es gibt keine Titelsuche.

Wenn weiterhin „Cover fehlt“ erscheint, das HA-Protokoll nach **`Kidsplayer-Coverdownload fehlgeschlagen`** bzw. **`Kidsplayer-Covermetadaten fehlen`** filtern. Die neue Meldung unterscheidet zum Beispiel HTTP 403, Zeitüberschreitung und ungültige Bilddaten. Eine erfolgreiche Darstellung auf dem echten Display ist erst nach dem Update und einem erneuten Abruf bestätigt.

## Update auf 0.1.7: Überschrift und runde Bedienelemente

Im Inspector besitzt jede Kidsplayer-Kachel die Option **Überschrift**. Dort beispielsweise `Mirellas Hörspiele` eintragen; ein leeres Feld blendet den Text aus. Auf der Folgenebene ersetzt ein Kreis mit Linkspfeil den bisherigen Zurück-Text. Der ausgewählte Reihenindex bleibt beim Zurückgehen erhalten.

Ab **280 × 220 Tessera-Referenzpixeln im Inhaltsbereich** erscheinen unten rechts zwei runde Knöpfe mit jeweils 44 Referenzpixeln Durchmesser. Die tatsächlichen Pixelmaße skalieren mit Tessera. In schmalen/niedrigen Kacheln werden beide weggelassen. Titel und Meldungen erhalten Platz links neben den Knöpfen; die eigentlichen Cover bleiben vollständig sichtbar.

- **⋯** öffnet die vorhandene Tessera-Mediensteuerung mit Cover, Lautstärke, Fortschritt und weiteren Playerfunktionen. **Voraussetzung:** Im Kidsplayer-Inspector einen Player auswählen und für **dieselbe Entity** zusätzlich eine normale Tessera-Medienkachel im Layout anlegen. Diese darf auf einer anderen Seite liegen. Kidsplayer öffnet deren echte Detailansicht als Overlay, ohne die Seite oder seine Auswahl zu wechseln. Der native Zurückknopf schließt die Steuerung. Fehlt die Medienkachel, erscheint `Medienkachel fuer Player fehlt`.
- **▶ / Ⅱ** pausiert oder setzt die aktuelle Warteschlange fort. Der Knopf folgt dem Playerzustand aus Home Assistant und sendet Tessera's `Wish::PLAYING` (`media_player.media_play_pause`). Es wird **kein** erneuter `kidsplayer/play`-Aufruf gesendet: Die Folge startet beim Fortsetzen nicht erneut am Anfang. Beim unbekannten Anfangszustand erscheint das kombinierte Play/Pause-Symbol. Ein nicht erreichbarer Player bzw. ein fehlgeschlagener Versand erzeugt eine Meldung; es gibt keine automatische Wiederholung.

Die beiden Knöpfe benötigen den **Player im Inspector**. Ist nur `player:` in der Backend-YAML gesetzt, funktionieren Bibliothek und Folgenwiedergabe weiterhin, die neuen Knöpfe bleiben verborgen. Dadurch steuern sie immer den Player dieser Kachel. Zwei Kidsplayer-Kacheln mit verschiedenen Playern bleiben unabhängig.

**Technische Grenze:** Tessera API 0.24 bietet `open_card` nur für Plugin-eigene Karten an. Deshalb verbindet ein kleiner Codegen-Adapter den Knopf mit `runtime_tiles::hold_card` der vorhandenen Medienkachel. Das Tessera-Kernprojekt wird nicht geändert; die Medienansicht wird nicht kopiert. Der Adapter verwendet aber eine interne Kernfunktion und ist deshalb bei Tessera-Upgrades erneut zu prüfen. Grundlage ist der untersuchte Kerncommit `9c7c6a674d2e214355b85d810fb7d08f8fcd3544`. Ohne eine zusätzliche Medienkachel fehlen dem Kern die benötigten Playerdaten und Fähigkeiten.

**Installation:** Kidsplayer auf **0.1.7** aktualisieren, Display-Firmware in Tessera neu bauen und installieren. HA-Companion **0.1.7**, Bibliotheksdatei und Cover bleiben unverändert. Danach Überschrift und Player im Inspector einstellen, die normale Medienkachel bei Bedarf ergänzen und das Layout senden. Änderungen an der Überschrift benötigen danach keinen weiteren Firmwarebau.

**Am Display prüfen:** Reihe öffnen, runden Zurückknopf testen, erneut eine Folge starten, mit dem unteren rechten Knopf pausieren und fortsetzen. Die Position muss erhalten bleiben. Mit **⋯** die native Steuerung öffnen und wieder schließen: Dieselbe Folge und Bibliotheksauswahl müssen sichtbar bleiben. Zusätzlich eine kleine Kachel testen: Dort fehlen die beiden unteren Knöpfe absichtlich.
