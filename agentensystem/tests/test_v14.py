import csv
from pathlib import Path
import tempfile
import unittest
import robustness_lab as rb
import improvement_agent as ia

class RobustnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=rb.read_scenarios(rb.INPUT)
    def test_exactly_40_new_examples(self):
        self.assertEqual(len(self.rows),40)
        self.assertEqual(len(set(r['Test-ID'] for r in self.rows)),40)
    def test_label_not_leaked(self):
        for r in self.rows:
            other=dict(r)
            other[rb.EXPECT]='KEIN_SPEZIELLER_HINWEIS' if r[rb.EXPECT]!='KEIN_SPEZIELLER_HINWEIS' else 'META'
            other[rb.MANUAL]='BESTAETIGT'
            self.assertEqual(ia.proposed_issue(r),ia.proposed_issue(other))
    def test_rule_is_not_retrained(self):
        self.assertEqual(ia.proposed_issue({'Aussage':'Keine Quelle belegt diesen Anspruch.','Quellen-ID':'S01','Automatischer Suchstatus':'NORMAL'}),'PAUSCHALE_ABSENZ')
    def test_counts_are_consistent(self):
        results=rb.evaluate(self.rows)
        self.assertEqual(results['gesamt'],40)
        self.assertEqual(sum(v['gesamt'] for v in results['pro_kategorie'].values()),40)
        self.assertEqual(sum(d['Ergebnis']=='TREFFER_IM_SYNTHETISCHEN_TEST' for d in results['details']),results['szenario_treffer'])
    def test_no_auto_approval_and_preserve_annotated_csv(self):
        with tempfile.TemporaryDirectory() as td:
            dest=Path(td)
            manual=dest/'MENSCHLICHE_PRUEFUNG_40_FAELLE.csv'
            manual.write_text('ECHTE NOTIZEN',encoding='utf-8')
            result=rb.export(rb.evaluate(self.rows),dest)
            self.assertEqual(manual.read_text('utf-8'),'ECHTE NOTIZEN')
            self.assertTrue((dest/'ROBUSTHEITSTEST.html').is_file())
            self.assertEqual(result['gesamt'],40)
            self.assertTrue(all(r['Menschliche Bewertung']=='OFFEN' for r in result['details']))
    def test_invalid_label_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'x.csv'
            with p.open('w',encoding='utf-8',newline='') as f:
                wr=csv.DictWriter(f,fieldnames=self.rows[0].keys(),delimiter=';')
                wr.writeheader()
                row=dict(self.rows[0]);row[rb.EXPECT]='FREIGEGEBEN';wr.writerow(row)
            with self.assertRaises(ValueError):rb.read_scenarios(p)
    def test_html_escaped(self):
        self.assertIn('&lt;script&gt;',rb.esc('<script>'))
    def test_csv_formula_escape(self):
        self.assertTrue(ia.prevent_excel_formula('=2+2').startswith("'"))
    def test_existing_legacy_report_not_touched(self):
        with tempfile.TemporaryDirectory() as td:
            dest=Path(td);legacy=dest/'letzter_bericht.html'
            legacy.write_text('DONOTTOUCH',encoding='utf-8')
            rb.export(rb.evaluate(self.rows),dest)
            self.assertEqual(legacy.read_text('utf-8'),'DONOTTOUCH')
if __name__=='__main__':unittest.main()
