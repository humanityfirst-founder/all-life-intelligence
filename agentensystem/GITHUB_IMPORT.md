# Import von ALL-LIFE INTELLIGENCE 1.9

KI-unterstützte Übertragung auf ausdrücklichen Auftrag des Repository-Inhabers,
31. Oktober 2026. Ausgangspunkt ist das separat erhaltene Originalpaket 1.9.
Die lokal vorhandene Weiterentwicklung 1.10 ist nicht Teil dieses Imports.

## Umfang

Alle 14 Anwendungsmodule, 14 Testmodule, Startskripte, Anleitungen,
Quellenkataloge, Evaluationsdaten und mitgelieferten Beispielberichte werden
unverändert übernommen. Die CSV-Dateien unter `reports/` gehören zum
historischen Test- und Forschungsstand; insbesondere die Kontextprüfungen
1.6.1 und 1.6.2 werden von Tests beziehungsweise dem Forschungsrat benötigt.
Die enthaltenen menschlichen Freigaben sind offen, keine persönlichen Bewertungen.

Ausgenommen ist die lokale Datei `sources/cache/S01.txt`. Sie enthält einen
kurzen simulierten Testtext und ist kein Originalquellenbeleg. Caches sind
Laufzeitdaten und werden nicht versioniert. Lokale Auditprotokolle,
Zugangsdaten, persönliche Dateien und Entwicklungsstände 1.10 werden nicht übertragen.

Zusätzlich zu dieser Importnotiz wird nur `.gitignore` um Regeln für
Zugangsdaten, virtuelle Umgebungen und Laufzeitdateien ergänzt. Der vorhandene
CI-Entwurf bleibt unter `github_vorbereitung/` als inaktive Vorlage erhalten.
Es wird kein GitHub-Actions-Workflow eingerichtet und keine Website-Datei geändert.

## Prüfung

- Alle 84 Dateien des Originalpakets inventarisiert, gelesen und auf typische
  Schlüssel, Zugangsdaten, E-Mail-Adressen und persönliche Dateipfade geprüft.
  Die drei Schlüsselverdachtsstellen sind `DUMMY_TEST_ONLY` in Test-Backends.
- Python-Syntax aller Module geprüft.
- 158 von 158 vorhandenen Tests bestanden unter Python 3.15.2 auf Windows.
- Die Suite lief in einer temporären Kopie ohne Zugangsdaten aus der Umgebung.
  Ein Python-Audit-Hook sperrte Netzwerkverbindungen, DNS, Datagramme und
  zusätzliche Unterprozesse während des Testlaufs. Keine kostenpflichtigen Aufrufe.
- Das Originalpaket blieb laut SHA-256-Vergleich unverändert.

Standardaufruf der bestehenden Tests aus diesem Ordner:

```text
python -m unittest discover -s tests -v
```

Python ab 3.10, nur Standardbibliothek. Die Tests verwenden Demo-Ausgaben und
simulierte Backends. Der alte Integrationstest kann einen simulierten Text in
`sources/cache/` schreiben; daher wurde für den Import eine Wegwerfkopie verwendet.
Die Tests belegen Softwareverhalten, keine wissenschaftliche Verlässlichkeit.
Optionale Echtbetrieb-Startskripte gehören zum Originalumfang, wurden aber
nicht ausgeführt. Version 1.9 erzwingt mit `ALI_OFFLINE_ONLY` allein noch keine
allgemeine Netzsperre; die Importsitzung nutzte dafür den beschriebenen Audit-Hook.
