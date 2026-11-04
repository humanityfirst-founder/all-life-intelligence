#!/usr/bin/env python3
"""Offline-Qualitätsbilanz aus bereits vorhandenen Prüfergebnissen.

Keine externe Anfrage, keine semantische Verifikation, keine autonome Freigabe.
CSV ist eine manuelle Arbeitsliste, nicht ein Beleg- oder Wahrheitsdatensatz.
"""
from __future__ import annotations
from collections import Counter
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import re
import shutil
import webbrowser

BASE = Path(__file__).resolve().parent
REPORT_PATH = BASE / 'reports' / 'letzter_bericht.json'


def safe_for_spreadsheet(value: object) -> str:
    """CSV-Formel-Injektion bei Modelltext/Quellentext entschärfen."""
    value = str(value if value is not None else '')
    # Excel interpretiert je nach Import auch Formeln nach initialem Whitespace.
    if re.match(r'^\s*[=+@\-\t\r]', value):
        return "'" + value
    return value


def build_overview(report: dict) -> dict:
    check = report.get('source_checks')
    if not isinstance(check, dict) or 'claims' not in check:
        raise ValueError('Keine vorherige Online-Quellenprüfung in der JSON-Datei enthalten.')
    claims = check.get('claims', [])
    sources = check.get('sources', [])
    flags = report.get('study_protocol_gate', {}).get('flags', [])
    counts = Counter(i.get('status', 'UNBEKANNT') for i in claims)
    by_issue = Counter(i.get('code', 'UNBEKANNT') for i in flags)
    return {
        'origin': report.get('application', '?'),
        'created_utc': report.get('created_utc', ''),
        'source_check_version': check.get('checker_version', 'unbekannt'),
        'quality_check_version': report.get('quality_check_version', 'unbekannt'),
        'sources_retrieved': sum(x.get('status') == 'HTML_ABGERUFEN_TEXTAUSZUG' for x in sources),
        'sources_total': len(sources),
        'claim_source_pairs': len(claims),
        'candidate_passages': sum('THEMATISCH_PASSENDE' in i.get('status','') for i in claims),
        'weak_passages': sum('SCHWACHER' in i.get('status','') for i in claims),
        'not_found': sum('KEINE_PASSENDE' in i.get('status','') for i in claims),
        'other_unverified': len(claims) - sum('THEMATISCH_PASSENDE' in i.get('status','') or 'SCHWACHER' in i.get('status','') or 'KEINE_PASSENDE' in i.get('status','') for i in claims),
        'flags_total': len(flags),
        'flags_by_type': dict(by_issue),
        'statuses': dict(counts),
        'content_verified_automatically': 0,
        'manual_approval': False,
        'latest_check_utc': check.get('checked_at_utc', ''),
    }


def make_html(overview: dict, report: dict) -> str:
    esc = lambda x: html.escape(str(x), quote=True)
    gate = report.get('study_protocol_gate', {})
    flags = gate.get('flags', [])
    flagrows = ''.join('<tr><td>' + esc(f.get('role', '')) + '</td><td>' + esc(f.get('code', '')) +
                       '</td><td>' + esc(f.get('issue', '')) + '</td><td>' + esc(f.get('action', '')) + '</td></tr>' for f in flags)
    if not flagrows: flagrows = '<tr><td colspan="4">Keine automatischen Treffer. Das ist keine Freigabe.</td></tr>'
    counts = ''.join('<tr><td>' + esc(k) + '</td><td>' + esc(v) + '</td></tr>' for k, v in sorted(overview['statuses'].items()))
    css = '''body{font:16px/1.6 system-ui,Arial,sans-serif;max-width:980px;margin:20px auto;padding:0 16px;color:#172b44;background:#f0f4f8}
    section,header{background:white;border:1px solid #d6e1ea;border-radius:12px;padding:18px 23px;margin:14px 0}
    table{width:100%;border-collapse:collapse;font-size:.9rem}th,td{border:1px solid #dce5ed;padding:9px;text-align:left;vertical-align:top}
    th{background:#edf3f8}.alert{border-left:4px solid #c57d2e;padding:12px;background:#fff6e6}
    .muted{color:#52677a}.grid{display:flex;gap:10px;flex-wrap:wrap}.metric{border:1px solid #dce5ed;border-radius:8px;padding:12px;flex:1;min-width:150px}
    .num{font-size:1.6rem;font-weight:700}.scroll{overflow-x:auto}'''
    return f'''<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>ALL-LIFE INTELLIGENCE – Qualitätsbilanz v1.2</title><style>{css}</style></head><body>
    <header><h1>ALL-LIFE INTELLIGENCE – Qualitätsbilanz 1.2</h1>
    <p class="muted">Ursprüngliche Forschung: {esc(overview['origin'])} · Quellencheck: {esc(overview['source_check_version'])} · Methodenprüfung: {esc(overview['quality_check_version'])}</p>
    <p class="alert"><b>Keine wissenschaftliche Freigabe!</b> Diese Bilanz zählt maschinelle Suchtreffer und Warnungen. 
    Eine thematisch passende Textstelle ist kein Beleg; ein fehlender Treffer kein Gegenbeweis. Null automatisch bestätigte Aussagen bedeutet nicht, dass die Aussagen falsch sind.</p></header>
    <section><h2>Überblick</h2><div class="grid">
      <div class="metric"><div class="num">{overview['sources_retrieved']}/{overview['sources_total']}</div><div>Originalseiten abgerufen</div></div>
      <div class="metric"><div class="num">{overview['claim_source_pairs']}</div><div>Quelle–Aussage-Paare untersucht</div></div>
      <div class="metric"><div class="num">{overview['candidate_passages']}</div><div>Thematisch passende Textstellen (unbestätigt)</div></div>
      <div class="metric"><div class="num">{overview['flags_total']}</div><div>Methodische Warnungen</div></div>
    </div><p><b>Inhaltlich automatisch verifiziert: 0.</b> Eine korrekte Quellenzuordnung oder statistische Studie wurde durch diese Software nicht bewiesen.</p></section>
    <section><h2>Ergebnisse der Textsuche</h2><p>Die Kategorien beschreiben ausschliesslich den Suchalgorithmus.</p>
    <table><thead><tr><th>Kategorie</th><th>Anzahl</th></tr></thead><tbody>{counts}</tbody></table></section>
    <section><h2>Methodische Warnungen – offene Prüfaufträge</h2><div class="scroll"><table><thead><tr><th>Rolle</th><th>Regel</th><th>Problem</th><th>Nächster überprüfbarer Schritt</th></tr></thead><tbody>{flagrows}</tbody></table></div></section>
    <section><h2>Wie wir daraus lernen können</h2><p>Die beiliegende <a href="PRUEFLISTE.csv">PRUEFLISTE.csv</a> enthält jede Quelle–Aussage-Kombination samt Status und Originaltextauszug. Die Spalten für menschliche Bewertung sind absichtlich leer.
    Eine Person kann prüfen und dokumentieren, ob die Fundstelle eine bestimmte Aussage tatsächlich trägt. Nur diese dokumentierte Prüfung ermöglicht später einen belastbaren Qualitätsvergleich.</p>
    <p><b>Keine automatische Selbstveränderung:</b> Das Programm verändert weder sein Sprachmodell noch seine Sicherheitsregeln selbstständig. Es macht offene Aufgaben sichtbar und reproduzierbar.</p></section>
    </body></html>'''


