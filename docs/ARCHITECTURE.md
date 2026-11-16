# Technische Untersuchung

Stand der lokal untersuchten Git-Checkouts:

| Quelle | Exakter Stand |
| --- | --- |
| New music, vollständige Referenz | `ae25258d1a8d96ae9d6a521ee313179532a7ea08` |
| Tessera Core main | `9c7c6a674d2e214355b85d810fb7d08f8fcd3544` |
| Home Assistant Core dev | `0fc2cd50ca147c23a466b0b7b614884f59f2d853` |
| MA Python Client, zusätzlich Release v1.8.0 untersucht | main `c8525a08d2a37ad21efa2c6c5ed5e63878d295b4` |
| MA Server dev | `d85c4ab29f5d8438552d977b758b16a7d732075a` |

Diese Referenzen belegen die untersuchten Schnittstellen. Sie bedeuten keine Laufzeitprüfung oder allgemeine Kompatibilitätszusage für beliebige ältere Releaseversionen.

## A: Konfiguration pro Kachel

Tessera's aktuelle API ist 0.24, New music benennt 0.17. Die Manifestnamen, `register_plugin`, Tile-Lebenszyklus, Picture API und `tessera::send(const Plugin*, JsonObjectConst)` wurden gegen den aktuellen Header geprüft.

- `screen_manager/app/plugin_manifest.py`: `OPTION_KINDS` enthält `text`, `choice`, `number`, `toggle`, `entity`. Kein mehrzeiliger YAML-Editor. `MAX_TEXT=64`, maximal zwölf Optionen pro Kachel, gemeinsam 1280 JSON-Bytes (`core.plugin_options`). Daher ist Bibliotheks-YAML als Textoption ungeeignet.
- `docs/PLUGINS.md`, `plugins.py`: Kein ausführbarer Backend- oder Editorcode aus Plugins. `fetch` ist deklarativ und darf öffentliche, freigegebene JSON-Hosts anfragen, keine lokalen HA-/MA-Server.
- Optionen sind Teil des gespeicherten Layoutdokuments und seiner Laufzeitübertragung. Sie benötigen keinen Build. Plugininstallation und Firmwarecodeänderungen benötigen einen Build. Plugininstallationen/-inputs werden in `/data/plugins.json`, Secrets separat in `/data/plugin_secrets.json` gehalten; die Bibliotheksdatei des Companions liegt unabhängig davon in `/config`.
- Pro Kachel deshalb eine kurze Bibliotheks-ID plus Tessera's bestehende Playerauswahl über `domains: [media_player]`, `has_attributes: [mass_player_type]`. Der Player wird in `TileContext.entity` übergeben. Der Companion unterstützt den YAML-Player als Rückfall, sofern die Editorversion eine ungebundene Kachel zulässt.
- Ein YAML-Wrapper `libraries:` erlaubt mehrere vollständige Bibliotheken. Verbindliche Grenzen und Felder in `library.py`, Beispiel in `kidsplayer/examples/libraries.yaml`. Kein Upload von YAML oder Audio zum ESP32.

Der Companion wird **in HA**, nicht im Tessera-Add-on installiert. Er nutzt HA's bestehende administrative Websocket-Verbindung aus Tessera. Manifestrechte `ha_commands: [kidsplayer/browse, kidsplayer/play]` beschränken die Firmware auf diese beiden Methoden. Diese sind nach Tessera's regulären Regeln gültige Befehlsnamen. Es gibt keinen Kernpatch und keinen zusätzlichen Port.

## B: Geordnete Wiedergabe

