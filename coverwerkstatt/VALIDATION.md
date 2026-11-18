# Prüfung der Coverwerkstatt

Erfolgreich: **16 Node.js-Tests** ohne externe Abhängigkeiten.

- Größtmögliches Quadrat für Hochformat, Querformat und quadratische Bilder; gültige ganzzahlige Quellkoordinaten auch bei ungeraden Größen und weit über den Bildrand gezogenen Positionen.
- Seitenverhältnis der Anzeige, zulässige Bildabmessungen, Dateinamen und Tastatursteuerung inklusive größerer Schritte und Ränder.
- Ausführung des tatsächlichen HTML-Seitencontrollers mit kleinen DOM-/Bild-/Canvas-Doubles: Bild laden, Range verschieben, Pointerbewegung auf eine Achse beschränken, zentrieren und JPG-Export ausschließlich des gewählten Ausschnitts in nativer Quadratgröße.
- Lesefehler behalten das vorherige nutzbare Bild. Langsam abgeschlossene ältere Ladevorgänge überschreiben keine neueren Bilder. Eine ungültige zweite Datei lässt die Steuerung nicht dauerhaft im Ladezustand.
- Keine externen Skripte, Styles, Fonts, Bild-URLs oder Upload-/Fetch-Aufrufe in der HTML-Datei. Quelle und fertige Downloadkopie sind identisch.

Die Tests prüfen keine realen Browserpixel. Zwei Versuche mit dem vorhandenen Chrome im Headless-Modus scheiterten beim Browserstart im eingeschränkten lokalen Ausführungskontext. Es wurde kein Browser installiert und kein bestehendes Browserprofil verwendet oder verändert. Eine manuelle Prüfung in Safari/Chrome und auf Touchgeräten steht aus, insbesondere tatsächliches Bilddecoding, Dateidownload und die responsive Darstellung. Die Seite verwendet die üblichen Browser-APIs Image.decode, Canvas.toBlob, Pointer Events und ResizeObserver.

Die private Sites-Registrierung wurde angelegt. Die Quellsynchronisierung scheiterte an `Could not resolve host: git.chatgpt-team.site`; es gibt deshalb noch keine veröffentlichte Site-URL. Die vollständige lokale Seite und das Installieren ohne Webserver sind davon unabhängig. Site-Zugangsdaten wurden nicht in Dateien gespeichert. Die lokalen, unbenutzten Sites-Git-Metadaten ohne Commit liegen separat unter `/private/tmp/kidsplayer-coverwerkstatt-site.git`; der eigentliche Quellstand wird im bestehenden Projekt-Repository verwaltet.

Displayplugin, Companion, Bibliothek und Home-Assistant-/Tessera-Konfiguration wurden für dieses Werkzeug nicht verändert.
