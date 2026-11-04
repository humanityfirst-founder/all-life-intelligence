#!/usr/bin/env python3
"""v1.2: manueller Start, sicherer Abruf offizieller HTML-Seiten und Textstellen-Suche.

KEIN autonomer Faktencheck: Ähnliche Wörter / Passagen beweisen keine Sachbehauptung.
Keine API, keine kostenpflichtigen Modellaufrufe, keine Quelleninhalte an ein Modell.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
import webbrowser

import agent
import claimmatching

ALLOWED_PAGES = {
    'S01': 'https://airc.nist.gov/airmf-resources/airmf/5-sec-core/',
    'S02': 'https://oecd.ai/en/ai-principles',
    'S03': 'https://www.unesco.org/en/legal-affairs/recommendation-ethics-artificial-intelligence',
    'S04': 'https://arxiv.org/abs/2308.08708',
}
MAX_RESPONSE_BYTES = 1_800_000
MAX_TEXT_CHARS = 200_000
MIN_TEXT_CHARS = 180
BLOCK_TAGS = {'p', 'li', 'h1', 'h2', 'h3', 'h4', 'blockquote', 'div', 'section', 'article', 'main'}
SKIP_TAGS = {'script', 'style', 'nav', 'footer', 'header', 'aside', 'template', 'svg', 'noscript'}

# Stichwortpaare helfen beim Auffinden englischer Passagen zu deutschen Behauptungen.
# Dies ist KEIN semantischer Beweis und liefert KEINE Wahrscheinlichkeit für Wahrheit.
KEYWORDS = {
    'risiko': ['risk'], 'risiken': ['risk'], 'risikomanagement': ['risk management', 'risk'],
    'menschenrecht': ['human rights'], 'demokrat': ['democratic', 'democracy'],
    'rechenschaft': ['accountability'], 'transparent': ['transparency', 'transparent'],
    'sicherheit': ['safety', 'security'], 'robust': ['robustness', 'robust'],
    'umwelt': ['environment', 'ecosystems'], 'ökolog': ['ecosystems', 'ecological'],
    'ökosystem': ['ecosystems'], 'ethik': ['ethics', 'ethical'],
    'bewusst': ['consciousness', 'conscious'], 'indikator': ['indicator'],
    'theorie': ['theories', 'theory'], 'aufsicht': ['oversight'],
    'freiheit': ['freedoms', 'freedom'], 'schutz': ['protection', 'protect'],
    'bewert': ['assess', 'measure'], 'messen': ['measure'], 'nachhalt': ['sustainable'],
    'werte': ['values'], 'kontrolle': ['control'], 'verantwort': ['responsible', 'responsibility'],
    'audit': ['audit'], 'forsch': ['research'], 'wirksam': ['effective', 'efficacy'],
    'regierung': ['government'], 'regulierung': ['regulation'],
}
STOP = set('durch indem darauf sind ist soll sollen einer eines eine diese dieser das dies ihre seinen sowie ohne noch keine nicht alle beide eine die der des dem den und oder von auf mit als bei dass für fuer zur zum im in am an zu den ein wird werden nach nur können kann wichtig kein keine kein'.split())


class HtmlBlocks(HTMLParser):
    """Einfacher, passiver HTML-Text-Extraktor ohne Skriptausführung."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip_stack = []
        self.parts = []
        self.out = []
    def handle_starttag(self, tag, attrs):
        if self.skip_stack:
            if tag in SKIP_TAGS: self.skip_stack.append(tag)
            return
        if tag in SKIP_TAGS:
            self.skip_stack.append(tag)
            return
        if tag in BLOCK_TAGS and self.parts:
            self.flush()
    def handle_endtag(self, tag):
        if self.skip_stack:
            if tag == self.skip_stack[-1]: self.skip_stack.pop()
            return
        if tag in BLOCK_TAGS:
            self.flush()
    def handle_data(self, data):
        if not self.skip_stack and data.strip(): self.parts.append(data)
    def flush(self):
        if self.parts:
            s = re.sub(r'\s+', ' ', ' '.join(self.parts)).strip()
            if len(s) > 30: self.out.append(s)
            self.parts = []
    def blocks(self):
        self.flush()
        # Wiederholte Navigation/gleiche Absätze nur einmal behalten.
        return list(dict.fromkeys(self.out))


