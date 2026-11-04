#!/usr/bin/env python3
"""ALL-LIFE INTELLIGENCE v1.3: Offline-Verbesserungsvorschlaege aus einem Referenzset.

Kein KI-Aufruf, kein Internet, kein autonomes Umschreiben, keine Freigabe.
Das mitgelieferte Referenzset enthaelt KI-Vorbewertungen, KEINE validierte Wahrheit.
"""
from __future__ import annotations
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import html
import json
import re
from pathlib import Path
import webbrowser

ROOT = Path(__file__).resolve().parent
EXAMPLE = ROOT / 'evaluation' / 'BEISPIEL_Prueffaelle_25_KI_Vorpruefung.csv'
OUT = ROOT / 'reports'
LABEL_COL = 'KI-Vorpruefung (keine menschliche Freigabe)'
MANUAL_COL = 'Menschliche Bewertung (OFFEN / GESTUETZT / NICHT_GESTUETZT / UNKLAR)'
REFERENCE = {
    'META_KEINE_SACHBEHAUPTUNG':'META',
    'METHODISCHES_URTEIL':'METHODE',
    'ZU_WEITREICHENDE_ABSENZBEHAUPTUNG':'PAUSCHALE_ABSENZ',
    'FALSCHER_ANWENDUNGSBEREICH':'DOMAENENFEHLER',
}
ISSUES = ('META','METHODE','PAUSCHALE_ABSENZ','DOMAENENFEHLER')
PROPOSALS = [
  {'id':'V13-01','prioritaet':'P1','titel':'Pauschale Abwesenheitsbehauptungen markieren',
   'praezisierung':'Formulierungen wie „Keine Quelle belegt ...“ als unzulässig weitreichend markieren. Stattdessen: „Die geprüften Quellen liefern keinen solchen Nachweis.“',
   'test':'Vier Fälle (KOORDINATOR, S01–S04) und neue Negativbeispiele mit legitimen begrenzten Aussagen.',
   'umsetzung':'Nur Warnhinweis; Originalaussage und Quellen nicht automatisch korrigieren.'},
  {'id':'V13-02','prioritaet':'P1','titel':'Methodische Urteile von Zitierbehauptungen trennen',
   'praezisierung':'„Normative Leitlinien ≠ Wirksamkeitsnachweis“ als methodische Bewertung statt als angebliches direktes Zitat kennzeichnen.',
   'test':'Zwei A6-Fälle und unabhängige Sätze ohne Zitierverweis.',
   'umsetzung':'Textstellenvergleich für reine Methodenaussagen nicht als Belegentscheidung anzeigen.'},
  {'id':'V13-03','prioritaet':'P1','titel':'Quellen und Themenbereiche getrennt halten',
   'praezisierung':'Die KI-Bewusstseinsarbeit S04 darf nicht als fachlicher Beleg für allgemeine Tierleid- oder Tierempfindungsmessung erscheinen.',
   'test':'S04-Anwendungsbereich plus Kontrollfälle über KI-Bewusstseinsindikatoren.',
   'umsetzung':'Domänenwarnung; keine automatische inhaltliche Ablehnung.'},
  {'id':'V13-04','prioritaet':'P2','titel':'Meta-Angaben von Sachbehauptungen abtrennen',
   'praezisierung':'Reine Aufzählungen wie „Existente IDs: [S01]...“ sollen nicht in den wissenschaftlichen Belegzähler eingehen.',
   'test':'Vier A6-Metazeilen; negative Fälle mit echten Sachbehauptungen.',
   'umsetzung':'Metadaten weiterhin im Bericht dokumentieren, separat zählen.'},
  {'id':'V13-05','prioritaet':'P2','titel':'Teilunterstützung statt pauschale Vollbestätigung prüfen',
   'praezisierung':'Mehrfachzitierte oder zusammengesetzte Aussagen nach Quellen und Aussagebestandteilen trennen; starke und schwache Unterstützung offen lassen.',
   'test':'Fünf teilweise gestützte Fälle gegen neun vorläufig gestützte Fälle.',
   'umsetzung':'Manuelle Belegprüfung priorisieren, keine wissenschaftliche Freigabe.'},
  {'id':'V13-06','prioritaet':'P2','titel':'Externe Qualitätsprüfung vorbereiten',
   'praezisierung':'Unabhängige menschlich geprüfte Referenzfälle und neue unbekannte Fälle sammeln. Erst dann Übertragbarkeit messen.',
   'test':'Getrennter, nicht zur Regelerstellung verwendeter Datensatz von mindestens 20 zusätzlichen Fällen als erster Pilot.',
   'umsetzung':'Nur menschlich freigegebene Labels als Goldstandard verwenden.'},
]


