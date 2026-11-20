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

Jede Episode enthält entweder ihre `playback.items` oder ab Companion 0.1.9 eine eindeutige Album-Trackauswahl. Es gibt keinen alternativen Quellenmodus. Die Folgen 1–3 dürfen disjunkte URI-Listen desselben Albums verwenden. Es wird keine übergeordnete Album-URI mitgeschickt; nach dem Ende ist keine weitere Episode Teil der Queue. Autoplay ist ausdrücklich deaktiviert, weil `radio_mode=false` allein moderne MA-Autoplay-Konfigurationen nicht ausschaltet.

Ab Companion 0.1.9 löst `album_uri` plus `tracks` oder `track_range` eine Folge zu genau den gewählten Tracks auf. Die Auswahl erfolgt nach MA-Disc-/Tracknummern, nicht Listenposition. Bei mehreren Discs ist eine explizite `disc` erforderlich; fehlende/mehrdeutige Nummern sind Fehler. Die Auflösung wird bei jedem Start neu vorgenommen. Die vorhandene Konfigurationsrevision schützt weiterhin vor geänderter YAML; MA-Metadaten werden nicht durch eine zusätzliche Kidsplayer-Revision eingefroren. Eine umnummerierte Veröffentlichung kann deshalb andere Inhalte unter derselben Nummer liefern; wer feste Track-IDs benötigt, verwendet `items`. Zeitbasiertes Schneiden ist nicht implementiert.

## Transport und Speicher

Eine Anfrage enthält Bibliotheks-ID, Player, Kategorie, Index oder Episoden-ID und Revision. Sie bleibt unter `tessera::send`'s Grenze von 512 Bytes. Die Antwort liefert das Zentrum plus bis zu drei Nachbarn je Seite als verschachtelte Objekte und wenige skalare Felder. Keine Medien-URIs gehen an die Firmware.

Tessera `plugins.bounded`: Antwort maximal rund 3200 Bytes, Texte auf 48 UTF-8-Bytes, Objektschlüssel auf 32 Zeichen. Die tatsächliche Kidsplayer-Antwort ist viel kleiner, es gibt keine unbemerkt abgeschnittene ganze Folgenliste. Antwortkennungen `re` werden dem richtigen Tile zugeordnet; gelöschte Tiles werden aus dem Register entfernt. Kategorien, Indizes und Status liegen ausschließlich im Tile, nicht global im Plugin. Lediglich die Instanzliste und der Antwortverteiler gehören dem Pluginobjekt.

Firmware: bis zu sieben `ui::picture`-Plätze pro Kachel, deklarierte Tile-Memory ab 0.1.12 7600 Bytes; `tessera::Text/List` nutzen Tessera's PSRAM-Allocator. Bild-/Atlas-Speicher und Layoutbudget verwaltet Tessera zusätzlich. Diese Deklaration ist eine konservative Schätzung, keine Hardwaremessung. Der Guition besitzt PSRAM; mehrere große Kacheln teilen trotzdem dessen endlichen Bildspeicher. Keine Bibliotheksgröße wächst im ESP32-RAM mit.

Backend: Datei maximal 512 KiB, kein URI-Limit im Transport, Coverregistrierung LRU maximal 512 Einträge. Tessera's vorhandener Bildcache begrenzt nach untersuchtem Core auf 16 MiB/256 Einträge, behält Bilder bis zu sechs Stunden und bündelt die bis zu sieben Cover in einen Atlas. Coverquellen werden durch einen authentifizierten HA-View unter dem von Tessera erlaubten `/api/image/serve/`-Präfix abgebildet. Ein Token ist 20 Hexzeichen lang, die gesamte Bildadresse bleibt unter 48 Bytes. Downloadlimit 2 MiB und Decoderlimit 16 Megapixel, Ausgang maximal 360 × 360. Keine öffentliche Dateifreigabe.

## Wiederverwendung von New music

