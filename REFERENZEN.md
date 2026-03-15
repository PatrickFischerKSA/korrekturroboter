# Hinterlegte Referenzen

## Quellen

- `/Users/patrickfischer/Desktop/Argumentationslehre.pdf`
- `/Users/patrickfischer/Desktop/Rhetorische_Formen_Theorieblatt.pdf`
- `/Users/patrickfischer/Desktop/Gütekriterien für einen Essay.docx`
- `/Users/patrickfischer/Desktop/Guetekriterien_Redemanuskript_Maturaufsatz.docx`
- `/Users/patrickfischer/Library/Containers/com.lukilabs.lukiapp/Data/tmp/3accea14e4708f9ef951e3c32116d668/Lineare und dialektische Erörterung.pdf`

## Umsetzung im Repo

### Essay

Die Essay-Kriterien wurden in `review_engine.py` als Leitfragen für Inhalt, Aufbau und Ausdruck hinterlegt. Verwendet werden insbesondere:

- klare Auseinandersetzung mit der Fragestellung
- eigenständige These oder Position
- nachvollziehbare und differenzierte Argumentation
- roter Faden, sinnvolle Übergänge und runder Schluss
- präziser Wortschatz und essayistischer Stil

### Redemanuskript

Die Kriterien für Redemanuskripte wurden ebenfalls in `review_engine.py` kodiert. Schwerpunkte sind:

- klare Botschaft
- adressatenbezogene Dramaturgie
- logischer Aufbau
- überzeugender Schluss oder Appell
- redeartiger, wirkungsorientierter Stil

### Lineare Erörterung

Aus dem PDF wurden für die lineare Erörterung insbesondere diese Punkte übernommen:

- Thema als vorgegebene Frage oder Aussage klar erfassen
- eigene Grundhaltung deutlich formulieren
- Argumente steigernd anordnen: wichtig, wichtiger, am wichtigsten
- jedes Argument mit Beispielen, Zahlen, Fakten, Zitaten oder Erfahrungen stützen
- Schluss mit Gesamturteil und Ausblick

### Dialektische Erörterung

Aus dem PDF wurden für die dialektische Erörterung insbesondere diese Punkte übernommen:

- strittige Ausgangsfrage sauber herausarbeiten
- Pro- und Contra-Argumente klar unterscheiden
- möglicher Aufbau als Blockstruktur oder wechselnde Argumentation
- sichtbarer Wendepunkt zwischen den Positionen
- das schlussnahe, stärkste Argument bestimmt den bleibenden Eindruck
- Schluss mit klarer Stellungnahme, Zusammenfassung oder Ausblick

### Argumentationslehre

Die PDF war technisch nicht verlässlich maschinell extrahierbar. Daher ist ein standardisiertes Raster hinterlegt:

- These
- Begründung
- Beleg
- Einwand
- Entkräftung oder Abwägung
- Schluss

Dieses Raster dient als Gradmesser für die Plausibilität argumentativer Kommentare.

### Rhetorische Formen

Auch hier ist ein didaktisch brauchbares Raster im Code hinterlegt:

- rhetorische Frage
- Anapher
- Antithese
- Parallelismus
- Klimax
- Metapher
- Vergleich
- Wiederholung
- Appell

### Sprachliche Korrektheit

Die Teilnote für Kriterium 4 wird mit denselben Schwellenwerten berechnet, die bereits im Repo `aufsatzkorrekturtrainer` für das Excel-basierte Bewertungsmodell umgesetzt wurden. Gezählt werden ausschließlich Grammatik- und Rechtschreibfehler.
