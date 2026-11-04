#!/usr/bin/env python3
"""Cost-free local developer quality gate: no paid API or autonomous changes."""
from __future__ import annotations

import csv
import datetime as dt
import html
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
SOURCE_CSV = Path('reports/KONTEXTPRUEFUNG_1_6_2_FAELLE.csv')
OUTPUT_HTML = Path('reports/AUTOMATISCHE_QUALITAET_1_7.html')
OUTPUT_JSON = Path('reports/AUTOMATISCHE_QUALITAET_1_7.json')
REQUIRED = ('Test-ID', 'Szenario-Erwartung', 'KI-Kontextkategorie', 'Menschliche Freigabe')


def analyse_cases(file_path: Path) -> dict:
    """Counts synthetic labels without treating them as objective ground truth."""
    with file_path.open('r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f, delimiter=';')
        if not reader.fieldnames or any(k not in reader.fieldnames for k in REQUIRED):
            raise ValueError('Fehlende oder unlesbare CSV-Spalten')
        rows = list(reader)
    if not rows or any(not r['Test-ID'].strip() for r in rows):
        raise ValueError('Keine gueltigen Testfall-IDs')
    ids = [r['Test-ID'].strip() for r in rows]
    if len(set(ids)) != len(ids):
        raise ValueError('Doppelte Testfall-IDs')
    evaluated = [r for r in rows if r['KI-Kontextkategorie'].strip() not in ('', 'UNKLAR', 'NICHT_AUSGEFUEHRT')]
    pending = len(rows) - len(evaluated)
    matches = sum(r['KI-Kontextkategorie'] == r['Szenario-Erwartung'] for r in evaluated)
    human_verified = sum(r['Menschliche Freigabe'].strip().upper() in {'BESTAETIGT', 'BESTÄTIGT', 'FREIGEGEBEN'} for r in rows)
    return {
        'cases_total': len(rows),
        'cases_evaluated': len(evaluated),
        'matches_with_internal_labels': matches,
        'differences_from_internal_labels': len(evaluated) - matches,
        'cases_pending': pending,
        'human_confirmations_reported': human_verified,
        'source_content_verified': 0,
    }


def run_tests(root: Path) -> dict:
    """Runs repository tests once. Explicitly omits all API credentials from child env."""
    env = os.environ.copy()
    for key in list(env):
        if key.upper().endswith('_API_KEY') or key.upper().endswith('_TOKEN') or key.upper() in {'OPENAI_API_KEY','OPENAI_ORGANIZATION'}:
            env.pop(key, None)
    env['ALI_OFFLINE_ONLY'] = '1'
    try:
        completed = subprocess.run(
            [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-q'],
            cwd=root, env=env, capture_output=True, text=True, timeout=90,
            check=False,
        )
        out = completed.stderr + '\n' + completed.stdout
        import re
        m = re.search(r'Ran (\d+) tests?', out)
        # No 'Ran ...' means failure even if subprocess exited normally.
        success = completed.returncode == 0 and m is not None and int(m.group(1)) > 0
        return {'passed': success, 'tests_run': int(m.group(1)) if m else 0,
                'returncode': completed.returncode, 'diagnostic_excerpt': out[-2500:]}
    except (subprocess.TimeoutExpired, OSError) as exc:
        return {'passed': False, 'tests_run': 0, 'returncode': None,
                'diagnostic_excerpt': type(exc).__name__}


def generate_report(root: Path = ROOT) -> dict:
    cases_path = root / SOURCE_CSV
    test_status = run_tests(root)
    try:
        cases = analyse_cases(cases_path)
        cases_error = None
    except (OSError, ValueError) as exc:
        cases = None
        cases_error = f'{type(exc).__name__}: {exc}'
    publishable = bool(test_status['passed'] and cases is not None)
    result = {
        'version': '1.7',
        'created_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'mode': 'offline_local_development',
        'technical_gate_passed': publishable,
        'scientific_validation': False,
        'model_updated': False,
        'api_calls_executed': 0,
        'code_changed_automatically': False,
        'manual_release_required': True,
        'tests': test_status,
        'synthetic_context_cases': cases,
        'case_loading_error': cases_error,
    }
    report_path = root / OUTPUT_HTML
    report_path.parent.mkdir(parents=True, exist_ok=True)
    (root / OUTPUT_JSON).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    status = 'Technische Offline-Pruefung BESTANDEN' if publishable else 'Technische Offline-Pruefung NICHT BESTANDEN'
    if cases:
        s = (f"{cases['cases_evaluated']} von {cases['cases_total']} KI-Faellen bewertet; "
             f"{cases['matches_with_internal_labels']} Uebereinstimmungen, "
             f"{cases['differences_from_internal_labels']} Abweichungen, "
             f"{cases['cases_pending']} noch offen. "
             f"Menschlich freigegeben: {cases['human_confirmations_reported']}.")
    else:
        s = 'Falldaten nicht verfuegbar: ' + str(cases_error)
    esc = html.escape
    doc = f"""<!doctype html><html lang="de"><head><meta charset="utf-8"><title>ALL-LIFE INTELLIGENCE – Automatische Qualitaetspruefung 1.7</title>
    <style>body{{font:16px/1.6 system-ui,Arial;max-width:850px;margin:35px auto;padding:0 20px;background:#f1f4f8;color:#233}}section{{background:white;padding:24px;margin:18px 0;border-radius:12px}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px}}</style></head><body>
    <h1>ALL-LIFE INTELLIGENCE – Offline-Qualitaetspruefung 1.7</h1>
    <section><h2>{esc(status)}</h2><p>{test_status['tests_run']} Python-Softwaretests ausgefuehrt. Keine kostenpflichtigen API-Abfragen.</p><p>{esc(s)}</p></section>
    <section><h2>Methodische Grenzen</h2><p>Die Szenarien und Labels wurden intern entworfen. Eine Uebereinstimmung ist keine wissenschaftliche Validierung. Aus der Datei wurden keine Originalquellen semantisch bestaetigt. Das Programm hat weder seine Regeln noch sein KI-Modell selbst geaendert.</p><p>Berichte und vorhandene menschliche Freigaben wurden nicht ueberschrieben. Fuer produktive Freigaben und kostenpflichtige Arbeit ist weiterhin eine menschliche Entscheidung erforderlich.</p></section>
    <section><h2>Technische Testdiagnose</h2><pre>{esc(test_status['diagnostic_excerpt'])}</pre></section></body></html>"""
    report_path.write_text(doc, encoding='utf-8')
    return result


if __name__ == '__main__':
    result = generate_report()
    print('Ergebnis:', 'TECHNISCH BESTANDEN' if result['technical_gate_passed'] else 'NICHT BESTANDEN')
    print('Tests:', result['tests']['tests_run'])
    print('Bericht:', ROOT / OUTPUT_HTML)
    sys.exit(0 if result['technical_gate_passed'] else 1)
