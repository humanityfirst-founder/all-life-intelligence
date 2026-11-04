"""Nur Offline-Tests: der Verbesserungsmodul darf keinerlei externe Aktion auslösen."""
import csv
from io import StringIO
from pathlib import Path
import tempfile
import unittest
import improvement_agent as ia

class ImprovementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=ia.load_rows(ia.EXAMPLE)

    def test_25_known_examples(self):
        self.assertEqual(len(self.rows),25)
        self.assertEqual(len(set(r['Fall-ID'] for r in self.rows)),25)

    def test_premature_approval_never_created(self):
        stats=ia.classify_coverage(self.rows)
        self.assertEqual(stats['wissenschaftliche_belege_automatisch_bestaetigt'],0)
        self.assertEqual(stats['menschliche_freigaben_vom_programm'],0)
        self.assertEqual(stats['vorlaeufige_referenzhinweise'],11)

    def test_new_rules_detect_known_risk_categories(self):
        stats=ia.classify_coverage(self.rows)
        self.assertEqual(stats['baseline_wiedergefunden'],4)
        self.assertEqual(stats['regelvorschlag_wiedergefunden'],11)

    def test_predictions_never_read_reference_labels(self):
        original=self.rows[19]
        changed=dict(original)
        changed[ia.LABEL_COL]='VORLAEUFIG_GESTUETZT'
        changed[ia.MANUAL_COL]='GESTUETZT'
        self.assertEqual(ia.proposed_issue(original),ia.proposed_issue(changed))

    def test_meta_marked(self):
        self.assertEqual(ia.proposed_issue(self.rows[7]),'META')

    def test_absence_marked(self):
        self.assertEqual(ia.proposed_issue(self.rows[19]),'PAUSCHALE_ABSENZ')

    def test_methodological_comment_marked(self):
        self.assertEqual(ia.proposed_issue(self.rows[4]),'METHODE')

    def test_source_domain_flag(self):
        self.assertEqual(ia.proposed_issue(self.rows[24]),'DOMAENENFEHLER')

    def test_no_domain_warning_on_valid_ai_consciousness(self):
        self.assertEqual(ia.proposed_issue(self.rows[3]),'KEIN_SPEZIELLER_HINWEIS')

    def test_never_change_or_replace_input_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            inp=Path(tmp)/'dataset.csv'; inp.write_bytes(ia.EXAMPLE.read_bytes())
            initial=inp.read_bytes()
            dest=Path(tmp)/'results'
            ia.write_results(ia.load_rows(inp),dest)
            self.assertEqual(inp.read_bytes(),initial)
            self.assertTrue((dest/'VERBESSERUNGSANALYSE.html').is_file())
            self.assertTrue((dest/'VERBESSERUNGSVORSCHLAEGE.json').is_file())
            self.assertTrue((dest/'ENTWICKLUNGSPLAN.md').is_file())
            self.assertTrue((dest/'VERGLEICH_25_FAELLE.csv').is_file())
            self.assertNotIn('manual_approval', (dest/'VERBESSERUNGSVORSCHLAEGE.json').read_text('utf-8'))

    def test_existing_files_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)
            prior=dest/'letzter_bericht.json'; prior.write_text('KEEP',encoding='utf-8')
            manual=dest/'PRUEFLISTE.csv'; manual.write_text('MANUAL',encoding='utf-8')
            ia.write_results(self.rows,dest)
            self.assertEqual(prior.read_text('utf-8'),'KEEP')
            self.assertEqual(manual.read_text('utf-8'),'MANUAL')

    def test_formula_escape(self):
        for v in ('=1+1','+2','@cmd','\t=1','-3'):
            self.assertTrue(ia.prevent_excel_formula(v).startswith("'"))
        self.assertEqual(ia.prevent_excel_formula('normal'),'normal')

    def test_html_escaping(self):
        self.assertEqual(ia.esc('<script>'), '&lt;script&gt;')

    def test_duplicate_ids_rejected(self):
        text=ia.EXAMPLE.read_text(encoding='utf-8-sig')
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'cases.csv'
            r=list(csv.DictReader(StringIO(text),delimiter=';'))
            r[1]['Fall-ID']=r[0]['Fall-ID']
            with p.open('w',encoding='utf-8',newline='') as f:
                w=csv.DictWriter(f,fieldnames=r[0].keys(),delimiter=';')
                w.writeheader(); w.writerows(r)
            with self.assertRaises(ValueError):ia.load_rows(p)

    def test_missing_input_columns_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'bad.csv';p.write_text('x;y\na;b\n',encoding='utf-8')
            with self.assertRaises(ValueError):ia.load_rows(p)

    def test_proposals_never_contain_code_patches(self):
        for p in ia.PROPOSALS:
            self.assertIn('id',p)
            self.assertNotIn('patch',p)

if __name__=='__main__': unittest.main()
