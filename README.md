# Korrekturroboter

Dieses Repo ist die **Codebasis** der Plattform, nicht die laufende Plattform selbst.

## Wichtig

GitHub kann **keinen lokalen Startbutton ausführen**.  
Die GitHub-Seite zeigt nur Dateien und das `README.md`.

Die Anwendung startest du **lokal auf deinem Mac** per Doppelklick auf:

- `Korrekturroboter.app`

Falls du im Finder arbeitest, öffne einfach den Ordner `korrekturroboter` und doppelklicke auf `Korrekturroboter.app`.

Alternativ:

- `START_HIER.command`

## Direkt starten

```bash
cd "/Users/patrickfischer/Documents/New project/korrekturroboter"
open Korrekturroboter.app
```

Danach öffnet sich die Plattform automatisch in deinem Browser auf einem freien lokalen Port.

Falls der Start fehlschlägt, findest du die genaue Ursache in:

- `.korrekturroboter.log`

Dort stehen jetzt direkt zur Verfügung:

- eine lokale Startseite mit Button zur Korrekturplattform
- ein großer Button zum Laden eines eigenen `.docx`
- ein Demo-Modus mit vorbereitetem Beispieldokument

Alternativ manuell:

```bash
python3 server.py
```

Die Anwendung nimmt ein `.docx` entgegen, analysiert es lokal über LM Studio und erzeugt ein neues Word-Dokument mit roten Fehlermarkierungen, textbezogenen Kommentaren und ausführlichem Gesamtfeedback.

## Was das Repo leistet

- Upload eines `.docx`-Aufsatzes über die Weboberfläche
- zuschaltbare Eingabe der originalen Aufgabenstellung per Button
- manuelle Angabe von Thema und Textform
- pflichtige Angabe von Leitfrage oder These des Aufsatzes
- formabhängige Hilfetexte und Beispiel-Aufgabenstellungen in der UI
- Lokale Anbindung an LM Studio über den OpenAI-kompatiblen Endpoint
- automatische oder manuelle Formwahl zwischen:
  - Essay
  - Redemanuskript
  - linearer Erörterung
  - dialektischer Erörterung
- Ausführliche, lernförderliche Kommentare für:
  - Kriterium 1: Inhalt
  - Kriterium 2: Aufbau
  - Kriterium 3: Ausdruck
- Textstellenkommentare direkt im erzeugten Word-Dokument
- Rote Fehlermarkierungen für Grammatik- und Rechtschreibfehler
- Teilnote für Kriterium 4 auf Basis des bereits verwendeten Excel-Schlüssels

## Datensicherheit

Die Anwendung ist für den lokalen Betrieb mit LM Studio gebaut. Im harten Datenschutzmodus akzeptiert der Server nur lokale LM-Studio-Endpunkte auf `127.0.0.1`, `localhost` oder `::1`. Externe LM-Studio-URLs werden technisch abgewiesen.

Der Server startet lokal auch dann, wenn LM Studio noch nicht bereit ist. Der LM-Studio-Status wird in der Weboberfläche geprüft und dort klar angezeigt.

## GitHub und Vendor

Der Ordner `vendor/` kann mit ins eigene GitHub-Repo aufgenommen werden. Für dieses Projekt ist das vor allem für den lokalen `LanguageTool`-Server sinnvoll.

Bewusst **mit versionieren**:

- `vendor/languagetool/LanguageTool/`

Bewusst **nicht versionieren**:

- `.lt-java/` lokale Java-Laufzeit für genau diesen Mac
- `vendor/languagetool/LanguageTool-latest-snapshot.zip` reines Download-Artefakt
- `vendor/languagetool/LanguageTool-6.8-SNAPSHOT/` doppelt entpackter Zwischenstand
- Log- und PID-Dateien

Wichtig: Der übergeordnete Ordner `New project` hängt aktuell an einem anderen GitHub-Repo. Für `korrekturroboter` ist deshalb ein **eigenes Repository** der saubere Weg.

## Voraussetzungen

- Python 3.10 oder neuer
- Ein in LM Studio geladenes Sprachmodell
- Aktivierter lokaler Server in LM Studio, standardmäßig `http://127.0.0.1:1234/v1`

## Konfiguration

Optionale Umgebungsvariablen:

- `LM_STUDIO_BASE_URL` nur lokal, z. B. `http://127.0.0.1:1234/v1`
- `LM_STUDIO_MODEL`
- `KORREKTURROBOTER_HOST`
- `KORREKTURROBOTER_PORT`

Beispiel:

```bash
export LM_STUDIO_BASE_URL="http://127.0.0.1:1234/v1"
export KORREKTURROBOTER_PORT="8090"
python3 server.py
```

Wichtig: Eine externe URL wird im Datenschutzmodus nicht akzeptiert.

## Fachliche Grundlage

Die Bewertungslogik basiert auf diesen Materialien:

- `Argumentationslehre.pdf`
- `Rhetorische_Formen_Theorieblatt.pdf`
- `Guetekriterien für einen Essay.docx`
- `Guetekriterien_Redemanuskript_Maturaufsatz.docx`
- `Lineare und dialektische Erörterung.pdf`
- der bereits im Repo `aufsatzkorrekturtrainer` umgesetzten Excel-Logik für sprachliche Korrektheit

Die Kriterien für Essay, Rede, lineare Erörterung, dialektische Erörterung, Argumentationslehre und rhetorische Formen sind im Code als Referenzraster hinterlegt, damit die Anwendung lokal und reproduzierbar arbeiten kann.

## Wichtige technische Grenze

Das generierte Ausgabe-DOCX übernimmt den Fließtext aus dem Ausgangsdokument, aber nicht dessen komplettes Layout oder seine ursprünglichen Word-Formatierungen. Der Schwerpunkt liegt auf didaktisch sauberer Korrektur, Kommentierung und sicherem lokalem Betrieb.
