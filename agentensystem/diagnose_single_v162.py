#!/usr/bin/env python3
"""ALL-LIFE INTELLIGENCE 1.6.2: diagnose failures and resume ONE missing case.

- Offline by default, no key/network, no unapproved API call.
- Paid mode requires explicit confirmation and calls the API at most once.
- Previous results are preserved; manual approval CSVs are never modified.
- Failure messages contain only safe status classifications, never response bodies.
"""
from __future__ import annotations
import argparse
import csv
import getpass
import html
import re
from pathlib import Path
import webbrowser
from context_review_v16 import (
    OUTPUT, COLS, INSTRUCTIONS, MODEL, rows24, payload, parse_response,
    evaluate, render,
)
from rule_comparison_v15 import EXPECT
from agent import call_openai, ApiProblem, offline_only, OFFLINE_MESSAGE
from improvement_agent import prevent_excel_formula

PREVIOUS = OUTPUT / 'KONTEXTPRUEFUNG_1_6_1_FAELLE.csv'
RESULT = OUTPUT / 'KONTEXTPRUEFUNG_1_6_2_FAELLE.csv'
REPORT = OUTPUT / 'KONTEXTPRUEFUNG_1_6_2.html'


def load_records(source=None):
    """Read last output (if any), verify every original case before considering API."""
    file = Path(source) if source is not None else (RESULT if RESULT.exists() else PREVIOUS)
    if file.stat().st_size > 1_000_000:
        raise ValueError('Pruefdatei zu gross.')
    with file.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f, delimiter=';')
        if not reader.fieldnames or set(COLS) - set(reader.fieldnames):
            raise ValueError('Fehlende Spalten in der Pruefdatei.')
        records = list(reader)
    rows = rows24()
    if len(records) != 24:
        raise ValueError('Die Pruefdatei muss genau 24 Faelle enthalten.')
    checked = ('Test-ID', 'Aussage', 'Quellen-ID', 'KI-Rolle')
    for old, row in zip(records, rows):
        if any(old[k] != row[k] for k in checked) or old['Szenario-Erwartung'] != row[EXPECT]:
            raise ValueError('Originalfall veraendert; kein Live-Aufruf.')
        category = old['KI-Kontextkategorie']
        if category not in {'META','METHODE','PAUSCHALE_ABSENZ','DOMAENENFEHLER',
                            'KEIN_SPEZIELLER_HINWEIS','UNKLAR'}:
            raise ValueError('Unerwartete KI-Kategorie; kein Live-Aufruf.')
    return rows, records


def is_pending(row):
    return row['KI-Kontextkategorie'] == 'UNKLAR' and row['KI-Begruendung'].startswith('API-Fehler')


def safe_diagnosis(exc):
    """No raw API output, credentials or messages from unknown origins in reports."""
    if isinstance(exc, ApiProblem):
        msg = str(exc)
        m = re.search(r'API-Fehler HTTP (\d{3})\b', msg)
        if m:
            code = int(m.group(1))
            explanations = {
                400: 'Anfrage vom API-Server abgewiesen (Eingabe oder Parameter).',
                401: 'API-Authentifizierung fehlgeschlagen.',
                403: 'API-Zugriff nicht erlaubt.',
                404: 'Modell oder API-Endpunkt nicht gefunden.',
                408: 'API-Zeitueberschreitung.',
                413: 'API-Anfrage zu gross.',
                422: 'API kann Anfrage nicht verarbeiten.',
                429: 'Rate-Limit oder Kontingent erreicht (Details im API-Konto pruefen).',
                500: 'Interner API-Serverfehler.',
                502: 'API-Gatewayfehler.',
                503: 'API-Service momentan nicht verfuegbar.',
                504: 'API-Gateway-Zeitueberschreitung.',
            }
            return f'HTTP {code}: ' + explanations.get(code,'API-Fehler; Ursache noch unklar.')
        if 'UNVOLLSTAENDIGE' in msg: return 'Unvollstaendige Modellantwort; moegliches Ausgabetokenlimit.'
        if 'Keine Textantwort' in msg: return 'API lieferte keine verwendbare Textantwort.'
        if 'Netzwerkfehler' in msg: return 'Netzwerkverbindung fehlgeschlagen.'
        if 'Unerwartete JSON-Antwort' in msg: return 'API-Antwort war kein gueltiges JSON-Protokoll.'
        if 'Modellantwort nicht abgeschlossen' in msg: return 'API-Modellantwort nicht abgeschlossen.'
        return 'API-Fehler ohne im Programm verfuegbare Einzelursache.'
    if isinstance(exc, ValueError):
        # These are errors from our own strict parser; never include raw text.
        msg = str(exc)
        known = {'Unerwartete Zahl an KI-Bewertungen.': 'Modell lieferte nicht exakt eine Bewertung.',
                 'Bewertung ist kein Objekt.': 'Antwortstruktur enthaelt keine gueltige Bewertung.',
                 'Fehlende, doppelte oder fremde Fall-ID.': 'Fall-ID im Antwortformat fehlerhaft.',
                 'Ungueltige Bewertung oder Begründung.': 'Antwortkategorie oder Begruendung ungueltig.'}
        return known.get(msg,'KI-Antwort konnte nicht strukturiert ausgewertet werden.')
    return 'Technischer Fehler; ohne Rohdaten nicht naeher bestimmbar.'