def extract_blocks(page: str) -> list[str]:
    p = HtmlBlocks()
    p.feed(page)
    return p.blocks()


class RestrictedRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self, host):
        self.host = host
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        u = urllib.parse.urlsplit(newurl)
        if u.scheme != 'https' or u.hostname != self.host or u.username or u.password or (u.port and u.port != 443):
            raise urllib.error.HTTPError(newurl, code, 'Redirect zu anderem Host blockiert', headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_original(source: dict, *, timeout: int = 12, opener=None) -> dict:
    """Nur vier hart freigegebene HTTPS-HTML-Seiten; Netzwerkfehler offen kennzeichnen."""
    sid = source['id']
    url = source['url']
    result = {'id': sid, 'url': url, 'status': 'NICHT_ABGERUFEN', 'message': '',
              'fetched_at_utc': datetime.now(timezone.utc).isoformat(),
              'sha256': None, 'text_length': 0, 'blocks': []}
    if ALLOWED_PAGES.get(sid) != url:
        result['status'] = 'BLOCKIERT_NICHT_FREIGEGEBENE_URL'
        result['message'] = 'Nur bekannte Original-URLs erlaubt.'
        return result
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != 'https' or parsed.username or parsed.password or parsed.port:
        result['status'] = 'BLOCKIERT_UNSICHERE_URL'
        result['message'] = 'Nur HTTPS ohne Benutzerdaten/abweichenden Port.'
        return result
    if agent.offline_only():
        result.update(status='BLOCKIERT_OFFLINE', message=agent.OFFLINE_MESSAGE)
        return result
    if opener is None:
        opener = urllib.request.build_opener(RestrictedRedirect(parsed.hostname))
    req = urllib.request.Request(url, headers={
        'User-Agent': 'All-Life-Intelligence-SourceCheck/1.2 (educational research; no publishing)',
        'Accept': 'text/html,application/xhtml+xml;q=0.9',
    })
    try:
        with opener.open(req, timeout=timeout) as response:
            final = urllib.parse.urlsplit(response.geturl())
            if final.scheme != 'https' or final.hostname != parsed.hostname:
                result['status'] = 'BLOCKIERT_WEITERLEITUNG'
                result['message'] = 'Nicht freigegebene Weiterleitung.'
                return result
            content_type = response.headers.get('Content-Type', '').lower()
            if not ('text/html' in content_type or 'application/xhtml+xml' in content_type):
                result['status'] = 'NICHT_HTML'
                result['message'] = f'Quellformat nicht unterstützt: {content_type[:75]}'
                return result
            payload = response.read(MAX_RESPONSE_BYTES + 1)
            if len(payload) > MAX_RESPONSE_BYTES:
                result['status'] = 'SEITE_ZU_GROSS'
                result['message'] = 'Maximalgröße überschritten; kein vollständiger Abruf.'
                return result
            charset = response.headers.get_content_charset() or 'utf-8'
            try:
                doc = payload.decode(charset, errors='replace')
            except LookupError:
                doc = payload.decode('utf-8', errors='replace')
            blocks = extract_blocks(doc)
            original = '\n'.join(blocks)
            if len(original) < MIN_TEXT_CHARS:
                result['status'] = 'UNBRAUCHBARER_QUELLENTEXT'
                result['message'] = 'Zu wenig extrahierbarer HTML-Text (evtl. dynamische Website).'
                return result
            if len(original) > MAX_TEXT_CHARS:
                original = original[:MAX_TEXT_CHARS]
                blocks = [b for b in blocks if b and original.find(b) >= 0]
                result['message'] = 'Quellenauszug auf 200.000 Zeichen begrenzt.'
            result.update(status='HTML_ABGERUFEN_TEXTAUSZUG',
                          message=(result['message'] + ' Kein Volltextbeweis.').strip(),
                          sha256=hashlib.sha256(payload).hexdigest(),
                          text_length=len(original), blocks=blocks)
            return result
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, ValueError) as err:
        result['status'] = 'ABRUF_FEHLGESCHLAGEN'
        # Keine externen Fehlerdetails in den Bericht übernehmen (URL kann interne Angaben enthalten).
        code = getattr(err, 'code', None)
        result['message'] = f'HTTP {code}' if code is not None else type(err).__name__
        return result


