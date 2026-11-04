# ALL-LIFE INTELLIGENCE 1.6.2 – Diagnose statt teurer Wiederholung

Die Live-Nachprüfung aus 1.6.1 scheiterte erneut und meldete `ApiProblem`, ohne einen HTTP-Status zu nennen. **Die exakte Ursache lässt sich aus dem HTML-Bericht nicht rekonstruieren.**

## Neu

- `START_DIAGNOSE_1_6_2_OFFLINE.bat`: überprüft die vorhandenen Daten **kostenlos und offline**, ändert keine KI-Bewertungen und zeigt die Zahl offener Fälle.
- `START_EINEN_FALL_ECHT_OPTIONAL.bat`: bittet um eine neue ausdrückliche Bestätigung und den Schlüssel und sendet **genau einen** der noch offenen Fälle an die API. Keine automatischen Wiederholungen. Dies ist **optional und kann Kosten verursachen**, auch wenn die Antwort fehlschlägt.
- Die Offline-Diagnose kann den Grund des früheren `ApiProblem` **nicht nachträglich aufklären**. Wenn die freiwillige Einzelanfrage erneut scheitert, zeigt der neue Report den HTTP-Status (z. B. 401, 429) oder die Art des Antwortproblems an, aber keine API-Rohantwort und keinen Schlüssel.
- Erfolgreich geprüfte Fälle werden fortlaufend in `reports/KONTEXTPRUEFUNG_1_6_2_FAELLE.csv` aufbewahrt. Jeder weitere Fall verlangt eine **eigene** Bestätigung. Die bisherigen 18 Ergebnisse bleiben erhalten. Version 1.6.1 bleibt im Archiv.
- `reports/MENSCHLICHE_BEWERTUNG_1_6.csv` und weitere manuelle Freigabedateien bleiben unangetastet.

## Start

1. ZIP vollständig in einen neuen Ordner entpacken.
2. `START_TESTS.bat` ausführen (offline).
3. `START_DIAGNOSE_1_6_2_OFFLINE.bat` starten (offline). Der Bericht liegt danach in `reports/KONTEXTPRUEFUNG_1_6_2.html`.
4. **Nicht erforderlich:** Falls du bewusst eine einzelne kostenpflichtige Modellanfrage zur Diagnose erlauben möchtest, `START_EINEN_FALL_ECHT_OPTIONAL.bat` starten und die Frage mit `ja` bestätigen. Danach neuen Bericht hochladen. **Bei erneutem Fehler nicht mehrfach starten**; der Status muss zuerst ausgewertet werden.

## Grenzen

Dieses Paket führt weder Modelltraining noch selbstständige Codeänderungen aus. Es validiert keine Originalquellen und verwendet intern erstellte, nicht unabhängig bestätigte Szenarien. Ein korrektes Label ist keine wissenschaftliche Verifikation. Der Ablauf legt keine API-Anfragen ohne ausdrückliche Bestätigung aus.
