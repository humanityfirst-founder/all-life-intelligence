#!/usr/bin/env python3
"""Offline research council for ALL-LIFE INTELLIGENCE v1.9.

A1/A2/A6/Coordinator are separate deterministic audit perspectives, NOT independent
LLM invocations. No network, no paid API, no self-modification, no publication.
Existing human labels and the frozen v1.7 reference are never overwritten.
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import html
import json
from pathlib import Path
from typing import Any

from dev_cycle_v18 import (ROOT, CASES, BASELINE, FROZEN_V17_SHA,
                           analyse, digest_reference, read_cases)
from auto_qa_v17 import run_tests

OUTPUT_DIR = Path('reports')
REPORT_NAME = 'FORSCHUNGSRAT_1_9'
ROLES = ('A1', 'A2', 'A6', 'KOORDINATOR')
PENDING = {'UNKLAR', 'NICHT_AUSGEFUEHRT', ''}
REVIEW_LABELS = {'OFFEN', '', 'NICHT_GEPRUEFT', 'NICHT_GEPRÜFT'}


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require_original_evidence(root: Path) -> tuple[list[dict], dict]:
    baseline = json.loads((root / BASELINE).read_text(encoding='utf-8'))
    if baseline.get('schema_version') != 1 or baseline.get('reference_sha256') != FROZEN_V17_SHA:
        raise ValueError('Baseline ungueltig: Forschungsrat gestoppt')
    if baseline.get('reference_case_count') != 24:
        raise ValueError('Baseline hat unerwartete Fallzahl')
    rows = read_cases(root / CASES)
    if digest_reference(rows) != FROZEN_V17_SHA:
        raise ValueError('Eingefrorene Modell-Referenz hat sich veraendert')
    return rows, baseline


def _record(role: str, topic: str, case_ids: list[str],
            finding: str, limitation: str, next_action: str) -> dict:
    return dict(role=role, topic=topic, case_ids=case_ids, finding=finding,
                limitation=limitation, next_action=next_action,
                evidence_type='DETERMINISTISCHE_DATEIAUSWERTUNG',
                source_verified=False, independent_human_review=False)


def build_council(rows: list[dict], baseline: dict) -> dict:
    """Four genuinely distinct *procedural* perspectives; no fake AI role calls."""
    audit = analyse(rows, baseline)
    by_id = {r['Test-ID']: r for r in rows}
    all_ids = sorted(by_id)
    disagreements = [r for r in rows if r['KI-Kontextkategorie'] not in PENDING
                     and r['KI-Kontextkategorie'] != r['Szenario-Erwartung']]
    pending = [r for r in rows if r['KI-Kontextkategorie'] in PENDING]
    unapproved = [r for r in rows if r['Menschliche Freigabe'].strip().upper() in REVIEW_LABELS]
    if len(rows) != len(all_ids) or len(unapproved) != len(rows):
        # This test corpus has not been independently reviewed. A genuine human
        # update should be examined rather than silently represented as zero.
        if len(unapproved) != len(rows):
            raise ValueError('Manuelle Bewertungsfelder wurden veraendert: erneut pruefen')
    a1 = _record(
        'A1','Methodische Robustheit und technische Integritaet',
        [r['Test-ID'] for r in pending],
        f'{len(pending)} technisch oder inhaltlich unbewertete Faelle; '
        f'{len(disagreements)} Abweichungen von internen Szenariolabels; '
        f'Referenz-SHA unveraendert: {audit["baseline_unchanged"]}.',
        'Testlabels intern erstellt; keine externe Zuverlaessigkeitsmetrik.',
        'Fuer jeden Ausfall Ursache dokumentieren; kein automatischer API-Nachlauf.'
    )
    a2_ids = [r['Test-ID'] for r in rows if r['Quellen-ID'].strip() == 'S04']
    a2 = _record(
        'A2','Empfindungsfaehigkeit und Grenzen des Quellenbereichs', a2_ids,
        f'{len(a2_ids)} Testfaelle mit Quellen-ID S04. '
        'S04 behandelt KI-Bewusstseinsindikatoren, ist kein validierter experimenteller '
        'Messstandard fuer Tierleid.',
        'Die Quellen-ID allein verifiziert keinen einzelnen Sachverhalt; '
        'keine neue Originalquellenanalyse in diesem Offline-Lauf.',
        'Separate Quellen fuer Tierleid und KI-Bewusstsein fordern; '
        'Aussagen anhand der Originaltexte fachlich pruefen.'
    )
    a6_ids = [r['Test-ID'] for r in disagreements]
    a6 = _record(
        'A6','Kritische Gegenpruefung: Overfitting und Label-Gueltigkeit',a6_ids,
        f'{len(disagreements)} Klassifikationskonflikte, darunter '
        'Zitier-/Methodikfragen; die Referenzlabels sind nicht begutachtet.',
        'Ein besserer Vergleichswert auf den Entwicklungsdaten kann Overfitting sein. '
        'Eine interne Uebereinstimmung ist kein Beweis fuer wissenschaftliche Richtigkeit.',
        'Blindes unabhaengiges Bewertungsprotokoll mit doppelt beurteilten neuen Faellen erstellen.'
    )
    coordinator = _record(
        'KOORDINATOR','Priorisierte naechste Forschungsentscheidung',
        [r['Test-ID'] for r in pending+disagreements],
        'Technischer Fortschritt und wissenschaftliche Freigabe sind getrennt. '
        'Prioritaet: erst unabhängige Referenzdaten und Quellennachweise, '
        'dann Agentenregeln an unbekannten Faellen testen.',
        'Kein laufender autonomer LLM-Forschungsprozess; nur deterministische '
        'Rollenpruefung vorhandener Daten.',
        'Drei pruefbare Arbeitspakete formulieren, keine neuen Labels/Regeln automatisch uebernehmen.'
    )
    backlog = [
        {
          'id':'M19-01', 'priority':'P1', 'owner':'A1 + A6',
          'title':'Externe Referenzfaelle mit unabhaengiger Bewertung',
          'why':f'{len(disagreements)} strittige, {len(pending)} ungepruefte Faelle; '
                'alle 24 bisherigen Labels ohne unabhaengige Fachfreigabe.',
          'acceptance':'Mindestens 20 NEUE, zuvor nicht zur Regelentwicklung verwendete '
                       'Faelle, zwei getrennte menschliche Bewertungen je Fall und dokumentierte '
                       'Konfliktklaerung vor jeglicher Leistungsbehauptung.',
          'status':'VORSCHLAG', 'requires_approval':True,
        },
        {
          'id':'M19-02', 'priority':'P1', 'owner':'A2 + A6',
          'title':'Originalquellen und Behauptungen getrennt nachweisen',
          'why':'Themenueberschneidung oder Quellen-ID beweisen keine Behauptung.',
          'acceptance':'Pro belastbarer Tatsachenbehauptung: Quellentitel, Fundstelle, '
                       'woertliche oder sauber paraphrasierte Textgrundlage, '
                       'getrennte Aussage der Stuetzung/Grenzen und manuelles Urteil.',
          'status':'VORSCHLAG', 'requires_approval':True,
        },
        {
          'id':'M19-03', 'priority':'P2', 'owner':'A1 + A2 + A6',
          'title':'Kontextpruefung mit Behauptung/Zitat/Kritik auftrennen',
          'why':'Drei bekannte Konflikte behandeln Methodenaussagen, Zitate und Kritik.',
          'acceptance':'Sprechakt und Sachkategorie separat ausgeben; '
                       'Abstention moeglich; Vergleich gegen festgefrorene '
                       'alte und unabhaengige neue Faelle mit Fehlalarmquote.',
          'status':'VORSCHLAG', 'requires_approval':True,
        },
    ]
    return {
        'version':'1.9', 'mode':'OFFLINE_DETERMINISTIC_ROLE_AUDIT',
        'agent_roles_executed_as_language_models':0,
        'role_reports':{'A1':a1,'A2':a2,'A6':a6,'KOORDINATOR':coordinator},
        'backlog':backlog,
        'case_counts':{
          'total':len(rows),'internal_matches':audit['matches_internal_labels'],
          'disagreements':len(disagreements),'unreviewed':len(pending),
          'independent_human_labels':0,
          'automatically_verified_source_claims':0,
        },
        'baseline_sha256':FROZEN_V17_SHA,
        'baseline_unchanged':audit['baseline_unchanged'],
        'input_sha256':None, # assigned by run_council; not a signature
        'unapproved_changes':0, 'api_calls_executed':0,
        'automatic_code_changes':0,'automatic_publication':False,
        'release_decision':'HOLD_FOR_HUMAN_AND_INDEPENDENT_REVIEW',
    }


def _escape_csv(value: Any) -> str:
    s = str(value)
    return "'" + s if s.lstrip().startswith(('=', '+', '-', '@')) else s


def write_board_outputs(root: Path, council: dict) -> None:
    out = root / OUTPUT_DIR
    out.mkdir(parents=True, exist_ok=True)
    js = out / (REPORT_NAME + '.json')
    js.write_text(json.dumps(council, ensure_ascii=False, indent=2), encoding='utf-8')
    with (out / (REPORT_NAME + '_AUFGABEN.csv')).open('w',encoding='utf-8-sig',newline='') as file:
        cols = ['id','priority','owner','title','why','acceptance','status','requires_approval']
        writer=csv.DictWriter(file,fieldnames=cols,delimiter=';')
        writer.writeheader()
        for row in council['backlog']:
            writer.writerow({col:_escape_csv(row[col]) for col in cols})
    esc=lambda x:html.escape(str(x),quote=True)
    role_table=''.join('<tr>'+''.join('<td>'+esc(x)+'</td>' for x in
        (r['role'],r['topic'],', '.join(r['case_ids']) or '–',r['finding'],r['limitation'],r['next_action']))+'</tr>'
        for r in council['role_reports'].values())
    tasks=''.join('<tr>'+''.join('<td>'+esc(item[k])+'</td>' for k in
        ('id','priority','owner','title','acceptance','status'))+'</tr>'
        for item in council['backlog'])
    tests=council.get('technical_tests',{})
    technical_status=('BESTANDEN' if tests.get('passed') else 'NICHT BESTANDEN')
    htmltext=f'''<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ALL-LIFE INTELLIGENCE – Forschungsrat 1.9</title>
<style>body{{font:15px/1.6 system-ui,Arial;max-width:1180px;margin:22px auto;padding:0 18px;background:#f1f4f8;color:#182b40}}header,section{{padding:20px 24px;background:white;border:1px solid #dae3ea;border-radius:12px;margin:15px 0}}table{{width:100%;border-collapse:collapse;font-size:12px}}td,th{{border:1px solid #dce5ed;padding:8px;text-align:left;vertical-align:top}}th{{background:#edf3f8}}.scroll{{overflow-x:auto}}.notice{{border-left:5px solid #b38a34;padding:10px;background:#fff4df}}</style></head><body>
<header><h1>ALL-LIFE INTELLIGENCE – Forschungsrat v1.9</h1>
<p class="notice"><b>Offline-Rollenpruefung, keine echten separaten Modellagenten.</b> Die Perspektiven A1, A2, A6 und Koordinator werden anhand der vorhandenen Daten und festgelegter Pruefregeln erzeugt. Keine kostenpflichtigen API-Aufrufe, keine neue Originalquellenpruefung und keine unabhaengige Fachvalidierung.</p></header>
<section><h2>Qualitaet und Integritaet</h2><p>Softwaretests: <b>{esc(tests.get('tests_run','NICHT AUSGEFUEHRT'))}</b>, Status: <b>{esc(technical_status)}</b>. Eingefrorene Referenz unveraendert: <b>{esc(council['baseline_unchanged'])}</b>.</p>
<p>Interne Uebereinstimmungen: <b>{council['case_counts']['internal_matches']}</b> / 24; strittige Bewertungen: <b>{council['case_counts']['disagreements']}</b>; technisch offen: <b>{council['case_counts']['unreviewed']}</b>.</p>
<p>Unabhaengig gepruefte Quellen-Aussagen: <b>0</b>. Unabhaengig bestaetigte Fachlabels: <b>0</b>. Externe Freigabe: <b>NICHT ERTEILT</b>.</p></section>
<section><h2>Vier voneinander getrennte Pruefperspektiven</h2><div class="scroll"><table><thead><tr><th>Rolle</th><th>Schwerpunkt</th><th>Betroffene Faelle</th><th>Feststellung</th><th>Grenze</th><th>Naechste Handlung</th></tr></thead><tbody>{role_table}</tbody></table></div></section>
<section><h2>Entwicklungsauftraege – nur Vorschlaege</h2><div class="scroll"><table><thead><tr><th>ID</th><th>Prioritaet</th><th>Rolle</th><th>Aufgabe</th><th>Pruefbares Abnahmekriterium</th><th>Status</th></tr></thead><tbody>{tasks}</tbody></table></div></section>
<section><h2>Naechste Entscheidung</h2><p>Die drei Arbeitspakete sind vorbereitet, aber weder automatisch umgesetzt noch wissenschaftlich bestaetigt. Ein eigener LLM-Agentenlauf braucht eine gesonderte ausdrueckliche API-Kostenfreigabe. Die Software veroeffentlicht keine Daten und veraendert keine Regeln oder Modelle selbststaendig.</p>
<p>Maschinenlesbare Ergebnisse: <code>FORSCHUNGSRAT_1_9.json</code>; pruefbare Aufgaben: <code>FORSCHUNGSRAT_1_9_AUFGABEN.csv</code>.</p></section></body></html>'''
    (out / (REPORT_NAME + '.html')).write_text(htmltext,encoding='utf-8')


def run_council(root: Path=ROOT, *, do_tests: bool=True) -> dict:
    rows, baseline = _require_original_evidence(root)
    board = build_council(rows,baseline)
    board['input_sha256'] = sha_file(root/CASES)
    board['created_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
    board['technical_tests'] = (run_tests(root) if do_tests else
        {'passed':False,'tests_run':0,'diagnostic_excerpt':'Nicht ausgefuehrt'})
    board['technical_candidate_gate'] = ('PASS' if board['technical_tests']['passed']
                                          and board['baseline_unchanged'] else 'BLOCK')
    write_board_outputs(root, board)
    return board


if __name__ == '__main__':
    result=run_council()
    print('Forschungsrat: 4 regelbasierte Rollen, 0 externe API-Aufrufe')
    print('Software-Tests:',result['technical_tests']['tests_run'])
    print('Qualitaetsgate:',result['technical_candidate_gate'])
    print('Offene Faelle:',result['case_counts']['disagreements'] + result['case_counts']['unreviewed'])
    print('Bericht:',ROOT / OUTPUT_DIR / (REPORT_NAME + '.html'))
    raise SystemExit(0 if result['technical_candidate_gate']=='PASS' else 1)
