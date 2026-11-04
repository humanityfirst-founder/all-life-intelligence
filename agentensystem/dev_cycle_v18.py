#!/usr/bin/env python3
"""Reproducible, offline development QA; compares to a frozen reference.

No external calls, no self-modification and no automatic release. All output
is derived from local, untrusted test results and labelled as such.
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import html
import json
import os
from pathlib import Path
import sys

from auto_qa_v17 import run_tests

ROOT = Path(__file__).resolve().parent
CASES = Path('reports/KONTEXTPRUEFUNG_1_6_2_FAELLE.csv')
BASELINE = Path('evaluation/BASELINE_1_7_FROZEN.json')
OUTPUT = Path('reports')
BASE_COLS = ('Test-ID', 'Szenario-Erwartung', 'KI-Kontextkategorie', 'KI-Sprechakt')
REQUIRED = BASE_COLS + ('Aussage', 'Quellen-ID', 'KI-Begruendung', 'Menschliche Freigabe')
KNOWN = frozenset({'META','METHODE','PAUSCHALE_ABSENZ','DOMAENENFEHLER','KEIN_SPEZIELLER_HINWEIS','UNKLAR','NICHT_AUSGEFUEHRT'})
NOT_DONE = frozenset({'UNKLAR','NICHT_AUSGEFUEHRT',''})
# Independently pinned in the code so a changed baseline JSON does not silently redefine history.
FROZEN_V17_SHA = '6ca6be16d7d97fdd96146cb9e6a4f666a759b55a615b6800f178cddd29fbeec6'


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalized_reference(rows: list[dict]) -> list[dict]:
    """Exclude human columns: editing a review does not corrupt the model baseline."""
    return [{field: row[field].strip() for field in BASE_COLS} for row in sorted(rows, key=lambda r: r['Test-ID'])]


def digest_reference(rows: list[dict]) -> str:
    encoded = json.dumps(normalized_reference(rows), sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    return _sha(encoded)


def read_cases(path: Path) -> list[dict]:
    with path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream, delimiter=';')
        if not reader.fieldnames or any(field not in reader.fieldnames for field in REQUIRED):
            raise ValueError('Prueffalldatei hat fehlende Spalten')
        result = list(reader)
    if len(result) != 24:
        raise ValueError('Erwartet sind 24 synthetische Testfaelle')
    ids = [r['Test-ID'].strip() for r in result]
    if any(not x for x in ids) or len(set(ids)) != len(ids):
        raise ValueError('Doppelte oder leere Testfall-ID')
    for row in result:
        if row['Szenario-Erwartung'].strip() not in KNOWN - {'UNKLAR','NICHT_AUSGEFUEHRT'}:
            raise ValueError(f"Nicht erlaubte Vorgabe: {row['Test-ID']}")
        if row['KI-Kontextkategorie'].strip() not in KNOWN:
            raise ValueError(f"Unerwartete KI-Kategorie: {row['Test-ID']}")
    return result


def analyse(rows: list[dict], baseline: dict) -> dict:
    data_hash = digest_reference(rows)
    baseline_matches = data_hash == baseline['reference_sha256']
    items = []
    matches = differences = technical_failures = semantic_abstentions = 0
    for row in rows:
        verdict = row['KI-Kontextkategorie'].strip()
        label = row['Szenario-Erwartung'].strip()
        reason = row['KI-Begruendung'].strip()
        if verdict in NOT_DONE:
            # UNKLAR can mean an abstention, or a failed request; don't conflate the two.
            if 'API-Fehler' in reason or 'ungueltige Antwort' in reason or verdict == 'NICHT_AUSGEFUEHRT':
                kind = 'TECHNISCH_UNBEWERTET'
                technical_failures += 1
                action = 'Zuerst technische Ursache untersuchen; kein blindes Nachfragen.'
            else:
                kind = 'INHALTLICH_UNKLAR'
                semantic_abstentions += 1
                action = 'Mit neuem Kontext und getrennten Menschenurteilen pruefen.'
        elif verdict != label:
            kind = 'LABEL_ABWEICHUNG'
            differences += 1
            action = 'Pruefen, ob KI-Ausgabe oder interne Szenariovorgabe falsch ist.'
        else:
            kind = 'INTERNE_UEBEREINSTIMMUNG'
            matches += 1
            action = 'Nicht als unabhängigen Quellenbeleg ausgeben.'
        if kind != 'INTERNE_UEBEREINSTIMMUNG':
            items.append({'id':row['Test-ID'], 'kind':kind, 'expected':label,
                          'observed':verdict, 'text':row['Aussage'], 'reason':reason,
                          'source':row['Quellen-ID'], 'action':action,
                          'human_confirmation':row['Menschliche Freigabe']})
    return {
        'cases_total':len(rows), 'matches_internal_labels':matches,
        'differences_internal_labels':differences,
        'technical_unreviewed':technical_failures,
        'semantic_abstentions':semantic_abstentions,
        'open_cases':items,
        'baseline_sha256':baseline['reference_sha256'],
        'current_reference_sha256':data_hash,
        'baseline_unchanged':baseline_matches,
        'human_labels_independently_verified':0,
        'scientific_claims_verified':0,
    }


def source_fingerprints(root:Path) -> dict:
    """Record code hashes, without publishing credentials, caches or personal reports."""
    names = ['agent.py', 'sourcecheck.py', 'context_review_v16.py',
             'diagnose_single_v162.py', 'auto_qa_v17.py', 'dev_cycle_v18.py']
    return {name:_sha((root/name).read_bytes()) if (root/name).is_file() else None
            for name in names}


def _write_csv(path:Path, items:list[dict]) -> None:
    headers = ['id','kind','expected','observed','text','reason','source','action','human_confirmation']
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        writer = csv.DictWriter(f, delimiter=';', fieldnames=headers)
        writer.writeheader()
        for item in items:
            # CSV formula protection for text from model/user files.
            writer.writerow({key:("'"+str(item[key]) if str(item[key]).lstrip().startswith(('=','+','-','@')) else item[key])
                             for key in headers})


def run_cycle(root: Path=ROOT, do_tests: bool=True) -> dict:
    with (root/BASELINE).open(encoding='utf-8') as f:
        baseline=json.load(f)
    if baseline.get('schema_version') != 1:
        raise ValueError('Unbekanntes Baseline-Format')
    if baseline.get('reference_sha256') != FROZEN_V17_SHA:
        raise ValueError('Eingefrorener v1.7-Referenzwert wurde veraendert')
    if baseline.get('reference_case_count') != 24:
        raise ValueError('Unbekannte Zahl im eingefrorenen Referenzsatz')
    rows=read_cases(root/CASES)
    scan=analyse(rows,baseline)
    tests = run_tests(root) if do_tests else {'passed':False,'tests_run':0,'diagnostic_excerpt':'Tests deaktiviert: keine technische Freigabe','returncode':None}
    # No automatic scientific release regardless of whether internal test data matches.
    code_gate = bool(tests['passed'] and tests['tests_run'] >= baseline['min_software_tests'] and scan['baseline_unchanged'])
    result={
        'version':'1.8', 'created_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
        'mode':'offline_reproducible_development',
        'technical_candidate_gate': 'PASS' if code_gate else 'BLOCK',
        'external_release_decision':'HOLD_FOR_HUMAN_AND_INDEPENDENT_REVIEW',
        'reasons':(['Softwaretests oder feste Referenzbasis haben sich verschlechtert.'] if not code_gate else []) + [
            'Interne Testlabels sind keine unabhaengige Wahrheit.',
            'Fuenf ehemals fehlgeschlagene API-Faelle werden nicht automatisch erneut angefragt.',
            'Fachliche Freigabe und unabhaengige Testfaelle fehlen.',
        ],
        'tests':tests,'case_audit':scan,'code_fingerprints':source_fingerprints(root),
        'api_calls_executed':0,'automatic_code_changes':0,'automatic_publication':False,
    }
    out = root/OUTPUT
    out.mkdir(parents=True,exist_ok=True)
    (out/'ENTWICKLUNGSZYKLUS_1_8.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    _write_csv(out/'OFFENE_FRAGEN_1_8.csv',scan['open_cases'])
    esc=lambda x:html.escape(str(x),quote=True)
    rows_html=''.join('<tr>'+''.join('<td>'+esc(entry[key])+'</td>' for key in ('id','kind','expected','observed','text','action'))+'</tr>' for entry in scan['open_cases'])
    status = 'TECHNISCHER KANDIDAT – NOCH NICHT FREIGEGEBEN' if code_gate else 'TECHNISCHE PRUEFUNG BLOCKIERT'
    doc=f'''<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>ALL-LIFE INTELLIGENCE – Entwicklungszyklus 1.8</title><style>body{{font:15px/1.6 system-ui,Arial;max-width:1140px;margin:24px auto;padding:0 16px;background:#f0f3f7;color:#17283d}}header,section{{border:1px solid #d8e1eb;border-radius:12px;background:#fff;padding:20px 24px;margin:14px 0}}table{{width:100%;border-collapse:collapse;font-size:12px}}th,td{{border:1px solid #d8e1eb;padding:8px;text-align:left;vertical-align:top}}th{{background:#edf2f7}}.scroll{{overflow-x:auto}}</style></head><body>
<header><h1>ALL-LIFE INTELLIGENCE 1.8 – Kontrollierter Entwicklungszyklus</h1><p><b>{esc(status)}</b></p><p>Alle Tests und Auswertungen wurden lokal offline ausgefuehrt. Keine API-Kosten, keine Publikation und keine Selbstmodifikation.</p></header>
<section><h2>Software und Integritaet</h2><p>Python-Tests: <b>{tests['tests_run']}</b> (bestanden: {esc(tests['passed'])}). Feste Referenz gegen v1.7 unveraendert: <b>{esc(scan['baseline_unchanged'])}</b>.</p><p>Quellcode-Hashes und Eingabe-Hash stehen in der JSON-Datei. Eine geaenderte Referenz stoppt das technische Kandidaten-Gate, auch wenn Python-Tests bestehen.</p></section>
<section><h2>Wissenschaftliche Einordnung</h2><p><b>{scan['matches_internal_labels']}</b> Uebereinstimmungen mit internen Vorgaben, <b>{scan['differences_internal_labels']}</b> Abweichungen, <b>{scan['technical_unreviewed']}</b> technische Ausfaelle, <b>{scan['semantic_abstentions']}</b> inhaltliche Enthaltungen.</p><p><b>0</b> unabhaengig bestaetigte Fachlabels und <b>0</b> automatisch verifizierte Originalbelege. Kein Beweis fuer Alignment, Bewusstsein, Superintelligenz oder die Gueltigkeit der Testlabels.</p></section>
<section><h2>Automatisch erstellte Arbeitsliste – noch offen</h2><div class="scroll"><table><thead><tr><th>Fall</th><th>Art</th><th>Interne Erwartung</th><th>KI-Ausgabe</th><th>Aussage</th><th>Naechste Pruefung</th></tr></thead><tbody>{rows_html}</tbody></table></div></section>
<section><h2>Entwicklungsentscheidung</h2><p>Weder die Testregeln noch die interne Referenzbasis werden automatisch geaendert. Keine GitHub-Commits oder Merges. Freigabe bleibt <b>ausgesetzt</b>, bis neue extern bewertete Beispiele und eine Quellenpruefung vorliegen.</p></section></body></html>'''
    (out/'ENTWICKLUNGSZYKLUS_1_8.html').write_text(doc,encoding='utf-8')
    return result


if __name__=='__main__':
    try:
        outcome=run_cycle()
    except (ValueError, KeyError, OSError, json.JSONDecodeError) as exc:
        print('ENTWICKLUNGSZYKLUS GESCHEITERT:',type(exc).__name__,exc,file=sys.stderr)
        sys.exit(1)
    print('Technisches Gate:',outcome['technical_candidate_gate'])
    print('Python-Tests:',outcome['tests']['tests_run'])
    print('Fallpruefung:',outcome['case_audit']['matches_internal_labels'],'passend /',outcome['case_audit']['differences_internal_labels'],'abweichend /',outcome['case_audit']['technical_unreviewed'],'technisch offen')
    print('Freigabe:',outcome['external_release_decision'])
    sys.exit(0 if outcome['technical_candidate_gate']=='PASS' else 1)