def one_step(rows, prior, backend=None, api_key=None):
    """At most ONE API call, updating precisely one pending case. Test backend injectable."""
    remaining = [i for i, row in enumerate(prior) if is_pending(row)]
    assessments = {row['Test-ID']: {'category':row['KI-Kontextkategorie'],
                                     'stance':row['KI-Sprechakt'],
                                     'reason':row['KI-Begruendung']} for row in prior}
    problems = []
    if backend is not None and remaining:
        if not api_key: raise ValueError('API-Schluessel fehlt.')
        i = remaining[0]
        case = rows[i]
        try:
            response = backend(instructions=INSTRUCTIONS, input_text=payload([case]),
                               model=MODEL,api_key=api_key,max_tokens=1800)
            assessments.update(parse_response(response,[case['Test-ID']]))
        except (ApiProblem, ValueError, TypeError, KeyError) as exc:
            problems.append('Einzelpruefung fehlgeschlagen: ' + safe_diagnosis(exc))
    records = evaluate(rows, assessments)
    # Preserve any human entries in this data file, and never touch the separate manual file.
    for old, new in zip(prior, records):
        for field in ('Menschliche Freigabe','Menschliche Bewertung','Notiz'):
            new[field] = old[field]
    return records, problems


def save(records, problems, mode, root=OUTPUT):
    root = Path(root)
    root.mkdir(parents=True,exist_ok=True)
    report = root / REPORT.name
    data = root / RESULT.name
    # report uses the established HTML renderer, with a distinct version label
    overview = render(records, mode, problems).replace('Kontextpruefung 1.6.1', 'Kontextpruefung 1.6.2')
    report.write_text(overview,encoding='utf-8')
    with data.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=COLS,delimiter=';',lineterminator='\n')
        writer.writeheader()
        for row in records:
            writer.writerow({key:prevent_excel_formula(row[key]) for key in COLS})
    return report


def main(argv=None):
    ap=argparse.ArgumentParser(description='ALL-LIFE INTELLIGENCE 1.6.2 – sichere Einzel-Diagnose')
    ap.add_argument('--live',action='store_true')
    ap.add_argument('--open',action='store_true')
    opts=ap.parse_args(argv)
    if opts.live and offline_only():
        print(OFFLINE_MESSAGE)
        return 2
    try:
        rows, prior = load_records()
    except (OSError,ValueError,UnicodeError,csv.Error) as exc:
        print('Offline-Pruefung fehlgeschlagen:',str(exc));return 1
    remaining = [r['Test-ID'] for r in prior if is_pending(r)]
    print('Gesicherte Bewertungen:', 24 - len(remaining), '/ 24')
    print('Noch offen:',len(remaining), 'Faelle')
    print('Zuletzt gemeldeter Fehler: ApiProblem; genauer HTTP-/API-Grund unbekannt.')
    if not opts.live:
        records,problems=one_step(rows,prior)
        print('OFFLINE: keine API-Anfrage, keine Kosten.')
        path=save(records,problems,'Offline-Diagnose; kein API-Aufruf')
        print('Bericht:',path)
        if opts.open:webbrowser.open(path.resolve().as_uri())
        return 0
    if not remaining:
        print('Keine fehlenden Faelle mehr. Kein API-Aufruf.');return 0
    print('OPTIONAL: GENAU EIN moeglicherweise kostenpflichtiger API-Aufruf, fuer den Fall',remaining[0])
    print('Kein automatischer zweiter Versuch und keine weiteren API-Aufrufe.')
    if input('Diesen EINEN API-Aufruf ausfuehren? (ja/nein): ').strip().lower() != 'ja':
        print('Abbruch: null API-Aufrufe.');return 0
    key=getpass.getpass('OpenAI-API-Schluessel (unsichtbar): ').strip()
    if not key:
        print('Kein API-Schluessel; null API-Aufrufe.');return 1
    records,problems=one_step(rows,prior,backend=call_openai,api_key=key)
    del key
    result=save(records,problems,'Live-Einzelpruefung'+(' mit Fehler' if problems else ''))
    print('Bericht:',result)
    if problems:
        print('Fehlerdiagnose:',problems[0]);print('Kein automatischer neuer Aufruf.')
        return 1
    print('Genau ein Fall wurde bewertet. Weitere Faelle bleiben ohne automatische Anfrage.')
    if opts.open:webbrowser.open(result.resolve().as_uri())
    return 0

if __name__=='__main__': raise SystemExit(main())
