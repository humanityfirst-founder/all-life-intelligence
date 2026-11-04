#!/usr/bin/env python3
"""Offline v1.5: eingefrorene v1.3-Regel vs. Kandidat v1.5.

Die 25+40 Beispiele WAREN bei der Kandidatenentwicklung bekannt.
Die 24 QA-Fälle sind synthetisch und NICHT unabhängig fachlich gelabelt.
Kein Modelltraining, kein Internet, keine Freigabe oder Codeänderung.
"""
from __future__ import annotations
import argparse
import csv
import html
from pathlib import Path
import webbrowser
from collections import Counter
from improvement_agent import proposed_issue as old_rule, prevent_excel_formula
from improvement_agent import load_rows as read_25, EXAMPLE as PATH25, LABEL_COL, REFERENCE
from robustness_lab import read_scenarios, INPUT as PATH40, EXPECT
from candidate_rules_v15 import candidate_issue

ROOT=Path(__file__).resolve().parent
PATH24=ROOT/'evaluation'/'WEITERE_QA_FAELLE_24.csv'
REPORTS=ROOT/'reports'
ALLOWED={'META','METHODE','PAUSCHALE_ABSENZ','DOMAENENFEHLER','KEIN_SPEZIELLER_HINWEIS'}
FIELDS=['Testgruppe','Test-ID','Rolle','Quellen-ID','Aussage','Szenario-Erwartung','Alte Regel v1.3','Kandidat v1.5','Alt richtig','Kandidat richtig','Menschliche Freigabe','Pruefnotiz']

def load_24(path:Path):
    if path.stat().st_size > 2_000_000: raise ValueError('Datei zu gross.')
    with path.open('r',encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f,delimiter=';'))
    if not rows or not {'Test-ID','KI-Rolle','Quellen-ID','Automatischer Suchstatus','Aussage',EXPECT}.issubset(rows[0]):
        raise ValueError('Neue QA-Testfälle: falsches CSV-Format.')
    ids=[r['Test-ID'] for r in rows]
    if len(ids)!=len(set(ids)) or any(r[EXPECT] not in ALLOWED or not r['Aussage'].strip() for r in rows):
        raise ValueError('Neue QA-Testfälle: ungueltige Zeile oder ID.')
    return rows


def evaluate(path24=PATH24):
    items=[]
    for group,rows in (('25 bekannte KI-vorbewertete Beispiele',read_25(PATH25)),
                       ('40 bekannte synthetische Entwicklungsbeispiele',read_scenarios(PATH40)),
                       ('24 zusaetzliche synthetische QA-Faelle',load_24(path24))):
        for r in rows:
            ref=(REFERENCE.get(r[LABEL_COL],'KEIN_SPEZIELLER_HINWEIS')
                 if group.startswith('25 ') else r[EXPECT])
            old=old_rule(r)
            new=candidate_issue(r)
            items.append({'Testgruppe':group,'Test-ID':r.get('Test-ID',r.get('Fall-ID','')),
                          'Rolle':r['KI-Rolle'],'Quellen-ID':r['Quellen-ID'], 'Aussage':r['Aussage'],
                          'Szenario-Erwartung':ref,'Alte Regel v1.3':old,'Kandidat v1.5':new,
                          'Alt richtig':'JA' if ref==old else 'NEIN',
                          'Kandidat richtig':'JA' if ref==new else 'NEIN',
                          'Menschliche Freigabe':'OFFEN','Pruefnotiz':''})
    summary={}
    for group in dict.fromkeys(r['Testgruppe'] for r in items):
        sub=[r for r in items if r['Testgruppe']==group]
        summary[group]={'gesamt':len(sub),
                        'alt':sum(r['Alt richtig']=='JA' for r in sub),
                        'neu':sum(r['Kandidat richtig']=='JA' for r in sub),
                        'fehler_alt':sum(r['Alt richtig']=='NEIN' for r in sub),
                        'fehler_neu':sum(r['Kandidat richtig']=='NEIN' for r in sub)}
    return {'details':items,'gruppen':summary}


def esc(v):return html.escape(str(v),quote=True)