def load_rows(path: Path) -> list[dict[str,str]]:
    if path.stat().st_size > 2_000_000:
        raise ValueError('Prüfdatei zu groß (maximal 2 MB).')
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        rows=list(csv.DictReader(f, delimiter=';'))
    needed={'Fall-ID', 'KI-Rolle', 'Quellen-ID', 'Aussage',
            'Automatischer Suchstatus', LABEL_COL, MANUAL_COL}
    if not rows or not needed.issubset(rows[0]):
        raise ValueError('CSV enthält nicht alle erforderlichen Spalten oder ist leer.')
    ids=[r['Fall-ID'] for r in rows]
    if len(ids)!=len(set(ids)) or any(not x.strip() for x in ids):
        raise ValueError('Fall-IDs müssen eindeutig und nicht leer sein.')
    return rows


def baseline_issue(row:dict[str,str]) -> str:
    if row['Automatischer Suchstatus'] == 'METAAUSSAGE_KEIN_INHALTSBELEG':
        return 'META'
    return 'KEIN_SPEZIELLER_HINWEIS'


def proposed_issue(row:dict[str,str]) -> str:
    """Deterministische Hinweise, KEINE Tatsachenklassifikation.

    Liest NIE das Feld 'KI-Vorpruefung' oder die menschliche Bewertung.
    """
    statement = row['Aussage']
    norm = re.sub(r'\s+', ' ', statement.casefold())
    if row['Automatischer Suchstatus'] == 'METAAUSSAGE_KEIN_INHALTSBELEG' or re.search(r'\bexistente ids\s*:', norm):
        return 'META'
    if 'keine quelle belegt' in norm or 'keine quellen belegen' in norm:
        return 'PAUSCHALE_ABSENZ'
    if ('normen liefern' in norm and 'nicht' in norm) or ('normative leitprinzipien' in norm and 'falsche ableitung' in norm):
        return 'METHODE'
    if row['Quellen-ID'] == 'S04' and ('messbarkeit von empfindungsfähigkeit' in norm or
                                       'tierleid' in norm or 'tierliche empfindungsfähigkeit' in norm):
        return 'DOMAENENFEHLER'
    return 'KEIN_SPEZIELLER_HINWEIS'


def classify_coverage(rows:list[dict[str,str]]) -> dict:
    detail=[]
    for row in rows:
        reference=REFERENCE.get(row[LABEL_COL], 'KEIN_SPEZIELLER_HINWEIS')
        old, new=baseline_issue(row),proposed_issue(row)
        detail.append({'fall_id':row['Fall-ID'],'rolle':row['KI-Rolle'],'quelle':row['Quellen-ID'],
                       'referenz_ki_vorpruefung':row[LABEL_COL], 'belegpruefung':'NICHT_VERIFIZIERT',
                       'menschliche_freigabe': row[MANUAL_COL], 'baseline':old,
                       'regelhinweis_v13':new, 'referenz_hinweis':reference,
                       'vergleich':('REFERENZ_HINWEIS_GETROFFEN' if reference in ISSUES and new==reference
                                   else 'REFERENZ_HINWEIS_VERFEHLT' if reference in ISSUES
                                   else 'ZUSATZHINWEIS_PRUEFEN' if new in ISSUES
                                   else 'KEIN_KRITISCHER_REFERENZFALL')})
    positive=[d for d in detail if d['referenz_hinweis'] in ISSUES]
    base_hits=sum(d['baseline']==d['referenz_hinweis'] for d in positive)
    new_hits=sum(d['regelhinweis_v13']==d['referenz_hinweis'] for d in positive)
    added=sum(d['regelhinweis_v13'] in ISSUES for d in detail if d['referenz_hinweis'] not in ISSUES)
    return {'gesamte_faelle':len(detail), 'vorlaeufige_referenzhinweise':len(positive),
            'baseline_wiedergefunden':base_hits,'regelvorschlag_wiedergefunden':new_hits,
            'neue_hinweise_ausserhalb_referenz':added,
            'labelverteilung':dict(Counter(r[LABEL_COL] for r in rows)),
            'hinweisverteilung':dict(Counter(d['regelhinweis_v13'] for d in detail)),
            'detail':detail, 'wissenschaftliche_belege_automatisch_bestaetigt':0,
            'menschliche_freigaben_vom_programm':0,
            'limitation':'GLEICHE_25_FAELLE_WIE_REGELENTWICKLUNG; KI-VORPRUEFUNG_KEIN_GOLDSTANDARD'}


