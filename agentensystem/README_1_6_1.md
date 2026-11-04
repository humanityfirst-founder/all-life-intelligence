# ALL-LIFE INTELLIGENCE – Technische Korrektur 1.6.1

Dies ist eine **Fehlerbehebungs- und Nachprüfversion**, keine wissenschaftliche Validierung und kein neues Modelltraining. Ausgangspunkt ist der vom Nutzer hochgeladene Live-Bericht von 1.6 mit 24 internen Testfällen: 15 Übereinstimmungen, 3 abweichende Modellbewertungen und 6 technisch nicht ausgewertete Fälle (Batch 4: ValueError). Der genaue Auslöser des ursprünglichen Fehlers ist ohne Rohantwort nicht bekannt.

## Was korrigiert wurde

- Die sechs Fälle mit API-Fehler werden **nicht mehr als inhaltliche Modellfehler gezählt**, sondern als **NICHT_GEPRUEFT**. Unklarheit als echte Modellbewertung bleibt separat behandelbar.
- Die 18 bereits vorhandenen semantischen Bewertungen sind als strukturierte CSV aus dem Nutzerdokument übernommen. Sie müssen **nicht erneut kostenpflichtig angefordert werden**.
- Die Originalfassung des hochgeladenen Berichts liegt in `reports/ORIGINALBERICHT_1_6.html`. Die Kopie `reports/KONTEXTPRUEFUNG_1_6_FAELLE.csv` bewahrt die ausgeführten KI-Vorschläge.
- Ein neues Skript kann **ausschliesslich die sechs ausgefallenen Fälle 19–24** erneut anfragen. Es gibt maximal **einen API-Aufruf**, keine automatische Wiederholung, und es fordert jedes Mal eine neue ausdrückliche Kostenbestätigung sowie den API-Schlüssel an. Alte Bewertungen und manuelle Freigabedateien werden nicht überschrieben.
- Eine strengere Fehlermeldung kann bei neuen `ValueError`s den **internen Validierungsgrund**, nie aber die Rohantwort oder den Schlüssel nennen. Die ursprüngliche genaue Ursache ist rückwirkend nicht rekonstruierbar.

## Start unter Windows

1. ZIP vollständig entpacken.
2. `START_TESTS.bat` starten (offline und kostenlos).
3. `START_BERICHT_KORRIGIEREN_OFFLINE.bat` starten (offline und kostenlos). Die Datei `reports/KONTEXTPRUEFUNG_1_6_1.html` zeigt 15 richtige, 3 abweichende, 6 noch offene Bewertungen.
4. **Nur wenn ein weiterer kostenpflichtiger Aufruf erwünscht ist:** `START_NUR_BATCH_4_ECHT_OPTIONAL.bat` starten. Bestätigung `ja` und API-Schlüssel eingeben. Die sechs noch offenen Fälle werden ein einziges Mal angefragt; Ergebnis `reports/KONTEXTPRUEFUNG_1_6_1.html`.

Die eingebaute frühere Datei `START_KONTEXTPRUEFUNG_ECHT_OPTIONAL.bat` startet **erneut alle vier Batches** und wird zur Fortsetzung ausdrücklich **nicht** empfohlen.

Die vorgesehenen Kategorien sind **intern festgelegte Testvorgaben**. Eine Übereinstimmung ist kein Nachweis der faktischen Richtigkeit. Drei gemeldete Abweichungen sind nicht notwendigerweise drei wissenschaftlich falsche Antworten; auch die Testvorgaben können diskutabel sein.

Die Programme machen keine Webrecherche, keine Veröffentlichungen und keine Code-Selbständerungen. API-Kosten können bei der optionalen Einzelanfrage entstehen, auch wenn deren Antwort erneut unbrauchbar ist.
