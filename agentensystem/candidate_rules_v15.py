#!/usr/bin/env python3
"""Experimenteller Regelsatz v1.5: Vorschläge, KEINE Quellenbestätigung.

Die Regeln wurden nach Sichtung der 25+40 Fälle entwickelt. Daher zeigen
Vergleiche mit diesen Fällen NUR Passung an bekannte Entwicklungsbeispiele.
Keine automatische Modell-/Codeänderung. Keine Netzwerkzugriffe.
"""
from __future__ import annotations
import re

NONE = 'KEIN_SPEZIELLER_HINWEIS'

# Sprachliche Varianten; die Erkennung bleibt heuristisch, keine Semantik-Garantie.
_META_HEAD = re.compile(r'^\s*(?:existente\s+ids|vorhandene\s+quellen\s*[- ]?ids|aufgelistete\s+belegkennungen|quellen[üu]bersicht)\s*:', re.I)
_SOURCE = re.compile(r'(?:\[\s*S\d{2}(?:\s*[–-]\s*S?\d{2})?\s*\]|\bS\d{2}\b)',re.I)
_ABSENCE = (
 re.compile(r'\bkeine\s+quellen?\s+beleg(?:t|en)\b'),
 re.compile(r'\bweltweit\b.{0,85}\bkeinerlei\b.{0,60}\b(?:nachweis|beleg|studie)\b'),
 re.compile(r'\bkeine\s+studie\b.{0,35}\b(?:weltweit|jemals)\b'),
 re.compile(r'\bnirgendwo\b.{0,75}\b(?:literatur|beleg|nachweis)\b'),
)
_LIMITED = re.compile(r'\b(?:in den (?:vier|hier|gepr[üu]ften)|in der hier verwendeten auswahl|im vorliegenden katalog|in (?:diesem|unserem) (?:katalog|quellenset|datensatz)|nur die geprüften|der bisherige katalog|ein umfassender literaturreview fehlt)\b')
_WARN_QUOTE = re.compile(r'\b(?:die (?:pauschale|zitierte|fragw[üu]rdige) formulierung|sollten wir ersetzen|wird (?:nur|hier) zitiert|w[öo]rtlich|als zitat|steht als zitat|die autoren schreiben|warn(?:t|en|ung) vor|falsch w[äa]re)\b')
_METHOD = (
 re.compile(r'\bnormen?\b.{0,70}\b(?:kein|nicht|ohne|statt)\b.{0,55}\b(?:wirksamkeit|wirkung|beleg|nachweis|kausal)\w*'),
 re.compile(r'\bnormative?\s+(?:leitlinien|leitprinzipien|empfehlungen)\b.{0,80}\b(?:keine?|nicht)\b.{0,60}\b(?:beleg|nachweis|wirkung|wirksamkeit)\w*'),
 re.compile(r'\baus\s+ethikleitlinien\b.{0,70}\b(?:keine?|nicht)\b.{0,55}\b(?:wirkung|wirksamkeit|beleg|nachweis)\w*'),
 re.compile(r'\bquellen\s*[- ]?id\b.{0,65}\b(?:keine?|nicht)\b.{0,55}\b(?:kausal|wirksamkeit|wirkung)\w*'),
 re.compile(r'\bmethodisch(?:e|er|en)?\s+(?:schluss|bewertung|urteil|pr[üu]fung)\b'),
 re.compile(r'\b(?:falsche ableitung|norm(?:en|ative)?\b.{0,45}\bwirksamkeitsnachweis)\b'),
)
# No classification based on source ID alone: S04 specifically concerns possible AI consciousness.
_ANIMAL = re.compile(r'\b(?:tier\w*|nutztiere?\w*|s[äa]ugetier\w*|schmerzreaktion\w*|empfindungsf[äa]higkeit\s+(?:bei|von)\s+\w*tiere?\w*|tierwohl\w*|tierleid\w*)\b')
_AI_CONSCIOUS = re.compile(r'\b(?:ki[- ]bewusstsein|k[üu]nstliche[nrsm]?\s+intelligenz\b.{0,25}\bbewusstsein|ki[- ]bewusstheit)\b')
_DENIAL = re.compile(r'\b(?:kein\s+beleg|nicht\s+als\s+(?:beleg|nachweis)|sondern\s+behandelt|muss\s+aus\s+anderen\s+quellen|keine\s+tierleidmessung|keine\s+tier\w+\s+belegt)\b')
_UNSUPPORTED = re.compile(r'\b(?:beweis(?:t|en)?|zeigt|zeigen|liefert|ableiten|messen|messwerte|indikatoren|funktionieren|zuverl[äa]ssig|validiert|validierte|unmittelbar|quantitativ)\b')


def _normalize(text: str) -> str:
    return re.sub(r'\s+', ' ', str(text).casefold()).strip()


def _is_meta(text: str) -> bool:
    if not _META_HEAD.match(text): return False
    # Only references, connective words, and explicit audit comment are meta-data.
    after = text.split(':',1)[1]
    after = _SOURCE.sub(' ',after)
    after = re.sub(r'\([^)]*(?:id.audit|formaler.*audit|inhaltliche validierung)[^)]*\)', ' ', after, flags=re.I)
    after = re.sub(r'\b(?:und|sowie|ohne weitere sachbehauptung|ids|quellen|belegkennungen)\b',' ',after,flags=re.I)
    return not re.search(r'[\wÄÖÜäöü]{3,}',after)


def candidate_issue(row:dict[str,str]) -> str:
    """Only text, source-ID and raw search status, NEVER labels/annotations.

    Outputs technical warning labels, not factual decisions or approvals.
    """
    raw = str(row.get('Aussage',''))
    x = _normalize(raw)
    source = str(row.get('Quellen-ID','')).strip().upper()
    if _is_meta(raw):
        return 'META'
    # Note: legacy META search status can refer to a compound scientific claim;
    # do not automatically treat a row as metadata solely because of this field.
    if not _WARN_QUOTE.search(x) and any(p.search(x) for p in _ABSENCE) and not _LIMITED.search(x):
        return 'PAUSCHALE_ABSENZ'
    if not re.search(r'\b(?:die autoren schreiben|steht als zitat|w[öo]rtlich zu verifizieren)\b',x):
        if any(p.search(x) for p in _METHOD):
            return 'METHODE'
    # Distinguish positive misuse of S04 for animals from warnings about misuse.
    if source=='S04':
        if ('messbarkeit von empfindungsfähigkeit' in x and not _AI_CONSCIOUS.search(x) and not _DENIAL.search(x)):
            return 'DOMAENENFEHLER'
        if _ANIMAL.search(x) and not _DENIAL.search(x) and _UNSUPPORTED.search(x):
            return 'DOMAENENFEHLER'
    return NONE
