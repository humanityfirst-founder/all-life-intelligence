#!/usr/bin/env python3
"""Diagnose and optionally resume ONLY the missing six QA cases from a v1.6 live report.

No API calls unless --live and explicit 'ja' plus key. At most one charged call,
no automatic retry; previous outputs and human review files are not overwritten.
"""
from __future__ import annotations
import argparse
import csv
import getpass
import json
from pathlib import Path
import webbrowser
from context_review_v16 import (ROOT,OUTPUT,COLS,rows24,INSTRUCTIONS,MODEL,parse_response,
                                payload,evaluate,render)
from agent import call_openai,ApiProblem
from improvement_agent import prevent_excel_formula

SOURCE = OUTPUT/'KONTEXTPRUEFUNG_1_6_FAELLE.csv'
MISSING_MESSAGE = 'API-Fehler oder ungueltige Antwort; keine automatische Wiederholung.'


def load_existing(path=SOURCE):
    with Path(path).open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f,delimiter=';')
        if not reader.fieldnames or set(COLS)-set(reader.fieldnames):
            raise ValueError('Die Eingabedatei hat unerwartete Spalten.')
        records=list(reader)
    examples=rows24()
    if len(records)!=len(examples):
        raise ValueError('Es muessen 24 Originalfaelle vorhanden sein.')
    for before,expected in zip(records,examples):
        if (before['Test-ID']!=expected['Test-ID'] or before['Aussage']!=expected['Aussage'] or
            before['Quellen-ID']!=expected['Quellen-ID']):
            raise ValueError('Originaltexte oder Reihenfolge veraendert: kein Live-Aufruf moeglich.')
    return examples,records


def prepare(rows,prior):
    pending=[];assessments={}
    for i,r in enumerate(prior):
        c=r['KI-Kontextkategorie'];reason=r['KI-Begruendung']
        if c=='UNKLAR' and reason.startswith('API-Fehler'):
            pending.append(i)
        elif c=='NICHT_AUSGEFUEHRT':
            raise ValueError('Bisherige Auswertung nicht gestartet: kein Batch-4-Resume moeglich.')
        else:
            if c not in ('META','METHODE','PAUSCHALE_ABSENZ','DOMAENENFEHLER','KEIN_SPEZIELLER_HINWEIS','UNKLAR'):
                raise ValueError('Unbekannte vorhandene KI-Kategorie.')
            assessments[r['Test-ID']]={'category':c,'stance':r['KI-Sprechakt'],'reason':reason}
    if pending != list(range(18,24)):
        raise ValueError('Nur der konkrete fehlgeschlagene Batch 4 (Faelle 19-24) darf nachgeprueft werden.')
    return assessments,pending


def merge(rows,prior,backend=None,api_key=None):
    """backend=None is an offline preparation. With backend, run only one charged call."""
    assessments, pending=prepare(rows,prior)
    errors=[]
    for i in pending:
        r=prior[i]
        assessments[r['Test-ID']]={'category':r['KI-Kontextkategorie'],
                                   'stance':r['KI-Sprechakt'],'reason':r['KI-Begruendung']}
    if backend is not None:
        if not api_key:
            raise ValueError('API-Schluessel fehlt.')
        try:
            subset=[rows[i] for i in pending]
            result=backend(instructions=INSTRUCTIONS,input_text=payload(subset),model=MODEL,
                           api_key=api_key,max_tokens=3400)
            updated=parse_response(result,[x['Test-ID'] for x in subset])
            assessments.update(updated)
        except (ApiProblem,ValueError,TypeError,json.JSONDecodeError) as exc:
            # Do not log model response content or API key.
            if isinstance(exc,ValueError) and not isinstance(exc,json.JSONDecodeError):
                problem=str(exc)[:100]
            else:
                problem=type(exc).__name__
            errors.append('Nur Batch 4: technische Auswertung fehlgeschlagen; kein erneuter Aufruf. '+problem)
    return evaluate(rows,assessments), errors


def save_only_new(records,errors,output=OUTPUT,mode="offline-Berichtsbereinigung"):
    output=Path(output)
    output.mkdir(parents=True,exist_ok=True)
    out_html=output/'KONTEXTPRUEFUNG_1_6_1.html'
    out_csv=output/'KONTEXTPRUEFUNG_1_6_1_FAELLE.csv'
    out_html.write_text(render(records,mode,errors),encoding='utf-8')
    with out_csv.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=COLS,delimiter=';',lineterminator='\n');w.writeheader()
        for rec in records:w.writerow({key:prevent_excel_formula(rec[key]) for key in COLS})
    # Do not create or overwrite any human approvals.
    return out_html


def cli(argv=None):
    p=argparse.ArgumentParser(description='ALL-LIFE INTELLIGENCE 1.6.1 – Batch-4-Nachpruefung')
    p.add_argument('--live',action='store_true')
    p.add_argument('--source',type=Path,default=SOURCE)
    p.add_argument('--out',type=Path,default=OUTPUT)
    p.add_argument('--open',action='store_true')
    a=p.parse_args(argv)
    try:
        rows,prior=load_existing(a.source)
        _,missing=prepare(rows,prior)
    except (OSError,UnicodeError,ValueError) as e:
        print('Abbruch ohne API-Aufruf:',str(e));return 1
    print('Auswertung: 18 vorhandene KI-Faelle bleiben unveraendert; sechs Faelle aus Batch 4 fehlen.')
    if not a.live:
        recs,errs=merge(rows,prior)
        mode_msg='OFFLINE: ausschliesslich technische Berichtsbereinigung, keine Modellanfrage.'
        html_path=save_only_new(recs,errs,a.out,mode='offline-Berichtsbereinigung')
        print(mode_msg,'\nBericht:',html_path)
        if a.open:webbrowser.open(html_path.resolve().as_uri())
        return 0
    print('OPTIONAL: Genau ein neuer KOSTENPFLICHTIGER API-Aufruf fuer sechs synthetische Faelle.')
    print('Keine Wiederholungen. Alte Bewertungen bleiben erhalten. Kostenhoehe ist nicht garantiert.')
    if input('Kostenpflichtige einmalige Nachpruefung starten? (ja/nein): ').strip().lower()!='ja':
        print('Nicht gestartet: null API-Aufrufe.');return 0
    key=getpass.getpass('OpenAI-API-Schluessel (unsichtbar): ').strip()
    if not key:
        print('Kein Schluessel: null API-Aufrufe.');return 1
    recs,errs=merge(rows,prior,backend=call_openai,api_key=key)
    del key
    html_path=save_only_new(recs,errs,a.out,mode=('Live-Nachpruefung mit Fehler' if errs else 'Live-Nachpruefung'))
    print('Bericht:',html_path)
    print('Keine wissenschaftliche Freigabe und keine Originalquellenverifikation.')
    if errs:
        print('Der eine API-Aufruf konnte nicht ausgewertet werden; keine automatische Wiederholung.');return 1
    if a.open:webbrowser.open(html_path.resolve().as_uri())
    return 0

if __name__=='__main__':raise SystemExit(cli())