def cues_from_claim(statement: str) -> list[str]:
    clean = re.sub(r'\[S\d{2,}\]', ' ', statement.lower())
    words = re.findall(r'\b[\wäöüß]{4,}\b', clean, re.UNICODE)
    terms = set()
    for word in words:
        if word in STOP or word in {'nist','unesco','oecd','unbelegt','quellengestützt','quellengestuetzt','quelle','aussage'}:
            continue
        for stem, translations in KEYWORDS.items():
            if word.startswith(stem): terms.update(translations)
        if word in ('govern','map','measure','manage','transparency','consciousness','indicator'):
            terms.add(word)
    return sorted(terms)


def find_passage(statement: str, blocks: list[str]) -> tuple[str, int]:
    terms = cues_from_claim(statement)
    if not terms or not blocks:
        return '', 0
    ranked = []
    for block in blocks:
        lower = block.lower()
        overlap = sum(1 for t in terms if t in lower)
        if overlap:
            # Bevorzuge mehrere Treffer und sachliche Textlänge statt Website-Menüs.
            ranked.append((overlap, -abs(len(block)-260), block))
    if not ranked:
        return '', 0
    score, _, best = max(ranked)
    if score < 2:
        return '', score
    # Kompakter Ausschnitt um den ersten erkannten Begriff.
    positions = [best.lower().find(t) for t in terms if best.lower().find(t) >= 0]
    start = max(0, (min(positions) - 55) if positions else 0)
    return ('…' if start else '') + best[start:start+240].strip() + ('…' if len(best) > start+240 else ''), score


def check_report(report: dict, sources: list[dict], fetcher=fetch_original) -> dict:
    fetched = {s['id']: fetcher(s) for s in sources}
    out = []
    for item in report.get('verification_queue', []):
        # Satzteile pro Quelle statt pauschaler Gesamtzeile; Status stets unbestätigt.
        for atomic in claimmatching.split_claims(item['statement'], item['source_ids']):
            if atomic['kind'] == 'UNATTRIBUTED':
                out.append({'role':item['role'],'source_id':'KEINE','statement':atomic['statement'],
                            'status':'OHNE_ZUGEORDNETE_QUELLE','passage':'',
                            'warning':'Dieser Satzteil ist nicht eindeutig zitiert.'})
                continue
            for sid in atomic['source_ids']:
                fetched_source = fetched.get(sid)
                statement = atomic['statement']
                if atomic['kind'] == 'META':
                    status, passage = 'METAAUSSAGE_KEIN_INHALTSBELEG', ''
                    warning = 'Eine Aufzählung von Quellen-IDs ist keine Sachbehauptung und keine Belegprüfung.'
                elif not fetched_source or fetched_source['status'] != 'HTML_ABGERUFEN_TEXTAUSZUG':
                    status, passage = 'ORIGINAL_QUELLE_NICHT_PRUEFBAR', ''
                    warning = 'Abruf fehlgeschlagen, Aussage bleibt ungeprüft.'
                else:
                    match = claimmatching.keyword_match(statement, fetched_source['blocks'], sid)
                    status, passage, warning = match['status'], match['passage'], match['warning']
                    if sid == 'S04' and re.search(r'\b(?:Tier\w*|Spezies|Organismen|Leidenszust\w*)\b', statement, re.I):
                        warning += ' S04 behandelt KI-Bewusstsein, keine Tierleidmessung.'
                out.append({'role':item['role'], 'source_id':sid, 'statement':statement,
                            'status':status, 'passage':passage, 'warning':warning})
    summary = []
    for sid, data in fetched.items():
        summary.append({k: data[k] for k in ('id','url','status','message','fetched_at_utc','sha256','text_length')})
    return {'checked_at_utc':datetime.now(timezone.utc).isoformat(),
            'audit_type':'QUELLENBEZOGENE_EINZELAUSSAGEN_SUCHE_KEINE_INHALTLICHE_VALIDIERUNG',
            'checker_version':'1.2',
            'sources':summary,'claims':out,
            'limitations':'Kein semantischer Wahrheitsdetektor und keine experimentelle Verifikation. Ein Themen-Treffer ist kein Beleg; ein fehlender Treffer kein Gegenbeweis. S01 nutzt nun NIST Core Kapitel 5 und S04 weiterhin nur den arXiv-Abstract.',
            '_source_blocks':fetched}