def prevent_excel_formula(value:str) -> str:
    value=str(value)
    return "'"+value if re.match(r'^\s*[=+@\-\t\r]', value) else value


def esc(v): return html.escape(str(v),quote=True)


def build_html(stats:dict) -> str:
    lines=[]
    for d in stats['detail']:
        lines.append('<tr>'+''.join('<td>'+esc(d[col])+'</td>' for col in
            ('fall_id','rolle','quelle','referenz_ki_vorpruefung','baseline','regelhinweis_v13','vergleich'))+'</tr>')
    proposals=[]
    for p in PROPOSALS:
        proposals.append('<tr><td>'+esc(p['id'])+'</td><td>'+esc(p['prioritaet'])+'</td><td>'+esc(p['titel'])+'</td><td>'+esc(p['praezisierung'])+'</td><td>'+esc(p['test'])+'</td></tr>')
    total=stats['vorlaeufige_referenzhinweise']; old=stats['baseline_wiedergefunden']; new=stats['regelvorschlag_wiedergefunden']
    return f'''<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ALL-LIFE INTELLIGENCE – Verbesserungsanalyse 1.3</title>
<style>body{{font:15px/1.56 system-ui,Arial,sans-serif;max-width:1140px;margin:25px auto;padding:0 20px;background:#eef2f6;color:#152439}}
header,section{{background:white;border:1px solid #dbe3ec;border-radius:12px;padding:20px 24px;margin:14px 0}}
table{{border-collapse:collapse;width:100%;font-size:12px}}td,th{{padding:8px;border:1px solid #dee5ed;text-align:left;vertical-align:top}}th{{background:#eaf1f7}}
.note{{background:#fff3d5;padding:13px;border-left:4px solid #b8791c}}.numbers{{display:flex;gap:14px;flex-wrap:wrap}}
.metric{{flex:1;min-width:160px;border:1px solid #d9e3ea;padding:13px;border-radius:8px}}.metric strong{{display:block;font-size:28px}}
.scroll{{overflow-x:auto}}a{{color:#165985}}</style></head><body>
<header><h1>ALL-LIFE INTELLIGENCE – Verbesserungsanalyse 1.3</h1><p>Offline-Regressionstest mit 25 KI-vorbewerteten Quellen-Aussage-Paaren.</p>
<p class="note"><b>Keine wissenschaftliche Validierung und keine automatische Freigabe.</b>
Die vorläufigen Labels stammen aus einer früheren KI-Auswertung; sie sind nicht von unabhängigen Menschen bestätigt.
Die Erkennungsregeln wurden nach Kenntnis dieser 25 Fälle entwickelt. Das Ergebnis ist daher <b>kein unabhängiger Leistungstest</b>.
Das Programm verändert weder sein Modell noch seinen Programmcode.</p></header>
<section><h2>Technischer Vergleich (nur Wiedererkennung früherer Hinweise)</h2>
<div class="numbers"><div class="metric"><strong>{stats['gesamte_faelle']}</strong>Untersuchte Fälle</div>
<div class="metric"><strong>{total}</strong>Vorläufige kritische Hinweise</div>
<div class="metric"><strong>{old}/{total}</strong>Bisherige formale Hinweise</div>
<div class="metric"><strong>{new}/{total}</strong>Neue, regelbasierte Hinweise</div></div>
<p>Zusätzliche Warnhinweise ausserhalb der früheren kritischen Kategorien: {stats['neue_hinweise_ausserhalb_referenz']}. 
Eine höhere Wiedererkennung in denselben Beispielen beweist keine Übertragbarkeit auf neue Fälle.
Quellen inhaltlich automatisch bestätigt: <b>0</b>. Menschliche Freigaben durch die Software: <b>0</b>.</p></section>
<section><h2>Vorgeschlagene Verbesserungen – NICHT ANGEWENDET</h2><div class="scroll">
<table><thead><tr><th>ID</th><th>Priorität</th><th>Verbesserung</th><th>Verfahren</th><th>Nächster Test</th></tr></thead><tbody>{''.join(proposals)}</tbody></table></div></section>
<section><h2>Fallweiser Vergleich</h2><div class="scroll"><table><thead><tr><th>Fall-ID</th><th>Rolle</th><th>Quelle</th><th>Vorläufiges KI-Label</th><th>v1.2</th><th>Regelvorschlag 1.3</th><th>Status</th></tr></thead><tbody>{''.join(lines)}</tbody></table></div></section>
<section><h2>Nächste Entwicklungsentscheidung</h2><p>Erst weitere Fälle unabhängig prüfen lassen, danach Verbesserungen an einer separaten Testversion umsetzen und auf neuen Beispielen testen.
Über die Übernahme der Änderungen entscheidet ein Mensch. Das Programm führt keine Codeänderungen, Zahlungen, Veröffentlichungen oder eigenständigen Webaktionen aus.</p></section></body></html>'''


