# Kidsplayer 0.1.0

Kidsplayer zeigt Hörspielreihen und deren Folgen innerhalb derselben Tessera-Kachel. Seitlich tippen blättert; das mittlere Cover öffnet eine Reihe oder startet eine Folge. Oben führt „Zurueck“ zur Reihenebene. Die Tessera-Seite bleibt erhalten. Drei Coverplätze mit Perspektive und optionaler kurzer Gleitbewegung verwenden Tessera-Bildübertragung und Cache. Spiegelung ist in dieser Version zugunsten großer Cover weggelassen.

**Status:** Beta-Implementierung mit Mocktests und ausgeführten nativen C++-Navigationstests. Home Assistant und Hardware wurden nicht gestartet. Die Installationsschritte sind für einen anschließenden Test beschrieben, nicht bereits auf deinem Display ausgeführt.

## Set up

Voraussetzungen und Installation auf dem Guition

1. Home Assistant mit der **offiziellen** Integration `music_assistant`, einem eingerichteten MA-Server, Apple-Music-/Dateianbieter und einem erreichbaren MA-Lautsprecher. Die alte benutzerdefinierte Integration `mass` wird nicht unterstützt.
2. Tessera mit Plugin-API **0.24** oder kompatibler neuerer API. Die Analyse verwendet den in `docs/ARCHITECTURE.md` festgehaltenen Core-Commit. Der Companion benutzt die Schnittstellen von `music-assistant-client` **v1.8.0**, den die untersuchte HA-Version selbst mitbringt. Ein älterer Server/Client ohne `autoplay`, `shuffle` oder Benutzerparameter muss aktualisiert werden; es gibt keinen stillen Rückfall auf eine unsichere Teilwiedergabe. MA-Serverberechtigungen müssen die Benutzerzuordnung erlauben.
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
9. Im Layout eine **Kidsplayer**-Kachel ab **2 × 2** hinzufügen. Für den ersten Guition-Test möglichst den Großteil der 480 × 480-Seite verwenden. Als Player den MA-Mediaplayer auswählen; unter **Bibliotheks-ID** `kinderzimmer_1` eintragen. Speichern und senden.
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
      animation: true
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

Der Companion stellt die Grafik unter einer kurzen, **authentifizierten** HA-Bildadresse bereit. Tessera lädt sie mit seinen vorhandenen Zugangsdaten, skaliert sie in die drei Coverplätze und cached das Ergebnis. Das Bild behält sein Seitenverhältnis (`contain`), ohne Abdunklung oder Text über dem Motiv. Download maximal 2 MiB, Ausgangsbild höchstens 360 × 360 Pixel. Der Originalcoverinhalt verlässt nur den bestehenden HA/Tessera-Bildweg; keine Schlüssel gehen an das Display. Ein bestehendes lokales Bild nach Austausch durch eine kleine YAML-Änderung invalidieren; ansonsten kann Tessera es bis zu sechs Stunden cachen.

## Mehrere Kacheln, Player und Benutzer

Kachel A wählt `kinderzimmer_1`, Kachel B `kinderzimmer_2`; beide können auf derselben Seite stehen. Jede Tile-Instanz hält ihre Kategorie, Auswahlindizes und ausstehenden Anfragekennungen selbst. Nach Neuanlage/Neustart beginnt sie auf der Reihenebene. Ein Player im Inspector überschreibt `player:` der Bibliothek. Fehlt er, wird YAML verwendet.

Mit unterschiedlichen Playern spielen beide unabhängig. Wählen zwei Kacheln denselben Player, teilen sie dessen MA-Queue: Die zuletzt gestartete Folge ersetzt die vorherige. Das ist beabsichtigt. Parallel gestartete Aktionen desselben Players werden im Backend serialisiert.

Optional wird `music_assistant_user: kind1` als `user` an MA weitergereicht, bei Metadaten und Wiedergabe. Der Name muss in MA existieren; MA muss Impersonation erlauben. Dies bereitet spätere kontogebundene Medien vor. Audiobookshelf-Integration, Hörfortschritt, Fortsetzen von Hörbüchern und echte Inhaltssperren gehören noch nicht zu 0.1.0. Die Auswahl in Kidsplayer ist keine Zugriffskontrolle für MA.