[HA's aktuelle Aktion und Schema](https://github.com/home-assistant/core/tree/0fc2cd50ca147c23a466b0b7b614884f59f2d853/homeassistant/components/music_assistant) erlauben `media_id: list[str]`, `enqueue`, `radio_mode`, `shuffle`, `start_item`, `username`. Der Handler bewahrt die Listenreihenfolge. Bei nicht verifizierter URI kann er jedoch `get_item_by_name` aufrufen. Genau dieser Rückfall widerspricht dem gewünschten Verhalten.

Kidsplayer nutzt deshalb als Alternative die [offiziellen MA-Clientmethoden](https://github.com/music-assistant/client/tree/v1.8.0/music_assistant_client):

1. `music.get_item_by_uri(uri, user=...)` für jedes konfigurierte Objekt, ohne Titelsuche.
2. Album bei Bedarf über `music.get_album_tracks(item_id, provider, user=...)` expandieren. Sortierung explizit `(disc_number, track_number)`; Mehrdeutigkeit oder fehlende Nummern sind Fehler.
3. Verfügbarkeit aller ermittelten Tracks prüfen; Fehler vor Queueänderung zurückgeben.
4. `player_queues.get_active_queue(player_id, user=...)`: unterstützt grundsätzlich aktive/Synchronisationsqueues, jedoch bisher nur durch Codeanalyse bestätigt.
5. `repeat(..., OFF)`, `autoplay(..., False)`; anschließend **ein** `play_media(media=alle_tracks, option=REPLACE, shuffle=False, radio_mode=False, user=...)`.

Die Reihenfolge expliziter Listen wird nicht sortiert. Gemischte Anbieter sind durch die Listenschnittstelle möglich; die reale Abspielbarkeit richtet sich nach den installierten Providern. MA übernimmt Fortsetzung, Pause und Stop. Kidsplayer überwacht kein Trackende und besitzt keinen Wiederanlaufmechanismus. Ein verlorenes Play-Acknowledgement führt zum Hinweis „Player pruefen“, niemals zu automatischer Wiederholung.

Praktische Grenzen: Ein verfügbares Metadatenobjekt garantiert keinen später erfolgreichen Stream. MA kann seine eigenen Provider-Mappings auswerten. Kidsplayer implementiert keine zusätzliche Suche; eine Garantie gegen serverinterne Alternativen erfordert reale Tests und gegebenenfalls eine künftige serverseitige Quellenbindung. Bereits vollständig vom Provider verschwundene Albumtracks können ohne explizite Soll-Liste nicht entdeckt werden. Queueänderungen durch andere Apps bleiben möglich. Schlagen Queueeinstellungen nach einem erfolgreichen Teilschritt fehl, kann Repeat/Autoplay bereits geändert sein, ohne dass neue Wiedergabe startet; kein Wiederherstellen, das unbeabsichtigt Audio starten könnte.

## C: Mehrere Folgen desselben Apple-Albums

Jede Episode enthält ausschließlich ihre `playback.items`. Es gibt keinen alternativen Quellenmodus. Die Folgen 1–3 dürfen disjunkte URI-Listen desselben Albums verwenden. Es wird keine übergeordnete Album-URI mitgeschickt; nach dem Ende ist keine weitere Episode Teil der Queue. Autoplay ist ausdrücklich deaktiviert, weil `radio_mode=false` allein moderne MA-Autoplay-Konfigurationen nicht ausschaltet.

Zukünftig lässt sich `album_uri` plus Disc-/Trackauswahl vor dem bestehenden Playbackmodell zu einer Liste auflösen. Die MA-API stellt Albumtracks mit URI, Track- und Discnummer bereit. Wiederholte Tracknummern über Discs erfordern eine eindeutige Discangabe; unbekannte/fehlende Nummern müssen Fehler sein. Auflösungen müssen gegen Metadatenrevisionen validiert werden. In 0.1.0 wird diese Komfortsyntax abgewiesen. Zeitbasiertes Schneiden ist nicht implementiert.

## Transport und Speicher

Eine Anfrage enthält Bibliotheks-ID, Player, Kategorie, Index oder Episoden-ID und Revision. Sie bleibt unter `tessera::send`'s Grenze von 512 Bytes. Die Antwort liefert genau drei Nachbarn als verschachtelte Objekte und wenige skalare Felder. Keine Medien-URIs gehen an die Firmware.

Tessera `plugins.bounded`: Antwort maximal rund 3200 Bytes, Texte auf 48 UTF-8-Bytes, Objektschlüssel auf 32 Zeichen. Die tatsächliche Kidsplayer-Antwort ist viel kleiner, es gibt keine unbemerkt abgeschnittene ganze Folgenliste. Antwortkennungen `re` werden dem richtigen Tile zugeordnet; gelöschte Tiles werden aus dem Register entfernt. Kategorien, Indizes und Status liegen ausschließlich im Tile, nicht global im Plugin. Lediglich die Instanzliste und der Antwortverteiler gehören dem Pluginobjekt.

Firmware: drei `ui::picture`-Plätze pro Kachel, deklarierte Tile-Memory 3600 Bytes; `tessera::Text/List` nutzen Tessera's PSRAM-Allocator. Bild-/Atlas-Speicher und Layoutbudget verwaltet Tessera zusätzlich. Diese Deklaration ist eine konservative Schätzung, keine Hardwaremessung. Der Guition besitzt PSRAM; mehrere große Kacheln teilen trotzdem dessen endlichen Bildspeicher. Keine Bibliotheksgröße wächst im ESP32-RAM mit.

Backend: Datei maximal 512 KiB, kein URI-Limit im Transport, Coverregistrierung LRU maximal 512 Einträge. Tessera's vorhandener Bildcache begrenzt nach untersuchtem Core auf 16 MiB/256 Einträge, behält Bilder bis zu sechs Stunden und bündelt die drei Cover in einen Atlas. Coverquellen werden durch einen authentifizierten HA-View unter dem von Tessera erlaubten `/api/image/serve/`-Präfix abgebildet. Ein Token ist 20 Hexzeichen lang, die gesamte Bildadresse bleibt unter 48 Bytes. Downloadlimit 2 MiB und Decoderlimit 16 Megapixel, Ausgang maximal 360 × 360. Keine öffentliche Dateifreigabe.

## Wiederverwendung von New music

Übernommen wurden das visuelle Grundprinzip (großes Mittelcover, kleinere perspektivische Nachbarn), der Tessera-Picture-/Slide-Weg und die kurze ESPHome-Registrierung. Neu sind Companion, strikter Parser, Paging, verschachtelte Navigation, Instanzrouting, exakte Playbacklisten, Revisionprüfung und Fehlerbehandlung. Deezer-Fetch, automatische Rotation, globale Release-Card-Auswahl und Titelsuche wurden nicht übernommen. Seit 0.1.2 entsprechen die drei sichtbaren Plätze den Proportionen, perspektivischen Höhen, Abstand, Spiegelung und 320-ms-Slide-Parametern der Referenz. Der Slide startet wegen des asynchronen Paging erst zusammen mit der Antwort und nur bei geändertem, vorhandenem Mittelcover. Eine kontinuierliche 3D-Animation bietet diese Tessera-Slide-API nicht. Das Original bleibt unverändert unter `examples/new_music/`.

[Öffentliche Pluginanleitung](https://tessera-maxgramser.on-forge.com/docs/plugins) und [Pluginübersicht](https://tessera-maxgramser.on-forge.com/plugins) wurden ebenfalls konsultiert; für Details sind die oben festgehaltenen Quellstände maßgeblich.
