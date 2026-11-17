# Tessera Kidsplayer 0.1.9

Aktueller HA-Companion: **0.1.7** (Coverdownload-Korrektur, kein Firmwareupdate erforderlich). [**Fertiges HA-Installationsarchiv herunterladen**](https://github.com/met-theokoch-schule/tessera-plugins/raw/refs/heads/main/downloads/kidsplayer-ha-companion-0.1.7.zip).

Kindgerechte Hörspielbibliothek für Tessera und Music Assistant: Reihen und Folgen als verschachtelte Cover-Flows innerhalb einer Kachel. Explizite Tracklisten bleiben geordnet; jede Kachel hat ihre eigene Bibliotheks-ID und ihren eigenen Player.

**Entwicklungsstand:** Implementierung und automatisierte Mocktests vorhanden. Eine echte Home-Assistant-Installation, ESP32-Firmware und Audiowiedergabe wurden in dieser Entwicklungsumgebung nicht ausgeführt. Vor dem Einsatz bitte den Abnahmeplan durchführen.

- [Installation, Konfiguration und Wiedergabetest](kidsplayer/README.md)
- [Vollständige Beispielbibliothek](kidsplayer/examples/libraries.yaml) (absichtlich ungültige Platzhalter ersetzen)
- [API-Untersuchung und Architektur](docs/ARCHITECTURE.md)
- [Prüfergebnisse und Grenzen](docs/VALIDATION.md)

`examples/new_music/` enthält die vollständige, unveränderte Referenz von Max Gramser am Commit `ae25258d1a8d96ae9d6a521ee313179532a7ea08`. Herkunft und Lizenz stehen in [NOTICE](NOTICE). Kidsplayer hat die eigene ID `kidsplayer`.

Die aktuelle Plugin-API erlaubt weder große YAML-Textfelder noch Python-Backendmodule in Tessera. Deshalb gehört die zusätzliche Home-Assistant-Integration unter `kidsplayer/backend/custom_components/kidsplayer/` zur Installation. Bibliotheksänderungen benötigen danach keinen Firmwarebau.

Tests: `python3 -m pip install -r requirements-dev.txt`, dann `python3 -m unittest discover -s kidsplayer/tests -v`.
