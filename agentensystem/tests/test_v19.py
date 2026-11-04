import copy
import csv
import json
import tempfile
import unittest
from pathlib import Path

from research_board_v19 import (ROOT, CASES, BASELINE, REPORT_NAME, ROLES,
                                _require_original_evidence, build_council,
                                write_board_outputs, run_council, _escape_csv)


class ResearchCouncilTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows, cls.baseline = _require_original_evidence(ROOT)

    def test_four_separate_roles_present(self):
        board = build_council(self.rows, self.baseline)
        self.assertEqual(tuple(board['role_reports']), ROLES)
        self.assertEqual(board['agent_roles_executed_as_language_models'], 0)

    def test_frozen_input_counts(self):
        c = build_council(self.rows, self.baseline)['case_counts']
        self.assertEqual((c['total'],c['internal_matches'],c['disagreements'],c['unreviewed']), (24,16,3,5))

    def test_security_boundaries_in_board(self):
        b=build_council(self.rows,self.baseline)
        self.assertEqual(b['api_calls_executed'],0)
        self.assertEqual(b['automatic_code_changes'],0)
        self.assertFalse(b['automatic_publication'])
        self.assertEqual(b['release_decision'],'HOLD_FOR_HUMAN_AND_INDEPENDENT_REVIEW')
        self.assertEqual(b['case_counts']['automatically_verified_source_claims'],0)

    def test_role_specific_evidence(self):
        b=build_council(self.rows,self.baseline)
        a1=b['role_reports']['A1']
        self.assertEqual(len(a1['case_ids']),5)
        a2=b['role_reports']['A2']
        self.assertTrue('QA15-022' in a2['case_ids'])
        a6=b['role_reports']['A6']
        self.assertEqual(set(a6['case_ids']),{'QA15-013','QA15-014','QA15-018'})

    def test_no_linguistic_model_claims(self):
        b=build_council(self.rows,self.baseline)
        for r in b['role_reports'].values():
            self.assertEqual(r['evidence_type'],'DETERMINISTISCHE_DATEIAUSWERTUNG')
            self.assertFalse(r['independent_human_review'])
            self.assertFalse(r['source_verified'])

    def test_acceptance_criteria_for_every_mission(self):
        b=build_council(self.rows,self.baseline)
        self.assertEqual(len(b['backlog']),3)
        self.assertTrue(all(x['requires_approval'] for x in b['backlog']))
        self.assertTrue(all(x['status']=='VORSCHLAG' for x in b['backlog']))
        self.assertTrue(all(len(x['acceptance'])>80 for x in b['backlog']))

    def test_input_is_not_modified_by_board(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/'evaluation').mkdir()
            (root/'reports').mkdir()
            (root/BASELINE).write_bytes((ROOT/BASELINE).read_bytes())
            (root/CASES).write_bytes((ROOT/CASES).read_bytes())
            old=(root/CASES).read_bytes()
            b=run_council(root,do_tests=False)
            self.assertEqual(old,(root/CASES).read_bytes())
            self.assertEqual(b['technical_candidate_gate'],'BLOCK')
            self.assertEqual((root/'reports'/(REPORT_NAME+'.json')).exists(),True)

    def test_bad_baseline_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'evaluation').mkdir();(root/'reports').mkdir()
            baseline=copy.deepcopy(self.baseline)
            baseline['reference_sha256']='0'*64
            (root/BASELINE).write_text(json.dumps(baseline),encoding='utf-8')
            (root/CASES).write_bytes((ROOT/CASES).read_bytes())
            with self.assertRaises(ValueError):run_council(root,do_tests=False)

    def test_tampering_with_context_label_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'evaluation').mkdir();(root/'reports').mkdir()
            (root/BASELINE).write_bytes((ROOT/BASELINE).read_bytes())
            rows=copy.deepcopy(self.rows)
            rows[0]['KI-Kontextkategorie']='METHODE'
            with (root/CASES).open('w',encoding='utf-8-sig',newline='') as f:
                writer=csv.DictWriter(f,delimiter=';',fieldnames=list(rows[0]))
                writer.writeheader();writer.writerows(rows)
            with self.assertRaises(ValueError):run_council(root,do_tests=False)

    def test_csv_formula_injection_defended(self):
        self.assertTrue(_escape_csv('=HYPERLINK("x")').startswith("'="))
        self.assertTrue(_escape_csv(' +2+2').startswith("'"))
        self.assertEqual(_escape_csv('normal'),'normal')

    def test_html_escaped(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            b=build_council(self.rows,self.baseline)
            b['role_reports']['A1']['finding']='<script>alert(1)</script>'
            write_board_outputs(root,b)
            s=(root/'reports'/(REPORT_NAME+'.html')).read_text(encoding='utf-8')
            self.assertNotIn('<script>',s)
            self.assertIn('&lt;script&gt;',s)

    def test_report_explicitly_not_real_agents(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            b=build_council(self.rows,self.baseline)
            write_board_outputs(root,b)
            s=(root/'reports'/(REPORT_NAME+'.html')).read_text(encoding='utf-8')
            self.assertIn('keine echten separaten Modellagenten',s)
            self.assertIn('keine unabhaengige Fachvalidierung',s)

    def test_deterministic_order_of_reports(self):
        b1=build_council(self.rows,self.baseline)
        b2=build_council(self.rows,self.baseline)
        self.assertEqual(b1,b2)

    def test_not_allow_unverified_human_review(self):
        rows=copy.deepcopy(self.rows)
        rows[0]['Menschliche Freigabe']='BESTAETIGT'
        with self.assertRaises(ValueError):build_council(rows,self.baseline)

    def test_no_new_api_key_output(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            b=build_council(self.rows,self.baseline)
            write_board_outputs(root,b)
            s=(root/'reports'/(REPORT_NAME+'.json')).read_text(encoding='utf-8')
            self.assertNotIn('OPENAI_API_KEY',s)
            self.assertEqual(json.loads(s)['api_calls_executed'],0)

if __name__=='__main__':unittest.main()
