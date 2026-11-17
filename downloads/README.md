# Home-Assistant-Companion herunterladen

[**Kidsplayer HA-Companion 0.1.7 als ZIP herunterladen**](https://github.com/met-theokoch-schule/tessera-plugins/raw/refs/heads/main/downloads/kidsplayer-ha-companion-0.1.7.zip)

Dies ist das fertige Paket für die **Home-Assistant-Custom-Integration**. Es ist ein anderes Paket als das Tessera-Displayplugin. Keine Firmware und keine private Konfiguration enthalten.

1. ZIP auf den Home-Assistant-Rechner nach `/config/kidsplayer-ha-companion-0.1.7.zip` kopieren.
2. Im HA-Terminal ausführen:

   ```sh
   unzip -o /config/kidsplayer-ha-companion-0.1.7.zip -d /config
   ls -l /config/custom_components/kidsplayer/
   ```

3. In diesem Ordner müssen `__init__.py`, **`manifest.json`**, `library.py`, `playback.py`, `compat.py`, `images.py` und die Lizenz liegen.
4. Home Assistant neu starten. Keine Änderung an YAML oder Display-Firmware erforderlich, wenn Kidsplayer bereits konfiguriert war.

Die ZIP beginnt direkt mit `custom_components/kidsplayer/`, ohne zusätzliche Repositoryebene. Nicht in `/config/tessera-plugins/kidsplayer/` entpacken.

Wer stattdessen GitHub's **Code → Download ZIP** verwendet, erhält das ganze Quellrepository. Darin liegt der Companion erst unter `tessera-plugins-main/kidsplayer/backend/custom_components/kidsplayer/`. Der äußere Ordner `kidsplayer/` enthält das Tessera-Plugin und ist nicht selbst die HA-Custom-Integration.

Erzeugung aus diesem Checkout: `python3 tools/package-companion.py downloads/kidsplayer-ha-companion-0.1.7.zip`. Das Skript prüft alle erforderlichen Dateien einschließlich `manifest.json` und die ZIP-Integrität.
