import copy
import csv
import json
import tempfile
import unittest
from pathlib import Path

from dev_cycle_v18 import (ROOT, BASELINE, CASES, digest_reference, read_cases,
                           analyse, run_cycle, _write_csv)


class ReproducibleDevelopmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=read_cases(ROOT/CASES)
        cls.base=json.loads((ROOT/BASELINE).read_text(encoding='utf-8'))

    def test_reference_digest_locked(self):
        self.assertEqual(digest_reference(self.rows),self.base['reference_sha256'])

    def test_original_classification_counts(self):
        result=analyse(self.rows,self.base)
        self.assertEqual((result['matches_internal_labels'],result['differences_internal_labels'],result['technical_unreviewed']), (16,3,5))
        self.assertEqual(len(result['open_cases']),8)
        self.assertTrue(result['baseline_unchanged'])

    def test_human_edits_do_not_change_model_baseline(self):
        rows=copy.deepcopy(self.rows)
        rows[0]['Menschliche Freigabe']='BESTAETIGT'
        rows[0]['Notiz']='Geprueft von extern'
        self.assertEqual(digest_reference(rows),self.base['reference_sha256'])

    def test_changed_classification_blocks_regression(self):
        rows=copy.deepcopy(self.rows)
        rows[0]['KI-Kontextkategorie']='METHODE'
        self.assertFalse(analyse(rows,self.base)['baseline_unchanged'])

    def test_changed_scenario_label_blocks_regression(self):
        rows=copy.deepcopy(self.rows)
        rows[0]['Szenario-Erwartung']='METHODE'
        self.assertFalse(analyse(rows,self.base)['baseline_unchanged'])

    def test_added_unknown_is_valid_abstention_not_api_error(self):
        rows=copy.deepcopy(self.rows)
        rows[0]['KI-Kontextkategorie']='UNKLAR'
        rows[0]['KI-Begruendung']='Fachlicher Kontext fehlt.'
        result=analyse(rows,self.base)
        self.assertEqual(result['semantic_abstentions'],1)
        self.assertEqual(result['technical_unreviewed'],5)

    def test_api_error_remains_technical_unreviewed(self):
        self.assertTrue(all(x['kind']=='TECHNISCH_UNBEWERTET' for x in analyse(self.rows,self.base)['open_cases'] if x['id']>='QA15-020'))

    def test_empty_id_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'a.csv'
            with (ROOT/CASES).open(encoding='utf-8-sig',newline='') as f:
                rows=list(csv.DictReader(f,delimiter=';'))
            rows[0]['Test-ID']=''
            with p.open('w',encoding='utf-8-sig',newline='') as f:
                w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter=';')
                w.writeheader();w.writerows(rows)
            with self.assertRaises(ValueError):read_cases(p)

    def test_invalid_label_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'a.csv'
            with (ROOT/CASES).open(encoding='utf-8-sig',newline='') as f:
                rows=list(csv.DictReader(f,delimiter=';'))
            rows[0]['KI-Kontextkategorie']='VERIFIZIERT'
            with p.open('w',encoding='utf-8-sig',newline='') as f:
                w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter=';')
                w.writeheader();w.writerows(rows)
            with self.assertRaises(ValueError):read_cases(p)

    def test_untrusted_spreadsheet_formula_escaped(self):
        item=analyse(self.rows,self.base)['open_cases'][0].copy()
        item['text']='=DANGEROUS()'
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'o.csv';_write_csv(p,[item])
            with p.open(encoding='utf-8-sig',newline='') as f:
                x=next(csv.DictReader(f,delimiter=';'))
            self.assertTrue(x['text'].startswith("'="))

    def test_do_not_allow_release_based_only_on_successful_offline_cases(self):
        # Disable tests: even valid CSV/baseline must never imply release.
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'evaluation').mkdir()
            (root/'reports').mkdir()
            (root/BASELINE).write_bytes((ROOT/BASELINE).read_bytes())
            (root/CASES).write_bytes((ROOT/CASES).read_bytes())
            result=run_cycle(root,do_tests=False)
            self.assertEqual(result['technical_candidate_gate'],'BLOCK')
            self.assertEqual(result['external_release_decision'],'HOLD_FOR_HUMAN_AND_INDEPENDENT_REVIEW')
            self.assertEqual(result['api_calls_executed'],0)
            self.assertFalse(result['automatic_publication'])
            self.assertTrue((root/'reports/ENTWICKLUNGSZYKLUS_1_8.html').is_file())
            self.assertTrue((root/'reports/OFFENE_FRAGEN_1_8.csv').is_file())

    def test_no_input_file_modification(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'evaluation').mkdir()
            (root/'reports').mkdir()
            (root/BASELINE).write_bytes((ROOT/BASELINE).read_bytes())
            original=(ROOT/CASES).read_bytes()
            (root/CASES).write_bytes(original)
            run_cycle(root,do_tests=False)
            self.assertEqual((root/CASES).read_bytes(),original)


if __name__=='__main__':unittest.main()

class FrozenBaselineIntegrityTests(unittest.TestCase):
    def test_changed_baseline_file_prevents_pass(self):
        from dev_cycle_v18 import ROOT, BASELINE, CASES, run_cycle
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'evaluation').mkdir();(root/'reports').mkdir()
            ref=json.loads((ROOT/BASELINE).read_text(encoding='utf-8'))
            ref['reference_sha256']='0'*64
            (root/BASELINE).write_text(json.dumps(ref),encoding='utf-8')
            (root/CASES).write_bytes((ROOT/CASES).read_bytes())
            with self.assertRaises(ValueError):run_cycle(root,do_tests=False)
