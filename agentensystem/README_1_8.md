# ALL-LIFE INTELLIGENCE 1.8 – kontrollierter Entwicklungszyklus

**Diese Version wurde vom Assistenten lokal entwickelt und ausgeführt.** Der Nutzer muss hierfür keine Dateien herunterladen, Programme starten oder Prüfergebnisse hochladen.

## Was tatsächlich automatisch geschieht

- Startet die lokalen Python-Softwaretests in einem gesonderten Prozess ohne API-Schlüssel im Environment.
- Kontrolliert die 24 früheren KI-Kontexttestfälle auf falsche/fehlende IDs und ungültige Klassifikationen.
- Vergleicht die ursprünglichen Modellbewertungen und internen Soll-Labels mit einer in v1.7 festgehaltenen Referenz. Die Referenz besitzt einen SHA-256-Digest, der zusätzlich im Prüfcode fixiert ist.
- Trennt 16 Übereinstimmungen mit **internen** Vorgaben, 3 Abweichungen und 5 *technisch fehlgeschlagene* KI-Fälle. Bewusste inhaltliche Enthaltungen werden separat ausgewiesen.
- Führt eine Prioritäten-/Arbeitsliste in `reports/OFFENE_FRAGEN_1_8.csv` und erzeugt einen HTML-Bericht sowie ein maschinenlesbares JSON-Protokoll.
- Verzeichnet die SHA-256-Fingerprints zentraler Python-Dateien. So sind Änderungsspuren erkennbar.

## Grenzen – ausdrücklich wichtig

- Der Vergleich mit dem eingefrorenen Referenzwert ist ein **Regressionsschutz**, kein Beweis für die Richtigkeit der alten KI-Ergebnisse. Er ist **keine kryptografische Signatur** und kein unabhängiger Audit.
- Die Bewertungen und Soll-Kategorien der 24 Fälle stammen aus intern erstellten Beispielen. **0 unabhängige Fachlabels, 0 automatisch verifizierte wissenschaftliche Quellen**.
- Bestandenes technisches Gate bedeutet **nur**: Lokale Softwaretests und Referenzintegrität sind bestanden. Veröffentlichung und produktive Freigaben bleiben ausdrücklich gesperrt.
- Es gibt **keine** weiteren OpenAI-API-Aufrufe, keine erneute Bearbeitung der fünf technischen Fehler, keine Modelländerung und keine automatische Übernahme neuer Regeln.
- Ein wahrhaft selbstständig laufender Agent benötigt einen dauerhaft ausgeführten Dienst und eine Infrastruktur, die hier noch nicht eingerichtet ist.
- Die GitHub-Integration kann das bestehende Repository lesen, wurde für Schreibzugriffe jedoch mit `403 Resource not accessible by integration` abgewiesen. Die öffentliche GitHub-Website wurde nicht geändert.

## Ausführen (für Entwicklungsumgebung, nicht als Nutzeraufgabe)

```
python dev_cycle_v18.py
```

Ausgaben: `reports/ENTWICKLUNGSZYKLUS_1_8.html`, `.json` und `reports/OFFENE_FRAGEN_1_8.csv`.

## Nächste Forschungsaufgabe

Ein **neuer, wirklich vorher ungesehener und unabhängig beurteilter** Datensatz soll erstellt werden. Die getrennten Beurteilungen und Originalquellen müssen vor der methodischen Freigabe dokumentiert sein. Neue Klassifikationsregeln sollen mit diesem Satz verglichen werden, ohne ihn für die Regelerstellung zu verwenden.
