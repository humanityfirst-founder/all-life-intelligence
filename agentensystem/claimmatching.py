#!/usr/bin/env python3
"""Konservative, quellenspezifische Recherchehilfe (v1.2).

Keine semantische Wahrheitsprüfung; nur kurze zitierte Einzelaussagen und
passende Originalstellen zur unabhängigen inhaltlichen Nachprüfung vorbereiten.
"""
from __future__ import annotations
import re

REF = re.compile(r'\[(S\d{2,})\]')
SEP = re.compile(r'(?<=\])\s*[;.!?]\s+(?=[A-ZÄÖÜ])')
SKIP_META = re.compile(r'^\s*(?:existente\s+(?:quellen.?ids|ids)|erwähnte\s+(?:quellen.?ids|ids)|id[- ]audit|(?:es\s+gibt\s+)?gültige\s+ids)\s*:', re.I)
# Kleine Liste von *Recherchebegriffen*, keine Bedeutungs- oder Wahrheitsontologie.
GROUPS = [
    (('menschenrecht','human right'), ('human rights',)),
    (('demokrat','democra'), ('democratic', 'democracy')),
    (('transparen','transparen'), ('transparen',)),
    (('rechenschaft','accountab'), ('accountab',)),
    (('risikomanagement','risk management'), ('risk management',)),
    (('risik','risk'), ('risk',)),
    (('robust','robust'), ('robust',)),
    (('umwelt','environment'), ('environment', 'ecosystem', 'ecological')),
    (('ökosystem','ecosystem'), ('ecosystem',)),
    (('ethik','ethical','ethics'), ('ethic',)),
    (('bewusst','conscious'), ('conscious',)),
    (('indikator','indicator'), ('indicator',)),
    (('theorie','theor'), ('theor',)),
    (('aufsicht','oversight'), ('oversight',)),
    (('tierwohl','animal welfare'), ('animal welfare',)),
    (('tierleid','animal suffering'), ('animal welfare', 'animal suffering')),
    (('freiheit','freedom'), ('freedom', 'freedoms')),
    (('bewert','assessment'), ('assess',)),
    (('kontroll','control'), ('control',)),
    (('govern',), ('govern',)),
    (('manage',), ('manage',)),
    (('measure',), ('measure',)),
    (('audit',), ('audit',)),
]


def split_claims(statement: str, source_ids: list[str]) -> list[dict]:
    """Citation-nahe Teilaussagen; Aussagen ohne örtlich zuordenbares Zitat bleiben ungeklärt."""
    if SKIP_META.search(statement):
        return [{'statement': statement, 'source_ids':source_ids, 'kind':'META'}]
    parts = SEP.split(statement)
    if len(parts) <= 1:
        # Auch explizite Satzgrenzen mit [S01]. Der nächste Abschnitt beginnt groß.
        parts = re.split(r'(?<=\])\.\s+(?=[A-ZÄÖÜ])', statement)
    if len(parts) == 1:
        return [{'statement':statement, 'source_ids':source_ids, 'kind':'CLAIM'}]
    result = []
    for part in parts:
        citations = sorted(set(REF.findall(part)))
        if citations:
            result.append({'statement':part.strip(), 'source_ids':citations, 'kind':'CLAIM'})
        elif part.strip():
            result.append({'statement':part.strip(), 'source_ids':[], 'kind':'UNATTRIBUTED'})
    return result


def cue_groups(statement: str) -> list[tuple[str,...]]:
    s = REF.sub('', statement).lower()
    found = []
    for stems, possibilities in GROUPS:
        if any(x in s for x in stems) and possibilities not in found:
            found.append(possibilities)
    return found


def keyword_match(statement: str, blocks: list[str], source_id: str) -> dict:
    """Nur thematische Textsuche; Status ist ausnahmslos KEIN_WAHRHEITSBELEG."""
    cues = cue_groups(statement)
    if not cues:
        return {'status':'KEINE_AUSREICHENDEN_SUCHBEGRIFFE', 'passage':'', 'matched_cues':0, 'total_cues':0,
                'warning':'Für diese Aussage sind keine geeigneten Suchbegriffe hinterlegt; manuelle Volltextprüfung nötig.'}
    # Spezifische dokumentierte Prüfung gegen falsche NIST-Treffer über kritische Infrastruktur:
    requested_nist_functions = source_id == 'S01' and all(w in statement.lower() for w in ('govern','map','measure','manage'))
    best = (0, 0., -999999, '', [])
    for block in blocks:
        lower=block.lower()
        matched=[cue for cue in cues if any(t in lower for t in cue)]
        score=len(matched)
        if score == 0:
            continue
        # Wenn vier RMF-Funktionen behauptet werden, muss die belegende Passage
        # sie auch tatsächlich zusammen enthalten. Sonst NICHT als Themenpassage verwenden.
        if requested_nist_functions and not all(re.search(r'\b'+w+r'\b',lower) for w in ('govern','map','measure','manage')):
            continue
        ratio=score/len(cues)
        rank=(score,ratio,-abs(len(block)-310),block,matched)
        if rank[:3] > best[:3]:
            best=rank
    score,ratio,_,passage,matched=best
    if not passage:
        warning='Die vier Funktionen GOVERN, MAP, MEASURE, MANAGE wurden nicht zusammen in einem Textabschnitt nachgewiesen. NIST-Volltext separat prüfen.' if requested_nist_functions else 'Keine ausreichend passende Original-Textstelle automatisch gefunden; kein Gegenbeweis.'
        return {'status':'KEINE_PASSENDE_TEXTSTELLE_GEFUNDEN','passage':'','matched_cues':0,'total_cues':len(cues),'warning':warning}
    good = score >= 2 and ratio >= .60
    status = 'THEMATISCH_PASSENDE_STELLE_KEIN_BELEG' if good else 'SCHWACHER_STICHWORT_TREFFER_KEIN_BELEG'
    terms=[x for cue in matched for x in cue if x in passage.lower()]
    first=min([passage.lower().find(t) for t in terms] or [0])
    start=max(0,first-70)
    snippet=('…' if start else '') + passage[start:start+320].strip() + ('…' if len(passage)>start+320 else '')
    return {'status':status,'passage':snippet,'matched_cues':score,'total_cues':len(cues),
            'warning':'Themenähnlichkeit ist weder ein inhaltlicher Beleg noch eine Prüfung auf Widersprüche; Original im Kontext lesen.'}
