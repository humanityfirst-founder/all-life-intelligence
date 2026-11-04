"""Gezielte Regressionsprüfungen aus dem echten v0.9-Nutzerbericht."""
import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import agent
import claimmatching
import sourcecheck


class AtomicClaimTests(unittest.TestCase):
    def test_nist_and_oecd_are_not_mixed(self):
        original=('QUELLENGESTÜTZT: Leitprinzipien für vertrauenswürdige KI betonen Menschenrechte, '
                  'Transparenz, Robustheit und Rechenschaftspflicht [S02]; Rahmen für Risikoidentifikation, '
                  '-messung und -management empfiehlt GOVERN, MAP, MEASURE, MANAGE [S01].')
        atomic=claimmatching.split_claims(original,['S01','S02'])
        self.assertEqual(len(atomic),2)
        self.assertEqual(atomic[0]['source_ids'],['S02'])
        self.assertEqual(atomic[1]['source_ids'],['S01'])
        self.assertNotIn('Govern',atomic[0]['statement'])

    def test_two_sentences_separated_by_citation(self):
        original=('UNESCO betont Menschenrechte und Umwelt [S03]. '
                  'Theoretische Indikatoren für KI-Bewusstsein sind unsicher [S04].')
        items=claimmatching.split_claims(original,['S03','S04'])
        self.assertEqual([x['source_ids'] for x in items],[['S03'],['S04']])

    def test_source_id_list_not_factual_claim(self):
        items=claimmatching.split_claims('Existente IDs: [S01],[S02],[S03],[S04].',['S01','S02','S03','S04'])
        self.assertEqual(items[0]['kind'],'META')

    def test_nist_overview_not_falsely_matching_four_functions(self):
        fake=['We guide critical infrastructure operators towards specific risk management practices to consider AI-enabled capabilities.']
        statement='NIST empfiehlt GOVERN, MAP, MEASURE, MANAGE [S01].'
        out=claimmatching.keyword_match(statement,fake,'S01')
        self.assertEqual(out['status'],'KEINE_PASSENDE_TEXTSTELLE_GEFUNDEN')
        self.assertEqual(out['passage'],'')

    def test_nist_exact_span_for_manual_review(self):
        fake=['The NIST AI RMF uses four functions: GOVERN, MAP, MEASURE, MANAGE. They organize AI risk management.']
        out=claimmatching.keyword_match('Die Funktionen GOVERN, MAP, MEASURE, MANAGE strukturieren Risikomanagement [S01]',fake,'S01')
        self.assertIn('GOVERN',out['passage'])
        self.assertNotIn('BESTAETIGT',out['status'])

    def test_reports_retain_old_core_version_correctly(self):
        r=agent.research('Frage',['A1'],'demo','none')
        html=agent.make_html(r)
        self.assertIn('Agentensystem v1.2',html)
        self.assertNotIn('v0.8 ·',html)
        r['application']='ALL-LIFE INTELLIGENCE – Agentensystem v0.8'
        r['source_checks']={'checker_version':'1.0','sources':[],'claims':[]}
        html=agent.make_html(r)
        self.assertIn('Agentensystem v0.8',html)
        self.assertIn('Quellenprüfung: 1.0',html)

    def test_noninferiority_warns(self):
        rep=agent.study_protocol_gate({'KOORDINATOR':'Erfolg bei signifikant weniger Schäden und nicht-signifikanter Verschlechterung der Zielerfüllung.'})
        self.assertIn('NONINFERIORITY_NOT_ESTABLISHED',[x['code'] for x in rep['flags']])

    def test_nisource_match_cannot_be_published(self):
        r=agent.research('Frage',['A1'],'demo','none')
        def fake(src):
            return {'id':src['id'],'url':src['url'],'status':'HTML_ABGERUFEN_TEXTAUSZUG',
                    'message':'','fetched_at_utc':'2026','sha256':'f','text_length':420,
                    'blocks':['Principles promote human rights and democratic values, transparency and accountability.']}
        out=sourcecheck.check_report(r,agent.read_catalog(),fetcher=fake)
        self.assertTrue(out['claims'])
        self.assertEqual(out['checker_version'],'1.2')
        self.assertNotIn('VERIFIZIERT',str([x['status'] for x in out['claims']]))

if __name__=='__main__': unittest.main()
