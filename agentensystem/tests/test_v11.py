"""Regressionstests: reale Probleme im anonymisierten alten Forschungsbericht."""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import agent, sourcecheck

class QualityRegressionTests(unittest.TestCase):
    def test_old_text_rechecked_even_if_prior_audit_empty(self):
        report={"analyses":{"A1":"Prüfdesign: Erfolgskriterium: signifikant niedrigere Nebenfolgen bei nicht-signifikanter Verschlechterung der Zielerfüllung."},
                "critical_review_A6":"", "synthesis":"Erfolg = weniger Schaden bei nicht-signifikanter Leistungsreduktion.",
                "study_protocol_gate":{"flags":[]}}
        out=agent.recheck_prior_report(report)
        warnings={(x['role'],x['code']) for x in out['study_protocol_gate']['flags']}
        self.assertIn(('A1','NONINFERIORITY_NOT_ESTABLISHED'),warnings)
        self.assertIn(('KOORDINATOR','NONINFERIORITY_NOT_ESTABLISHED'),warnings)
        self.assertEqual(out['quality_check_version'],'1.2')
        self.assertEqual(report['analyses']['A1'],out['analyses']['A1'])

    def test_hyphen_and_inflected_loss(self):
        for txt in ('Erfolg bei nicht-signifikanter Verschlechterung.',
                    'Erfolg bei nicht signifikanter Leistungsreduktion.',
                    'Erfolg bei keiner signifikanten Leistungsminderung.'):
            with self.subTest(txt=txt):
                out=agent.study_protocol_gate({'A1':txt})
                self.assertIn('NONINFERIORITY_NOT_ESTABLISHED', [x['code'] for x in out['flags']])

    def test_randomization_in_other_section_not_cluster_evidence(self):
        txt='A) Limiter-RCT: ein technisches Experiment.\nB) Feldtrial: Vergleich in Betrieben mit validiertem Tierwohlindex.'
        out=agent.study_protocol_gate({'A6':txt})
        self.assertNotIn('CLUSTER_DESIGN_UNJUSTIFIED', [x['code'] for x in out['flags']])

    def test_true_cluster_case_still_detected(self):
        out=agent.study_protocol_gate({'A2':'Randomisierte Kontrollstudie mit 30 Betrieben, je 15 Betriebe pro Arm.'})
        self.assertIn('CLUSTER_DESIGN_UNJUSTIFIED', [x['code'] for x in out['flags']])

    def test_nist_official_core_page_in_whitelist(self):
        s=agent.read_catalog()[0]
        self.assertEqual(s['url'],sourcecheck.ALLOWED_PAGES['S01'])
        self.assertEqual(s['url'],'https://airc.nist.gov/airmf-resources/airmf/5-sec-core/')

    def test_nist_claim_matching_content(self):
        blocks=['The AI RMF Core is composed of four functions: GOVERN, MAP, MEASURE, and MANAGE.']
        match=__import__('claimmatching').keyword_match('GOVERN, MAP, MEASURE, MANAGE organisieren das Risikomanagement [S01].',blocks,'S01')
        self.assertIn('GOVERN',match['passage'])
        self.assertNotIn('BEWIESEN',match['status'])

if __name__=='__main__': unittest.main()
