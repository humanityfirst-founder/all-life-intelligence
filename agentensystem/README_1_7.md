# ALL-LIFE INTELLIGENCE 1.7 – weniger manuelle Entwicklungsschritte

Diese Version ergaenzt **keinen neuen KI-Forschungsagenten**, sondern einen lokalen, kostenlosen Entwicklungs- und Qualitaetslauf. Der Bericht wird direkt in der Entwicklungsumgebung erstellt. Ein ZIP-Download, Windows-Start oder erneuter Upload ist fuer die Weiterentwicklung in dieser Chat-Sitzung nicht noetig.

## Aufruf fuer die Entwicklung

`python auto_qa_v17.py`

Das Programm startet die vorhandenen Python-Unittests, kontrolliert die synthetischen Testfall-Ergebnisse und schreibt `reports/AUTOMATISCHE_QUALITAET_1_7.html` sowie eine maschinenlesbare JSON-Datei. Es verwendet keine API-Schluessel, loest keine kostenpflichtigen KI-Aufrufe aus und aendert weder Code noch Modell. Freigaben bleiben menschlich.

**Methodischer Hinweis:** Die 24 QA-Faelle sind synthetisch und nicht unabhaengig begutachtet. Eine Uebereinstimmung mit internen Labels beweist keine wissenschaftliche Gueltigkeit. Die Offline-Tests pruefen Softwareverhalten, nicht Alignment oder die Sicherheit einer Superintelligenz.

## GitHub Status

Eine GitHub-Actions-Automatik ist vorbereitet, konnte jedoch nicht installiert werden: Die GitHub-Integration verweigerte Schreibzugriff (`403 Resource not accessible by integration`). Erst nach ausdruecklich erlaubtem GitHub-Contents-Schreibzugriff und einer kontrollierten Quellcode-Uebernahme kann der CI-Lauf auf GitHub aktiviert werden. Die bisherige oeffentliche Projektwebsite wurde nicht geaendert.
