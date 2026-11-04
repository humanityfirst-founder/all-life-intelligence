import csv
import json
import tempfile
import unittest
from pathlib import Path
from context_review_v16 import rows24, COLS
from resume_context_v161 import load_existing, prepare, merge, save_only_new, SOURCE

class Resume161Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows,cls.prior=load_existing(SOURCE)

    def test_supplied_report_reconstructs_18_valid_and_6_missing(self):
        self.assertEqual(len(self.prior),24)
        assessments,missing=prepare(self.rows,self.prior)
        self.assertEqual(len(assessments),18)
        self.assertEqual(missing,list(range(18,24)))

    def test_offline_counters_distinguish_failed_from_wrong(self):
        records,errors=merge(self.rows,self.prior)
        self.assertEqual(errors,[])
        from collections import Counter
        counts=Counter(r['Stimmt mit Szenariovorgabe ueberein'] for r in records)
        self.assertEqual(counts['JA'],15)
        self.assertEqual(counts['NEIN'],3)
        self.assertEqual(counts['NICHT_GEPRUEFT'],6)

    def test_only_six_sent_in_single_live_call(self):
        calls=[]
        def fake(**kw):
            calls.append(kw)
            inputs=json.loads(kw['input_text'])['faelle']
            return json.dumps({'items':[{'id':x['id'],'category':'KEIN_SPEZIELLER_HINWEIS','stance':'BEHAUPTUNG','reason':'neutral'} for x in inputs]})
        recs,errors=merge(self.rows,self.prior,backend=fake,api_key='DUMMY')
        self.assertFalse(errors)
        self.assertEqual(len(calls),1)
        self.assertEqual(len(json.loads(calls[0]['input_text'])['faelle']),6)
        self.assertEqual(recs[0]['KI-Kontextkategorie'],'META')
        self.assertEqual(recs[12]['KI-Kontextkategorie'],'METHODE')
        self.assertTrue(all(recs[i]['KI-Kontextkategorie']=='KEIN_SPEZIELLER_HINWEIS' for i in range(18,24)))

    def test_failed_retry_preserves_six_missing(self):
        calls=[]
        def fails(**kw):calls.append(kw);raise ValueError('Unerwartete Zahl an KI-Bewertungen.')
        recs,errors=merge(self.rows,self.prior,backend=fails,api_key='DUMMY')
        self.assertEqual(len(calls),1)
        self.assertTrue(errors)
        self.assertEqual(sum(r['Stimmt mit Szenariovorgabe ueberein']=='NICHT_GEPRUEFT' for r in recs),6)

    def test_tampered_csv_refused_and_output_kept_separate(self):
        with tempfile.TemporaryDirectory() as t:
            csv_path=Path(t)/'existing.csv'
            with csv_path.open('w',encoding='utf-8-sig',newline='') as f:
                w=csv.DictWriter(f,fieldnames=COLS,delimiter=';');w.writeheader()
                for i,r in enumerate(self.prior):
                    cp=r.copy()
                    if i==0:cp['Aussage']='manipuliert'
                    w.writerow(cp)
            with self.assertRaises(ValueError):load_existing(csv_path)
            out=Path(t)/'reports';out.mkdir()
            human=out/'MENSCHLICHE_BEWERTUNG_1_6.csv';human.write_text('MANUELL',encoding='utf-8')
            recs,_=merge(self.rows,self.prior)
            html=save_only_new(recs,[],out)
            self.assertTrue(html.exists())
            self.assertEqual(human.read_text(encoding='utf-8'),'MANUELL')
            self.assertIn('6 ohne Kontextbewertung',html.read_text(encoding='utf-8'))

if __name__=='__main__':unittest.main()