Übernommen wurden das visuelle Grundprinzip (großes Mittelcover, kleinere perspektivische Nachbarn), der Tessera-Picture-/Slide-Weg und die kurze ESPHome-Registrierung. Neu sind Companion, strikter Parser, Paging, verschachtelte Navigation, Instanzrouting, exakte Playbacklisten, Revisionprüfung und Fehlerbehandlung. Deezer-Fetch, automatische Rotation, globale Release-Card-Auswahl und Titelsuche wurden nicht übernommen. Ab 0.1.3 wird die Bildplatz-Schleife der Referenz unverändert übernommen: bis zu drei Nachbarn auf jeder Seite, überlappend von außen nach innen geschichtet und bei Platzmangel weggelassen. Die normale Kachelhöhe wird mit der Referenzformel unterhalb der Zurück-Zeile berechnet. Sieben Plätze werden im Manifest deklariert, das Backend liefert sieben Objekte. Eine quadratische Kachel kann nach denselben Originalregeln trotzdem nur drei sichtbare Cover haben; breite, niedrige Kacheln können sieben aufnehmen. Bis 0.1.4 startete der Slide wegen des asynchronen Paging erst zusammen mit der Antwort und nur bei geändertem, vorhandenem Mittelcover. Ab 0.1.5 wird kein Slide mehr verwendet: Der Kern behält nicht leere alte Bildplätze bis zum neuen Atlas, die Kachel hält Titel und Header bis zur Bildrückmeldung zurück. Bibliotheksabfragen erzeugen keine Ladeanzeige. Eine kontinuierliche 3D-Animation bietet diese Tessera-Slide-API nicht. Das Original bleibt unverändert unter `examples/new_music/`.