## Wiedergabe auf dem Testdisplay abnehmen

1. Prüfe denselben MA-Player zuerst in der MA-Oberfläche mit dem gewünschten Anbieter.
2. Beginne mit einer Folge aus zwei oder drei bekannten, kurzen Tracks. In der MA-Queue müssen exakt diese Tracks in YAML-Reihenfolge erscheinen; Shuffle, Repeat und Autoplay müssen aus sein.
3. Prüfe ein komplettes Album, einschließlich Discwechsel. Die Queue muss Disc 1 vor Disc 2 zeigen.
4. Prüfe die drei Folgen eines zwölfteiligen Apple-Albums separat. Bei Folge 2 müssen ausschließlich Tracks 5–8 erscheinen, Track 5 zuerst. Bis zum Ende laufen lassen: Track 9 darf nicht starten.
5. Starte während einer laufenden Folge eine andere: Die Queue muss ersetzt werden und bei deren erstem Track beginnen. Pause/Stop anschließend beobachten: Kidsplayer darf nicht neu starten.
6. Prüfe fünf lokale Tracks und eine gemischte Liste über denselben Player.
7. Trage testweise eine nicht verfügbare URI ein: Fehlermeldung muss erscheinen; kein Ersatzalbum darf gesucht werden. Beachte: Der tatsächliche Player kann bei erst während des Streamings erkannten Fehlern anders reagieren als der Metadaten-Preflight.
8. Setze zwei Kacheln auf dieselbe Seite und navigiere unabhängig. Ändere YAML ohne Firmwarebau und prüfe die Aktualisierung.
9. Entferne ein Cover, prüfe Platzhalter und Fehlerrückmeldung; teste lange Titel und Kachelgrößen ab 2 × 2.

## Fehleranalyse und Grenzen

- „Bibliotheks-ID fehlt“: Inspector ergänzen. Unbekannte ID/ungültige YAML: HA-Protokoll nach `custom_components.kidsplayer` filtern.
- „Tessera nicht verbunden“ oder Timeout: Verbindung zu Tessera/HA und Companion-Installation prüfen. Bei einem Wiedergabetimeout zuerst die MA-Queue prüfen, da die Aktion bereits angekommen sein kann.
- Kein Player: offizielle MA-Entity auswählen; ein gewöhnlicher Cast-/Sonos-Player außerhalb der MA-Integration genügt nicht.
- Benutzerfehler: Namen und MA-Berechtigung prüfen; ohne gewünschte Benutzerzuordnung das YAML-Feld entfernen.
- Kein Cover: Leserechte, Größe, Bildformat und relativen Pfad prüfen. Bei Netzwerkcovern folgt der Companion keinen HTTP-Redirects.
- Änderungen werden nicht übernommen: Datei vollständig speichern, 30 Sekunden warten oder nach einem Fehler erneut tippen. Gelöschte Kategorie mit „Zurueck“ verlassen.
- Fehler nach Start, Provider-Fallback, Gruppen-/Syncplayer, echte Streamverfügbarkeit und Benutzerfortschritt sind bislang nicht am echten Server geprüft. Keine Aussage über eine bereits erfolgte Hardwareabnahme.
- Keine vollständige grafische Vorschau der verschachtelten Bibliothek im Tessera-Editor, keine Swipe-Gesten, kein persistenter Navigationszustand, keine Reflexion und keine Bibliotheks-YAML im Inspector. Firmwaretexte sind momentan deutsch in ASCII-Schreibweise.
- Album-Tracknummern (`album_uri`, `tracks`, `track_range`) sind **noch nicht implementiert** und werden als unbekannte Felder abgewiesen. Die MA-Albumtrack-API liefert die notwendigen URIs und Disc-/Tracknummern; eine spätere Erweiterung muss Disc explizit behandeln, fehlende Nummern verweigern und Metadatenänderungen berücksichtigen.

## Privacy

Bibliotheken bleiben in Home Assistant; das Display erhält nur die sichtbaren Titel, IDs und Coveradressen. Music Assistant kontaktiert die konfigurierten Medienanbieter. Automatische Cover werden vom durch MA angegebenen Host über HA geladen; dieser Host sieht die IP von Home Assistant. Keine Telemetrie in Kidsplayer.
