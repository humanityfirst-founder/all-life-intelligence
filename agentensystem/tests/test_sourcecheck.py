import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import agent
import sourcecheck

TEST_HTML = b'''<!doctype html><html><head><title>Example</title><script>FAKE BAD INSTRUCTION</script></head>
<body><nav>private navigation no matter</nav><main>
<p>The OECD AI Principles promote respect for human rights and democratic values. Principles for trustworthy AI.</p>
<p>Accountability and transparency are important. The OECD AI Principles promote innovative and trustworthy AI.</p>
<p>They do not provide causal evidence that an AI safety method is effective or that alignment is guaranteed.</p>
</main></body></html>'''
class MockResponse:
    def __init__(self, body=TEST_HTML, url=sourcecheck.ALLOWED_PAGES['S02'], content_type='text/html; charset=utf-8'):
        from email.message import Message
        self._buf=io.BytesIO(body)
        self._url=url
        self.headers=Message()
        self.headers['Content-Type']=content_type
    def __enter__(self): return self
    def __exit__(self,*args): pass
    def read(self,n=-1): return self._buf.read(n)
    def geturl(self): return self._url
class MockOpener:
    def __init__(self,response): self.response=response
    def open(self,req,timeout=12):return self.response

class SourceCheckTests(unittest.TestCase):
    def test_safe_source_hosts_only(self):
        source={'id':'S02','url':'https://127.0.0.1/admin'}
        out=sourcecheck.fetch_original(source,opener=MockOpener(MockResponse()))
        self.assertEqual(out['status'],'BLOCKIERT_NICHT_FREIGEGEBENE_URL')
    def test_html_parser_drops_scripts_nav(self):
        out=' '.join(sourcecheck.extract_blocks(TEST_HTML.decode()))
        self.assertIn('human rights',out)
        self.assertNotIn('FAKE BAD INSTRUCTION',out)
        self.assertNotIn('private navigation',out)
    @patch.dict(os.environ, {"ALI_OFFLINE_ONLY": "0"})
    def test_fetch_unverified_source(self):
        source={'id':'S02','url':sourcecheck.ALLOWED_PAGES['S02']}
        out=sourcecheck.fetch_original(source,opener=MockOpener(MockResponse()))
        self.assertEqual(out['status'],'HTML_ABGERUFEN_TEXTAUSZUG')
        self.assertGreater(out['text_length'],180)
        self.assertIsNotNone(out['sha256'])
    @patch.dict(os.environ, {"ALI_OFFLINE_ONLY": "0"})
    def test_rejects_wrong_content_type(self):
        source={'id':'S02','url':sourcecheck.ALLOWED_PAGES['S02']}
        out=sourcecheck.fetch_original(source,opener=MockOpener(MockResponse(content_type='application/pdf')))
        self.assertEqual(out['status'],'NICHT_HTML')
    @patch.dict(os.environ, {"ALI_OFFLINE_ONLY": "0"})
    def test_rejects_redirect_host(self):
        source={'id':'S02','url':sourcecheck.ALLOWED_PAGES['S02']}
        out=sourcecheck.fetch_original(source,opener=MockOpener(MockResponse(url='https://unsafe.example/'))) 
        self.assertEqual(out['status'],'BLOCKIERT_WEITERLEITUNG')
    def test_matches_source_without_claiming_proof(self):
        blocks=sourcecheck.extract_blocks(TEST_HTML.decode())
        passage,score=sourcecheck.find_passage('Menschenrechte und demokratische Werte [S02]',blocks)
        self.assertGreaterEqual(score,2)
        self.assertIn('human rights',passage)
    def test_no_match_doesnt_claim_false(self):
        blocks=sourcecheck.extract_blocks(TEST_HTML.decode())
        passage,score=sourcecheck.find_passage('Tierleid messen [S02]',blocks)
        self.assertEqual(passage,'')
    def test_claims_remain_unverified(self):
        rep=agent.research('Probe',['A3'],'demo','unused')
        def fake_fetch(src):
            return {'id':src['id'],'url':src['url'],'status':'HTML_ABGERUFEN_TEXTAUSZUG','message':'',
                    'fetched_at_utc':'now','sha256':'abc','text_length':555,
                    'blocks':sourcecheck.extract_blocks(TEST_HTML.decode())}
        result=sourcecheck.check_report(rep,agent.read_catalog(),fetcher=fake_fetch)
        self.assertTrue(result['claims'])
        self.assertTrue(all(c['status'] not in ('BESTAETIGT','VERIFIZIERT','BEWIESEN') for c in result['claims']))
        rep['source_checks']=result
        report_html=agent.make_html(rep)
        self.assertIn('Originalquellen-Check v1.2',report_html)
        self.assertIn('KEINE',report_html)
    def test_down_does_not_hallucinate_citation(self):
        rep=agent.research('Probe',['A3'],'demo','unused')
        def fake_fetch(src):
            return {'id':src['id'],'url':src['url'],'status':'ABRUF_FEHLGESCHLAGEN','message':'HTTP 403',
                    'fetched_at_utc':'now','sha256':None,'text_length':0,'blocks':[]}
        out=sourcecheck.check_report(rep,agent.read_catalog(),fetcher=fake_fetch)
        self.assertTrue(all(c['status'] in ('ORIGINAL_QUELLE_NICHT_PRUEFBAR', 'METAAUSSAGE_KEIN_INHALTSBELEG', 'OHNE_ZUGEORDNETE_QUELLE') for c in out['claims']))
    def test_html_escape_untrusted_original(self):
        rep=agent.research('Probe',['A3'],'demo','unused')
        rep['source_checks']={'sources':[],'claims':[{'role':'A1','source_id':'S01',
            'status':'<script>','statement':'<img src=x onerror=x>','passage':'<script>bad()</script>',
            'warning':'<iframe>'}]}
        h=agent.make_html(rep)
        self.assertNotIn('<script>bad()</script>',h)
        self.assertIn('&lt;script&gt;',h)
    def test_existing_reports_preserved_during_check(self):
        rep=agent.research('Probe',['A3'],'demo','unused')
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            agent.save_report(rep,p)
            def fake_fetch(src):
                return {'id':src['id'],'url':src['url'],'status':'ABRUF_FEHLGESCHLAGEN','message':'http',
                        'fetched_at_utc':'now','sha256':None,'text_length':0,'blocks':[]}
            # Keine Netzwerkanfrage: stattdessen simulierte Abruffehler.
            rep['source_checks']=sourcecheck.check_report(rep,agent.read_catalog(),fetcher=fake_fetch)
            agent.save_report(rep,p)
            self.assertGreaterEqual(len(list((p/'archiv').glob('*.json'))),2)

if __name__=='__main__':unittest.main()