def run(report_path: Path, confirm: bool = True, open_report: bool = False) -> int:
    if agent.offline_only():
        print(agent.OFFLINE_MESSAGE, file=sys.stderr)
        return 2
    if not report_path.is_file():
        print('Kein Forschungsbericht gefunden. Kopiere letzter_bericht.json aus v1.1 in den Ordner reports. Keine Demo starten, wenn echte Daten geprueft werden sollen.')
        return 2
    try:
        report=json.loads(report_path.read_text(encoding='utf-8'))
        sources=agent.read_catalog()
    except (OSError, ValueError, KeyError) as exc:
        print('Bericht oder Quellenkatalog ist nicht lesbar:',type(exc).__name__)
        return 2
    if confirm:
        print('Originalquellen-Check v1.2: Vier öffentliche Webseiten (NIST, OECD, UNESCO, arXiv).')
        print('Nur HTTP-Lesezugriffe, keine API-Kosten, keine Veröffentlichung.')
        print('Es werden keinerlei Forschungsfragen, Schlüssel oder Berichte an diese Websites gesendet.')
        if input('Originalseiten jetzt abrufen? (ja/nein): ').strip().lower() != 'ja':
            print('Abgebrochen, keine Internetanfrage.')
            return 0
    # Beim Nachprüfen alter Forschungsberichte müssen NEUE Prüfregeln
    # erneut auf den alten KI-Text angewandt werden. Der Forschungstext bleibt erhalten.
    report=agent.recheck_prior_report(report)
    print('Methodische Qualitätskontrolle mit Version 1.2 erneut ausgeführt.')
    print('Quellen werden einzeln geladen und mit den zitierten Aussagen verglichen...')
    result=check_report(report,sources)
    cache=agent.BASE/'sources'/'cache'
    cache.mkdir(exist_ok=True)
    for sid, source in result.pop('_source_blocks').items():
        print(sid, source['status'])
        if source['status']=='HTML_ABGERUFEN_TEXTAUSZUG':
            (cache/f'{sid}.txt').write_text('\n'.join(source['blocks']),encoding='utf-8')
    report['source_checks']=result
    report['quality_status']='ORIGINALTEXTE_ABGERUFEN_ABER_INHALTLICH_NICHT_BESTAETIGT'
    paths=agent.save_report(report, report_path.parent)
    # Erzeugt nur eine qualitätsorientierte Arbeitsliste für Menschen. Kein Modellaufruf.
    from review_export import write_exports
    overview_html, review_csv = write_exports(report, report_path.parent)
    print('Originalquellen-Prüfbericht erstellt:',paths[1])
    print('Qualitaetsbilanz erstellt:',overview_html)
    print('Manuelle Pruefliste erstellt:',review_csv)
    print('Textstellen sind KEINE wissenschaftlich bestätigten Belege.')
    if open_report:
        webbrowser.open(paths[1].resolve().as_uri())
    return 0


def cli(argv=None):
    p=argparse.ArgumentParser(description='ALL-LIFE INTELLIGENCE – Quellen-Textcheck v1.2')
    p.add_argument('--report',type=Path,default=agent.REPORTS/'letzter_bericht.json')
    p.add_argument('--open-report',action='store_true')
    p.add_argument('--yes',action='store_true',help='Nur für nichtinteraktive Tests: Bestätigungsdialog überspringen')
    args=p.parse_args(argv)
    return run(args.report,confirm=not args.yes,open_report=args.open_report)

if __name__=='__main__':
    raise SystemExit(cli())