def write_results(rows:list[dict[str,str]], dest:Path) -> dict:
    stats=classify_coverage(rows)
    dest.mkdir(parents=True,exist_ok=True)
    # Diese Dateinamen sind absichtlich eigenständig; vorherige Reports und Prüflisten bleiben unberührt.
    (dest/'VERBESSERUNGSANALYSE.html').write_text(build_html(stats),encoding='utf-8')
    (dest/'VERBESSERUNGSVORSCHLAEGE.json').write_text(json.dumps({
        'version':'1.3','status':'NICHT_FREIGEGEBEN','vorschlaege':PROPOSALS,
        'auswertung':{k:v for k,v in stats.items() if k!='detail'},
    },ensure_ascii=False,indent=2),encoding='utf-8')
    with (dest/'VERGLEICH_25_FAELLE.csv').open('w',encoding='utf-8-sig',newline='') as f:
        cols=list(stats['detail'][0])
        writer=csv.DictWriter(f,fieldnames=cols,delimiter=';',lineterminator='\n')
        writer.writeheader()
        for item in stats['detail']:
            writer.writerow({k:prevent_excel_formula(v) for k,v in item.items()})
    plan='''# ALL-LIFE INTELLIGENCE – Verbesserungsplan 1.3\n\n**Status: Vorschläge – keine Freigabe, keine autonomen Änderungen.**\n\nDer Bericht in `VERBESSERUNGSANALYSE.html` benutzt 25 bereits bekannte Fälle und eine frühere **KI-Vorprüfung**. Er enthält keine wissenschaftlich bestätigten Labels und darf nicht als unabhängiger Benchmark bezeichnet werden.\n\n'''
    for p in PROPOSALS:
        plan+=f"## {p['id']} – {p['titel']}\n\nPriorität: {p['prioritaet']}\n\n{p['praezisierung']}\n\n**Überprüfung:** {p['test']}\n\n**Umsetzung:** {p['umsetzung']}\n\n"
    plan+='''## Freigaberegel\n\nEine Regel darf nur nach manueller Kontrolle an einem **neuen**, nicht zur Entwicklung verwendeten Testdatensatz übernommen werden.\nDer Quellenauszug ist keine semantische Bestätigung. Ohne menschlichen Prüfer bleibt die Quellenbewertung OFFEN.\n'''
    (dest/'ENTWICKLUNGSPLAN.md').write_text(plan,encoding='utf-8')
    return stats


def cli(argv=None) -> int:
    parser=argparse.ArgumentParser(description='ALL-LIFE INTELLIGENCE: Offline-Verbesserungsanalyse – keine API-Kosten')
    parser.add_argument('--input',type=Path,default=EXAMPLE)
    parser.add_argument('--out',type=Path,default=OUT)
    parser.add_argument('--open',action='store_true')
    args=parser.parse_args(argv)
    try:
        rows=load_rows(args.input)
        stats=write_results(rows,args.out)
    except (OSError, UnicodeError, ValueError, csv.Error) as err:
        print('Fehler:',err)
        return 1
    print(f"Fälle: {stats['gesamte_faelle']} | Kritische KI-Vorhinweise: {stats['vorlaeufige_referenzhinweise']}")
    print(f"v1.2 wiedergefunden: {stats['baseline_wiedergefunden']} | v1.3-Regelvorschlag: {stats['regelvorschlag_wiedergefunden']}")
    print('Keine wissenschaftliche Validierung; menschliche Freigabe bleibt OFFEN.')
    print('Ergebnis:',args.out/'VERBESSERUNGSANALYSE.html')
    if args.open:
        webbrowser.open((args.out/'VERBESSERUNGSANALYSE.html').resolve().as_uri())
    return 0

if __name__ == '__main__':
    raise SystemExit(cli())
