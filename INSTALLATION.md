# Installation auf einem zweiten Mac

Diese Installation ist für einen **lokalen, datenschutzorientierten Betrieb** gedacht.  
Die Aufsätze bleiben lokal, `LM Studio` läuft auf `localhost`, und `LanguageTool` wird im Projekt mitgeliefert.

## Zielbild

Nach der Einrichtung laufen lokal:

- `LM Studio` auf `http://127.0.0.1:1234`
- `LanguageTool` auf `http://127.0.0.1:8081`
- der `Korrekturroboter` auf einem freien lokalen Port

## Was im Repo schon enthalten ist

Bereits im Repository enthalten:

- der komplette `LanguageTool`-Server unter `vendor/languagetool/LanguageTool/`
- die App-Starter
- die Weboberfläche
- die Korrekturlogik

Nicht im Repository enthalten:

- eine lokale Java-Laufzeit
- ein lokales Sprachmodell in `LM Studio`

## Voraussetzungen

Du brauchst auf dem Ziel-Mac:

- `LM Studio`
- ein geladenes lokales Modell in `LM Studio`
- eine `conda`-Installation

Geeignet sind zum Beispiel:

- `Anaconda`
- `Miniforge`

Wichtig: Für die automatische Java-Nachinstallation nutzt der Starter `conda`.  
Wenn `conda` fehlt, kann `LanguageTool` nicht automatisch gestartet werden.

## Empfohlene Einrichtung

### 1. Repository laden

```bash
git clone git@github.com:PatrickFischerKSA/korrekturroboter.git
cd korrekturroboter
```

### 2. LM Studio vorbereiten

In `LM Studio`:

1. Ein lokales Modell laden
2. `Local Server` aktivieren
3. Port `1234` verwenden
4. `Require Authentication` ausgeschaltet lassen
5. `Serve on Local Network` ausgeschaltet lassen

### 3. Korrekturroboter starten

Im Finder:

- `Korrekturroboter.app` doppelklicken

oder im Terminal:

```bash
cd "/Pfad/zum/korrekturroboter"
open Korrekturroboter.app
```

## Was beim ersten Start automatisch passiert

Wenn noch keine lokale Java-Laufzeit vorhanden ist:

1. der Starter sucht nach `conda`
2. er installiert `openjdk=21` lokal in:
   - `~/.korrekturroboter-runtime/openjdk-21`
3. danach startet er `LanguageTool` lokal auf Port `8081`
4. anschließend startet er den `Korrekturroboter`

Du musst dafür normalerweise nichts manuell nachinstallieren.

## Manuelles Starten von LanguageTool

Falls du den Sprachdienst separat prüfen willst:

- [start_languagetool.command](/Users/patrickfischer/Documents/New%20project/korrekturroboter/start_languagetool.command)

Danach kannst du im Browser prüfen:

- `http://127.0.0.1:8081/v2/check?language=de-CH&text=Das+ist+ein+Tesst`

Wenn JSON erscheint, läuft `LanguageTool`.

## Wichtige Logdateien

Wenn etwas nicht startet, sind diese Dateien entscheidend:

- [.korrekturroboter.log](/Users/patrickfischer/Documents/New%20project/korrekturroboter/.korrekturroboter.log)
- [.languagetool.log](/Users/patrickfischer/Documents/New%20project/korrekturroboter/.languagetool.log)
- [.runtime-bootstrap.log](/Users/patrickfischer/Documents/New%20project/korrekturroboter/.runtime-bootstrap.log)

## Typische Probleme

### `LM Studio` rot

Dann läuft meist der lokale Server in `LM Studio` nicht oder kein Modell ist geladen.

### `LanguageTool Lokal` rot

Dann ist meist eines von drei Dingen der Fall:

- `conda` fehlt
- die lokale Java-Installation konnte nicht angelegt werden
- `LanguageTool` konnte nicht auf `localhost:8081` starten

### Kriterium 4 bleibt zu schwach

Dann läuft die App ohne `LanguageTool` nur mit Fallbacks.  
In diesem Fall zuerst die Dienstekarten in der Oberfläche prüfen.