[Öffentliche Pluginanleitung](https://tessera-maxgramser.on-forge.com/docs/plugins) und [Pluginübersicht](https://tessera-maxgramser.on-forge.com/plugins) wurden ebenfalls konsultiert; für Details sind die oben festgehaltenen Quellstände maßgeblich.

## Kompatibilitätskorrektur 0.1.4

Die ursprüngliche Analyse anhand der Entwicklungsstände reichte für den installierten stabilen HA-Client nicht aus. Der reale Versionsvergleich ergab HA 2026.11.1 mit Client 1.6.0 und Server 2.10.12/Schema 65. `compat.py` berücksichtigt daher sowohl Methodensignatur als auch Serverschema. Ein neuer Client allein erlaubt noch keine neuen Kontextparameter an einen alten Server.

Auf Schema 65 laufen Metadaten und Queueeinstellungen im HA-Verbindungskontext, während der eine Wiedergabeaufruf den optionalen MA-Benutzer trägt. Autoplay wird über den offiziellen alten Alias deaktiviert. Weil Client 1.6 `shuffle` nicht weiterleiten kann, wird das vom Server unterstützte offizielle `player_queues/play_media`-Kommando direkt über dessen vorhandenen Clienttransport gesendet. Alle Tracks bleiben in einem Aufruf und in Reihenfolge; `replace`, Shuffle aus und Radiomodus aus sind explizit. Für diesen Pfad verlangt der Companion mindestens das untersuchte Schema 65. Neue Schema-101-/Client-1.8-Aufrufe bleiben unterstützt. Kein TypeError-basiertes Wiederholen eines Play-Aufrufs.

Tessera's `server.Refused` hält den Detailtext separat, `plugins.answer` überträgt aber nur `str(error)` und verliert ihn. Ohne Kernpatch löst ein optionales Kidsplayer-Protokollfeld dies: `protocol: 1` liefert Anwendungsfehler als `result: {ok:false,error,message}` innerhalb einer transportseitig erfolgreichen Antwort. Die Firmware prüft diesen Fehler vor der Wiedergabe-Erfolgsmeldung. Ohne das Feld bleibt es bei der ursprünglichen HA-Fehlerantwort, damit alte Firmware keinen fehlgeschlagenen Start als erfolgreich meldet. Die Adminprüfung wird beibehalten.

## Kachelbedienung und native Mediensteuerung ab 0.1.7

`options.heading` ist ein kurzer Inspector-Text (Standard `Reihen`, bis 64 Zeichen), unabhängig pro Kachel. Ein eigener runder Back-Key wird zusammen mit den Labels erst beim Bildwechsel auf die Folgenebene eingeblendet. Ab 0.1.8 oben rechts angeordnete Player-Keys sind an die nutzbare Größe (280 × 220 Referenzpixel) und einen Inspector-Player gebunden. Alle Touchbereiche laufen weiterhin ausschließlich durch `Tile::on_tap`; es gibt keine eigenen LVGL-Touchhandler.

`on_state` verarbeitet den HA-Playerzustand für Play/Pause. `tessera::wish(player, Wish::PLAYING, value)` nutzt den nativen optimistischen Aktionspfad, ohne die Folge erneut einzureihen. Der Manifest-Eintrag `home_assistant_actions` deklariert deshalb `media_player.media_play_pause`. Schnell aufeinanderfolgende Doppeltipps werden 400 ms lang unterdrückt. Keine automatischen Play/Pause-Wiederholungen; ein Backend-Browse/Atlastransfer blockiert die Medienknöpfe nicht.

API 0.24 bietet keine öffentliche Funktion zum Öffnen beliebiger nativer Entity-Karten (`tessera::open_card` öffnet nur Plugin-Karten). `native_media.h` und ein Codegen-Lambda suchen daher eine normale Medienkachel derselben Entity in `runtime_tiles::model` und rufen deren vorhandenes `hold_card(index)` auf. Das öffnet den originalen Medien-Overlay inklusive dessen Datenversorgung; keine Seite wird gewechselt, keine Model-Kachel angelegt oder umgeschrieben. Die zusätzliche Medienkachel darf auf einer anderen Seite stehen. Fehlt sie, wird der Fehler angezeigt. Die Verbindung hängt gezielt nur an `enabled`, `model` und `hold_card` des untersuchten Kerncommits `9c7c6a674d2e214355b85d810fb7d08f8fcd3544`; diese internen Namen sind keine stabile Plugin-API. Bei Kernupdates ist dieser Adapter erneut zu prüfen. Ein öffentlicher nativer Entity-Karten-Opener könnte ihn später ersetzen.

Die eigentliche Darstellung/Bedienung der Medienkarte bleibt vollständig im Tessera-Kern. Keine HA-Companion-Änderung; YAML-only Player bleiben für Browse/Play unterstützt, liefern dem Frontend aber keine Entity-Zustandsbindung und erhalten daher keine Playerknöpfe.

## Position der Bedienelemente ab 0.1.8

Back, Medienansicht und Play/Pause teilen bei großen Kacheln eine obere Navigationszeile mit gleichem Durchmesser und y-Wert. Der Wurzel-Header endet vor den Playerknöpfen; seine Langtextkürzung bleibt aktiv. Cover und Reflexion beginnen unter dieser Zeile. Die Fußzeile wird wieder ausschließlich von Titel bzw. Meldung belegt, beide horizontal über die volle Inhaltsbreite zentriert. In kleinen Kacheln bleiben die Playerknöpfe ausgeblendet.

`Normale Medienkachel fehlt` benennt die Voraussetzung für den nativen Opener deutlicher. Die Rückmeldung bedeutet nicht, dass der Inspector-Player unbekannt wäre; die normale Player-Kachel im Layout fehlt. Ein zusätzlicher Kern-Playerzustand wird weiterhin nicht angelegt und kein laufendes Layout automatisch umgeschrieben.

## Coverfläche ab 0.1.9

Die bisherige Breitenbegrenzung von zwei Dritteln nach seitlichen Abständen wird auf drei Viertel erhöht. Dazu sinkt die Bedingung außerhalb der unveränderten Referenz-Schleife von `side >= w / 4` auf `side >= max(1, w / 6)`; damit bleiben auch bei größerem Mittelcover innere Nachbarn sichtbar. Keine Änderung an der Referenz unter `examples/new_music/`.

Die Kachel vergleicht die mögliche Covergröße mit und ohne die feste Tessera-Spiegelung (30% Zusatzhöhe). Eine Spiegelung bleibt nur auf nicht kompakten Kacheln erhalten, wenn die Coverkante dabei mindestens 90% der ohne Spiegelung möglichen Kante erreicht. Andernfalls wird die frei werdende Höhe dem Cover gegeben; dessen Gruppe steht mittig zwischen Navigations- und Titelzeile. Die gesamte tatsächliche Motivhöhe bleibt oberhalb des Titels, beide seitlichen Motive bleiben in der Kachel. Mehr dargestellte Pixel erhöhen den von Tessera verwalteten Atlasbedarf, nicht die Bibliotheks-/Transportgröße oder die Zahl der Bildplätze. Kein zusätzlicher Bildweg, keine Tessera-Kernänderung, keine Änderung am HA-Companion.

## Lokales HomePod-mini-Piktogramm ab 0.1.11

Die Playeransicht verwendet statt des Ellipsis-Glyphs eine aus dem bereitgestellten SVG erzeugte, konstante 32 × 32 A8-Maske (1024 Pixelbytes). `homepod_mini_icon.h` enthält die Bilddaten und den LVGL-9-Deskriptor. Das nicht anklickbare Image-Objekt liegt im vorhandenen runden Key; Touch bleibt ausschließlich bei `Tile::on_tap`. Es wird auf 28 Referenzpixel skaliert und per `theme::INK` eingefärbt; `on_theme` aktualisiert die Bildfarbe. Die Darstellung belegt keinen Cover-/Atlasplatz, öffnet keine Verbindung und benötigt keine eigene Schrift oder SVG-Laufzeitbibliothek. Bei `LV_USE_IMAGE=0` bleibt derselbe Key als Lautsprecherglyph erhalten. Der native Medien-Opener und alle Wiedergabeaktionen bleiben unverändert.

Quelle-SVG, Lizenz, erzeugter Header und optionales AppKit-Regenerationswerkzeug sind eingecheckt. Swift wird nicht für Firmwarebuilds benötigt. Der deklarierte Flashbedarf steigt konservativ von 16 auf 18 KiB; dies ist weiterhin eine Schätzung, keine vollständige Firmwaremessung.

## Überlagerte Kopfzeile und Spiegelung ab 0.1.12

Die obere Grenze der Coverfläche wird bei nicht kompakten Kacheln um bis zu 40 Referenzpixel angehoben, begrenzt durch den Innenrand. Die Höhenberechnung nutzt wieder die feste Tessera-Spiegelung (30%) und begrenzt die vollständige Motivhöhe oberhalb der Titelzeile; die auslaufende Reflexion darf wie in New music unter der Fußzeile liegen. Die adaptive Abschaltung aus 0.1.9 entfällt außerhalb kompakter Kacheln. Die Gruppe bleibt innerhalb ihrer verfügbaren Fläche zentriert und nutzt weiterhin die erhöhte Breitenobergrenze.

Hinter dem Header liegt ein nicht interaktiver `ui::block` in `theme::KEY`, im hellen Design hellgrau, im dunklen Design dunkelgrau. Textbreite aus `ui::text_width`, horizontale/vertikale Innenabstände und eine Breitenbegrenzung vor den Playerknöpfen bestimmen seine Größe. Die Fläche wird nach den Bildern erzeugt und der zuvor erzeugte Header darüber angehoben. Knöpfe werden anschließend erzeugt und liegen ebenfalls über den Bildern. Header und Fläche werden gemeinsam beim abgeschlossenen Browse-/Atlaswechsel umgeschaltet. Auf der Folgenebene und bei leerem Header bleibt die Fläche verborgen. `on_theme` aktualisiert ihre Farbe; alle Touchereignisse laufen weiterhin über `Tile::on_tap` mit Vorrang für die runden Knöpfe und ohne Navigation beim Antippen des Headers.

## A8-Codegenerierung ab 0.1.13

ESPHome 2026.10.2 verwendet LVGL 9.5.0 und generiert deaktivierte, nicht angeforderte `LV_DRAW_SW_SUPPORT_*`-Formate in `lv_conf.h`. Das hier in C++ erzeugte lokale A8-Symbol gehört nicht zu den YAML-`image`-IDs und wurde deshalb nicht als A8-Bild erkannt. LVGLs `lv_draw_sw_transform` enthält den A8-Fall nur bei `LV_DRAW_SW_SUPPORT_A8=1`; fehlt er, wird der skalierte Zwischenpuffer nicht mit den Maskenpixeln beschrieben. Das erklärt die fehlerhafte Darstellung, obwohl Maske und Deskriptor in den bisherigen Tests korrekt waren.

`to_code` fordert A8 nun explizit über `esphome.components.lvgl.defines.add_define` an. `coroutine_with_priority(1.0)` registriert dies vor der standardpriorisierten LVGL-Codegenerierung. Keine Änderung an der Quellgrafik, kein eigenes Decoderformat, keine Änderung an Tessera-Kerndateien oder der HA-Installation. Quellen: [ESPHome-Codegenerierung](https://github.com/esphome/esphome/blob/2026.10.2/esphome/components/lvgl/__init__.py), [LVGL-A8-Transformation](https://github.com/lvgl/lvgl/blob/v9.5.0/src/draw/sw/lv_draw_sw_transform.c).

## Lokale Coverdateien und Cacheidentität ab Companion 0.1.8

Die vorherige lokale Coveradresse enthielt nur die YAML-Revision und den aufgelösten Pfad. Ein reiner Bilddateitausch änderte weder Revision noch URL. Weil Tessera separat cached, musste weder ein Display- noch ein HA-Neustart einen neuen Download auslösen.

`local_cover_source` löst den Pfad innerhalb `cover_root` auf und bildet SHA-256 aus den tatsächlichen Dateibytes. Die lokale URL enthält im weiterhin 20-stelligen Token die Revision, den Pfad und diesen Fingerabdruck (`local-image-v3`). Der Backend-Browse führt das im HA-Executor aus; gelesen wird in 64-KiB-Blöcken bis höchstens 2 MiB. Es wird kein voller Bildinhalt im Backendregistrierungscache oder im ESP32-Datenmodell gehalten. Auch Austausch bei gleichem Namen, gleicher Größe und kopierten Zeitstempeln wird erkannt; unveränderte Bytes verursachen keine neue URL. Die vorherigen Remote-/MA-Coveridentitäten, 512er-LRU-Registrierung, Authentifizierung und kurze URL-Länge bleiben gleich.

Die vorhandene periodische Browseabfrage liefert normalerweise innerhalb etwa 30 Sekunden die neue Adresse. Eine neue Firmware ist für diesen Companionfix nicht nötig; nach einmaliger Companioninstallation und HA-Neustart benötigen spätere JPG-Wechsel keinen Neustart. Die alte URL wird nicht aktiv aus fremden Tessera-Caches gelöscht; stattdessen wird sie bei geänderten Bytes korrekt durch eine neue Adresse ersetzt.

## AlbumSelection ab Companion 0.1.9

Der strikte Parser akzeptiert genau eine Wiedergabeform: bestehende `items` oder `album_uri` mit genau einem Selektor (`tracks` / inklusivem `track_range`) und optionaler `disc`. `AlbumSelection` hält nur Album-URI, bis zu 256 Nummern und Disc; `Episode.items` bleibt für bestehende Bibliotheken erhalten. `Episode.first_uri` liefert für automatische Bilder entweder die erste explizite URI oder die Album-URI. Keine neue Datei/Abhängigkeit im Companion-Paket.

`resolve_album_selection` verwendet dieselben kompatiblen `contextual`-Aufrufe wie bisher: exakte Album-URI nachschlagen, `music.get_album_tracks` abfragen, Disc-/Trackpositionen validieren und eine vollständige Auswahl erstellen. Ganze Alben verwenden ebenfalls die gemeinsame Positionsprüfung und bleiben nach Disc/Track sortiert. Nummernlisten behalten ihre YAML-Reihenfolge. Nur ausgewählte Tracks werden auf Verfügbarkeit geprüft und genau einmal in die Queue gegeben. Fehlende Nummern, Disc, Track-URI oder Verfügbarkeit werden vor `get_active_queue` bzw. Änderungen an Repeat/Autoplay abgefangen. Die bisherigen per-Player-Locks und die Schema-65/101-Wiedergabewege bleiben erhalten.

Automatische Cover einer Kategorie mit einer solchen ersten Folge verwenden deren Album-URI. Format der Browse-/Play-Nachrichten und Firmware bleiben unverändert. Der Companion wird auf 0.1.9 aktualisiert; neue Bibliotheksfelder können nach einmaliger Installation/HA-Neustart danach wieder ohne weitere Neustarts geändert werden.
