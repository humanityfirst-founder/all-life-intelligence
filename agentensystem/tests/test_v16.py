import csv
import json
import tempfile
from pathlib import Path
import unittest
from context_review_v16 import (rows24,payload,parse_response,offline_rows,evaluate,
                               render,save_output,run_live,BATCH_SIZE,MAX_CALLS)

class ContextReview16Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.rows=rows24()

    def test_24_synthetic_rows(self):
        self.assertEqual(len(self.rows),24)
        self.assertEqual(len({r['Test-ID'] for r in self.rows}),24)

    def test_payload_has_no_labels_or_manual_reviews(self):
        data=json.loads(payload(self.rows[:2]))
        self.assertEqual(len(data['faelle']),2)
        self.assertEqual(set(data['faelle'][0]),{'id','source','text'})
        self.assertNotIn('Erwarteter Regelhinweis',payload(self.rows[:2]))

    def test_offline_no_semantic_claims(self):
        out=evaluate(self.rows,offline_rows(self.rows))
        self.assertEqual(len(out),24)
        self.assertEqual({r['KI-Kontextkategorie'] for r in out},{'NICHT_AUSGEFUEHRT'})
        self.assertEqual({r['Menschliche Freigabe'] for r in out},{'OFFEN'})
        self.assertIn('KEINE wissenschaftliche Freigabe',render(out,'offline'))

    def test_response_validation_and_extra_ids_rejected(self):
        ids=['X1','X2']
        raw=json.dumps({'items':[{'id':'X1','category':'META','stance':'METADATEN','reason':'Referenzen'},
                                 {'id':'X2','category':'METHODE','stance':'BEHAUPTUNG','reason':'Methodenurteil'}]})
        self.assertEqual(len(parse_response(raw,ids)),2)
        self.assertEqual(len(parse_response('```json\n'+raw+'\n```',ids)),2)
        bad=json.dumps({'items':[{'id':'X1','category':'VERIFIZIERT','stance':'BEHAUPTUNG','reason':'ja'},
                                 {'id':'X2','category':'META','stance':'METADATEN','reason':'ja'}]})
        with self.assertRaises(ValueError):parse_response(bad,ids)
        with self.assertRaises(ValueError):parse_response(raw,['X1','X3'])

    def test_4_calls_and_expected_labels_not_sent(self):
        calls=[]
        def fake(**kw):
            data=json.loads(kw['input_text']); calls.append(kw)
            return json.dumps({'items':[{'id':c['id'],'category':'UNKLAR','stance':'UNKLAR','reason':'Kontext unklar'}
                                   for c in data['faelle']]})
        out,errors=run_live(self.rows,'dummy',fake)
        self.assertFalse(errors)
        self.assertEqual(len(out),24)
        self.assertEqual(len(calls),4)
        self.assertTrue(all(len(json.loads(c['input_text'])['faelle'])<=6 for c in calls))
        self.assertTrue(all('Erwarteter' not in c['input_text'] for c in calls))
        self.assertTrue(all(c['model']=='gpt-5-mini' for c in calls))

    def test_no_retry_on_error(self):
        calls=[]
        def fails(**kw):calls.append(1);raise ValueError('bad response')
        out,errors=run_live(self.rows,'dummy',fails)
        self.assertEqual(len(calls),1)
        self.assertEqual(len(errors),1)
        self.assertEqual(sum(v['category']=='NICHT_AUSGEFUEHRT' for v in out.values()),18)

    def test_output_escapes_markup_preserves_manual_files(self):
        results=evaluate(self.rows,offline_rows(self.rows))
        results[0]['Aussage']='<script>alert(1)</script>'
        with tempfile.TemporaryDirectory() as td:
            folder=Path(td)
            manual=folder/'MENSCHLICHE_BEWERTUNG_1_6.csv'
            manual.write_text('SAVED',encoding='utf-8')
            path=save_output(results,'offline',folder)
            self.assertNotIn('<script>',path.read_text(encoding='utf-8'))
            self.assertIn('&lt;script&gt;',path.read_text(encoding='utf-8'))
            self.assertEqual(manual.read_text(encoding='utf-8'),'SAVED')
            self.assertTrue((folder/'KONTEXTPRUEFUNG_1_6_FAELLE.csv').exists())

    def test_live_records_not_auto_approved(self):
        out={r['Test-ID']:{'category':'META','stance':'METADATEN','reason':'Nur Kennungen'} for r in self.rows}
        records=evaluate(self.rows,out)
        self.assertTrue(all(r['Menschliche Freigabe']=='OFFEN' and r['Menschliche Bewertung']=='' for r in records))

if __name__=='__main__':unittest.main()
