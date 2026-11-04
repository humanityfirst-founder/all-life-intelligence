#!/usr/bin/env python3
"""v1.4: Retrospektiver Robustheitstest auf 40 synthetischen NEUEN Faellen.
Verwendet die UNVERAENDERTEN Heuristiken aus improvement_agent.py (v1.3).
Szenario-Labels sind Testdesign, KEINE verifizierten wissenschaftlichen Wahrheiten.
Keine API, keine Netzwerkanfragen, keine Code-Aenderung, keine Freigaben.
"""
from __future__ import annotations
import argparse
import csv
from collections import Counter
import html
from pathlib import Path
import re
import webbrowser
from improvement_agent import proposed_issue, prevent_excel_formula

ROOT=Path(__file__).resolve().parent
INPUT=ROOT/'evaluation'/'NEUE_SYNTHETISCHE_PRUEFFAELLE_40.csv'
OUTPUT=ROOT/'reports'
EXPECT='Erwarteter Regelhinweis (Szenario, NICHT fachlich validiert)'
MANUAL='Menschliche Bewertung (OFFEN / BESTAETIGT / KORRIGIERT)'
CATEGORIES={'META','METHODE','PAUSCHALE_ABSENZ','DOMAENENFEHLER','KEIN_SPEZIELLER_HINWEIS'}


def read_scenarios(p:Path)->list[dict[str,str]]:
    if p.stat().st_size>2_000_000:
        raise ValueError('Testdatei zu gross (>2 MB).')
    with p.open('r',encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f,delimiter=';'))
    keys={'Test-ID','KI-Rolle','Quellen-ID','Automatischer Suchstatus','Aussage',EXPECT,MANUAL}
    if not rows or not keys.issubset(rows[0]):
        raise ValueError('Testdatei leer oder erforderliche Spalten fehlen.')
    ids=[r['Test-ID'] for r in rows]
    if len(set(ids)) != len(ids) or any(not x.strip() for x in ids):
        raise ValueError('Test-IDs nicht eindeutig oder leer.')
    if any(r[EXPECT] not in CATEGORIES or not r['Aussage'].strip() for r in rows):
        raise ValueError('Ungueltige Erwartung oder leere Aussage.')
    return rows


def evaluate(rows):
    details=[]
    for item in rows:
        # Preserve exactly the v1.3 rule function; no label or annotation passed in.
        prediction=proposed_issue(item)
        exp=item[EXPECT]
        details.append({'Test-ID':item['Test-ID'], 'KI-Rolle':item['KI-Rolle'],
            'Quellen-ID':item['Quellen-ID'],'Aussage':item['Aussage'],
            'Erwartung':exp,'Regel_v1.3':prediction,
            'Ergebnis':'TREFFER_IM_SYNTHETISCHEN_TEST' if exp==prediction else 'ABWEICHUNG',
            'Menschliche Bewertung':'OFFEN','Pruefnotiz':''})
    hits=sum(d['Erwartung']==d['Regel_v1.3'] for d in details)
    unexpected=sum(d['Erwartung']=='KEIN_SPEZIELLER_HINWEIS' and d['Regel_v1.3']!='KEIN_SPEZIELLER_HINWEIS' for d in details)
    missed=sum(d['Erwartung']!='KEIN_SPEZIELLER_HINWEIS' and d['Regel_v1.3']=='KEIN_SPEZIELLER_HINWEIS' for d in details)
    wrongtype=sum(d['Erwartung']!='KEIN_SPEZIELLER_HINWEIS' and d['Regel_v1.3'] not in {'KEIN_SPEZIELLER_HINWEIS',d['Erwartung']} for d in details)
    counts=Counter(d['Erwartung'] for d in details)
    per_type={k:{'gesamt':sum(d['Erwartung']==k for d in details),
        'genau_erkannt':sum(d['Erwartung']==k and d['Regel_v1.3']==k for d in details),
        'falsch_ausgeloest':sum(d['Erwartung']!=k and d['Regel_v1.3']==k for d in details)}
        for k in sorted(CATEGORIES)}
    return {'gesamt':len(details),'szenario_treffer':hits,
        'fehlalarme_gegen_szenario':unexpected,'nicht_erkannt':missed,
        'falsche_warnkategorie':wrongtype,'pro_kategorie':per_type,'details':details}


def esc(v):return html.escape(str(v),quote=True)


def render(result):
    d=result
    summ=''.join('<tr><td>'+esc(k)+'</td><td>'+esc(c['gesamt'])+'</td><td>'+esc(c['genau_erkannt'])+'</td><td>'+esc(c['falsch_ausgeloest'])+'</td></tr>' for k,c in d['pro_kategorie'].items())
    cases=''.join('<tr><td>'+esc(x['Test-ID'])+'</td><td>'+esc(x['Aussage'])+'</td><td>'+esc(x['Quellen-ID'])+'</td><td>'+esc(x['Erwartung'])+'</td><td>'+esc(x['Regel_v1.3'])+'</td><td>'+esc(x['Ergebnis'])+'</td></tr>' for x in d['details'])
    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ALL-LIFE INTELLIGENCE – Robustheitstest 1.4</title><style>
