# ALL-LIFE INTELLIGENCE 1.9 – Forschungsrat

Diese Version wurde hier direkt entwickelt und lokal getestet; **kein Download-/Upload-Zyklus durch den Nutzer notwendig**.

## Was neu ist

- `research_board_v19.py` prüft die **eingefrorenen 24** Kontexttestfälle auf Integrität und übernimmt daraus eine getrennte Perspektive von **A1 (KI-Sicherheit)**, **A2 (Ethik/Bewusstsein)**, **A6 (kritische Gegenprüfung)** sowie einem **Koordinator**.
- Die Rollen sind im kostenlosen Offline-Modus **separate, deterministische Prüfverfahren**, **keine vier unabhängigen Sprachmodell-Aufrufe**. Sie können keine neuen wissenschaftlichen Erkenntnisse oder semantische Quellenbelege erzeugen.
- Drei überprüfbare Vorhaben M19-01 bis M19-03 mit Prioritäten und messbaren Abnahmekriterien sind als **Vorschläge** erzeugt.
- Nach jedem Lauf entstehen: `reports/FORSCHUNGSRAT_1_9.html`, `.json` sowie `_AUFGABEN.csv`.
- Die Programmbibliothek der bisherigen Versionen bleibt erhalten. Der neue Forschungsrat verändert weder Prüflabels noch Modelle, Zugangsschlüssel, GitHub-Dateien oder Freigaben.

## Qualitätsnachweis

`python research_board_v19.py` führt die komplette `unittest`-Suite ohne API-Schlüssel aus und prüft die eingefrorene SHA-256-Referenz aus v1.7. **Die Referenz belegt Unverändertheit, nicht Wahrheit.** Die Zahl bestandener Tests sagt nichts über wissenschaftliche Genauigkeit aus.

## Forschungsplanung

1. **M19-01, höchste Priorität:** neue vorher unbekannte Fälle, zweimal unabhängig menschlich bewertet, Konfliktklärung dokumentiert.
2. **M19-02:** Quellenbehauptungen anhand nachprüfbarer Originalstellen statt blossen IDs beurteilen.
3. **M19-03:** Behauptungsgehalt, Urheberschaft, Zitat und Kritik strukturiert unterscheiden; falsche Warnungen und Enthaltungen messen.

Alle Fallbewertungen und Quellenaussagen sind momentan **nicht unabhängig fachlich freigegeben**. Die fünf zuletzt technisch fehlgeschlagenen KI-Fälle werden nicht kostenpflichtig neu angefragt. Kein Autopilot für Web-, API-, GitHub-, Zahl- oder Veröffentlichungsaktionen.

## Grenzen der Eigenständigkeit

Die Rollenberatung ist eine **lokale analytische Automatisierung**. Die echte, in `agent.py` enthaltene LLM-Agentenarchitektur benötigt weiterhin einen gesonderten API-Zugriff. Ohne eine durch den Nutzer eingerichtete dauerhafte Laufzeit arbeitet das Programm nicht zwischen Chat-Sitzungen autonom weiter.
