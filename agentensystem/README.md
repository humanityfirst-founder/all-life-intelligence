# AKTUELL: Version 1.9 – Offline-Forschungsrat

Die neueste Anleitung ist **README_1_9.md**. Die frueheren Versionen sind erhalten. Fuer den letzten Entwicklungsdurchlauf musste der Nutzer keine PC-Schritte ausfuehren.

---

# AKTUELL: Version 1.8 – kontrollierter Entwicklungszyklus

Die neueste Anleitung ist **README_1_8.md**.
**Du musst keine Dateien herunterladen oder Tests manuell starten.** Die vorherigen Dokumente bleiben zur Nachvollziehbarkeit bestehen.

---

# AKTUELL: Version 1.6.2 – sichere Diagnose

Bitte zuerst **START_HIER.txt** und **README_1_6_2.md** lesen.
Die frueheren kostenpflichtigen Mehrfachdurchlaeufe sind in diesem
Diagnosepaket nur als nicht startbare Archivtexte enthalten.

---

# ALL-LIFE INTELLIGENCE – Agentensystem v1.6

**Stand: 28. Oktober 2026 · Windows · Python 3.10+**

## Warum es diese Version gibt

Der Regelvergleich 1.5 erreichte auf den **65 bereits bekannten Fällen 65/65**, auf 24 zusätzlichen synthetischen Texten jedoch nur **10/24** Übereinstimmungen mit den Szenario-Vorgaben. Das deutet auf die Grenzen starrer Wortmuster hin; diese Werte sind **keine wissenschaftlich validierten Genauigkeitswerte**.

Version 1.6 ergänzt deshalb eine **getrennte, experimentelle Kontextprüfschicht** `context_review_v16.py`, die optional das bisher verwendete OpenAI-Modell `gpt-5-mini` einsetzt. Ziel ist, in deutschen Aussagen zwischen Behauptung, Zitat, Kritik, Metadaten und Unklarheit zu unterscheiden und dabei vier spezielle Fehlertypen zu beachten:

- **META** – reine Quellen-ID-Aufzählung ohne Sachbehauptung;
- **PAUSCHALE_ABSENZ** – unbegrenzt behauptete Abwesenheit aller Belege;
- **METHODE** – methodisches Urteil statt direkt in einer Quelle berichtetes Ergebnis;
- **DOMAENENFEHLER** – Übertragung von KI-Bewusstseinsliteratur auf experimentelle Tierleidmessung;
- **KEIN_SPEZIELLER_HINWEIS / UNKLAR** – keine passende Kategorie bzw. Kontext reicht nicht.

Die bestehende `candidate_rules_v15.py` und der ursprüngliche Forschungsablauf bleiben erhalten. **Keine neue Regel wird automatisch produktiv geschaltet.** Die zusätzliche Prüfschicht verifiziert **nicht** den Inhalt der Originalquellen.

## Einfach starten

1. ZIP **vollständig entpacken** (nicht direkt aus der ZIP starten).
2. `START_TESTS.bat` starten: **kostenlos, offline**.
3. `START_KONTEXTPRUEFUNG_OFFLINE.bat` starten: **kostenlos, offline**. Erstellt `reports/KONTEXTPRUEFUNG_1_6.html` mit der bisherigen Regel und dem Vermerk **NICHT_AUSGEFUEHRT** für die KI-Kontextprüfung.
4. Optional und **nur bei ausdrücklichem Wunsch**: `START_KONTEXTPRUEFUNG_ECHT_OPTIONAL.bat` – siehe folgenden Abschnitt.

Der Offline-Modus täuscht **keine** semantische KI-Bewertung vor. Er bereitet die 24 Fälle und den Vergleich vor.

## Optionaler echter Kontextdurchlauf – kostenpflichtig

`START_KONTEXTPRUEFUNG_ECHT_OPTIONAL.bat` zeigt zuerst Zweck und maximale Aufrufzahl und verlangt explizit **ja**. Erst danach wird der API-Schlüssel unsichtbar abgefragt. Ohne Bestätigung gibt es **null API-Aufrufe**.

- Das Skript überträgt **nur die 24 synthetischen Beispielsätze, Fallkennungen und vier knappe Quellenbeschreibungen** an OpenAI.
- Verwendetes Modell: `gpt-5-mini`, höchstens **vier kostenpflichtige API-Aufrufe** zu je sechs Fällen, keine automatischen Wiederholungen, `store: false` in der API-Anfrage.
- API-Schlüssel wird **nicht in einer Datei gespeichert**, nicht an diesen Chat gesendet, nicht in Berichten ausgegeben.
- Es erfolgt **keine Webrecherche**, kein Zugriff auf private Dateien, keine Veröffentlichung, kein Upload zu GitHub.
- Die tatsächlichen API-Gebühren hängen von der Tokenmenge und den aktuellen Tarifen ab; die Software berechnet keinen garantierten Maximalbetrag.
- Wenn ein Aufruf fehlschlägt oder die JSON-Antwort ungültig ist, werden die betroffenen Fälle als **UNKLAR** markiert und es gibt **keinen automatischen Wiederholungsversuch**.

Die Resultate werden ausgegeben als:
- `reports/KONTEXTPRUEFUNG_1_6.html` – gut lesbarer Ergebnisbericht;
- `reports/KONTEXTPRUEFUNG_1_6_FAELLE.csv` – technische KI-Vorschläge und Vergleich mit internen Vorgaben;
- `reports/MENSCHLICHE_BEWERTUNG_1_6.csv` – nach einem erfolgreichen oder teilweisen **Live-Lauf** angelegtes separates Blatt für menschliche Beurteilungen; **wird nicht überschrieben**, wenn es bereits existiert.

Die bisherigen Bewertungen (`Erwarteter Regelhinweis`) und menschlichen Notizen gehen **nicht** in das KI-Modell-Prompt ein, um triviale Label-Lecks zu vermeiden. Die Quellenbeschreibungen stammen aus einem kuratierten Katalog und erlauben keine echte inhaltliche Quellenbestätigung.

## Grenzen und Sicherheit

Die 24 Fälle stammen aus internen synthetischen Tests, ihre erwarteten Kategorien wurden **nicht unabhängig fachlich geprüft**. Auch ein höherer Übereinstimmungswert beweist deshalb **keine Generalisierung, wissenschaftliche Wahrheit oder Autonomie**.

Sämtliche Vorschläge sind vorläufig. Der Prozess trainiert weder das zugrunde liegende Modell noch verändert er eigenständig Code, Sicherheitsregeln, API-Rechte, Dateien ausserhalb des Programmordners oder öffentliche Projektinhalte. Über neue Regeln und Veröffentlichungen entscheiden weiterhin Menschen.

## Vorhandene ältere Funktionen

`START_REGELVERGLEICH_1_5.bat`, `START_VERBESSERUNGSANALYSE.bat`, `START_ROBUSTHEITSTEST.bat`, `START_DEMO.bat` sowie der vorherige Forschungs-/Quellenworkflow bleiben vorhanden. **Für den neuen ersten Schritt werden diese nicht benötigt.** `START_ECHT.bat` ist der separate ältere kostenpflichtige Forschungsworkflow und darf nicht mit dem neuen Kontextprüfer verwechselt werden.

Projekt: https://humanityfirst-founder.github.io/all-life-intelligence/