body{{font:15px/1.6 system-ui,Arial;max-width:1160px;margin:auto;padding:20px;background:#eef3f7;color:#142741}}
header,section{{background:white;border:1px solid #dbe3ed;border-radius:12px;padding:20px 24px;margin:14px 0}}
table{{width:100%;border-collapse:collapse;font-size:12px}}td,th{{border:1px solid #dae3eb;text-align:left;vertical-align:top;padding:8px}}th{{background:#eef3f7}}
.note{{background:#fff2d7;padding:12px;border-left:4px solid #bb7918}}.tiles{{display:flex;flex-wrap:wrap;gap:12px}}.tile{{border:1px solid #d5dfe8;padding:12px;min-width:155px;flex:1;border-radius:9px}}strong.num{{font-size:29px;display:block}}.scroll{{overflow-x:auto}}</style></head><body>
<header><h1>ALL-LIFE INTELLIGENCE – Robustheitstest 1.4</h1><p>Unveraenderte v1.3-Warnregeln auf 40 neuen, absichtlich schwierigen Textszenarien.</p>
<p class="note"><b>Kein unabhängiger wissenschaftlicher Benchmark!</b> Die neuen Texte wurden synthetisch nach Kenntnis der alten Prüfregeln erstellt. Die erwarteten Kategorien sind vom Szenarioentwurf vorgegeben, nicht von unabhängigen Fachleuten bestätigt. Weder Originalquellen noch faktische Richtigkeit werden mit diesem Test validiert. Keine automatische Codeänderung oder Freigabe.</p></header>
<section><h2>Ergebnisse des festen Szenariotests</h2><div class="tiles">
<div class="tile"><strong class="num">{d['gesamt']}</strong>Neue Szenarien</div>
<div class="tile"><strong class="num">{d['szenario_treffer']}/{d['gesamt']}</strong>Regel stimmt mit Szenario überein</div>
<div class="tile"><strong class="num">{d['fehlalarme_gegen_szenario']}</strong>Unbegründete Warnungen gemäss Szenario</div>
<div class="tile"><strong class="num">{d['nicht_erkannt']}</strong>Erwartete Warnungen ausgeblieben</div>
<div class="tile"><strong class="num">{d['falsche_warnkategorie']}</strong>Falscher Warnungstyp</div></div>
<p><b>Interpretation:</b> Die Zahlen zeigen Grenzen der regelbasierten Mustererkennung, nicht ihren wissenschaftlichen Wahrheitsgehalt. Ein 11/11-Erfolg auf bekannten Beispielen darf hier nicht als Genauigkeitsprognose verwendet werden.</p></section>
<section><h2>Warnungen je Kategorie</h2><div class="scroll"><table><thead><tr><th>Kategorie</th><th>Szenarien insgesamt</th><th>Passend erkannt</th><th>Falsch ausgelöst</th></tr></thead><tbody>{summ}</tbody></table></div></section>
<section><h2>Alle 40 Testfälle</h2><div class="scroll"><table><thead><tr><th>ID</th><th>Aussage</th><th>Quelle</th><th>Szenario-Erwartung</th><th>Regel 1.3</th><th>Status</th></tr></thead><tbody>{cases}</tbody></table></div></section>
<section><h2>Entwicklungsentscheidung</h2><p>Bei Abweichungen zwischen Regel und Szenario zuerst Fehlalarm oder Lücke dokumentieren, dann zusätzliche Formulierungen sammeln und die Regel in einer separaten neuen Version ändern. Vor produktiver Übernahme neue, <b>menschlich geprüfte</b>, bisher ungesehene Fälle testen. Der Bericht ist kein unabhängiger oder repräsentativer Leistungstest.</p></section></body></html>"""


def export(result,out):
    out.mkdir(parents=True,exist_ok=True)
    (out/'ROBUSTHEITSTEST.html').write_text(render(result),encoding='utf-8')
    p=out/'ROBUSTHEITSTEST_FAELLE.csv'
    cols=list(result['details'][0])
    with p.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=cols,delimiter=';',lineterminator='\n')
        w.writeheader()
        w.writerows({k:prevent_excel_formula(str(v)) for k,v in r.items()} for r in result['details'])
    # Human validation file NEVER overwritten on subsequent runs.
    p=out/'MENSCHLICHE_PRUEFUNG_40_FAELLE.csv'
    if not p.exists():
        with p.open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=cols,delimiter=';',lineterminator='\n')
            w.writeheader()
            w.writerows({k:prevent_excel_formula(str(v)) for k,v in r.items()} for r in result['details'])
    return result


def cli(argv=None):
    ap=argparse.ArgumentParser(description='Offline-Robustheitstest; ohne API und Netzwerkanfragen')
    ap.add_argument('--input',type=Path,default=INPUT)
    ap.add_argument('--out',type=Path,default=OUTPUT)
    ap.add_argument('--open',action='store_true')
    args=ap.parse_args(argv)
    try:
        stats=export(evaluate(read_scenarios(args.input)),args.out)
    except (OSError,ValueError,UnicodeError,csv.Error) as e:
        print('Fehler:',e)
        return 1
    print('Neue Testszenarien:',stats['gesamt'])
    print('Szenarien richtig zugeordnet:',stats['szenario_treffer'])
    print('Fehlalarme nach Szenario:',stats['fehlalarme_gegen_szenario'])
    print('Nicht erkannte Warnungen:',stats['nicht_erkannt'])
    print('Hinweis: keine wissenschaftlich bestaetigten Labels; keine automatisch angewendeten Aenderungen.')
    print('Bericht:',args.out/'ROBUSTHEITSTEST.html')
    if args.open:
        webbrowser.open((args.out/'ROBUSTHEITSTEST.html').resolve().as_uri())
    return 0

if __name__=='__main__':
    raise SystemExit(cli())
