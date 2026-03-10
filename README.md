# Korrekturroboter

Lokaler Korrekturroboter für deutschsprachige Maturaufsatztexte. Ein hochgeladenes `.docx` wird über LM Studio analysiert und als neues Word-Dokument mit roten Fehlermarkierungen, textbezogenen Kommentaren und ausführlichem Gesamtfeedback zurückgegeben.

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

Zusätzlich startet der Server nur noch, wenn lokales LM Studio erreichbar ist und mindestens ein Modell geladen wurde.

## Voraussetzungen

- Python 3.10 oder neuer
- Ein in LM Studio geladenes Sprachmodell
- Aktivierter lokaler Server in LM Studio, standardmäßig `http://127.0.0.1:1234/v1`

## Start

```bash
cd "/Users/patrickfischer/Documents/New project/korrekturroboter"
python3 -m pip install -r requirements.txt
python3 server.py
```

Danach im Browser:

[http://127.0.0.1:8090](http://127.0.0.1:8090)

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