def render(result):
    groups=''.join(f"<tr><td>{esc(k)}</td><td>{v['gesamt']}</td><td>{v['alt']}/{v['gesamt']}</td><td>{v['neu']}/{v['gesamt']}</td><td>{v['fehler_neu']}</td></tr>" for k,v in result['gruppen'].items())
    misses=[r for r in result['details'] if r['Kandidat richtig']=='NEIN']
    mismatch=''.join('<tr>'+''.join('<td>'+esc(r[f])+'</td>' for f in ('Test-ID','Aussage','Szenario-Erwartung','Kandidat v1.5'))+'</tr>' for r in misses)
    return f'''<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ALL-LIFE INTELLIGENCE – Regelvergleich 1.5</title><style>
body{{font:15px/1.6 system-ui,Arial,sans-serif;max-width:1100px;margin:20px auto;background:#f1f4f8;padding:0 18px;color:#18253a}}
header,section{{background:white;border:1px solid #dbe3eb;border-radius:12px;padding:20px 24px;margin:16px 0}}
table{{width:100%;border-collapse:collapse}}th,td{{border:1px solid #d9e1e9;text-align:left;padding:9px;vertical-align:top}}th{{background:#eef2f7}}
.note{{background:#fff2d5;border-left:5px solid #bd8c2a;padding:12px}}.scroll{{overflow-x:auto}}
</style></head><body><header><h1>ALL-LIFE INTELLIGENCE – Regelvergleich 1.5</h1>
<p class="note"><b>Keine wissenschaftliche Validierung und keine automatische Freigabe.</b> Die 25 und 40 Fälle waren bei der Entwicklung der Version 1.5 bereits bekannt: ein besseres Ergebnis darauf ist daher <b>kein Nachweis einer Generalisierung</b>.
Die zusätzlichen 24 Beispiele sind ebenfalls synthetisch und intern definiert; ihre erwarteten Kategorien wurden nicht unabhängig bestätigt.
Kein KI-Modelltraining, keine Internetabfragen, keine autonomen Änderungen.</p></header>
<section><h2>Vergleich mit Testvorgaben</h2><div class="scroll"><table><thead><tr><th>Gruppe</th><th>Fälle</th><th>Regel v1.3</th><th>Kandidat v1.5</th><th>Abweichungen des Kandidaten</th></tr></thead><tbody>{groups}</tbody></table></div>
<p>Die Werte sind <b>Übereinstimmungen mit Testvorgaben</b>, nicht wissenschaftlich verifizierte Genauigkeit, Präzision oder Recall.</p></section>
<section><h2>Offene Abweichungen</h2><div class="scroll"><table><thead><tr><th>ID</th><th>Aussage</th><th>Erwartung des Szenarios</th><th>Prüfregel v1.5</th></tr></thead><tbody>{mismatch or '<tr><td colspan="4">Keine Abweichung in den vorgegebenen Beispielen. Die wissenschaftliche Qualität bleibt trotzdem ungeprüft.</td></tr>'}</tbody></table></div></section>
<section><h2>Weiterentwicklung</h2><p>Die restlichen Abweichungen werden <b>nicht automatisch behoben</b>. Neue, vorher nicht gesehene und von Menschen bewertete Quellen-Aussage-Paare sind für eine belastbare Beurteilung nötig.
Die Dateien <code>REGELVERGLEICH_1_5_FAELLE.csv</code> und <code>MENSCHLICHE_PRUEFUNG_24.csv</code> dokumentieren Einzelprüfungen; das manuelle Bewertungsblatt wird bei erneutem Start nicht überschrieben.</p></section></body></html>'''


def write_result(result,out:Path):
    out.mkdir(parents=True,exist_ok=True)
    (out/'REGELVERGLEICH_1_5.html').write_text(render(result),encoding='utf-8')
    path=out/'REGELVERGLEICH_1_5_FAELLE.csv'
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS,delimiter=';',lineterminator='\n');w.writeheader()
        for item in result['details']:w.writerow({k:prevent_excel_formula(item[k]) for k in FIELDS})
    manual=out/'MENSCHLICHE_PRUEFUNG_24.csv'
    if not manual.exists():
        with manual.open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=FIELDS,delimiter=';',lineterminator='\n');w.writeheader()
            for item in result['details']:
                if item['Testgruppe'].startswith('24 '):
                    w.writerow({k:prevent_excel_formula(item[k]) for k in FIELDS})
    return result


def cli(argv=None):
    ap=argparse.ArgumentParser(description='ALL-LIFE INTELLIGENCE v1.5: Offline-Regelvergleich')
    ap.add_argument('--out',type=Path,default=REPORTS)
    ap.add_argument('--open',action='store_true')
    args=ap.parse_args(argv)
    try: result=write_result(evaluate(),args.out)
    except (ValueError,UnicodeError,OSError,csv.Error) as ex:
        print('Fehler:',ex);return 1
    for group,r in result['gruppen'].items():
        print(group,'-> alt',str(r['alt'])+'/'+str(r['gesamt']),' neu',str(r['neu'])+'/'+str(r['gesamt']))
    print('Keine inhaltliche Belegfreigabe. Menschliche Bewertung OFFEN.')
    if args.open:webbrowser.open((args.out/'REGELVERGLEICH_1_5.html').resolve().as_uri())
    return 0

if __name__=='__main__':raise SystemExit(cli())