def write_exports(report: dict, target: Path, *, backup_existing: bool = True) -> tuple[Path, Path]:
    overview = build_overview(report)
    target.mkdir(parents=True, exist_ok=True)
    rows = []
    check = report['source_checks']
    urls = {s.get('id'):s.get('url','') for s in check.get('sources',[])}
    for i in check.get('claims',[]):
        role, sid, statement = (str(i.get(k, '')) for k in ('role','source_id','statement'))
        # Stable between repeated checks if the underlying model statement is unchanged.
        item_id = hashlib.sha256((role+'\x00'+sid+'\x00'+statement).encode('utf-8')).hexdigest()[:14]
        rows.append([item_id, role, sid, i.get('status',''), statement,
                     i.get('passage',''), urls.get(sid,''), i.get('warning',''),
                     'OFFEN', '', '', ''])
    csv_path = target / 'PRUEFLISTE.csv'
    if csv_path.exists() and backup_existing:
        archive = target / 'archiv'
        archive.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')
        shutil.copy2(csv_path, archive / ('PRUEFLISTE_vor_erneuter_Pruefung_'+stamp+'.csv'))
    with csv_path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f, delimiter=';', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['Fall-ID','KI-Rolle','Quellen-ID','Automatischer Suchstatus','Aussage',
                         'Originaltextauszug','Original-URL','Automatische Warnung',
                         'Menschliche Bewertung (OFFEN / GESTUETZT / NICHT_GESTUETZT / UNKLAR)',
                         'Pruefer','Datum','Notizen'])
        for row in rows:
            writer.writerow([safe_for_spreadsheet(x) for x in row])
    html_path = target / 'QUALITAETSBILANZ.html'
    html_path.write_text(make_html(overview, report),encoding='utf-8')
    overview_path = target / 'qualitaetskennzahlen.json'
    overview_path.write_text(json.dumps(overview,ensure_ascii=False,indent=2),encoding='utf-8')
    return html_path,csv_path


def cli(argv=None):
    p=argparse.ArgumentParser(description='Offline: Qualitätsbilanz und manuelle Prüfliste aus vorhandenem Bericht erstellen')
    p.add_argument('--report',type=Path,default=REPORT_PATH)
    p.add_argument('--open',action='store_true')
    args=p.parse_args(argv)
    if not args.report.is_file():
        print('Forschungsbericht fehlt:',args.report)
        return 2
    try:
        report=json.loads(args.report.read_text(encoding='utf-8'))
        paths=write_exports(report,args.report.parent)
    except (ValueError,OSError,KeyError,TypeError) as exc:
        print('Keine Bilanz erstellt:',exc)
        return 2
    print('Qualitaetsbilanz:',paths[0])
    print('Manuelle Pruefliste:',paths[1])
    print('Keine Quellenabrufe und keine API-Kosten.')
    if args.open: webbrowser.open(paths[0].resolve().as_uri())
    return 0

if __name__=='__main__':
    raise SystemExit(cli())
