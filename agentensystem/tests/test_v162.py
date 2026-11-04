import csv
import json
import tempfile
import unittest
from pathlib import Path

from agent import ApiProblem
from context_review_v16 import COLS
from diagnose_single_v162 import (
    load_records, is_pending, one_step, save, safe_diagnosis,
    RESULT,
)

class SingleDiagnosticV162Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows, cls.prior = load_records(source=Path(__file__).resolve().parents[1] / 'reports' / 'KONTEXTPRUEFUNG_1_6_1_FAELLE.csv')

    def test_initial_results_preserved_and_six_missing(self):
        self.assertEqual(sum(is_pending(r) for r in self.prior), 6)
        self.assertEqual(len(self.prior), 24)
        evaluated, errors = one_step(self.rows, self.prior)
        self.assertFalse(errors)
        self.assertEqual(evaluated[0]['KI-Kontextkategorie'], 'META')
        self.assertEqual(sum(r['Stimmt mit Szenariovorgabe ueberein']=='JA' for r in evaluated),15)
        self.assertEqual(sum(r['Stimmt mit Szenariovorgabe ueberein']=='NEIN' for r in evaluated),3)
        self.assertEqual(sum(r['Stimmt mit Szenariovorgabe ueberein']=='NICHT_GEPRUEFT' for r in evaluated),6)

    def test_exactly_one_case_sent_and_rest_untouched(self):
        requests = []
        def backend(**kwargs):
            requests.append(kwargs)
            cases = json.loads(kwargs['input_text'])['faelle']
            return json.dumps({'items':[{'id':item['id'], 'category':'KEIN_SPEZIELLER_HINWEIS',
                'stance':'BEHAUPTUNG','reason':'Thema KI-Bewusstsein'} for item in cases]})
        updated, errors = one_step(self.rows, self.prior, backend=backend, api_key='DUMMY_TEST_ONLY')
        self.assertEqual(errors,[])
        self.assertEqual(len(requests),1)
        self.assertEqual(len(json.loads(requests[0]['input_text'])['faelle']),1)
        self.assertEqual(requests[0]['model'],'gpt-5-mini')
        self.assertEqual(updated[18]['KI-Kontextkategorie'],'KEIN_SPEZIELLER_HINWEIS')
        self.assertEqual(sum(r['Stimmt mit Szenariovorgabe ueberein']=='NICHT_GEPRUEFT' for r in updated),5)
        self.assertEqual(updated[0]['KI-Kontextkategorie'], self.prior[0]['KI-Kontextkategorie'])
        with tempfile.TemporaryDirectory() as directory:
            html=save(updated, errors, 'test', root=directory)
            self.assertTrue(html.exists())
            html_text=html.read_text(encoding='utf-8')
            self.assertIn('Kontextpruefung 1.6.2', html_text)
            rrows=list(csv.DictReader((Path(directory)/RESULT.name).open(encoding='utf-8-sig'),delimiter=';'))
            self.assertEqual(len(rrows),24)
            self.assertEqual(rrows[18]['KI-Kontextkategorie'],'KEIN_SPEZIELLER_HINWEIS')

    def test_failed_call_does_not_erase_previous_results(self):
        calls=[]
        def backend(**kwargs):
            calls.append(kwargs)
            raise ApiProblem('API-Fehler HTTP 429. Bereits ausgeführte Aufrufe können Kosten verursachen.')
        updated, errors=one_step(self.rows,self.prior,backend=backend,api_key='DUMMY_TEST_ONLY')
        self.assertEqual(len(calls),1)
        self.assertIn('HTTP 429',errors[0])
        self.assertEqual(sum(is_pending(r) for r in updated),6)
        self.assertEqual(updated[12]['KI-Kontextkategorie'],self.prior[12]['KI-Kontextkategorie'])

    def test_malformed_response_not_retried(self):
        calls=[]
        def backend(**kwargs):
            calls.append(kwargs)
            return '{"items": []}'
        updated, errors=one_step(self.rows,self.prior,backend=backend,api_key='DUMMY_TEST_ONLY')
        self.assertEqual(len(calls),1)
        self.assertIn('nicht exakt eine Bewertung',errors[0])
        self.assertEqual(sum(is_pending(r) for r in updated),6)

    def test_human_inputs_preserved(self):
        data=[row.copy() for row in self.prior]
        data[0]['Menschliche Freigabe']='BESTAETIGT'
        data[0]['Menschliche Bewertung']='META'
        data[0]['Notiz']='Unabhaengig geprueft'
        records,_=one_step(self.rows,data)
        self.assertEqual(records[0]['Menschliche Freigabe'],'BESTAETIGT')
        self.assertEqual(records[0]['Menschliche Bewertung'],'META')
        self.assertEqual(records[0]['Notiz'],'Unabhaengig geprueft')

    def test_safe_error_types(self):
        self.assertIn('HTTP 401',safe_diagnosis(ApiProblem('API-Fehler HTTP 401.')))
        self.assertIn('Ausgabetokenlimit',safe_diagnosis(ApiProblem('UNVOLLSTAENDIGE Modellantwort (max_output_tokens)')))
        self.assertNotIn('sk-',safe_diagnosis(ApiProblem('sk-SECRETTOKEN')))

if __name__=='__main__': unittest.main()
